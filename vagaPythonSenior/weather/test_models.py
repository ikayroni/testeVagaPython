import pytest
from django.test import TestCase
from django.utils import timezone
from .models import WeatherQuery


class WeatherQueryModelTest(TestCase):
    """
    Testes unitários para o modelo WeatherQuery
    """
    
    def setUp(self):
        """
        Configuração inicial para os testes
        """
        self.weather_data = {
            'city': 'São Paulo',
            'country': 'BR',
            'temperature': 25.5,
            'feels_like': 27.2,
            'humidity': 65,
            'pressure': 1013,
            'description': 'Poucas nuvens',
            'icon': '02d',
            'wind_speed': 3.5,
            'wind_direction': 180,
            'visibility': 10000,
            'uv_index': 5.2,
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0 Test Browser'
        }
    
    def test_create_weather_query(self):
        """
        Testa a criação de uma consulta meteorológica
        """
        query = WeatherQuery.objects.create(**self.weather_data)
        
        self.assertEqual(query.city, 'São Paulo')
        self.assertEqual(query.country, 'BR')
        self.assertEqual(query.temperature, 25.5)
        self.assertEqual(query.feels_like, 27.2)
        self.assertEqual(query.humidity, 65)
        self.assertEqual(query.pressure, 1013)
        self.assertEqual(query.description, 'Poucas nuvens')
        self.assertEqual(query.icon, '02d')
        self.assertEqual(query.wind_speed, 3.5)
        self.assertEqual(query.wind_direction, 180)
        self.assertEqual(query.visibility, 10000)
        self.assertEqual(query.uv_index, 5.2)
        self.assertEqual(query.ip_address, '192.168.1.1')
        self.assertEqual(query.user_agent, 'Mozilla/5.0 Test Browser')
        self.assertIsNotNone(query.query_timestamp)
    
    def test_weather_query_str_representation(self):
        """
        Testa a representação string do modelo
        """
        query = WeatherQuery.objects.create(**self.weather_data)
        expected_str = f"São Paulo, BR - 25.5°C ({query.query_timestamp.strftime('%d/%m/%Y %H:%M')})"
        self.assertEqual(str(query), expected_str)
    
    def test_formatted_temperature_property(self):
        """
        Testa a propriedade formatted_temperature
        """
        query = WeatherQuery.objects.create(**self.weather_data)
        self.assertEqual(query.formatted_temperature, "25.5°C")
    
    def test_formatted_feels_like_property(self):
        """
        Testa a propriedade formatted_feels_like
        """
        query = WeatherQuery.objects.create(**self.weather_data)
        self.assertEqual(query.formatted_feels_like, "27.2°C")
    
    def test_weather_query_ordering(self):
        """
        Testa se as consultas são ordenadas por timestamp decrescente
        """
        # Cria primeira consulta
        query1 = WeatherQuery.objects.create(**self.weather_data)
        
        # Cria segunda consulta
        data2 = self.weather_data.copy()
        data2['city'] = 'Rio de Janeiro'
        query2 = WeatherQuery.objects.create(**data2)
        
        queries = WeatherQuery.objects.all()
        self.assertEqual(queries[0], query2)  # Mais recente primeiro
        self.assertEqual(queries[1], query1)
    
    def test_weather_query_optional_fields(self):
        """
        Testa criação com campos opcionais vazios
        """
        minimal_data = {
            'city': 'Brasília',
            'country': 'BR',
            'temperature': 22.0,
            'feels_like': 21.5,
            'humidity': 70,
            'pressure': 1015,
            'description': 'Céu limpo',
        }
        
        query = WeatherQuery.objects.create(**minimal_data)
        
        self.assertEqual(query.city, 'Brasília')
        self.assertEqual(query.wind_speed, 0)  # Valor padrão
        self.assertEqual(query.wind_direction, 0)  # Valor padrão
        self.assertEqual(query.visibility, 0)  # Valor padrão
        self.assertEqual(query.uv_index, 0)  # Valor padrão
        self.assertEqual(query.icon, '')  # Campo em branco
        self.assertIsNone(query.ip_address)  # Campo nulo
        self.assertEqual(query.user_agent, '')  # Campo em branco 