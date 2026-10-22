"""
Geographic calculation utilities for MediChain.

Provides distance computation, coordinate encoding/decoding for Solidity
smart contracts (int256 scaled by 1e6), and a simple bounding-box check
for Indian territory.

This module intentionally depends only on the Python standard library
(``math``) so it can be imported freely in lightweight workers and
Lambda-style handlers without pulling in heavy geo packages.
"""

import math
from typing import Tuple

# --------------------------------------------------------------------------- #
#  Constants                                                                   #
# --------------------------------------------------------------------------- #

# Mean radius of the Earth in kilometres (WGS-84 derived).
EARTH_RADIUS_KM: float = 6371.0

# Scaling factor used when storing float coordinates as integers on-chain.
# Solidity has no native floating-point type, so we multiply by 1e6 to
# preserve six decimal places of precision (~0.11 m at the equator).
COORD_SCALE_FACTOR: int = 1_000_000

# Approximate bounding box for India (generous margins to include island
# territories such as the Andaman & Nicobar Islands and Lakshadweep).
_INDIA_LAT_MIN: float = 6.0
_INDIA_LAT_MAX: float = 37.5
_INDIA_LNG_MIN: float = 68.0
_INDIA_LNG_MAX: float = 97.5


# --------------------------------------------------------------------------- #
#  Public API                                                                  #
# --------------------------------------------------------------------------- #


def haversine_distance(
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float,
) -> float:
    """Compute the great-circle distance between two points on Earth.

    Uses the Haversine formula, which gives good accuracy for most
    practical distances while remaining computationally inexpensive.

    Parameters
    ----------
    lat1, lng1:
        Latitude and longitude of the first point in **decimal degrees**.
    lat2, lng2:
        Latitude and longitude of the second point in **decimal degrees**.

    Returns
    -------
    float
        Distance between the two points in **kilometres**.
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_lat / 2.0) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return EARTH_RADIUS_KM * c


def coords_to_contract_int(
    lat: float,
    lng: float,
) -> Tuple[int, int]:
    """Convert floating-point coordinates to scaled integers for Solidity.

    Solidity does not support floating-point numbers natively.  This
    function multiplies each coordinate by ``1e6``, rounds, and returns
    the result as a pair of Python ``int`` values that map directly to
    ``int256`` in a smart contract.

    Six decimal places of latitude/longitude precision correspond to
    roughly 0.11 m at the equator, which is more than sufficient for
    supply-chain tracking.

    Parameters
    ----------
    lat:
        Latitude in decimal degrees (e.g. ``28.613939``).
    lng:
        Longitude in decimal degrees (e.g. ``77.209023``).

    Returns
    -------
    tuple[int, int]
        ``(lat_int, lng_int)`` scaled by ``1e6``.

    Examples
    --------
    >>> coords_to_contract_int(28.613939, 77.209023)
    (28613939, 77209023)
    """
    lat_int = int(round(lat * COORD_SCALE_FACTOR))
    lng_int = int(round(lng * COORD_SCALE_FACTOR))
    return lat_int, lng_int


def contract_int_to_coords(
    lat_int: int,
    lng_int: int,
) -> Tuple[float, float]:
    """Convert on-chain scaled integers back to floating-point coordinates.

    This is the inverse of :func:`coords_to_contract_int`.

    Parameters
    ----------
    lat_int:
        Latitude as an integer scaled by ``1e6``.
    lng_int:
        Longitude as an integer scaled by ``1e6``.

    Returns
    -------
    tuple[float, float]
        ``(lat, lng)`` in decimal degrees.

    Examples
    --------
    >>> contract_int_to_coords(28613939, 77209023)
    (28.613939, 77.209023)
    """
    lat = lat_int / COORD_SCALE_FACTOR
    lng = lng_int / COORD_SCALE_FACTOR
    return lat, lng


def is_within_india(lat: float, lng: float) -> bool:
    """Check whether a coordinate falls inside a generous bounding box of India.

    The bounding box is intentionally broad to cover island territories
    (Andaman & Nicobar, Lakshadweep) while still filtering out clearly
    invalid coordinates.  It is **not** a precise border check; use a
    proper geospatial library if you need polygon-level accuracy.

    Parameters
    ----------
    lat:
        Latitude in decimal degrees.
    lng:
        Longitude in decimal degrees.

    Returns
    -------
    bool
        ``True`` if the point lies within the bounding box, ``False``
        otherwise.
    """
    return (
        _INDIA_LAT_MIN <= lat <= _INDIA_LAT_MAX
        and _INDIA_LNG_MIN <= lng <= _INDIA_LNG_MAX
    )
