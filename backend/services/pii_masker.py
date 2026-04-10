"""PII (Personally Identifiable Information) masking for privacy protection.

Detects and masks sensitive data before indexing:
- Phone numbers (Chinese / international)
- ID card numbers (Chinese 18-digit)
- Email addresses
- Street addresses with apartment/room numbers
- Bank card numbers
- IP addresses
"""

from __future__ import annotations

import re


# ---- Compiled patterns ----
_PATTERNS: list[tuple[str, re.Pattern, str]] = [
    # Chinese mobile: 13x-19x, 11 digits
    ("phone", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "[手机号]"),
    # International phone with country code
    ("phone_intl", re.compile(r"\+\d{1,3}[-\s]?\d{6,12}"), "[电话号码]"),
    # Landline: 0xx-xxxxxxxx
    ("landline", re.compile(r"0\d{2,3}[-\s]?\d{7,8}"), "[座机号码]"),
    # Chinese ID card: 18 digits (last may be X)
    ("id_card", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"), "[身份证号]"),
    # Email
    ("email", re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"), "[邮箱]"),
    # Bank card: 16-19 digits
    ("bank_card", re.compile(r"(?<!\d)\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4,7}(?!\d)"), "[银行卡号]"),
    # IPv4
    ("ipv4", re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "[IP地址]"),
    # Detailed address: contains floor/room/apt number patterns (Chinese)
    ("address_detail", re.compile(
        r"[\u4e00-\u9fff]{2,}(?:省|市|区|县|镇|乡|村|路|街|道|巷|号|弄|幢|栋|楼|单元|室|房)"
        r"[\u4e00-\u9fff\d\-#]*(?:号|室|房|楼|层|单元)"
    ), "[详细地址]"),
]


def mask_pii(text: str) -> str:
    """Replace PII in text with placeholder tags."""
    for name, pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def mask_pii_batch(texts: list[str]) -> list[str]:
    """Mask PII in a batch of texts."""
    return [mask_pii(t) for t in texts]


def detect_pii(text: str) -> list[dict]:
    """Detect PII in text and return a list of findings."""
    findings = []
    for name, pattern, replacement in _PATTERNS:
        for match in pattern.finditer(text):
            findings.append({
                "type": name,
                "start": match.start(),
                "end": match.end(),
                "masked_as": replacement,
            })
    return findings
