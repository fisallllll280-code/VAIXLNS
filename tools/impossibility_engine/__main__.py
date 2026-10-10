"""CLI: python -m tools.impossibility_engine < problem.json"""
import json
import sys
from .engine import assess


def main() -> int:
    try:
        problem = json.load(sys.stdin)
        result = assess(problem)
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
