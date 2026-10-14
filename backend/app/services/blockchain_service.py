"""Immutable audit ledger — simulated private blockchain (MVP)."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from app.db.database import get_database

GENESIS_HASH = "0" * 64


def _hash_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def append_audit_block(
    complaint_id: str,
    from_status: str | None,
    to_status: str,
    actor_id: str,
    *,
    note: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str:
    db = get_database()
    oid = ObjectId(complaint_id)

    last = await db.blockchain_ledger.find_one(
        {"complaint_id": oid},
        sort=[("block_index", -1)],
    )
    previous_hash = last["record_hash"] if last else GENESIS_HASH
    block_index = (last["block_index"] + 1) if last else 0

    body = {
        "complaint_id": complaint_id,
        "from_status": from_status,
        "to_status": to_status,
        "actor_id": actor_id,
        "note": note,
        "metadata": metadata or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "previous_hash": previous_hash,
        "block_index": block_index,
    }
    record_hash = _hash_payload(body)

    doc = {
        **body,
        "complaint_id": oid,
        "actor_id": ObjectId(actor_id),
        "record_hash": record_hash,
        "created_at": datetime.now(timezone.utc),
    }
    await db.blockchain_ledger.insert_one(doc)
    return record_hash


async def get_complaint_chain(complaint_id: str) -> list[dict]:
    db = get_database()
    cursor = db.blockchain_ledger.find({"complaint_id": ObjectId(complaint_id)}).sort(
        "block_index", 1
    )
    chain = []
    async for block in cursor:
        chain.append(
            {
                "block_index": block["block_index"],
                "from_status": block.get("from_status"),
                "to_status": block["to_status"],
                "actor_id": str(block["actor_id"]),
                "note": block.get("note"),
                "metadata": block.get("metadata", {}),
                "timestamp": block["timestamp"],
                "previous_hash": block["previous_hash"],
                "record_hash": block["record_hash"],
            }
        )
    return chain


async def verify_complaint_chain(complaint_id: str) -> dict:
    chain = await get_complaint_chain(complaint_id)
    if not chain:
        return {"valid": True, "blocks": 0, "message": "No audit blocks yet"}

    expected_prev = GENESIS_HASH
    for block in chain:
        if block["previous_hash"] != expected_prev:
            return {
                "valid": False,
                "blocks": len(chain),
                "message": f"Chain broken at block {block['block_index']}",
            }
        body = {
            "complaint_id": complaint_id,
            "from_status": block.get("from_status"),
            "to_status": block["to_status"],
            "actor_id": block["actor_id"],
            "note": block.get("note"),
            "metadata": block.get("metadata", {}),
            "timestamp": block["timestamp"],
            "previous_hash": block["previous_hash"],
            "block_index": block["block_index"],
        }
        if _hash_payload(body) != block["record_hash"]:
            return {
                "valid": False,
                "blocks": len(chain),
                "message": f"Tampered block at index {block['block_index']}",
            }
        expected_prev = block["record_hash"]

    return {"valid": True, "blocks": len(chain), "message": "Chain integrity verified"}
