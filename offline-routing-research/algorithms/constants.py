"""Mirrors Humanizr routing codes — duplicated here to avoid importing backend."""

DEPARTMENT_CODES: tuple[str, ...] = ("PWD", "SAN", "WSD", "ELEC", "TNT", "PAR", "UNSUPPORTED")

PRIORITIES: tuple[str, ...] = ("low", "medium", "high", "critical")

CATEGORIES: tuple[str, ...] = (
    "road_damage",
    "garbage",
    "water",
    "electricity",
    "traffic",
    "parks",
    "other",
)
