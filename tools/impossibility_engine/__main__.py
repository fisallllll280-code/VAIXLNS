"""CLI for Ω-Impossibility Engine.

Backward compatible:
  python -m tools.impossibility_engine < problem.json
New modes:
  python -m tools.impossibility_engine batch --max-workers 8 < batch.json
  python -m tools.impossibility_engine serve --host 127.0.0.1 --port 8787
"""
import argparse
import json
import os
import sys
from .engine import assess


def _emit(value: dict) -> int:
    json.dump(value, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


def _assess() -> int:
    try:
        problem = json.load(sys.stdin)
        return _emit(assess(problem))
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


def _batch(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run a bounded batch through the Ω execution fabric.")
    parser.add_argument("--max-workers", type=int, default=None)
    parser.add_argument("--remote-config-env", default="OMEGA_REMOTE_WORKERS",
                        help="environment variable containing JSON worker endpoint configuration")
    parser.add_argument("--strict-remote", action="store_true",
                        help="fail tasks on remote errors instead of local fallback")
    args = parser.parse_args(argv)
    try:
        from .fabric import remote_workers_from_json, run_batch
        payload = json.load(sys.stdin)
        if isinstance(payload, list):
            problems = payload
            payload_workers = None
        elif isinstance(payload, dict):
            problems = payload.get("problems")
            payload_workers = payload.get("max_workers")
        else:
            raise ValueError("batch input must be a JSON list or object containing 'problems'")
        worker_count = args.max_workers if args.max_workers is not None else int(payload_workers or 4)
        workers_raw = os.environ.get(args.remote_config_env, "")
        remote_workers = remote_workers_from_json(workers_raw) if workers_raw.strip() else []
        result = run_batch(problems, max_workers=worker_count, remote_workers=remote_workers,
                           allow_local_fallback=not args.strict_remote)
        return _emit(result)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


def _serve(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run an Ω assessment worker.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--worker-id", default="omega-worker-local")
    parser.add_argument("--token-env", default="OMEGA_WORKER_TOKEN")
    args = parser.parse_args(argv)
    from .worker_server import serve
    serve(args.host, args.port, token_env=args.token_env, worker_id=args.worker_id)
    return 0


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] == "batch":
        return _batch(argv[1:])
    if argv and argv[0] == "serve":
        return _serve(argv[1:])
    if argv and argv[0] == "assess":
        argv = argv[1:]
    return _assess()


if __name__ == "__main__":
    raise SystemExit(main())
