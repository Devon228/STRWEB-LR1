import logging
from dataclasses import dataclass

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('pharmacy.api')


@dataclass
class WeatherInfo:
    city: str
    temperature: float
    description: str
    humidity: int
    wind_speed: float
    ok: bool = True
    error: str = ''


def fetch_weather(city=None):
    """
    OpenWeatherMap Current Weather API.
    Ключ: OPENWEATHER_API_KEY в переменных окружения.
    """
    city = city or getattr(settings, 'PHARMACY_CITY', 'Minsk')
    api_key = getattr(settings, 'OPENWEATHER_API_KEY', '')
    if not api_key:
        return WeatherInfo(
            city=city,
            temperature=0,
            description='',
            humidity=0,
            wind_speed=0,
            ok=False,
            error='Не задан OPENWEATHER_API_KEY. Получите ключ на openweathermap.org.',
        )
    url = 'https://api.openweathermap.org/data/2.5/weather'
    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric',
        'lang': 'ru',
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return WeatherInfo(
            city=data.get('name', city),
            temperature=round(data['main']['temp'], 1),
            description=data['weather'][0]['description'].capitalize(),
            humidity=data['main']['humidity'],
            wind_speed=round(data['wind'].get('speed', 0), 1),
        )
    except requests.RequestException as exc:
        logger.warning('OpenWeatherMap error: %s', exc)
        return WeatherInfo(
            city=city,
            temperature=0,
            description='',
            humidity=0,
            wind_speed=0,
            ok=False,
            error=f'Ошибка запроса погоды: {exc}',
        )


def get_weather_cached(city=None, ttl=600):
    """Кэшированная погода (по умолчанию 10 мин), для виджета на сайте."""
    city = city or getattr(settings, 'PHARMACY_CITY', 'Minsk')
    cache_key = f'pharmacy_weather_{city.lower()}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    weather = fetch_weather(city)
    cache.set(cache_key, weather, ttl)
    return weather
