import logging
from dataclasses import dataclass
from decimal import Decimal

import requests

logger = logging.getLogger('pharmacy.api')

FRANKFURTER_URL = 'https://api.frankfurter.app/latest'
NBRB_USD_URL = 'https://www.nbrb.by/api/exrates/rates/USD?parammode=2'
EXCHANGERATE_API_URL = 'https://api.exchangerate-api.com/v4/latest/USD'


@dataclass
class ExchangeRates:
    base: str
    rates: dict
    ok: bool = True
    error: str = ''
    date: str = ''
    sources: str = ''


def _fetch_usd_byn_nbrb():
    """Официальный курс USD→BYN (Нацбанк РБ)."""
    response = requests.get(NBRB_USD_URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    rate = Decimal(str(data['Cur_OfficialRate']))
    scale = Decimal(str(data.get('Cur_Scale', 1)))
    return rate / scale, data.get('Date', '')


def _fetch_usd_byn_fallback():
    """Резервный курс USD→BYN (exchangerate-api.com)."""
    response = requests.get(EXCHANGERATE_API_URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    return Decimal(str(data['rates']['BYN'])), data.get('date', '')


def fetch_exchange_rates(base='USD', targets=('BYN', 'EUR')):
    """
    Курсы валют: BYN — НБРБ (или резервный API), EUR — Frankfurter.
    """
    rates = {}
    sources = []
    date_str = ''
    errors = []

    if 'BYN' in targets:
        try:
            byn_rate, byn_date = _fetch_usd_byn_nbrb()
            rates['BYN'] = byn_rate
            date_str = byn_date
            sources.append('НБРБ')
        except requests.RequestException as exc:
            logger.warning('NBRB API error: %s', exc)
            try:
                byn_rate, byn_date = _fetch_usd_byn_fallback()
                rates['BYN'] = byn_rate
                date_str = byn_date
                sources.append('exchangerate-api.com')
            except requests.RequestException as exc2:
                logger.warning('BYN fallback API error: %s', exc2)
                errors.append(f'BYN: {exc}; резерв: {exc2}')

    other = [t for t in targets if t != 'BYN']
    if other:
        params = {'from': base, 'to': ','.join(other)}
        try:
            response = requests.get(FRANKFURTER_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            for code, rate in data.get('rates', {}).items():
                rates[code] = Decimal(str(rate))
            if not date_str:
                date_str = data.get('date', '')
            sources.append('Frankfurter')
        except requests.RequestException as exc:
            logger.warning('Frankfurter API error: %s', exc)
            errors.append(f'Frankfurter: {exc}')

    if rates:
        return ExchangeRates(
            base=base,
            rates=rates,
            date=date_str,
            sources=', '.join(sources),
        )
    return ExchangeRates(
        base=base,
        rates={},
        ok=False,
        error='; '.join(errors) or 'Курсы недоступны',
    )
