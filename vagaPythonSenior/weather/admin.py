from django.contrib import admin
from .models import WeatherQuery


@admin.register(WeatherQuery)
class WeatherQueryAdmin(admin.ModelAdmin):
    """
    Admin para consultas meteorológicas
    """
    list_display = [
        'city',
        'country',
        'formatted_temperature',
        'formatted_feels_like',
        'humidity',
        'description',
        'query_timestamp',
        'ip_address'
    ]
    
    list_filter = [
        'country',
        'query_timestamp',
    ]
    
    search_fields = [
        'city',
        'country',
        'description',
        'ip_address'
    ]
    
    readonly_fields = [
        'query_timestamp',
        'formatted_temperature',
        'formatted_feels_like'
    ]
    
    ordering = ['-query_timestamp']
    
    date_hierarchy = 'query_timestamp'
    
    fieldsets = (
        ('Localização', {
            'fields': ('city', 'country')
        }),
        ('Dados Meteorológicos', {
            'fields': (
                'temperature', 'formatted_temperature',
                'feels_like', 'formatted_feels_like',
                'humidity', 'pressure',
                'description', 'icon',
                'wind_speed', 'wind_direction',
                'visibility', 'uv_index'
            )
        }),
        ('Metadados', {
            'fields': ('query_timestamp', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        })
    )
    
    list_per_page = 25
