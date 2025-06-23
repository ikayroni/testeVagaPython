import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
from django.core.cache import cache
from django.conf import settings
from requests.exceptions import HTTPError, Timeout, RequestException

from .services import WeatherService
from .models import WeatherQuery


class WeatherServiceTest(TestCase):
    """
    Testes unitários para o WeatherService
    """
    
    def setUp(self):
        """
        Configuração inicial para os testes
        """
        self.service = WeatherService()
        self.mock_api_response = {
            'name': 'São Paulo',
            'sys': {'country': 'BR'},
            'main': {
                'temp': 25.5,
                'feels_like': 27.2,
                'humidity': 65,
                'pressure': 1013
            },
            'weather': [{
                'description': 'poucas nuvens',
                'icon': '02d'
            }],
            'wind': {
                'speed': 3.5,
                'deg': 180
            },
            'visibility': 10000
        }
        
        # Limpa o cache antes de cada teste
        cache.clear()
    
    def tearDown(self):
        """
        Limpeza após cada teste
        """
        cache.clear()
    
    def test_cache_key_generation(self):
        """
        Testa geração de chave de cache
        """
        # Apenas cidade
        key1 = self.service._make_cache_key('São Paulo', None)
        self.assertEqual(key1, 'weather:são paulo')
        
        # Cidade e país
        key2 = self.service._make_cache_key('São Paulo', 'BR')
        self.assertEqual(key2, 'weather:são paulo:br')
    
    def test_parse_weather_data(self):
        """
        Testa parsing da resposta da API
        """
        parsed_data = self.service._parse_weather_data(self.mock_api_response)
        
        self.assertEqual(parsed_data['city'], 'São Paulo')
        self.assertEqual(parsed_data['country'], 'BR')
        self.assertEqual(parsed_data['temperature'], 25.5)
        self.assertEqual(parsed_data['feels_like'], 27.2)
        self.assertEqual(parsed_data['humidity'], 65)
        self.assertEqual(parsed_data['pressure'], 1013)
        self.assertEqual(parsed_data['description'], 'poucas nuvens')
        self.assertEqual(parsed_data['icon'], '02d')
        self.assertEqual(parsed_data['wind_speed'], 3.5)
        self.assertEqual(parsed_data['wind_direction'], 180)
        self.assertEqual(parsed_data['visibility'], 10000)
        self.assertIn('timestamp', parsed_data)
    
    def test_parse_weather_data_missing_field(self):
        """
        Testa parsing quando campo obrigatório está ausente
        """
        incomplete_response = {'name': 'São Paulo'}
        
        with self.assertRaises(ValueError):
            self.service._parse_weather_data(incomplete_response)
    
    def test_cache_operations(self):
        """
        Testa operações de cache
        """
        city = 'São Paulo'
        country = 'BR'
        
        # Primeiro, não deve ter cache
        with patch.object(self.service, '_fetch_from_api') as mock_fetch:
            mock_fetch.return_value = self.mock_api_response
            result = self.service.get_weather(city, country)
            self.assertFalse(result.get('cached', True))
            mock_fetch.assert_called_once()
        
        # Segunda chamada deve vir do cache
        with patch.object(self.service, '_fetch_from_api') as mock_fetch:
            result = self.service.get_weather(city, country)
            self.assertTrue(result.get('cached', False))
            mock_fetch.assert_not_called()
    
    @patch('weather.services.requests.get')
    def test_fetch_weather_success(self, mock_get):
        """
        Testa busca bem-sucedida da API
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_api_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = self.service._fetch_from_api('São Paulo', 'BR')
        
        self.assertEqual(result['city'], 'São Paulo')
        self.assertEqual(result['country'], 'BR')
        self.assertEqual(result['temperature'], 25.5)
        mock_get.assert_called_once()
    
    @patch('weather.services.requests.get')
    def test_fetch_weather_city_not_found(self, mock_get):
        """
        Testa erro 404 - cidade não encontrada
        """
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        with self.assertRaises(ValueError) as context:
            self.service._fetch_from_api('CidadeInexistente', None)
        
        self.assertIn("não encontrada", str(context.exception))
    
    @patch('weather.services.requests.get')
    def test_fetch_weather_invalid_api_key(self, mock_get):
        """
        Testa erro 401 - API key inválida
        """
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        with self.assertRaises(ValueError) as context:
            self.service._fetch_from_api('São Paulo', None)
        
        self.assertIn("API key inválida", str(context.exception))
    
    @patch('weather.services.requests.get')
    def test_fetch_weather_timeout(self, mock_get):
        """
        Testa timeout na requisição
        """
        mock_get.side_effect = requests.exceptions.Timeout()
        
        with self.assertRaises(ValueError) as context:
            self.service._fetch_from_api('São Paulo', None)
        
        self.assertIn("Timeout", str(context.exception))
    
    @patch('weather.services.requests.get')
    def test_fetch_weather_connection_error(self, mock_get):
        """
        Testa erro de conexão
        """
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        with self.assertRaises(ValueError) as context:
            self.service._fetch_from_api('São Paulo', None)
        
        self.assertIn("conexão", str(context.exception))
    
    def test_fetch_weather_no_api_key(self):
        """
        Testa erro quando API key não está configurada
        """
        self.service.api_key = None
        
        with self.assertRaises(ValueError) as context:
            self.service._fetch_from_api('São Paulo', None)
        
        self.assertIn("API key", str(context.exception))
    
    def test_get_weather_history(self):
        """
        Testa obtenção do histórico de consultas
        """
        # Cria algumas consultas de teste
        for i in range(5):
            WeatherQuery.objects.create(
                city=f'Cidade{i+1}',
                country='BR',
                temperature=20.0 + i,
                feels_like=22.0 + i,
                humidity=60 + i,
                pressure=1010 + i,
                description='teste'
            )
        
        history = self.service.get_weather_history()
        
        self.assertEqual(len(history), 5)
        # Verifica se está ordenado pela data mais recente
        self.assertEqual(history[0].city, 'Cidade5')
    
    def test_get_weather_history_with_limit(self):
        """
        Testa histórico com limite
        """
        # Cria 15 consultas
        for i in range(15):
            WeatherQuery.objects.create(
                city=f'Cidade{i+1}',
                country='BR',
                temperature=20.0 + i,
                feels_like=22.0 + i,
                humidity=60 + i,
                pressure=1010 + i,
                description='teste'
            )
        
        history = self.service.get_weather_history(limit=5)
        
        self.assertEqual(len(history), 5) 