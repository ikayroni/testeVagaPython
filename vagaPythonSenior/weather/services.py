import json
import requests
import structlog
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from .models import WeatherQuery
from .tasks import save_weather_query_async

logger = structlog.get_logger(__name__)


class WeatherService:
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.cache_timeout = 600  # 10 minutos
    
    def get_weather(self, city, country=None, ip_address=None, user_agent=None):
        """Busca clima com cache"""
        # Chave do cache
        cache_key = self._make_cache_key(city, country)
        
        # Tenta cache primeiro
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info("Cache hit", city=city, country=country)
            cached_data['cached'] = True
            return cached_data
        
        logger.info("Cache miss", city=city, country=country)
        
        # Busca na API
        weather_data = self._fetch_from_api(city, country)
        
        # Salva no cache
        cache.set(cache_key, weather_data, self.cache_timeout)
        logger.info("Dados salvos no cache", city=city, country=country)
        
        # Salva histórico em background
        if ip_address:
            save_weather_query_async.delay(
                city, country, weather_data, ip_address, user_agent
            )
        
        weather_data['cached'] = False
        return weather_data
    
    def _make_cache_key(self, city, country):
        """Cria chave única para cache"""
        if country:
            return f"weather:{city.lower()}:{country.lower()}"
        return f"weather:{city.lower()}"
    
    def _fetch_from_api(self, city, country):
        """Busca dados na API do OpenWeatherMap"""
        if not self.api_key:
            raise ValueError("API key do OpenWeatherMap não configurada")
        
        # Monta URL
        params = {
            'q': f"{city},{country}" if country else city,
            'appid': self.api_key,
            'units': 'metric',
            'lang': 'pt_br'
        }
        
        logger.info("Buscando na API", city=city, country=country, url=self.base_url)
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 404:
                logger.warning("Cidade não encontrada", city=city, country=country)
                raise ValueError(f"Cidade '{city}' não encontrada")
            
            if response.status_code == 401:
                logger.error("API key inválida", city=city, country=country)
                raise ValueError("API key inválida")
            
            response.raise_for_status()
            
            data = response.json()
            logger.info("Dados obtidos com sucesso", city=city, country=country)
            
            return self._parse_weather_data(data)
            
        except requests.exceptions.Timeout:
            logger.error("Timeout na API", city=city, country=country)
            raise ValueError("Timeout ao buscar dados meteorológicos")
            
        except requests.exceptions.ConnectionError:
            logger.error("Erro de conexão", city=city, country=country, error="Connection error")
            raise ValueError("Erro de conexão com a API")
            
        except requests.exceptions.RequestException as e:
            logger.error("Erro na requisição", city=city, country=country, error=str(e))
            raise ValueError(f"Erro ao buscar dados: {str(e)}")
    
    def _parse_weather_data(self, data):
        """Converte dados da API para formato padrão"""
        try:
            return {
                'city': data['name'],
                'country': data['sys']['country'],
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'wind_speed': data['wind']['speed'],
                'wind_direction': data['wind'].get('deg', 0),
                'visibility': data.get('visibility', 0),
                'timestamp': timezone.now().isoformat()
            }
        except KeyError as e:
            logger.error("Erro no parse dos dados", data=data, error=str(e))
            raise ValueError(f"Dados da API incompletos: {str(e)}")
    
    def get_weather_history(self, limit=None):
        """Busca histórico de consultas"""
        if limit is None:
            limit = 10
        
        return WeatherQuery.objects.select_related().order_by('-query_timestamp')[:limit] 