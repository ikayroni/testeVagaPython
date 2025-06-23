from rest_framework import serializers
from .models import WeatherQuery


class WeatherQuerySerializer(serializers.ModelSerializer):
    """
    Serializer para consultas meteorológicas
    """
    formatted_temperature = serializers.ReadOnlyField()
    formatted_feels_like = serializers.ReadOnlyField()
    
    class Meta:
        model = WeatherQuery
        fields = [
            'id',
            'city',
            'country',
            'temperature',
            'formatted_temperature',
            'feels_like',
            'formatted_feels_like',
            'humidity',
            'pressure',
            'description',
            'icon',
            'wind_speed',
            'wind_direction',
            'visibility',
            'uv_index',
            'query_timestamp',
        ]
        read_only_fields = ['query_timestamp']


class WeatherRequestSerializer(serializers.Serializer):
    """
    Serializer para validar requisições de clima
    """
    city = serializers.CharField(
        max_length=100,
        help_text="Nome da cidade para consulta meteorológica"
    )
    country = serializers.CharField(
        max_length=2,
        required=False,
        help_text="Código do país (ISO 3166-1 alpha-2). Opcional."
    )

    def validate_city(self, value):
        """
        Valida o nome da cidade
        """
        if not value.strip():
            raise serializers.ValidationError("Nome da cidade não pode estar vazio.")
        
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Nome da cidade deve ter pelo menos 2 caracteres.")
            
        return value.strip()

    def validate_country(self, value):
        """
        Valida o código do país
        """
        if value and len(value) != 2:
            raise serializers.ValidationError("Código do país deve ter exatamente 2 caracteres.")
        
        return value.upper() if value else None


class WeatherResponseSerializer(serializers.Serializer):
    """
    Serializer para resposta da API de clima
    """
    city = serializers.CharField()
    country = serializers.CharField()
    temperature = serializers.FloatField()
    feels_like = serializers.FloatField()
    humidity = serializers.IntegerField()
    pressure = serializers.IntegerField()
    description = serializers.CharField()
    icon = serializers.CharField()
    wind_speed = serializers.FloatField()
    wind_direction = serializers.IntegerField()
    visibility = serializers.IntegerField()
    cached = serializers.BooleanField(default=False)
    timestamp = serializers.DateTimeField() 