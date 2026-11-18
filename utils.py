BRANCH_ALIASES = {
    "cs": "computer science",
    "cse": "computer science",
    "computer science": "computer science",
    "computer science engineering": "computer science",
    "computer science and engineering": "computer science",
    "it": "information technology",
    "information technology": "information technology",
    "ece": "electronics and communication",
    "electronics and communication": "electronics and communication",
    "electronics and communication engineering": "electronics and communication",
    "ee": "electrical engineering",
    "eee": "electrical engineering",
    "electrical engineering": "electrical engineering",
    "mech": "mechanical engineering",
    "me": "mechanical engineering",
    "mechanical engineering": "mechanical engineering",
    "civil": "civil engineering",
    "civil engineering": "civil engineering",
}


def normalize_branch(name: str) -> str:
    """Return a canonical lowercase branch name, resolving common abbreviations."""
    if not name:
        return ""
    key = name.strip().lower()
    return BRANCH_ALIASES.get(key, key)


def branch_is_eligible(student_branch: str, eligible_branch_field: str) -> bool:
    """
    Check whether a student's branch matches a drive's eligible_branch field
    (comma-separated list, or 'Any'), using alias-aware normalization.
    """
    if not eligible_branch_field or eligible_branch_field.strip().lower() == "any":
        return True
    allowed = [normalize_branch(b) for b in eligible_branch_field.split(",")]
    return normalize_branch(student_branch) in allowed