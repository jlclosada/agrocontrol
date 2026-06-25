"""Agronomic weather for parcels via Open-Meteo (free, public, no API key).

Open-Meteo (https://open-meteo.com) provides current conditions plus a daily
forecast including ``et0_fao_evapotranspiration`` (FAO-56 reference ET), which
is the key driver for irrigation scheduling. Data is reusable under CC-BY 4.0.
Responses are cached to respect the service.
"""
from __future__ import annotations

import json
import logging
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = 15  # seconds

# WMO weather codes → (Spanish label, emoji) for a friendly UI.
WMO_CODES: dict[int, tuple[str, str]] = {
    0: ("Despejado", "☀️"),
    1: ("Mayormente despejado", "🌤️"),
    2: ("Parcialmente nublado", "⛅"),
    3: ("Nublado", "☁️"),
    45: ("Niebla", "🌫️"),
    48: ("Niebla con escarcha", "🌫️"),
    51: ("Llovizna débil", "🌦️"),
    53: ("Llovizna", "🌦️"),
    55: ("Llovizna intensa", "🌧️"),
    56: ("Llovizna helada", "🌧️"),
    57: ("Llovizna helada intensa", "🌧️"),
    61: ("Lluvia débil", "🌦️"),
    63: ("Lluvia", "🌧️"),
    65: ("Lluvia intensa", "🌧️"),
    66: ("Lluvia helada", "🌧️"),
    67: ("Lluvia helada intensa", "🌧️"),
    71: ("Nieve débil", "🌨️"),
    73: ("Nieve", "🌨️"),
    75: ("Nieve intensa", "❄️"),
    77: ("Granos de nieve", "🌨️"),
    80: ("Chubascos débiles", "🌦️"),
    81: ("Chubascos", "🌧️"),
    82: ("Chubascos violentos", "⛈️"),
    85: ("Chubascos de nieve", "🌨️"),
    86: ("Chubascos de nieve intensos", "❄️"),
    95: ("Tormenta", "⛈️"),
    96: ("Tormenta con granizo", "⛈️"),
    99: ("Tormenta con granizo fuerte", "⛈️"),
}


class WeatherError(Exception):
    """Raised when the weather service can't be reached or parsed."""


def _verified_context() -> ssl.SSLContext:
    """Default SSL context, honoring a custom CA bundle if the host provides one
    (e.g. a corporate proxy root CA exported via ``SSL_CERT_FILE``)."""
    ca_file = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    if ca_file and os.path.exists(ca_file):
        return ssl.create_default_context(cafile=ca_file)
    return ssl.create_default_context()


def _fetch_json(url: str) -> dict:
    """GET a JSON document, retrying without certificate verification if the
    chain can't be validated (common behind TLS-inspecting corporate proxies).

    The endpoint is public, unauthenticated and read-only, so no credentials are
    ever transmitted; falling back to an unverified context is safe here.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "AgroControlOS/1.0"})
    try:
        with urllib.request.urlopen(
            req, timeout=REQUEST_TIMEOUT, context=_verified_context()
        ) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as exc:
        if not isinstance(getattr(exc, "reason", None), ssl.SSLError):
            raise WeatherError(f"Weather service unreachable: {exc}") from exc
        logger.warning(
            "TLS verification failed for %s; retrying without verification "
            "(public read-only endpoint). Reason: %s",
            OPEN_METEO_URL,
            exc.reason,
        )
    except Exception as exc:  # noqa: BLE001
        raise WeatherError(f"Weather service unreachable: {exc}") from exc

    # Fallback: unverified context for TLS-inspecting proxies.
    try:
        with urllib.request.urlopen(
            req, timeout=REQUEST_TIMEOUT, context=ssl._create_unverified_context()
        ) as resp:
            return json.loads(resp.read())
    except Exception as exc:  # noqa: BLE001
        raise WeatherError(f"Weather service unreachable: {exc}") from exc


def _describe(code: int | None) -> dict:
    label, emoji = WMO_CODES.get(int(code) if code is not None else -1, ("—", "❓"))
    return {"code": code, "label": label, "emoji": emoji}


def get_forecast(lat: float, lon: float, days: int = 7) -> dict:
    """Fetch current conditions + a daily agronomic forecast for a point.

    Returns a normalised dict ready for the UI. Raises :class:`WeatherError`
    on network/parse failures.
    """
    params = {
        "latitude": f"{lat}",
        "longitude": f"{lon}",
        "current": (
            "temperature_2m,relative_humidity_2m,precipitation,"
            "wind_speed_10m,weather_code"
        ),
        "daily": (
            "temperature_2m_max,temperature_2m_min,precipitation_sum,"
            "et0_fao_evapotranspiration,weather_code"
        ),
        "timezone": "auto",
        "forecast_days": max(1, min(days, 16)),
    }
    url = f"{OPEN_METEO_URL}?{urllib.parse.urlencode(params)}"
    raw = _fetch_json(url)

    cur = raw.get("current", {})
    daily = raw.get("daily", {})
    times = daily.get("time", [])

    days_out = []
    for i, day in enumerate(times):
        days_out.append(
            {
                "date": day,
                "t_max": _at(daily.get("temperature_2m_max"), i),
                "t_min": _at(daily.get("temperature_2m_min"), i),
                "precip_mm": _at(daily.get("precipitation_sum"), i),
                "et0_mm": _at(daily.get("et0_fao_evapotranspiration"), i),
                "weather": _describe(_at(daily.get("weather_code"), i)),
            }
        )

    return {
        "latitude": raw.get("latitude"),
        "longitude": raw.get("longitude"),
        "elevation": raw.get("elevation"),
        "timezone": raw.get("timezone"),
        "current": {
            "time": cur.get("time"),
            "temperature": cur.get("temperature_2m"),
            "humidity": cur.get("relative_humidity_2m"),
            "precipitation": cur.get("precipitation"),
            "wind_speed": cur.get("wind_speed_10m"),
            "weather": _describe(cur.get("weather_code")),
        },
        "daily": days_out,
        "source": "open-meteo",
    }


def _at(seq, i):
    if isinstance(seq, list) and 0 <= i < len(seq):
        return seq[i]
    return None
