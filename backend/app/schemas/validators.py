import re

_PHONE_DIGITS = re.compile(r"\D")


def normalize_and_validate_phone(value: str) -> str:
    """Require 10–15 digits (spaces/dashes allowed in input)."""
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Phone number is required")
    digits = _PHONE_DIGITS.sub("", cleaned)
    if len(digits) < 10 or len(digits) > 15:
        raise ValueError("Phone number must contain 10 to 15 digits")
    return cleaned
