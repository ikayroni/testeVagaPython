from django.shortcuts import render
import structlog
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from .services import WeatherService
from .serializers import (
    WeatherRequestSerializer,
    WeatherResponseSerializer,
    WeatherQuerySerializer
)

logger = structlog.get_logger(__name__)


def get_client_ip(request):
    """Pega o IP do cliente - funciona com proxy também"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@swagger_auto_schema(
    method='get',
    operation_description="Busca clima atual de uma cidade",
    operation_summary="Clima atual",
    manual_parameters=[
        openapi.Parameter(
            'city',
            openapi.IN_QUERY,
            description="Nome da cidade",
            type=openapi.TYPE_STRING,
            required=True,
            example="São Paulo"
        ),
        openapi.Parameter(
            'country',
            openapi.IN_QUERY,
            description="Código do país (BR, US, etc)",
            type=openapi.TYPE_STRING,
            required=False,
            example="BR"
        ),
    ],
    responses={
        200: WeatherResponseSerializer,
        400: openapi.Response(description="Parâmetros inválidos"),
        404: openapi.Response(description="Cidade não encontrada"),  
        429: openapi.Response(description="Muitas requisições"),
        500: openapi.Response(description="Erro interno"),
    },
    tags=['Weather']
)
@api_view(['GET'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
@ratelimit(key='ip', rate='60/h', method='GET')
@never_cache
def get_weather(request):
    """Busca clima atual com cache de 10min"""
    try:
        # Valida os parâmetros
        serializer = WeatherRequestSerializer(data=request.GET)
        if not serializer.is_valid():
            logger.warning("Parâmetros inválidos", errors=serializer.errors)
            return Response(
                {
                    'error': 'Parâmetros inválidos',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        city = data['city']
        country = data.get('country')
        
        # Info do cliente
        client_ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        logger.info("Nova consulta", city=city, country=country)
        
        # Busca o clima
        weather_svc = WeatherService()
        result = weather_svc.get_weather(
            city=city,
            country=country,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Resposta
        response_data = WeatherResponseSerializer(result)
        
        logger.info("Consulta ok", city=city, cached=result.get('cached', False))
        
        return Response(response_data.data, status=status.HTTP_200_OK)
        
    except ValueError as e:
        logger.warning("Erro de validação", error=str(e))
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
        
    except Exception as e:
        logger.error("Erro inesperado", error=str(e))
        return Response(
            {'error': 'Erro interno do servidor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description="Histórico das consultas",
    operation_summary="Histórico",
    manual_parameters=[
        openapi.Parameter(
            'limit',
            openapi.IN_QUERY,
            description="Quantas consultas retornar (max 100)",
            type=openapi.TYPE_INTEGER,
            required=False,
            example=10
        ),
    ],
    responses={
        200: WeatherQuerySerializer(many=True),
        400: openapi.Response(description="Parâmetros inválidos"),
        500: openapi.Response(description="Erro interno"),
    },
    tags=['Weather']
)
@api_view(['GET'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def get_history(request):
    """Histórico das consultas meteorológicas"""
    try:
        # Pega o limit
        limit_param = request.GET.get('limit')
        limit = None
        
        if limit_param:
            try:
                limit = int(limit_param)
                if limit <= 0:
                    return Response(
                        {'error': 'Limit deve ser positivo'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                # Max 100 consultas
                if limit > 100:
                    limit = 100
            except ValueError:
                return Response(
                    {'error': 'Limit deve ser um número'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        logger.info("Buscando histórico", limit=limit)
        
        # Busca histórico
        weather_svc = WeatherService()
        history = weather_svc.get_weather_history(limit=limit)
        
        # Serializa
        serializer = WeatherQuerySerializer(history, many=True)
        
        logger.info("Histórico retornado", count=len(history))
        
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error("Erro no histórico", error=str(e))
        return Response(
            {'error': 'Erro interno do servidor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description="Verifica se a API está funcionando",
    operation_summary="Health Check",
    responses={
        200: openapi.Response(
            description="API ok",
            examples={
                "application/json": {
                    "status": "ok",
                    "service": "Weather API",
                    "version": "1.0.0"
                }
            }
        )
    },
    tags=['Health']
)
@api_view(['GET'])
def health_check(request):
    """Verifica se a API está ok"""
    return Response({
        'status': 'ok',
        'service': 'Weather API',
        'version': '1.0.0'
    }, status=status.HTTP_200_OK)
