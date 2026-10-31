"""Offline, evidence-oriented Unicode Emoji 18.0 registry importer (stdlib only)."""
import argparse
import hashlib
import json
import re
from pathlib import Path

SOURCE_URL = "https://www.unicode.org/Public/18.0.0/emoji/emoji-test.txt"
VERSION = "18.0"
LINE = re.compile(r"^([0-9A-F ]+)\s*;\s*([a-z-]+)\s*#\s*(\S+)\s+E([0-9]+(?:\.[0-9]+)?)\s+(.+?)\s*$")
ALLOWED = {"fully-qualified", "minimally-qualified", "unqualified", "component"}

def build_registry(raw: bytes) -> dict:
    text = raw.decode("utf-8", errors="strict")
    if not re.search(r"(?m)^#\s*Version:\s*18\.0\s*$", text):
        raise ValueError("Input must declare Emoji Version: 18.0")
    group, subgroup, entries, ids = None, None, [], set()
    for line_number, line in enumerate(text.splitlines(), 1):
        if line.startswith("# group:"):
            group = line.partition(":")[2].strip()
            continue
        if line.startswith("# subgroup:"):
            subgroup = line.partition(":")[2].strip()
            continue
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = LINE.fullmatch(line)
        if match is None:
            raise ValueError(f"Malformed data line {line_number}")
        cps, status, rendered, emoji_ver, name = match.groups()
        points = [int(cp, 16) for cp in cps.split()]
        if status not in ALLOWED or not group or not subgroup:
            raise ValueError(f"Invalid status/group at line {line_number}")
        if any(cp > 0x10FFFF or 0xD800 <= cp <= 0xDFFF for cp in points):
            raise ValueError(f"Invalid scalar at line {line_number}")
        sequence = "".join(chr(cp) for cp in points)
        if rendered != sequence:
            raise ValueError(f"Rendered sequence mismatch at line {line_number}")
        key = "-".join(f"{cp:04X}" for cp in points)
        identity = (key, status)
        if identity in ids:
            raise ValueError(f"Duplicate identity at line {line_number}")
        ids.add(identity)
        entries.append({
            "id": "unicode-emoji-" + VERSION + ":" + key + ":" + status,
            "codepoints": [f"U+{cp:04X}" for cp in points],
            "sequence": sequence,
            "qualification": status,
            "group": group, "subgroup": subgroup,
            "emoji_version": emoji_ver,
            "name": name,
        })
    if not entries:
        raise ValueError("Empty registry")
    return {
        "registry_version": 1,
        "unicode_emoji_version": VERSION,
        "source_url": SOURCE_URL,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "record_count": len(entries),
        "verification_state": "PARSED_NOT_INDEPENDENTLY_VERIFIED",
        "records": entries,
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="Locally obtained official emoji-test.txt")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("Output must not overwrite source")
    raw = args.input.read_bytes()
    result = build_registry(raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"records": result["record_count"], "source_sha256": result["source_sha256"],
                      "state": result["verification_state"]}, sort_keys=True))

if __name__ == "__main__":
    main()
