import structlog
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from .models import WeatherQuery

logger = structlog.get_logger(__name__)


@shared_task
def save_weather_query_async(city, country, weather_data, ip_address, user_agent):
    """Salva consulta no histórico"""
    try:
        # Cria a consulta
        query = WeatherQuery.objects.create(
            city=city,
            country=country or '',
            temperature=weather_data.get('temperature', 0),
            description=weather_data.get('description', ''),
            ip_address=ip_address or '',
            user_agent=user_agent or ''
        )
        
        logger.info("Consulta salva", query_id=query.id, city=city)
        
        # Limpa consultas antigas (mantém só 100)
        cleanup_old_queries.delay()
        
        return query.id
        
    except Exception as e:
        logger.error("Erro ao salvar consulta", error=str(e), city=city)
        raise


@shared_task
def cleanup_old_queries():
    """Remove consultas antigas, mantém só as 100 mais recentes"""
    try:
        # Pega as 100 mais recentes
        keep_ids = WeatherQuery.objects.order_by('-created_at')[:100].values_list('id', flat=True)
        
        # Remove as antigas
        deleted_count, _ = WeatherQuery.objects.exclude(id__in=list(keep_ids)).delete()
        
        if deleted_count > 0:
            logger.info("Consultas antigas removidas", count=deleted_count)
        
        return deleted_count
        
    except Exception as e:
        logger.error("Erro na limpeza", error=str(e))
        raise


@shared_task
def health_check():
    """Task de health check para monitoramento"""
    try:
        # Testa banco de dados
        count = WeatherQuery.objects.count()
        
        logger.info("Health check ok", total_queries=count)
        
        return {
            'status': 'ok',
            'total_queries': count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Health check falhou", error=str(e))
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        } 