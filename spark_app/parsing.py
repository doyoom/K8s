import re
from typing import Optional


def extract_action_type(log: Optional[str]) -> Optional[str]:
    if not log:
        return None
    tokens = re.split(r"\] ?", log)
    if len(tokens) < 2:
        return None
    seg = tokens[1].strip().split(" ")
    if not seg:
        return None
    if seg[0] == "-" and len(seg) > 1:
        return seg[1]
    return seg[0]


def extract_endpoint(log: Optional[str]) -> Optional[str]:
    if not log:
        return None
    match = re.search(r"(GET|POST|PUT|DELETE)\s+(\S+)", log)
    if match:
        return match.group(2)
    return None

