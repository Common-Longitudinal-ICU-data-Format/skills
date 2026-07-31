#!/usr/bin/env python3
"""clif-icu PHI output scanner (PostToolUse). ADVISORY, never blocks.

Flags PHI-shaped patterns in tool output so the agent stops and sanitizes.
Synthetic data triggers false positives by design — the warning says how to
proceed if the data is confirmed non-PHI. CLIF_PHI_SCAN=off disables.
Exit 0 always. Stdlib only.
"""
import json, os, re, sys

PATTERNS = [
    ("MRN-like identifier", re.compile(r"\bMRN\W{0,3}\d{5,}", re.I)),
    ("SSN-like number",     re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("DOB-like field",      re.compile(r"\bDOB\W{0,3}(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})", re.I)),
    ("birth-date-like value", re.compile(r"\b(?:19[0-9]{2}|20[0-4][0-9])-\d{2}-\d{2}\b.{0,20}\b(?:birth|dob)\b|\b(?:birth|dob)\b.{0,20}\b(?:19[0-9]{2}|20[0-4][0-9])-\d{2}-\d{2}\b", re.I)),
]


def response_text(resp):
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict):
        return " ".join(str(v) for v in resp.values() if isinstance(v, (str, int, float)))
    return ""


def main():
    if os.environ.get("CLIF_PHI_SCAN", "").lower() == "off":
        return 0
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    text = response_text(data.get("tool_response"))[:200_000]
    hits = sorted({label for label, rx in PATTERNS if rx.search(text)})
    if hits:
        warning = (
            "clif-icu PHI scan: tool output contains PHI-shaped patterns ("
            + ", ".join(hits) + "). STOP: do not repeat, summarize, or reason "
            "over these values. If this is real data, the PHI-safe workflow has "
            "been violated — tell the user to open a NEW session against the "
            "non-PHI sandbox (reference/phi-safe-development.md). If the data "
            "is confirmed synthetic (e.g. the sandbox from setup_dev_data.sh), "
            "say so explicitly and continue.")
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse", "additionalContext": warning}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
