"""Small, deterministic reference slice for VX planning and XV continuity.

This module does not call LLMs, execute arbitrary commands, or perform external actions.
It creates an inspectable task plan and an append-only, hash-chained local event log.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Any, Iterable
import uuid

GENESIS_HASH = "0" * 64
EPISTEMIC_STATES = {
    "VERIFIED", "EVIDENCE_SUPPORTED", "INFERENCE", "HYPOTHESIS",
    "SPECIFICATION", "UNVERIFIED", "UNKNOWN", "CONFLICT"
}


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source_uri: str
    content_sha256: str
    retrieved_at: str
    locator: str = ""


@dataclass(frozen=True)
class Claim:
    claim_id: str
    statement: str
    state: str
    evidence_ids: tuple[str, ...] = ()
    verification_method: str | None = None
    independent_review: bool = False
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ClaimAssessment:
    effective_state: str
    admissible_as_verified: bool
    reasons: tuple[str, ...]


def evaluate_claim(claim: Claim, evidence: Iterable[Evidence] = ()) -> ClaimAssessment:
    """Fail closed: a VERIFIED label needs hashed evidence and a review method."""
    evidence_by_id = {item.evidence_id: item for item in evidence}
    if claim.state not in EPISTEMIC_STATES:
        return ClaimAssessment("UNVERIFIED", False, ("unknown epistemic state",))
    if claim.state == "CONFLICT":
        return ClaimAssessment("CONFLICT", False, ("conflicting records must be preserved",))
    if claim.state != "VERIFIED":
        return ClaimAssessment(claim.state, False, ("claim is not independently verified",))

    reasons: list[str] = []
    if not claim.evidence_ids:
        reasons.append("no evidence references supplied")
    for evidence_id in claim.evidence_ids:
        record = evidence_by_id.get(evidence_id)
        if record is None:
            reasons.append(f"evidence record not found: {evidence_id}")
            continue
        if not record.source_uri.strip():
            reasons.append(f"source URI missing: {evidence_id}")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", record.content_sha256 or ""):
            reasons.append(f"valid content SHA-256 missing: {evidence_id}")
        if not record.retrieved_at.strip():
            reasons.append(f"retrieval timestamp missing: {evidence_id}")
    if not claim.verification_method or not claim.verification_method.strip():
        reasons.append("verification method missing")
    if not claim.independent_review:
        reasons.append("independent review not recorded")
    if reasons:
        return ClaimAssessment("UNVERIFIED", False, tuple(reasons))
    return ClaimAssessment("VERIFIED", True, ("evidence metadata and review gate satisfied",))


@dataclass(frozen=True)
class TaskStep:
    step_id: str
    role: str
    objective: str
    expected_output: str
    acceptance_test: str
    depends_on: tuple[str, ...] = ()
    approval_required: bool = False


@dataclass(frozen=True)
class TaskPlan:
    task_id: str
    request: str
    goal: str
    intent_class: str
    status: str
    requires_approval: bool
    approval_reasons: tuple[str, ...]
    steps: tuple[TaskStep, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["steps"] = [asdict(step) for step in self.steps]
        return value


_HIGH_IMPACT_PATTERNS = (
    r"\b(delete|remove permanently|publish|deploy|merge|send|transfer|trade|buy|sell|pay|withdraw|change permissions|rotate key)\b",
    r"(احذف|حذف نهائي|انشر|نشر|انشر للعامة|انشر إلى الإنتاج|انشر للانتاج|ادمج|إرسال|ارسل|حوّل|حول|تداول|اشتر|شراء|بيع|ادفع|سحب أموال|تغيير الصلاحيات|مفتاح الوصول)"
)


def requires_human_approval(request: str) -> tuple[bool, tuple[str, ...]]:
    """Detect high-impact intents conservatively; this is a guard, not authorization."""
    reasons = []
    text = request.casefold()
    for pattern in _HIGH_IMPACT_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            reasons.append("request may create an external, financial, destructive, or hard-to-reverse effect")
            break
    if re.search(r"(project\.genome|Ω\.000|master index|canonical|المصدر الدستوري|الفهرس الرئيسي)", text, re.I):
        reasons.append("request may affect canonical authority or registry artifacts")
    return (bool(reasons), tuple(dict.fromkeys(reasons)))


def _contains(text: str, terms: tuple[str, ...]) -> bool:
    haystack = text.casefold()
    return any(term.casefold() in haystack for term in terms)


def build_task_plan(request: str) -> TaskPlan:
    """Compile a plain-language request into a deterministic, reviewable work plan."""
    original = request.strip()
    if not original:
        raise ValueError("request must not be empty")

    research = _contains(original, (
        "research", "search", "study", "explain", "analyze", "audit", "investigate",
        "ابحث", "بحث", "ادرس", "دراسة", "اشرح", "شرح", "حلل", "تحليل", "افحص", "تحقق"
    ))
    build = _contains(original, (
        "build", "create", "implement", "develop", "design", "write code", "generate",
        "ابن", "أنشئ", "انشئ", "طوّر", "طور", "نفذ", "نفّذ", "برمج", "صمم", "صمّم", "اجعل", "أضف", "اضف"
    ))
    repair = _contains(original, (
        "fix", "repair", "debug", "restore", "correct", "broken", "bug",
        "اصلح", "أصلح", "تصحيح", "صحح", "استرجع", "تعطل", "خطأ", "خلل", "رمم", "رمّم"
    ))
    if repair:
        intent_class = "repair"
    elif build:
        intent_class = "build"
    elif research:
        intent_class = "research"
    else:
        intent_class = "general"

    approval, approval_reasons = requires_human_approval(original)
    task_id = "VX-" + uuid.uuid4().hex[:12].upper()
    steps: list[TaskStep] = []

    def add(role: str, objective: str, output: str, test: str, gated: bool = False) -> None:
        step_id = f"S{len(steps) + 1:02d}"
        steps.append(TaskStep(
            step_id=step_id,
            role=role,
            objective=objective,
            expected_output=output,
            acceptance_test=test,
            depends_on=(steps[-1].step_id,) if steps else (),
            approval_required=gated,
        ))

    add(
        "vx.intent_analyst",
        "Preserve the original request; identify the desired outcome, constraints, assumptions, and deliverables.",
        "Task contract with explicit unknowns and assumptions.",
        "The contract retains the original request and does not invent missing requirements."
    )
    add(
        "xv.memory_steward",
        "Retrieve relevant saved tasks, known project constraints, and repository evidence before proposing new components.",
        "Context bundle with source locations and freshness.",
        "Every reused fact has a retrievable source or is labeled as a memory assertion."
    )
    if research or intent_class == "general":
        add(
            "vx.research_mind",
            "Gather the minimum evidence needed; separate sourced facts from inference and unresolved questions.",
            "Evidence ledger, key findings, contradictions, and confidence limitations.",
            "Material factual claims carry source identifiers and current retrieval metadata."
        )
    if build or repair:
        add(
            "vx.systems_architect",
            "Map the task to existing VAIXLNS components and identify the smallest non-duplicative change.",
            "Architecture delta, touched paths, dependencies, and rollback plan.",
            "No canonical or historical artifact is silently replaced."
        )
        add(
            "xv.repair_engineer" if repair else "vx.builder_executor",
            "Prepare a minimal implementation or repair candidate in an isolated, authorized workspace.",
            "Candidate patch plus reproducible steps; no implicit external side effects.",
            "The patch is scoped, inspectable, and does not claim completion before execution evidence exists.",
            gated=approval
        )
    add(
        "vx.adversarial_reviewer",
        "Challenge assumptions, look for failure cases, unsafe effects, missing evidence, and alternative explanations.",
        "Counterexamples, risk notes, and unresolved obligations.",
        "High-impact and contradictory cases are explicitly represented."
    )
    add(
        "vx.verification_mind",
        "Define and run applicable acceptance, regression, security, and replay checks when execution tools are authorized.",
        "Test report with commands or method, actual output, and untested boundaries.",
        "A pass is tied to observed output; unrun tests remain pending."
    )
    add(
        "vx.explainer",
        "Explain what is known, what was produced, what was tested, and what is still unknown.",
        "Plain-language result with evidence references and next safe action.",
        "No plan, mock result, or unverified claim is presented as completed reality."
    )
    add(
        "xv.memory_steward",
        "Append the task plan, evidence pointers, artifact references, and observed decisions/results to durable project memory.",
        "Traceable checkpoint and resumption pointer.",
        "The stored event passes the memory integrity check and contains no secrets."
    )

    return TaskPlan(
        task_id=task_id,
        request=original,
        goal=original,
        intent_class=intent_class,
        status="PLANNED",
        requires_approval=approval,
        approval_reasons=approval_reasons,
        steps=tuple(steps),
    )


class MemoryStore:
    """Local append-only SQLite event store with a SHA-256 event chain.

    The store is tamper-evident, not encrypted or a secure backup service.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.path), timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS memory_events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL UNIQUE
                )
            """)
            db.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_events_no_update
                BEFORE UPDATE ON memory_events
                BEGIN SELECT RAISE(ABORT, 'memory events are append-only'); END
            """)
            db.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_events_no_delete
                BEFORE DELETE ON memory_events
                BEGIN SELECT RAISE(ABORT, 'memory events are append-only'); END
            """)

    @staticmethod
    def _canonical(value: Any) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def _digest(cls, event_fields: dict[str, Any]) -> str:
        return hashlib.sha256(cls._canonical(event_fields).encode("utf-8")).hexdigest()

    def append(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not event_type.strip():
            raise ValueError("event_type must not be empty")
        # Validate serializability before starting a transaction.
        payload_json = self._canonical(payload)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute(
                "SELECT seq, event_hash FROM memory_events ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            prev_hash = previous["event_hash"] if previous else GENESIS_HASH
            seq = int(previous["seq"]) + 1 if previous else 1
            fields = {
                "seq": seq,
                "event_id": uuid.uuid4().hex,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "payload_json": payload_json,
                "previous_hash": prev_hash,
            }
            event_hash = self._digest(fields)
            db.execute(
                """INSERT INTO memory_events
                   (seq,event_id,created_at,event_type,payload_json,previous_hash,event_hash)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    fields["seq"], fields["event_id"], fields["created_at"],
                    fields["event_type"], fields["payload_json"], fields["previous_hash"],
                    event_hash,
                ),
            )
            db.commit()
            return {**fields, "event_hash": event_hash, "payload": json.loads(payload_json)}

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")
        with self._connect() as db:
            if query.strip():
                rows = db.execute(
                    """SELECT * FROM memory_events
                       WHERE lower(event_type || ' ' || payload_json) LIKE ?
                       ORDER BY seq DESC LIMIT ?""",
                    (f"%{query.casefold()}%", limit),
                ).fetchall()
            else:
                rows = db.execute(
                    "SELECT * FROM memory_events ORDER BY seq DESC LIMIT ?", (limit,)
                ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        result["payload"] = json.loads(result.pop("payload_json"))
        return result

    def verify_chain(self) -> dict[str, Any]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM memory_events ORDER BY seq ASC").fetchall()
        expected_previous = GENESIS_HASH
        expected_seq = 1
        for row in rows:
            fields = {
                "seq": row["seq"],
                "event_id": row["event_id"],
                "created_at": row["created_at"],
                "event_type": row["event_type"],
                "payload_json": row["payload_json"],
                "previous_hash": row["previous_hash"],
            }
            if row["seq"] != expected_seq:
                return {"valid": False, "events_checked": expected_seq - 1, "reason": "sequence_gap"}
            if row["previous_hash"] != expected_previous:
                return {"valid": False, "events_checked": expected_seq - 1, "reason": "previous_hash_mismatch"}
            if self._digest(fields) != row["event_hash"]:
                return {"valid": False, "events_checked": expected_seq - 1, "reason": "event_hash_mismatch"}
            expected_previous = row["event_hash"]
            expected_seq += 1
        return {
            "valid": True,
            "events_checked": len(rows),
            "head_hash": expected_previous,
            "reason": "ok",
        }

    def checkpoint_plan(self, plan: TaskPlan) -> dict[str, Any]:
        return self.append("task_plan", plan.to_dict())
