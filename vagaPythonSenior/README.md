# Weather API

API REST para consulta de dados meteorológicos usando OpenWeatherMap.

## Funcionalidades

- ✅ Consulta clima atual por cidade
- ✅ Cache Redis (10 minutos)
- ✅ Histórico das últimas consultas
- ✅ Rate limiting
- ✅ Celery para tasks assíncronas
- ✅ Logs estruturados
- ✅ Documentação Swagger
- ✅ Docker Compose

## Tecnologias

- **Django 4.2** + **DRF**
- **PostgreSQL** (banco de dados)
- **Redis** (cache)
- **Celery** (tasks assíncronas)
- **Docker** (containerização)

## Configuração

### 1. Variáveis de ambiente

Crie um arquivo `.env`:

```bash
# API Key do OpenWeatherMap
OPENWEATHER_API_KEY=sua_api_key_aqui

# Banco de dados
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/1

# Django
DEBUG=1
SECRET_KEY=sua_secret_key
```

### 2. Com Docker (recomendado)

```bash
# Iniciar todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar
docker-compose down
```

### 3. Instalação local

```bash
# Instalar dependências
pip install -r requirements.txt

# Migrações
python manage.py migrate

# Iniciar servidor
python manage.py runserver

# Celery (em outro terminal)
celery -A weather_project worker --loglevel=info
```

## Endpoints

### 🌤️ Consultar clima
```
GET /api/v1/weather/?city=São Paulo&country=BR
```

**Resposta:**
```json
{
    "city": "São Paulo",
    "country": "BR", 
    "temperature": 25.5,
    "feels_like": 27.2,
    "humidity": 65,
    "description": "poucas nuvens",
    "cached": false
}
```

### 📋 Histórico
```
GET /api/v1/weather/history/?limit=10
```

### ❤️ Health Check
```
GET /api/v1/health/
```

## Documentação

- **Swagger UI:** http://localhost:8000/
- **ReDoc:** http://localhost:8000/redoc/

## Testes

```bash
# Rodar todos os testes
python manage.py test

# Com Docker
docker-compose exec web python manage.py test
```

## Cache

- **Redis** com TTL de 10 minutos
- Chave do cache: `weather:{cidade}:{país}`

## Rate Limiting

- **Anônimos:** 100 req/hora
- **Autenticados:** 1000 req/hora

## Logs

Logs estruturados em JSON para facilitar monitoramento:

```json
{
    "level": "info",
    "event": "Nova consulta",
    "city": "São Paulo",
    "country": "BR",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

## Estrutura

```
weather_project/
├── weather/                 # App principal
│   ├── models.py           # Modelo WeatherQuery
│   ├── views.py            # Endpoints da API
│   ├── services.py         # Integração OpenWeatherMap
│   ├── tasks.py            # Tasks Celery
│   ├── serializers.py      # Serializers DRF
│   └── tests/              # Testes
├── docker-compose.yml      # Orquestração
├── Dockerfile             # Imagem da app
└── requirements.txt       # Dependências
```

## TODO

- [ ] Autenticação JWT
- [ ] Métricas Prometheus
- [ ] Deploy Kubernetes
- [ ] Webhooks para alertas 