"""
End-to-end check: citizen submit -> officer/dept_admin sees same reporter name/email.

Usage (API on 8002):
  cd backend && .\\venv\\Scripts\\python.exe scripts/verify_reporter_mapping.py
"""

from __future__ import annotations

import asyncio
import secrets
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

API = "http://127.0.0.1:8002/api/v1"
OFFICER_EMAIL = "ravi.kumar@civic.gov.in"
OFFICER_PW = "Officer@123"
ADMIN_EMAIL = "arjun.malhotra@civic.gov.in"
ADMIN_PW = "Admin@123"


async def main() -> None:
    tag = secrets.token_hex(4)
    citizen_email = f"reporter.test.{tag}@gmail.com"
    citizen_name = f"Reporter Test {tag.upper()}"
    password = "TestCitizen1!"

    async with httpx.AsyncClient(timeout=120.0) as client:
        health = await client.get("http://127.0.0.1:8002/health")
        health.raise_for_status()

        reg = await client.post(
            f"{API}/auth/register",
            json={
                "email": citizen_email,
                "password": password,
                "full_name": citizen_name,
                "phone": "9876543210",
            },
        )
        if reg.status_code not in (200, 201):
            print("Register failed:", reg.status_code, reg.text[:300])
            sys.exit(1)

        login = await client.post(
            f"{API}/auth/login",
            json={"email": citizen_email, "password": password},
        )
        login.raise_for_status()
        citizen_token = login.json()["access_token"]
        headers_c = {"Authorization": f"Bearer {citizen_token}"}

        form = {
            "title": f"Mapping test {tag}",
            "description": "Verify reporter identity for officers.",
            "latitude": "28.6139",
            "longitude": "77.2090",
            "address": "Test address, Delhi",
        }
        created = await client.post(f"{API}/complaints", data=form, headers=headers_c)
        created.raise_for_status()
        body = created.json()
        complaint_oid = body["id"]
        print(f"Created complaint {body['complaint_id']} (id={complaint_oid}) as {citizen_name}")

        admin_login = await client.post(
            f"{API}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PW},
        )
        admin_login.raise_for_status()
        admin_token = admin_login.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {admin_token}"}

        detail = await client.get(f"{API}/complaints/{complaint_oid}", headers=headers_a)
        detail.raise_for_status()
        d = detail.json()
        ok_admin = d.get("citizen_name") == citizen_name and d.get("citizen_email") == citizen_email
        print(f"Admin detail view: name={d.get('citizen_name')} email={d.get('citizen_email')} -> {'OK' if ok_admin else 'MISMATCH'}")

        officer_login = await client.post(
            f"{API}/auth/login",
            json={"email": OFFICER_EMAIL, "password": OFFICER_PW},
        )
        officer_login.raise_for_status()
        officer_token = officer_login.json()["access_token"]

        listed = await client.get(
            f"{API}/complaints",
            params={"limit": 100},
            headers={"Authorization": f"Bearer {officer_token}"},
        )
        listed.raise_for_status()
        items = listed.json().get("items", [])
        match = next((i for i in items if i["id"] == complaint_oid), None)
        if match:
            ok_list = match.get("citizen_name") == citizen_name
            print(f"Officer list (if assigned): reporter={match.get('citizen_name')} -> {'OK' if ok_list else 'MISMATCH'}")
        else:
            print("Officer list: complaint not assigned yet (expected before routing/assign).")

        if not ok_admin:
            sys.exit(1)
        print("Reporter mapping verification passed for dept admin detail view.")


if __name__ == "__main__":
    asyncio.run(main())
