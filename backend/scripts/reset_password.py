"""Reset a user's password for development."""

import asyncio
import sys
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.security import hash_password


async def main() -> None:
    email = sys.argv[1] if len(sys.argv) > 1 else "nishi@gmail.com"
    password = sys.argv[2] if len(sys.argv) > 2 else "Password@123"

    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["civic_complaints"]

    result = await db.users.update_one(
        {"email": email.lower()},
        {"$set": {
            "password_hash": hash_password(password),
            "updated_at": datetime.now(timezone.utc),
        }},
    )

    if result.matched_count:
        print(f"Password reset for {email} -> {password}")
    else:
        print(f"User {email} not found")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
