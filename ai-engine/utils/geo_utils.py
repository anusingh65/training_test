"""
Geographic calculation utilities for MediChain.

Provides coordinate encoding/decoding for Solidity smart contracts
(int256 scaled by 1e6).
"""

from typing import Tuple

# Scaling factor used when storing float coordinates as integers on-chain.
# Solidity has no native floating-point type, so we multiply by 1e6 to
# preserve six decimal places of precision (~0.11 m at the equator).
COORD_SCALE_FACTOR: int = 1_000_000


def coords_to_contract_int(lat: float, lng: float) -> Tuple[int, int]:
    """Convert floating-point coordinates to scaled integers for Solidity.

    >>> coords_to_contract_int(28.613939, 77.209023)
    (28613939, 77209023)
    """
    lat_int = int(round(lat * COORD_SCALE_FACTOR))
    lng_int = int(round(lng * COORD_SCALE_FACTOR))
    return lat_int, lng_int


def contract_int_to_coords(lat_int: int, lng_int: int) -> Tuple[float, float]:
    """Convert on-chain scaled integers back to floating-point coordinates.

    >>> contract_int_to_coords(28613939, 77209023)
    (28.613939, 77.209023)
    """
    lat = lat_int / COORD_SCALE_FACTOR
    lng = lng_int / COORD_SCALE_FACTOR
    return lat, lng
