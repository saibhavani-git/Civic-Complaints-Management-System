"""
Seed departments, demo users (all roles), and sample complaints for local QA.
Idempotent: re-run safe (upserts users by email, complaints by seed_key).

Usage:
  cd backend
  .\\venv\\Scripts\\activate
  python scripts/seed_demo_data.py
  python scripts/seed_demo_data.py --verify   # also hit API smoke tests (API on 8002)
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from app.core.security import hash_password
from app.db.init_db import seed_departments
from app.schemas.complaint import ComplaintStatus

# Local dev passwords only.
# Municipal staff → @civic.gov.in  |  Residents → personal email (Gmail, Yahoo, etc.)
STAFF_PW_ADMIN = "Admin@123"
STAFF_PW_DEPT = "DeptAdmin@123"
STAFF_PW_OFFICER = "Officer@123"
CITIZEN_PW = "Citizen@123"

# Legacy / test accounts — deleted on each seed run (not recreated).
LEGACY_USER_EMAILS: tuple[str, ...] = (
    # Old dept heads
    "deptadmin@civic.gov",
    "pwdadmin@civic.gov",
    # Old officers (role-style names)
    "officer@civic.gov",
    "pwd.officer@civic.gov",
    "san.officer2@civic.gov",
    "saibhavanikokanti112@gmail.com",
    "nishi12@gmail.com",
    # Old citizens & manual test sign-ups
    "citizen@civic.gov",
    "citizen2@civic.gov",
    "citizen3@civic.gov",
    "nishi123@gmail.com",
    "saibhavanikokanti12@gmail.com",
    "testcitizen_hmn@example.com",
    "testuser99@test.com",
    "you@gmail.com",
    "sai12@gmail.com",
    "you1123@gmail.com",
)

DEMO_USERS = [
    # —— System administrators (city-wide) ——
    {
        "email": "arjun.malhotra@civic.gov.in",
        "password": STAFF_PW_ADMIN,
        "full_name": "Arjun Malhotra",
        "role": "admin",
        "phone": "+91 9876500001",
    },
    {
        "email": "nisha.rao@civic.gov.in",
        "password": STAFF_PW_ADMIN,
        "full_name": "Nisha Rao",
        "role": "admin",
        "phone": "+91 9876500002",
    },
    # —— Department heads (dept_admin) ——
    {
        "email": "meera.iyer@civic.gov.in",
        "password": STAFF_PW_DEPT,
        "full_name": "Meera Iyer",
        "role": "dept_admin",
        "department_code": "SAN",
        "phone": "+91 9876510001",
    },
    {
        "email": "vikram.desai@civic.gov.in",
        "password": STAFF_PW_DEPT,
        "full_name": "Vikram Desai",
        "role": "dept_admin",
        "department_code": "SAN",
        "phone": "+91 9876510002",
    },
    {
        "email": "karan.singh@civic.gov.in",
        "password": STAFF_PW_DEPT,
        "full_name": "Karan Singh",
        "role": "dept_admin",
        "department_code": "PWD",
        "phone": "+91 9876520001",
    },
    {
        "email": "anita.khurana@civic.gov.in",
        "password": STAFF_PW_DEPT,
        "full_name": "Anita Khurana",
        "role": "dept_admin",
        "department_code": "PWD",
        "phone": "+91 9876520002",
    },
    {
        "email": "rohit.banerjee@civic.gov.in",
        "password": STAFF_PW_DEPT,
        "full_name": "Rohit Banerjee",
        "role": "dept_admin",
        "department_code": "WSD",
        "phone": "+91 9876530001",
    },
    {
        "email": "sunita.pillai@civic.gov.in",
        "password": STAFF_PW_DEPT,
        "full_name": "Sunita Pillai",
        "role": "dept_admin",
        "department_code": "ELEC",
        "phone": "+91 9876540001",
    },
    {
        "email": "aditya.venkatesh@civic.gov.in",
        "password": STAFF_PW_DEPT,
        "full_name": "Aditya Venkatesh",
        "role": "dept_admin",
        "department_code": "TNT",
        "phone": "+91 9876550001",
    },
    {
        "email": "kavita.menon@civic.gov.in",
        "password": STAFF_PW_DEPT,
        "full_name": "Kavita Menon",
        "role": "dept_admin",
        "department_code": "TNT",
        "phone": "+91 9876550002",
    },
    {
        "email": "gaurav.mehta@civic.gov.in",
        "password": STAFF_PW_DEPT,
        "full_name": "Gaurav Mehta",
        "role": "dept_admin",
        "department_code": "PAR",
        "phone": "+91 9876560001",
    },
    {
        "email": "leela.rajan@civic.gov.in",
        "password": STAFF_PW_DEPT,
        "full_name": "Leela Rajan",
        "role": "dept_admin",
        "department_code": "PAR",
        "phone": "+91 9876560002",
    },
    {
        "email": "manish.gupta@civic.gov.in",
        "password": STAFF_PW_DEPT,
        "full_name": "Manish Gupta",
        "role": "dept_admin",
        "department_code": "WSD",
        "phone": "+91 9876530002",
    },
    {
        "email": "pooja.saxena@civic.gov.in",
        "password": STAFF_PW_DEPT,
        "full_name": "Pooja Saxena",
        "role": "dept_admin",
        "department_code": "ELEC",
        "phone": "+91 9876540002",
    },
    # —— Field officers ——
    {
        "email": "ravi.kumar@civic.gov.in",
        "password": STAFF_PW_OFFICER,
        "full_name": "Ravi Kumar",
        "role": "officer",
        "department_code": "SAN",
        "phone": "+91 9876610001",
        "service_area": "North & central wards — sanitation routes A–D",
    },
    {
        "email": "lakshmi.nair@civic.gov.in",
        "password": STAFF_PW_OFFICER,
        "full_name": "Lakshmi Nair",
        "role": "officer",
        "department_code": "SAN",
        "phone": "+91 9876610002",
        "service_area": "East wards — markets & residential blocks 5–9",
    },
    {
        "email": "imran.sheikh@civic.gov.in",
        "password": STAFF_PW_OFFICER,
        "full_name": "Imran Sheikh",
        "role": "officer",
        "department_code": "PWD",
        "phone": "+91 9876620001",
        "service_area": "Ring Road sector, flyovers, and main arterial roads",
    },
    {
        "email": "deepa.joshi@civic.gov.in",
        "password": STAFF_PW_OFFICER,
        "full_name": "Deepa Joshi",
        "role": "officer",
        "department_code": "PWD",
        "phone": "+91 9876620002",
        "service_area": "Street lighting — zones 1–3, metro corridors",
    },
    {
        "email": "mohit.agarwal@civic.gov.in",
        "password": STAFF_PW_OFFICER,
        "full_name": "Mohit Agarwal",
        "role": "officer",
        "department_code": "WSD",
        "phone": "+91 9876630001",
        "service_area": "Water mains — South Delhi zone 1 (Saket, Hauz Khas)",
    },
    {
        "email": "farhan.ali@civic.gov.in",
        "password": STAFF_PW_OFFICER,
        "full_name": "Farhan Ali",
        "role": "officer",
        "department_code": "ELEC",
        "phone": "+91 9876640001",
        "service_area": "Transformer & outage response — Grid East",
    },
    {
        "email": "sanjay.rawat@civic.gov.in",
        "password": STAFF_PW_OFFICER,
        "full_name": "Sanjay Rawat",
        "role": "officer",
        "department_code": "TNT",
        "phone": "+91 9876650001",
        "service_area": "Traffic signals & junctions — Central and Connaught Place grid",
    },
    {
        "email": "preeti.gautam@civic.gov.in",
        "password": STAFF_PW_OFFICER,
        "full_name": "Preeti Gautam",
        "role": "officer",
        "department_code": "TNT",
        "phone": "+91 9876650002",
        "service_area": "Bus routes, stops, and last-mile parking enforcement — South zone",
    },
    {
        "email": "anjali.deshmukh@civic.gov.in",
        "password": STAFF_PW_OFFICER,
        "full_name": "Anjali Deshmukh",
        "role": "officer",
        "department_code": "PAR",
        "phone": "+91 9876660001",
        "service_area": "Neighbourhood parks & tree maintenance — North Delhi wards",
    },
    {
        "email": "harish.patel@civic.gov.in",
        "password": STAFF_PW_OFFICER,
        "full_name": "Harish Patel",
        "role": "officer",
        "department_code": "PAR",
        "phone": "+91 9876660002",
        "service_area": "Playgrounds, sports courts, and recreation equipment — East zone",
    },
    {
        "email": "naveen.reddy@civic.gov.in",
        "password": STAFF_PW_OFFICER,
        "full_name": "Naveen Reddy",
        "role": "officer",
        "department_code": "WSD",
        "phone": "+91 9876630002",
        "service_area": "Pipeline leaks & valve repairs — North Delhi zone 2",
    },
    {
        "email": "shreya.bhatia@civic.gov.in",
        "password": STAFF_PW_OFFICER,
        "full_name": "Shreya Bhatia",
        "role": "officer",
        "department_code": "ELEC",
        "phone": "+91 9876640002",
        "service_area": "Street cabling & meter complaints — Grid West",
    },
    # —— Citizens (personal email — same as real sign-up) ——
    {
        "email": "priya.sharma@gmail.com",
        "password": CITIZEN_PW,
        "full_name": "Priya Sharma",
        "role": "citizen",
        "phone": "+91 9811000001",
    },
    {
        "email": "rahul.mehta88@yahoo.com",
        "password": CITIZEN_PW,
        "full_name": "Rahul Mehta",
        "role": "citizen",
        "phone": "+91 9811000002",
    },
    {
        "email": "amit.verma@outlook.com",
        "password": CITIZEN_PW,
        "full_name": "Amit Verma",
        "role": "citizen",
        "phone": "+91 9811000004",
    },
    {
        "email": "neha.kapoor@gmail.com",
        "password": CITIZEN_PW,
        "full_name": "Neha Kapoor",
        "role": "citizen",
        "phone": "+91 9811000005",
    },
]

# seed_key must be unique; used for upsert.
DEMO_COMPLAINTS = [
    {
        "seed_key": "demo-san-submitted",
        "citizen_email": "priya.sharma@gmail.com",
        "title": "Overflowing garbage bin near school gate",
        "description": "The municipal bin on Lane 4 has not been emptied for four days. Smell and stray dogs are affecting the school entrance.",
        "address": "Lane 4, Karol Bagh, New Delhi",
        "coordinates": [77.1909, 28.6519],
        "status": ComplaintStatus.SUBMITTED.value,
        "priority": "medium",
        "category": "garbage",
        "department_code": None,
        "assign_officer_email": None,
    },
    {
        "seed_key": "demo-san-await-assign",
        "citizen_email": "rahul.mehta88@yahoo.com",
        "title": "Street litter after market hours",
        "description": "Vegetable market on Sunday leaves large piles of waste on the footpath. Need sweeping and collection early Monday.",
        "address": "Sunday Market Road, Saket, New Delhi",
        "coordinates": [77.2197, 28.5244],
        "status": ComplaintStatus.ROUTED_TO_DEPARTMENT.value,
        "priority": "high",
        "category": "garbage",
        "department_code": "SAN",
        "assign_officer_email": None,
    },
    {
        "seed_key": "demo-san-assigned",
        "citizen_email": "priya.sharma@gmail.com",
        "title": "Dead animal removal request",
        "description": "A stray dog carcass has been on the roadside for two days near the bus stop. Please arrange disposal.",
        "address": "Bus Stand Road, Lajpat Nagar, New Delhi",
        "coordinates": [77.2433, 28.5677],
        "status": ComplaintStatus.ASSIGNED.value,
        "priority": "critical",
        "category": "garbage",
        "department_code": "SAN",
        "assign_officer_email": "ravi.kumar@civic.gov.in",
    },
    {
        "seed_key": "demo-san-in-progress",
        "citizen_email": "amit.verma@outlook.com",
        "title": "Blocked drain causing sewage backup",
        "description": "Rainwater mixed with sewage is pooling in front of our shop. The drain cover is clogged with plastic waste.",
        "address": "Shop 12, Chandni Chowk, Old Delhi",
        "coordinates": [77.2310, 28.6562],
        "status": ComplaintStatus.IN_PROGRESS.value,
        "priority": "high",
        "category": "garbage",
        "department_code": "SAN",
        "assign_officer_email": "lakshmi.nair@civic.gov.in",
    },
    {
        "seed_key": "demo-san-resolved",
        "citizen_email": "rahul.mehta88@yahoo.com",
        "title": "Missed garbage pickup — resolved",
        "description": "Household waste was not collected on scheduled day. Issue was fixed after follow-up.",
        "address": "Block C, Dwarka Sector 10, New Delhi",
        "coordinates": [77.0460, 28.5921],
        "status": ComplaintStatus.RESOLVED.value,
        "priority": "medium",
        "category": "garbage",
        "department_code": "SAN",
        "assign_officer_email": "ravi.kumar@civic.gov.in",
        "resolution_notes": "Extra pickup truck dispatched; lane added to Monday route.",
    },
    {
        "seed_key": "demo-pwd-await-assign",
        "citizen_email": "neha.kapoor@gmail.com",
        "title": "Large pothole on main road",
        "description": "Deep pothole near the zebra crossing is damaging vehicles and risky for two-wheelers, especially at night.",
        "address": "NH48 service lane, Gurgaon border, Delhi NCR",
        "coordinates": [77.0266, 28.4595],
        "status": ComplaintStatus.ROUTED_TO_DEPARTMENT.value,
        "priority": "high",
        "category": "road_damage",
        "department_code": "PWD",
        "assign_officer_email": None,
    },
    {
        "seed_key": "demo-pwd-assigned",
        "citizen_email": "priya.sharma@gmail.com",
        "title": "Broken streetlight on footpath",
        "description": "Streetlight pole 14 has been dark for a week. Pedestrians cannot see the broken tiles on the footpath.",
        "address": "Footpath near Metro Gate 2, Rajiv Chowk, New Delhi",
        "coordinates": [77.2197, 28.6328],
        "status": ComplaintStatus.WORK_STARTED.value,
        "priority": "medium",
        "category": "road_damage",
        "department_code": "PWD",
        "assign_officer_email": "imran.sheikh@civic.gov.in",
    },
    {
        "seed_key": "demo-unsupported-police",
        "citizen_email": "rahul.mehta88@yahoo.com",
        "title": "Theft reported at shop",
        "description": "My shop was broken into last night. I need police to register an FIR — not a sanitation or roads issue.",
        "address": "Market Line 2, Sadar Bazaar, Delhi",
        "coordinates": [77.2315, 28.6692],
        "status": ComplaintStatus.REJECTED.value,
        "priority": "medium",
        "category": "other",
        "department_code": None,
        "assign_officer_email": None,
        "unsupported": True,
    },
    {
        "seed_key": "demo-wsd-routed",
        "citizen_email": "amit.verma@outlook.com",
        "title": "Low water pressure in morning",
        "description": "For the past week, tap water pressure drops to almost nothing between 6–9 AM in our apartment block.",
        "address": "Tower B, Green Park Extension, New Delhi",
        "coordinates": [77.2069, 28.5598],
        "status": ComplaintStatus.ROUTED_TO_DEPARTMENT.value,
        "priority": "medium",
        "category": "water",
        "department_code": "WSD",
        "assign_officer_email": None,
    },
    {
        "seed_key": "demo-elec-assigned",
        "citizen_email": "neha.kapoor@gmail.com",
        "title": "Power outage in street",
        "description": "Entire lane lost power after last night's storm. Transformer makes a buzzing sound intermittently.",
        "address": "Lane 7, Mayur Vihar Phase 2, Delhi",
        "coordinates": [77.2944, 28.6092],
        "status": ComplaintStatus.ASSIGNED.value,
        "priority": "critical",
        "category": "electricity",
        "department_code": "ELEC",
        "assign_officer_email": "farhan.ali@civic.gov.in",
    },
    {
        "seed_key": "demo-wsd-assigned",
        "citizen_email": "priya.sharma@gmail.com",
        "title": "Visible pipeline leak on street",
        "description": "Water is bubbling up from a cracked joint near the manhole. Pressure is low in nearby flats.",
        "address": "Block D, Rohini Sector 9, New Delhi",
        "coordinates": [77.1197, 28.7434],
        "status": ComplaintStatus.ASSIGNED.value,
        "priority": "high",
        "category": "water",
        "department_code": "WSD",
        "assign_officer_email": "mohit.agarwal@civic.gov.in",
    },
    {
        "seed_key": "demo-tnt-routed",
        "citizen_email": "rahul.mehta88@yahoo.com",
        "title": "Traffic signal stuck on red",
        "description": "The signal at the main crossing has been stuck on red for both sides for over an hour, causing long jams.",
        "address": "ITO Crossing, Bahadur Shah Zafar Marg, New Delhi",
        "coordinates": [77.2410, 28.6289],
        "status": ComplaintStatus.ROUTED_TO_DEPARTMENT.value,
        "priority": "critical",
        "category": "traffic",
        "department_code": "TNT",
        "assign_officer_email": None,
    },
    {
        "seed_key": "demo-tnt-assigned",
        "citizen_email": "amit.verma@outlook.com",
        "title": "Bus stop shelter damaged",
        "description": "The glass panel of the bus shelter is shattered and sharp edges are exposed. Commuters stand on the road.",
        "address": "Bus Stop 42, Mathura Road, Nizamuddin, Delhi",
        "coordinates": [77.2505, 28.5910],
        "status": ComplaintStatus.ASSIGNED.value,
        "priority": "high",
        "category": "traffic",
        "department_code": "TNT",
        "assign_officer_email": "preeti.gautam@civic.gov.in",
    },
    {
        "seed_key": "demo-tnt-in-progress",
        "citizen_email": "neha.kapoor@gmail.com",
        "title": "Illegal parking blocking fire lane",
        "description": "Cars park all day in the no-parking zone beside the hospital emergency entrance. Ambulances cannot turn in easily.",
        "address": "Emergency Gate, LNJP Hospital, Delhi Gate",
        "coordinates": [77.2400, 28.6412],
        "status": ComplaintStatus.IN_PROGRESS.value,
        "priority": "high",
        "category": "traffic",
        "department_code": "TNT",
        "assign_officer_email": "sanjay.rawat@civic.gov.in",
    },
    {
        "seed_key": "demo-par-routed",
        "citizen_email": "neha.kapoor@gmail.com",
        "title": "Broken swing in children's park",
        "description": "One swing chain is rusted through and the seat hangs at an angle. Kids still try to use it after school.",
        "address": "Central Park, Dwarka Sector 12, New Delhi",
        "coordinates": [77.0465, 28.5925],
        "status": ComplaintStatus.ROUTED_TO_DEPARTMENT.value,
        "priority": "medium",
        "category": "parks",
        "department_code": "PAR",
        "assign_officer_email": None,
    },
]


def _print_login_cheatsheet() -> None:
    print("\n" + "=" * 60)
    print("Demo logins — http://localhost:3000/login")
    print("=" * 60)
    groups = [
        ("System admin (password: Admin@123)", "admin", STAFF_PW_ADMIN),
        ("Department admin (password: DeptAdmin@123)", "dept_admin", STAFF_PW_DEPT),
        ("Field officer (password: Officer@123)", "officer", STAFF_PW_OFFICER),
        ("Citizen / resident (password: Citizen@123)", "citizen", CITIZEN_PW),
    ]
    for title, role, pw in groups:
        print(f"\n{title}")
        for u in DEMO_USERS:
            if u["role"] != role:
                continue
            dept = f" [{u['department_code']}]" if u.get("department_code") else ""
            print(f"  {u['full_name']:28} {u['email']}{dept}")
    print("\nResidents use personal email (Gmail/Yahoo/Outlook), not @civic.gov.in")
    print("=" * 60)


async def _remove_legacy_users(db) -> None:
    for email in LEGACY_USER_EMAILS:
        result = await db.users.delete_one({"email": email.lower()})
        if result.deleted_count:
            print(f"  Removed legacy account {email}")


async def _upsert_users(db, now: datetime) -> dict[str, dict]:
    dept_by_code: dict[str, ObjectId] = {}
    async for doc in db.departments.find({"is_active": True}, {"code": 1}):
        dept_by_code[doc["code"]] = doc["_id"]

    by_email: dict[str, dict] = {}
    for spec in DEMO_USERS:
        email = spec["email"].lower()
        dept_id = None
        if spec.get("department_code"):
            dept_id = dept_by_code.get(spec["department_code"])
            if not dept_id:
                print(f"  skip user {email}: dept {spec['department_code']} missing")
                continue

        payload = {
            "full_name": spec["full_name"],
            "role": spec["role"],
            "phone": spec.get("phone"),
            "department_id": dept_id,
            "service_area": spec.get("service_area"),
            "is_active": True,
            "updated_at": now,
            "password_hash": hash_password(spec["password"]),
        }
        existing = await db.users.find_one({"email": email})
        if existing:
            await db.users.update_one({"email": email}, {"$set": payload})
            user_id = existing["_id"]
            action = "Updated"
        else:
            result = await db.users.insert_one({"email": email, "created_at": now, **payload})
            user_id = result.inserted_id
            action = "Created"
        by_email[email] = {"_id": user_id, **spec}
        print(f"  {action} {spec['role']:11} {email}")

    return by_email


def _status_history(status: str, citizen_oid: ObjectId, now: datetime) -> list[dict]:
    steps = [ComplaintStatus.SUBMITTED.value]
    if status != ComplaintStatus.SUBMITTED.value:
        steps.append(ComplaintStatus.AI_PROCESSING.value)
    if status in (
        ComplaintStatus.ROUTED_TO_DEPARTMENT.value,
        ComplaintStatus.ASSIGNED.value,
        ComplaintStatus.WORK_STARTED.value,
        ComplaintStatus.IN_PROGRESS.value,
        ComplaintStatus.RESOLVED.value,
    ):
        steps.append(ComplaintStatus.ROUTED_TO_DEPARTMENT.value)
    if status in (
        ComplaintStatus.ASSIGNED.value,
        ComplaintStatus.WORK_STARTED.value,
        ComplaintStatus.IN_PROGRESS.value,
        ComplaintStatus.RESOLVED.value,
    ):
        steps.append(ComplaintStatus.ASSIGNED.value)
    if status in (ComplaintStatus.WORK_STARTED.value, ComplaintStatus.IN_PROGRESS.value, ComplaintStatus.RESOLVED.value):
        steps.append(ComplaintStatus.WORK_STARTED.value)
    if status == ComplaintStatus.IN_PROGRESS.value:
        steps.append(ComplaintStatus.IN_PROGRESS.value)
    if status == ComplaintStatus.RESOLVED.value:
        steps.append(ComplaintStatus.RESOLVED.value)
    if status == ComplaintStatus.REJECTED.value:
        steps = [ComplaintStatus.SUBMITTED.value, ComplaintStatus.AI_PROCESSING.value, ComplaintStatus.REJECTED.value]

    history = []
    t = now - timedelta(days=len(steps))
    for s in steps:
        history.append(
            {
                "status": s,
                "changed_by": citizen_oid,
                "changed_at": t,
                "note": None,
            }
        )
        t += timedelta(hours=6)
    return history


async def _upsert_complaints(db, users_by_email: dict[str, dict], dept_by_code: dict[str, ObjectId], now: datetime) -> None:
    year = now.year
    seq = 0
    for spec in DEMO_COMPLAINTS:
        seq += 1
        citizen = users_by_email.get(spec["citizen_email"].lower())
        if not citizen:
            print(f"  skip complaint {spec['seed_key']}: citizen missing")
            continue

        citizen_oid = citizen["_id"]
        dept_oid = dept_by_code.get(spec["department_code"]) if spec.get("department_code") else None
        officer_oid = None
        if spec.get("assign_officer_email"):
            off = users_by_email.get(spec["assign_officer_email"].lower())
            officer_oid = off["_id"] if off else None

        complaint_number = f"HMN-SEED-{year}-{seq:03d}"
        ai_meta = None
        if spec.get("unsupported"):
            msg = (
                "We don't have a department for “Police” on this portal. "
                "We only handle: Public Works Department, Sanitation Department, "
                "Water Supply Department, Electricity Department, Traffic & Transport, Parks & Recreation."
            )
            ai_meta = {
                "summary": msg,
                "category": spec.get("category"),
                "unsupported_department": True,
                "public_message": msg,
                "routing": {"unsupported": True, "public_message": msg},
                "predicted_priority": spec["priority"],
            }
        elif dept_oid:
            ai_meta = {
                "summary": spec["title"][:120],
                "category": spec.get("category"),
                "unsupported_department": False,
                "routing": {"unsupported": False},
                "predicted_priority": spec["priority"],
            }

        doc = {
            "seed_key": spec["seed_key"],
            "complaint_id": complaint_number,
            "citizen_id": citizen_oid,
            "title": spec["title"],
            "description": spec["description"],
            "images": [],
            "location": {
                "type": "Point",
                "coordinates": spec["coordinates"],
                "address": spec["address"],
            },
            "status": spec["status"],
            "priority": spec["priority"],
            "category": spec.get("category"),
            "department_id": dept_oid,
            "assigned_officer_id": officer_oid,
            "ai_metadata": ai_meta,
            "status_history": _status_history(spec["status"], citizen_oid, now),
            "updated_at": now,
            "created_at": now - timedelta(days=3),
        }
        if spec.get("resolution_notes"):
            doc["resolution"] = {
                "notes": spec["resolution_notes"],
                "resolved_at": now - timedelta(days=1),
            }

        existing = await db.complaints.find_one({"seed_key": spec["seed_key"]})
        if existing:
            await db.complaints.update_one({"_id": existing["_id"]}, {"$set": doc})
            print(f"  Updated complaint {complaint_number} ({spec['status']})")
        else:
            await db.complaints.insert_one(doc)
            print(f"  Created complaint {complaint_number} ({spec['status']})")


async def seed_all() -> None:
    settings = get_settings()
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]
    now = datetime.now(timezone.utc)

    print("Seeding departments…")
    await seed_departments(db)

    dept_by_code: dict[str, ObjectId] = {}
    async for doc in db.departments.find({"is_active": True}, {"code": 1, "name": 1}):
        dept_by_code[doc["code"]] = doc["_id"]
    print(f"  {len(dept_by_code)} departments")

    print("\nSeeding users…")
    await _remove_legacy_users(db)
    users = await _upsert_users(db, now)

    print("\nSeeding complaints…")
    await _upsert_complaints(db, users, dept_by_code, now)

    total_c = await db.complaints.count_documents({})
    total_u = await db.users.count_documents({})
    print(f"\nDone. Users in DB: {total_u}, complaints in DB: {total_c}")
    _print_login_cheatsheet()

    client.close()


async def verify_api(base_url: str = "http://127.0.0.1:8002") -> bool:
    import httpx

    api = base_url.rstrip("/") + "/api/v1"
    ok = True

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            health = await client.get(base_url + "/health")
            health.raise_for_status()
            print(f"\nHealth: {health.json()}")
        except Exception as exc:
            print(f"\nHealth check failed: {exc}")
            return False

        async def login(email: str, password: str) -> str | None:
            r = await client.post(f"{api}/auth/login", json={"email": email, "password": password})
            if r.status_code != 200:
                print(f"  LOGIN FAIL {email}: {r.status_code} {r.text[:200]}")
                return None
            return r.json().get("access_token")

        checks = [
            ("priya.sharma@gmail.com", CITIZEN_PW, "citizen"),
            ("meera.iyer@civic.gov.in", STAFF_PW_DEPT, "dept_admin_san"),
            ("karan.singh@civic.gov.in", STAFF_PW_DEPT, "dept_admin_pwd"),
            ("rohit.banerjee@civic.gov.in", STAFF_PW_DEPT, "dept_admin_wsd"),
            ("sunita.pillai@civic.gov.in", STAFF_PW_DEPT, "dept_admin_elec"),
            ("aditya.venkatesh@civic.gov.in", STAFF_PW_DEPT, "dept_admin_tnt"),
            ("gaurav.mehta@civic.gov.in", STAFF_PW_DEPT, "dept_admin_par"),
            ("ravi.kumar@civic.gov.in", STAFF_PW_OFFICER, "officer"),
            ("arjun.malhotra@civic.gov.in", STAFF_PW_ADMIN, "admin"),
        ]
        for email, pw, role in checks:
            token = await login(email, pw)
            if not token:
                ok = False
                continue
            r = await client.get(
                f"{api}/complaints",
                params={"limit": 50},
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.status_code != 200:
                print(f"  LIST FAIL {role}: {r.status_code}")
                ok = False
                continue
            data = r.json()
            n = data.get("total", len(data.get("items", [])))
            print(f"  OK {role:12} complaints visible: {n}")

            if role.startswith("dept_admin") or role in ("officer", "admin"):
                if not data.get("items"):
                    continue
                cid = data["items"][0]["id"]
                d = await client.get(
                    f"{api}/complaints/{cid}",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if d.status_code != 200:
                    print(f"  DETAIL FAIL {role}: {d.status_code}")
                    ok = False
                else:
                    body = d.json()
                    has_citizen = bool(body.get("citizen_name") or body.get("citizen_email"))
                    print(f"  OK {role:12} detail + citizen fields: {has_citizen}")

    return ok


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", help="Run API smoke tests after seeding")
    parser.add_argument("--api", default="http://127.0.0.1:8002", help="API base URL for --verify")
    args = parser.parse_args()

    await seed_all()
    if args.verify:
        passed = await verify_api(args.api)
        if not passed:
            sys.exit(1)
        print("\nAll verification checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
