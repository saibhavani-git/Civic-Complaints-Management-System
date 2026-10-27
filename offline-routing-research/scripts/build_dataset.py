"""Generate simulated civic routing dataset (isolated lab). IDs: ORR-####."""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts._paths import DATA_DIR  # noqa: E402
from scripts.generate_images import caption_for, ensure_images  # noqa: E402

random.seed(42)

TEMPLATES: list[tuple[str, str, str, str, str]] = [
    ("Large pothole on main road", "Deep pothole near the bus stop causing two-wheeler accidents.", "PWD", "road_damage", "high"),
    ("Footpath tiles missing", "Elderly residents tripping where tiles broke off after monsoon.", "PWD", "road_damage", "medium"),
    ("Bridge expansion joint gap", "Vehicles bumping at speed on flyover joint.", "PWD", "road_damage", "high"),
    ("Road cave-in near manhole", "Small sinkhole forming; water seeping from edges.", "PWD", "road_damage", "critical"),
    ("Damaged speed breaker", "Concrete crumbled leaving sharp edges.", "PWD", "road_damage", "medium"),
    ("Missing road sign at curve", "No warning sign at blind turn; near-misses daily.", "PWD", "road_damage", "high"),
    ("Streetlight pole dark", "Three consecutive streetlights out after storm.", "PWD", "road_damage", "high"),
    ("Waterlogging on carriageway", "Blocked storm drain; ankle-deep water after rain.", "PWD", "road_damage", "medium"),
    ("Cracked footpath near metro", "Wheelchair users cannot pass.", "PWD", "road_damage", "medium"),
    ("Flyover railing rusted", "Sections of railing loose; debris falling to road below.", "PWD", "road_damage", "high"),
    ("Garbage not collected", "Bin overflowing for a week; smell in market lane.", "SAN", "garbage", "high"),
    ("Illegal dumping of rubble", "Construction debris on vacant plot; stray dogs gathering.", "SAN", "garbage", "medium"),
    ("Dead animal on road", "Carcass not removed for two days.", "SAN", "garbage", "critical"),
    ("Open drain foul smell", "Blocked sewer smell in housing colony.", "SAN", "garbage", "high"),
    ("Plastic burning at night", "Open waste burning; smoke in homes.", "SAN", "garbage", "high"),
    ("Community bin lid missing", "Crows scattering waste across street.", "SAN", "garbage", "low"),
    ("Market waste after festival", "Extra garbage piles not picked up.", "SAN", "garbage", "medium"),
    ("Clogged public toilet block", "Sanitation block unusable; hygiene risk.", "SAN", "garbage", "high"),
    ("Stray cattle near dump site", "Animals feeding on open waste heap.", "SAN", "garbage", "medium"),
    ("Drain silt not cleared", "Monsoon silt blocking outlet; stagnant water.", "SAN", "garbage", "medium"),
    ("Water pipeline burst", "Clean water flooding lane from broken pipe.", "WSD", "water", "critical"),
    ("Low morning water pressure", "Upper floors dry 6–9 AM in apartment block.", "WSD", "water", "high"),
    ("Brown sediment in tap water", "Discolored drinking water entire block.", "WSD", "water", "critical"),
    ("Public tap leaking continuously", "Wasted water running 24 hours near market.", "WSD", "water", "medium"),
    ("Sewage smell in water line", "Foul odor after upstream repair work.", "WSD", "water", "critical"),
    ("Tanker schedule missed", "No municipal tanker despite complaint.", "WSD", "water", "medium"),
    ("Valve chamber flooded", "Underground valve room filled with water.", "WSD", "water", "high"),
    ("Borewell contamination fear", "Milky foam in community borewell sample.", "WSD", "water", "high"),
    ("Pipeline excavation left open", "Trench open for days; safety hazard.", "WSD", "water", "medium"),
    ("Meter reading dispute after leak", "Huge bill after visible leak was fixed.", "WSD", "water", "low"),
    ("Fallen electric wire", "Cable hanging after branch fell; sparks seen.", "ELEC", "electricity", "critical"),
    ("Streetlight flickering", "Loose connection near school gate.", "ELEC", "electricity", "medium"),
    ("Transformer humming loudly", "Abnormal heat and noise from neighborhood transformer.", "ELEC", "electricity", "high"),
    ("Power outage twelve hours", "Whole sector dark; no official update.", "ELEC", "electricity", "high"),
    ("Open junction box", "Meter box cover missing; wires exposed.", "ELEC", "electricity", "critical"),
    ("Voltage fluctuation damaging appliances", "Fridges failing during peak hours.", "ELEC", "electricity", "high"),
    ("Street pole leaning", "Pole tilted after vehicle hit; wires taut.", "ELEC", "electricity", "high"),
    ("Faulty street LED batch", "New LEDs failing within a month.", "ELEC", "electricity", "medium"),
    ("Underground cable fault", "Intermittent outages on one street.", "ELEC", "electricity", "high"),
    ("Illegal hook connection", "Unsafe tapping from pole reported.", "ELEC", "electricity", "medium"),
    ("Traffic signal stuck on red", "Gridlock near school; signal not cycling.", "TNT", "traffic", "high"),
    ("Zebra crossing faded", "Pedestrians crossing blindly at market.", "TNT", "traffic", "medium"),
    ("Illegal parking blocking ambulance", "Cars block hospital emergency lane.", "TNT", "traffic", "critical"),
    ("Damaged traffic barrier", "Barrier bent into oncoming lane.", "TNT", "traffic", "high"),
    ("Bus stop shelter shattered", "Glass shards; commuters on carriageway.", "TNT", "traffic", "medium"),
    ("Wrong-way driving ramp", "Missing one-way sign at slip road.", "TNT", "traffic", "high"),
    ("School zone speed not enforced", "Cars speeding at bell time.", "TNT", "traffic", "high"),
    ("Broken bus route display", "Electronic board blank at stop.", "TNT", "traffic", "low"),
    ("Parking meter not working", "Confusion and double parking.", "TNT", "traffic", "low"),
    ("Auto stand blocking junction", "Autos occupy half the intersection.", "TNT", "traffic", "medium"),
    ("Broken swing in park", "Rusty chain; kids still using equipment.", "PAR", "parks", "high"),
    ("Fallen tree on jogging track", "Large branch after heavy rain.", "PAR", "parks", "medium"),
    ("Dry fountain in central park", "Basin algae; pump not running.", "PAR", "parks", "low"),
    ("Broken park bench splinters", "Unsafe seating for seniors.", "PAR", "parks", "medium"),
    ("Overgrown grass snakes sighted", "Grass waist-high on walking path.", "PAR", "parks", "medium"),
    ("Playground rubber mat torn", "Trip hazard under swings.", "PAR", "parks", "high"),
    ("Park gate lock broken", "Anti-social activity at night.", "PAR", "parks", "medium"),
    ("Dead trees not pruned", "Branches overhanging children's area.", "PAR", "parks", "high"),
    ("Sports court lines faded", "Cannot play organized matches.", "PAR", "parks", "low"),
    ("Public park toilet closed", "Only facility locked for months.", "PAR", "parks", "medium"),
    ("Property tax portal error", "Cannot pay online; not a roads issue.", "UNSUPPORTED", "other", "low"),
    ("Police FIR registration", "Theft at shop; need police not municipality.", "UNSUPPORTED", "other", "medium"),
    ("Airline flight cancelled", "Seeking refund from airline.", "UNSUPPORTED", "other", "low"),
    ("Private school fee dispute", "Not civic infrastructure.", "UNSUPPORTED", "other", "low"),
    ("Neighbor boundary wall dispute", "Need legal mediation.", "UNSUPPORTED", "other", "low"),
    ("Income tax refund pending", "Central tax matter.", "UNSUPPORTED", "other", "low"),
    ("Wedding hall noise past midnight", "Not PWD/SAN routing.", "UNSUPPORTED", "other", "medium"),
    ("Passport office delay", "Not municipal department.", "UNSUPPORTED", "other", "low"),
    # —— Additional templates (major-project scale, 500+ rows) ——
    ("Uneven road resurfacing", "Fresh layer uneven; water pools in wheel tracks.", "PWD", "road_damage", "medium"),
    ("Guard rail missing on bridge", "Long gap with no barrier after accident.", "PWD", "road_damage", "critical"),
    ("Kerbside drain cover stolen", "Open pit dangerous for cyclists at night.", "PWD", "road_damage", "high"),
    ("Hoarding fallen on footpath", "Metal sheet blocking pedestrian access.", "PWD", "road_damage", "high"),
    ("Biomedical waste in open bin", "Syringes visible in general waste pile.", "SAN", "garbage", "critical"),
    ("Food waste rotting near hostel", "Maggots and smell affecting students.", "SAN", "garbage", "high"),
    ("Sweeping not done on market road", "Leaves and plastic piled for days.", "SAN", "garbage", "medium"),
    ("Mosquito breeding in stagnant pool", "Open pool beside garbage dump after rains.", "SAN", "garbage", "high"),
    ("Air valve hissing on main line", "Constant hiss; pressure drop in nearby homes.", "WSD", "water", "high"),
    ("Cloudy water after pipe repair", "Milky water since contractor left site.", "WSD", "water", "high"),
    ("Hand pump dry in slum lane", "Only source dry since Monday.", "WSD", "water", "critical"),
    ("Water tanker queue chaos", "No token system; fights at filling point.", "WSD", "water", "medium"),
    ("Pole-mounted transformer oil leak", "Oil stain and smell near transformer base.", "ELEC", "electricity", "critical"),
    ("Generator noise all night", "Commercial generator violating silence zone.", "ELEC", "electricity", "medium"),
    ("Streetlight on daytime", "Wasteful lighting; possible control fault.", "ELEC", "electricity", "low"),
    ("Earthing fault in park kiosk", "Mild shock reported from metal railing.", "ELEC", "electricity", "critical"),
    ("Pedestrian signal too short", "Seniors cannot cross before red.", "TNT", "traffic", "medium"),
    ("Heavy truck route violation", "Overloaded trucks on residential street at night.", "TNT", "traffic", "high"),
    ("Cycle lane encroached by vendors", "Cycles forced into motor lane.", "TNT", "traffic", "medium"),
    ("Rumble strip worn away", "No speed feedback before school zone.", "TNT", "traffic", "medium"),
    ("Park pond algae bloom", "Green scum; foul smell in evening.", "PAR", "parks", "medium"),
    ("Exercise equipment vandalized", "Bars broken; sharp edges exposed.", "PAR", "parks", "high"),
    ("Irrigation sprinklers broken", "Water spraying on path instead of lawn.", "PAR", "parks", "low"),
    ("Dog bite incident reporting", "Need animal control or police, not roads dept.", "UNSUPPORTED", "other", "medium"),
    ("GST invoice correction", "Business billing issue; not municipal.", "UNSUPPORTED", "other", "low"),
    ("University exam reschedule", "Education board matter.", "UNSUPPORTED", "other", "low"),
]

