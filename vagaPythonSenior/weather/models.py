from django.db import models
from django.utils import timezone


class WeatherQuery(models.Model):
    """
    Modelo para armazenar o histórico de consultas meteorológicas
    """
    city = models.CharField(max_length=100, verbose_name="Cidade")
    country = models.CharField(max_length=2, verbose_name="País")
    temperature = models.FloatField(verbose_name="Temperatura (°C)")
    feels_like = models.FloatField(verbose_name="Sensação Térmica (°C)")
    humidity = models.IntegerField(verbose_name="Umidade (%)")
    pressure = models.IntegerField(verbose_name="Pressão (hPa)")
    description = models.CharField(max_length=200, verbose_name="Descrição")
    icon = models.CharField(max_length=10, verbose_name="Ícone", blank=True)
    wind_speed = models.FloatField(verbose_name="Velocidade do Vento (m/s)", default=0)
    wind_direction = models.IntegerField(verbose_name="Direção do Vento (graus)", default=0)
    visibility = models.IntegerField(verbose_name="Visibilidade (m)", default=0)
    uv_index = models.FloatField(verbose_name="Índice UV", default=0)
    
    # Metadados da consulta
    query_timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Data/Hora da Consulta")
    ip_address = models.GenericIPAddressField(verbose_name="IP do Solicitante", blank=True, null=True)
    user_agent = models.TextField(verbose_name="User Agent", blank=True)
    
    class Meta:
        verbose_name = "Consulta Meteorológica"
        verbose_name_plural = "Consultas Meteorológicas"
        ordering = ['-query_timestamp']
        indexes = [
            models.Index(fields=['-query_timestamp']),
            models.Index(fields=['city']),
        ]

    def __str__(self):
        return f"{self.city}, {self.country} - {self.temperature}°C ({self.query_timestamp.strftime('%d/%m/%Y %H:%M')})"

    @property
    def formatted_temperature(self):
        return f"{self.temperature:.1f}°C"

    @property
    def formatted_feels_like(self):
        return f"{self.feels_like:.1f}°C"
