"""Create category-themed SVG complaint photos for the offline dataset."""

from __future__ import annotations

from pathlib import Path

from scripts._paths import DATA_DIR

IMAGES_DIR = DATA_DIR / "images"

# category -> (filename stem, short caption for ML metadata)
TEMPLATES: dict[str, tuple[str, str]] = {
    "road_damage": ("road_pothole", "Photo of cracked road and pothole"),
    "garbage": ("sanitation_overflow", "Photo of overflowing municipal waste bin"),
    "water": ("water_leak", "Photo of water leaking from pipe on street"),
    "electricity": ("electric_hazard", "Photo of damaged cable near pole"),
    "traffic": ("traffic_signal", "Photo of traffic signal at junction"),
    "parks": ("park_damage", "Photo of fallen tree branch in park"),
    "other": ("generic_scene", "Photo of street scene"),
}


def _svg_road() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"><rect fill="#64748b" width="400" height="300"/><ellipse cx="200" cy="200" rx="90" ry="40" fill="#1e293b"/><ellipse cx="200" cy="190" rx="55" ry="22" fill="#0f172a"/><text x="200" y="40" text-anchor="middle" fill="#fff" font-size="14">Road damage</text></svg>"""


def _svg_garbage() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"><rect fill="#78716c" width="400" height="300"/><rect x="150" y="100" width="100" height="120" fill="#44403c"/><rect x="140" y="80" width="120" height="30" fill="#292524"/><circle cx="170" cy="200" r="15" fill="#84cc16"/><circle cx="230" cy="210" r="12" fill="#a3e635"/><text x="200" y="40" text-anchor="middle" fill="#fff" font-size="14">Garbage</text></svg>"""


def _svg_water() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"><rect fill="#475569" width="400" height="300"/><path d="M180 120 Q200 80 220 120 L220 220 Q200 250 180 220 Z" fill="#38bdf8"/><ellipse cx="200" cy="240" rx="80" ry="15" fill="#0ea5e9" opacity="0.6"/><text x="200" y="40" text-anchor="middle" fill="#fff" font-size="14">Water leak</text></svg>"""


def _svg_electric() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"><rect fill="#334155" width="400" height="300"/><rect x="190" y="60" width="20" height="180" fill="#57534e"/><path d="M120 140 Q200 100 280 160" stroke="#facc15" stroke-width="6" fill="none"/><text x="200" y="40" text-anchor="middle" fill="#fff" font-size="14">Electric hazard</text></svg>"""


def _svg_traffic() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"><rect fill="#64748b" width="400" height="300"/><rect x="175" y="70" width="50" height="160" fill="#374151"/><circle cx="200" cy="110" r="18" fill="#ef4444"/><circle cx="200" cy="160" r="18" fill="#eab308"/><circle cx="200" cy="210" r="18" fill="#22c55e"/><text x="200" y="40" text-anchor="middle" fill="#fff" font-size="14">Traffic signal</text></svg>"""


def _svg_parks() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"><rect fill="#166534" width="400" height="300"/><rect x="0" y="220" width="400" height="80" fill="#4ade80"/><ellipse cx="120" cy="180" rx="50" ry="70" fill="#15803d"/><rect x="250" y="150" width="100" height="20" fill="#854d0e" transform="rotate(-25 300 160)"/><text x="200" y="40" text-anchor="middle" fill="#fff" font-size="14">Park / tree</text></svg>"""


def _svg_generic() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"><rect fill="#94a3b8" width="400" height="300"/><rect x="80" y="180" width="240" height="8" fill="#64748b"/><text x="200" y="140" text-anchor="middle" fill="#1e293b" font-size="14">Street view</text></svg>"""


BUILDERS = {
    "road_damage": _svg_road,
    "garbage": _svg_garbage,
    "water": _svg_water,
    "electricity": _svg_electric,
    "traffic": _svg_traffic,
    "parks": _svg_parks,
    "other": _svg_generic,
}


def ensure_images() -> dict[str, str]:
    """Write SVGs; return category -> relative path from data/."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    for cat, (stem, _caption) in TEMPLATES.items():
        rel = f"images/{stem}.svg"
        path = DATA_DIR / rel
        if not path.exists():
            path.write_text(BUILDERS[cat](), encoding="utf-8")
        paths[cat] = rel
    return paths


def caption_for(category: str) -> str:
    return TEMPLATES.get(category, TEMPLATES["other"])[1]


if __name__ == "__main__":
    p = ensure_images()
    print(f"Ensured {len(p)} category images under {IMAGES_DIR}")