LANDMARKS = [
    "city hospital", "metro gate 2", "vegetable market", "primary school",
    "community hall", "police station", "railway crossing", "temple square",
    "bus depot", "shopping mall", "office complex", "river bridge",
]
AREAS = [
    "North", "South", "East", "West", "Central", "Lakeview", "Industrial",
    "Dwarka", "Rohini", "Saket", "Karol Bagh",
]
TIME_PHRASES = [
    "Reported yesterday evening.",
    "Issue ongoing for two weeks.",
    "Worsened after last night's rain.",
    "Residents complained multiple times.",
    "Escalated after no response to first complaint.",
    "Logged via citizen portal with photo attached.",
]
REPORTER_OPENINGS = [
    "I am writing to report that ",
    "Residents of our lane noticed ",
    "Since last week we have seen ",
]
IMAGE_RATE = 0.72
TARGET_MIN_RECORDS = 520


def _stratified_split(rows: list[dict]) -> None:
    by_dept: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_dept[r["department_code"]].append(r)
    for items in by_dept.values():
        random.shuffle(items)
        n = len(items)
        n_hold = max(2, int(round(n * 0.12)))
        n_val = max(2, int(round(n * 0.13)))
        for i, row in enumerate(items):
            if i < n_hold:
                row["split"] = "holdout"
            elif i < n_hold + n_val:
                row["split"] = "val"
            else:
                row["split"] = "train"


