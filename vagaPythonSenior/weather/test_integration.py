import pytest
from unittest.mock import patch, Mock
from django.test import TestCase, override_settings, Client
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.cache import cache
from .models import WeatherQuery


class WeatherAPIIntegrationTest(APITestCase):
    """
    Testes de integração para os endpoints da API de clima
    """
    
    def setUp(self):
        """
        Configuração inicial para os testes
        """
        self.client = Client()
        self.weather_url = reverse('weather:get_weather')
        self.history_url = reverse('weather:get_history')
        self.health_url = reverse('weather:health_check')
        
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
    
    def test_health_check_endpoint(self):
        """
        Testa o endpoint de health check
        """
        response = self.client.get(self.health_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['service'], 'Weather API')
        self.assertEqual(response.data['version'], '1.0.0')
    
    @patch('weather.services.requests.get')
    def test_get_current_weather_success(self, mock_get):
        """
        Testa consulta de clima bem-sucedida
        """
        # Mock da resposta da API
        mock_response = Mock()
        mock_response.json.return_value = self.mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Faz a requisição
        response = self.client.get(self.weather_url, {'city': 'São Paulo', 'country': 'BR'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['city'], 'São Paulo')
        self.assertEqual(response.data['country'], 'BR')
        self.assertEqual(response.data['temperature'], 25.5)
        self.assertEqual(response.data['feels_like'], 27.2)
        self.assertEqual(response.data['humidity'], 65)
        self.assertEqual(response.data['pressure'], 1013)
        self.assertEqual(response.data['description'], 'poucas nuvens')
        self.assertEqual(response.data['icon'], '02d')
        self.assertEqual(response.data['wind_speed'], 3.5)
        self.assertEqual(response.data['wind_direction'], 180)
        self.assertEqual(response.data['visibility'], 10000)
        self.assertFalse(response.data['cached'])
        self.assertIn('timestamp', response.data)
    
    def test_get_current_weather_missing_city(self):
        """
        Testa erro quando cidade não é fornecida
        """
        response = self.client.get(self.weather_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('details', response.data)
    
    def test_get_current_weather_invalid_city(self):
        """
        Testa erro com cidade inválida
        """
        response = self.client.get(self.weather_url, {'city': ''})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_get_current_weather_invalid_country_code(self):
        """
        Testa erro com código de país inválido
        """
        response = self.client.get(self.weather_url, {'city': 'São Paulo', 'country': 'INVALID'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    @patch('weather.services.requests.get')
    def test_get_current_weather_cache_functionality(self, mock_get):
        """
        Testa funcionalidade de cache
        """
        # Mock da resposta da API
        mock_response = Mock()
        mock_response.json.return_value = self.mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Primeira requisição - deve chamar a API
        response1 = self.client.get(self.weather_url, {'city': 'São Paulo', 'country': 'BR'})
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertFalse(response1.data['cached'])
        self.assertEqual(mock_get.call_count, 1)
        
        # Segunda requisição - deve usar cache
        response2 = self.client.get(self.weather_url, {'city': 'São Paulo', 'country': 'BR'})
        
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertTrue(response2.data['cached'])
        # Não deve ter chamado a API novamente
        self.assertEqual(mock_get.call_count, 1)
    
    @patch('weather.services.requests.get')
    @patch('weather.tasks.save_weather_query_async.delay')
    def test_weather_query_saves_to_database(self, mock_task, mock_get):
        """
        Testa se a consulta é salva no banco de dados via Celery
        """
        # Mock da resposta da API
        mock_response = Mock()
        mock_response.json.return_value = self.mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Verifica que não há consultas no banco
        self.assertEqual(WeatherQuery.objects.count(), 0)
        
        # Faz a requisição
        response = self.client.get(self.weather_url, {'city': 'São Paulo', 'country': 'BR'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verifica se a task foi chamada
        self.assertTrue(mock_task.called)
        
        # Verifica os argumentos da task (nova assinatura)
        call_args = mock_task.call_args
        self.assertTrue(len(call_args.args) >= 3)  # city, country, weather_data no mínimo
    
    def test_get_weather_history_empty(self):
        """
        Testa histórico quando não há consultas
        """
        response = self.client.get(self.history_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_get_weather_history_with_data(self):
        """
        Testa histórico com dados
        """
        # Cria algumas consultas de teste
        for i in range(5):
            WeatherQuery.objects.create(
                city=f'Cidade{i}',
                country='BR',
                temperature=20 + i,
                feels_like=22 + i,
                humidity=60 + i,
                pressure=1010 + i,
                description=f'Descrição {i}'
            )
        
        response = self.client.get(self.history_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
        
        # Verifica ordenação (mais recente primeiro)
        self.assertEqual(response.data[0]['city'], 'Cidade4')
        self.assertEqual(response.data[1]['city'], 'Cidade3')
    
    def test_get_weather_history_with_limit(self):
        """
        Testa histórico com limite
        """
        # Cria 5 consultas de teste
        for i in range(5):
            WeatherQuery.objects.create(
                city=f'Cidade{i}',
                country='BR',
                temperature=20 + i,
                feels_like=22 + i,
                humidity=60 + i,
                pressure=1010 + i,
                description=f'Descrição {i}'
            )
        
        # Testa com limite de 3
        response = self.client.get(self.history_url, {'limit': 3})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
    
    def test_get_weather_history_invalid_limit(self):
        """
        Testa histórico com limite inválido
        """
        response = self.client.get(self.history_url, {'limit': 'invalid'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_get_weather_history_negative_limit(self):
        """
        Testa histórico com limite negativo
        """
        response = self.client.get(self.history_url, {'limit': -1})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_get_weather_history_large_limit(self):
        """
        Testa histórico com limite muito grande (deve ser limitado a 100)
        """
        response = self.client.get(self.history_url, {'limit': 200})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Mesmo sem dados, não deve dar erro
    
    @override_settings(OPENWEATHER_API_KEY='')
    def test_get_current_weather_no_api_key(self):
        """
        Testa erro quando API key não está configurada
        """
        response = self.client.get(self.weather_url, {'city': 'São Paulo'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    @patch('weather.services.requests.get')
    def test_rate_limiting(self, mock_get):
        """
        Testa rate limiting básico (este teste é limitado pois não podemos testar o rate limiting real facilmente)
        """
        # Mock da resposta da API
        mock_response = Mock()
        mock_response.json.return_value = self.mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Faz várias requisições rápidas
        for i in range(5):
            response = self.client.get(self.weather_url, {'city': f'Cidade{i}'})
            # As primeiras requisições devem funcionar
            if i < 3:
                self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_endpoint_urls_resolution(self):
        """Testa se as URLs dos endpoints são resolvidas corretamente"""
        self.assertIsNotNone(self.weather_url)
        self.assertIsNotNone(self.history_url)
        self.assertIsNotNone(self.health_url)
        # URLs corretas após as mudanças
        self.assertEqual(self.weather_url, '/api/v1/')
        self.assertEqual(self.history_url, '/api/v1/history/')
        self.assertEqual(self.health_url, '/api/v1/health/') 