"""Public cadastral lookups for parcels.

Resolves a parcel's official geometry, surface and centroid from free, public
Spanish government services so users don't have to draw plots by hand:

* **Catastro INSPIRE WFS** (Dirección General del Catastro) — returns the
  cadastral parcel polygon by ``nationalCadastralReference``. Stable and the
  primary source used here.

The data is public and reusable (attribution: Dirección General del Catastro).
No API key is required. Responses are cached to respect the service.
"""
from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation

CATASTRO_WFS = "https://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx"
CATASTRO_RCCOOR = (
    "https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/"
    "OVCCoordenadas.asmx/Consulta_RCCOOR"
)
REQUEST_TIMEOUT = 20  # seconds

_NS = {
    "gml": "http://www.opengis.net/gml/3.2",
    "cp": "http://inspire.ec.europa.eu/schemas/cp/4.0",
}
_RC_NS = {"c": "http://www.catastro.meh.es/"}


class CadastreError(Exception):
    """Raised when a cadastral reference can't be resolved."""


class CadastreNotFound(CadastreError):
    """Raised when the service returns no matching parcel."""


def _to_decimal(value: str) -> Decimal | None:
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        return None


def _http_get(url: str) -> bytes:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AgroControlOS/1.0"})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return resp.read()
    except Exception as exc:  # noqa: BLE001 - surface a clean error to the API
        raise CadastreError(f"Catastro service unreachable: {exc}") from exc


def _parse_pos_list(text: str) -> list[list[float]]:
    """Convert a GML ``posList`` (``lat lon lat lon ...``) to GeoJSON ``[lon, lat]``.

    Catastro emits EPSG:4326 with lat/lon axis order, so we swap to the
    ``[lon, lat]`` convention used by GeoJSON and most JS map libraries.
    """
    nums = [float(n) for n in text.split()]
    ring: list[list[float]] = []
    for i in range(0, len(nums) - 1, 2):
        lat, lon = nums[i], nums[i + 1]
        ring.append([round(lon, 7), round(lat, 7)])
    return ring


def lookup_by_reference(refcat: str) -> dict:
    """Resolve a cadastral reference to geometry, area and centroid.

    Returns a dict with keys: ``reference``, ``area_ha`` (Decimal), ``polygon``
    (list of ``[lon, lat]``), ``latitude`` and ``longitude`` (Decimal). Raises
    :class:`CadastreNotFound` if there's no match or :class:`CadastreError` on
    network/parse failures.
    """
    refcat = (refcat or "").strip().upper()
    if not refcat:
        raise CadastreError("Empty cadastral reference.")
    # The WFS stored query matches on the 14-char parcel reference.
    refcat = refcat[:14]

    params = {
        "service": "wfs",
        "version": "2.0.0",
        "request": "getfeature",
        "STOREDQUERIE_ID": "GetParcel",
        "refcat": refcat,
        "srsname": "EPSG::4326",
    }
    url = f"{CATASTRO_WFS}?{urllib.parse.urlencode(params)}"

    raw = _http_get(url)

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise CadastreError("Invalid response from Catastro.") from exc

    parcel = root.find(".//cp:CadastralParcel", _NS)
    if parcel is None:
        raise CadastreNotFound(f"No cadastral parcel for reference '{refcat}'.")

    pos_list_el = parcel.find(".//gml:posList", _NS)
    if pos_list_el is None or not pos_list_el.text:
        raise CadastreNotFound("Parcel found but it has no geometry.")
    polygon = _parse_pos_list(pos_list_el.text)

    area_el = parcel.find("cp:areaValue", _NS)
    area_m2 = _to_decimal(area_el.text) if area_el is not None else None
    area_ha = (area_m2 / Decimal(10000)).quantize(Decimal("0.0001")) if area_m2 else None

    lat = lon = None
    point_el = parcel.find(".//cp:referencePoint/gml:Point/gml:pos", _NS)
    if point_el is not None and point_el.text:
        parts = point_el.text.split()
        if len(parts) == 2:
            lat, lon = _to_decimal(parts[0]), _to_decimal(parts[1])
    if lat is None and polygon:
        # Fallback centroid: average of ring vertices.
        lon = Decimal(str(round(sum(p[0] for p in polygon) / len(polygon), 6)))
        lat = Decimal(str(round(sum(p[1] for p in polygon) / len(polygon), 6)))

    ref_el = parcel.find("cp:nationalCadastralReference", _NS)
    reference = ref_el.text if ref_el is not None and ref_el.text else refcat

    return {
        "reference": reference,
        "area_ha": area_ha,
        "polygon": polygon,
        "latitude": lat,
        "longitude": lon,
        "source": "catastro",
    }


def lookup_by_coordinate(lat: float, lon: float) -> dict:
    """Resolve the cadastral parcel at a geographic point (lat/lon, EPSG:4326).

    Used by the interactive map: the user clicks a point, we ask Catastro for
    the reference there, then fetch its full geometry. Raises
    :class:`CadastreNotFound` if there's no parcel at that point.
    """
    params = {
        "SRS": "EPSG:4326",
        "Coordenada_X": f"{lon}",
        "Coordenada_Y": f"{lat}",
    }
    url = f"{CATASTRO_RCCOOR}?{urllib.parse.urlencode(params)}"
    raw = _http_get(url)

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise CadastreError("Invalid response from Catastro.") from exc

    err_el = root.find(".//c:control/c:cuerr", _RC_NS)
    if err_el is not None and (err_el.text or "0") != "0":
        raise CadastreNotFound("No hay parcela catastral en ese punto.")

    pc1 = root.find(".//c:pc/c:pc1", _RC_NS)
    pc2 = root.find(".//c:pc/c:pc2", _RC_NS)
    if pc1 is None or pc2 is None or not pc1.text or not pc2.text:
        raise CadastreNotFound("No hay parcela catastral en ese punto.")

    refcat = f"{pc1.text}{pc2.text}"
    return lookup_by_reference(refcat)