def main() -> None:
    image_paths = ensure_images()
    rows: list[dict] = []
    n = 0

    for title, desc, dept, cat, pri in TEMPLATES:
        variants = [
            (title, desc),
            (f"{title} — urgent", f"{desc} {random.choice(TIME_PHRASES)}"),
        ]
        for _ in range(5):
            lm, ar = random.choice(LANDMARKS), random.choice(AREAS)
            variants.append(
                (
                    f"{title} near {lm}",
                    f"{desc} Location: {ar} ward, opposite {lm}. {random.choice(TIME_PHRASES)}",
                )
            )
        variants.append(
            (
                title,
                f"{random.choice(REPORTER_OPENINGS)}{desc.lower()} {random.choice(TIME_PHRASES)}",
            )
        )
        for v_title, v_desc in variants:
            n += 1
            has_image = random.random() < IMAGE_RATE and cat in image_paths
            rows.append(
                {
                    "id": f"ORR-{n:04d}",
                    "title": v_title,
                    "description": v_desc,
                    "department_code": dept,
                    "category": cat,
                    "priority": pri,
                    "split": "train",
                    "has_image": has_image,
                    "image_path": image_paths[cat] if has_image else None,
                    "image_caption": caption_for(cat) if has_image else None,
                }
            )

    random.shuffle(rows)
    _stratified_split(rows)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_path = DATA_DIR / "civic_routing_v1.json"
    csv_path = DATA_DIR / "civic_routing_v1.csv"

    with_image = sum(1 for r in rows if r["has_image"])
    splits = defaultdict(int)
    for r in rows:
        splits[r["split"]] += 1

    dept_counts = defaultdict(int)
    for r in rows:
        dept_counts[r["department_code"]] += 1

    payload = {
        "name": "humanizr_civic_routing_sim_v3",
        "version": 3,
        "description": (
            "Simulated multimodal civic complaints for offline ML (500+ labeled samples). "
            "Production Humanizr uses Gemini only — this dataset is isolated research."
        ),
        "department_codes": ["PWD", "SAN", "WSD", "ELEC", "TNT", "PAR", "UNSUPPORTED"],
        "id_format": "ORR-NNNN (offline routing research row id)",
        "ml_protocol": {
            "stratified_by": "department_code",
            "splits": dict(splits),
            "typical_use": "train on train split, tune on val, report final metrics on holdout only",
        },
        "records_by_department": dict(dept_counts),
        "splits": dict(splits),
        "records_with_image": with_image,
        "record_count": len(rows),
        "records": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    fields = [
        "id", "title", "description", "department_code", "category", "priority", "split",
        "has_image", "image_path", "image_caption",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    assert len(rows) >= TARGET_MIN_RECORDS, f"Expected >={TARGET_MIN_RECORDS} rows, got {len(rows)}"
    print(f"Wrote {len(rows)} records -> {json_path}")
    print(f"Splits: {dict(splits)} | with_image: {with_image}")
    print(f"By department: {dict(dept_counts)}")


if __name__ == "__main__":
    main()
