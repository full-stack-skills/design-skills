#!/usr/bin/env python3
"""Minimal persistent runtime for design-harness SOP execution.

Pure-stdlib by design so the skill can run in most agent environments.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import uuid
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


class DesignHarnessError(RuntimeError):
    pass


class RunNotFoundError(DesignHarnessError):
    pass


class ValidationError(DesignHarnessError):
    pass


class TransitionError(DesignHarnessError):
    pass


class RunConflictError(DesignHarnessError):
    pass


class RunLockTimeoutError(DesignHarnessError):
    pass


class RunAmbiguityError(DesignHarnessError):
    pass


class RunAuthorityConflictError(DesignHarnessError):
    pass


class JournalIntegrityError(DesignHarnessError):
    pass


class JournalRecoveryError(DesignHarnessError):
    pass


class JournalRevisionNotFoundError(DesignHarnessError):
    pass


class EntityNotFoundError(DesignHarnessError):
    pass


PRIMARY_STATES = [
    "INIT",
    "BASELINE_BOUND",
    "BEHAVIOR_READY",
    "NAVIGATION_READY",
    "TASK_READY",
    "CONTINUITY_READY",
    "CANDIDATE_READY",
    "GUARD_REVIEWED",
    "AWAITING_USER_APPROVAL",
    "APPROVED",
    "DELIVERY_VERIFIED",
    "ARCHIVED",
]

CONTROL_STATES = {"RECONCILING", "BLOCKED", "CORRECTION", "CANCELLED"}
TERMINAL_STATES = {"ARCHIVED", "CANCELLED"}

EXPECTED_TRANSITIONS = {
    "INIT": ("baseline", "BASELINE_BOUND"),
    "BASELINE_BOUND": ("behavior", "BEHAVIOR_READY"),
    "BEHAVIOR_READY": ("navigation", "NAVIGATION_READY"),
    "NAVIGATION_READY": ("task", "TASK_READY"),
    "TASK_READY": ("continuity", "CONTINUITY_READY"),
    "CONTINUITY_READY": ("candidate", "CANDIDATE_READY"),
    "CANDIDATE_READY": ("guard", "GUARD_REVIEWED"),
    "GUARD_REVIEWED": ("approval-ready", "AWAITING_USER_APPROVAL"),
}

EVIDENCE_RESULT_STATE = {
    "baseline": "BASELINE_BOUND",
    "behavior": "BEHAVIOR_READY",
    "navigation": "NAVIGATION_READY",
    "task": "TASK_READY",
    "continuity": "CONTINUITY_READY",
    "candidate": "CANDIDATE_READY",
    "guard": "GUARD_REVIEWED",
    "approval-ready": "AWAITING_USER_APPROVAL",
    "delivery": "DELIVERY_VERIFIED",
}

DEFAULT_STAGE_HANDLERS = {
    "baseline": "product-design",
    "behavior": "feature-design",
    "navigation": "navigation-design",
    "task": "product-design",
    "continuity": "ui-continuity",
    "candidate": "renderer",
    "guard": "design-guard",
    "approval-ready": "design-harness",
    "delivery": "delivery-verification",
    "correction": "ui-continuity",
}

VALID_EVIDENCE_STATUSES = {"pass", "fail", "unknown", "needs-decision"}
VALID_ARTIFACT_STATUSES = {"valid", "invalidated", "superseded", "unknown"}
VALID_MATURITY = {
    "candidate",
    "preferred",
    "approved-master",
    "verified-delivery",
    "archived",
}

ENTITY_COLLECTIONS = {
    "evidence": ("evidence", "evidence_id"),
    "artifact": ("artifacts", "artifact_id"),
    "dispatch": ("dispatches", "dispatch_id"),
    "decision": ("decisions", "decision_id"),
    "invalidation": ("invalidations", "invalidation_id"),
}

PROFILE_DIR = Path(__file__).resolve().parents[1] / "profiles"


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"profile file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in profile file {path}: {exc}") from exc


def load_profile(profile_id: str) -> Dict[str, Any]:
    catalog = _read_json(PROFILE_DIR / "catalog.json")
    entries = catalog.get("profiles")
    if not isinstance(entries, list):
        raise ValidationError("profile catalog must contain a profiles list")

    entry = next((item for item in entries if item.get("id") == profile_id), None)
    if entry is None:
        raise ValidationError(f"unknown design harness profile: {profile_id}")

    file_name = entry.get("file")
    if not file_name:
        raise ValidationError(f"profile catalog entry has no file: {profile_id}")

    profile = _read_json(PROFILE_DIR / file_name)
    if profile.get("id") != profile_id:
        raise ValidationError(
            f"profile id mismatch: catalog={profile_id}, file={profile.get('id')}"
        )
    if not isinstance(profile.get("version"), int):
        raise ValidationError(f"profile version must be an integer: {profile_id}")
    if profile.get("entry_mode") not in {"start", "correction"}:
        raise ValidationError(f"invalid profile entry_mode: {profile_id}")

    stages = profile.get("stages")
    if not isinstance(stages, list) or not stages:
        raise ValidationError(f"profile must define a non-empty stages list: {profile_id}")
    for index, stage in enumerate(stages):
        for field in ("evidence_stage", "target_state", "handler"):
            if not stage.get(field):
                raise ValidationError(
                    f"profile {profile_id} stage {index} missing {field}"
                )
        _validate_state(stage["target_state"])

    return profile


def list_profiles() -> list[Dict[str, Any]]:
    catalog = _read_json(PROFILE_DIR / "catalog.json")
    result = []
    for entry in catalog.get("profiles", []):
        profile = load_profile(entry["id"])
        result.append(
            {
                "id": profile["id"],
                "version": profile["version"],
                "title": profile.get("title"),
                "description": profile.get("description"),
                "entry_mode": profile.get("entry_mode"),
                "parallel_policy": profile.get("parallel_policy"),
                "child_scope": profile.get("child_scope"),
                "final_gate": profile.get("final_gate"),
            }
        )
    return result


def _profile_next_stage(run: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    plan = run.get("stage_plan") or []
    cursor = int(run.get("stage_cursor", 0))
    if 0 <= cursor < len(plan):
        return deepcopy(plan[cursor])
    return None


def _profile_cursor_for_state(run: Dict[str, Any], affected_state: str) -> int:
    plan = run.get("stage_plan") or []
    affected_index = _state_index(affected_state)
    for index, stage in enumerate(plan):
        target = stage["target_state"]
        if target in PRIMARY_STATES and _state_index(target) >= affected_index:
            return index
    return len(plan)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _lease_expiry(lease_seconds: int) -> str:
    if not isinstance(lease_seconds, int) or lease_seconds <= 0:
        raise ValidationError("lease_seconds must be a positive integer")
    return (datetime.now(timezone.utc) + timedelta(seconds=lease_seconds)).isoformat()


def dispatch_lease_expired(
    dispatch: Dict[str, Any],
    *,
    now: Optional[datetime] = None,
) -> bool:
    if dispatch.get("status") != "claimed":
        return False
    value = dispatch.get("lease_expires_at")
    if not value:
        return False
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return _parse_utc(value) <= current.astimezone(timezone.utc)


def _runs_dir(store: Path | str) -> Path:
    return Path(store) / "runs"


def run_lock_path(store: Path | str, run_id: str) -> Path:
    return _runs_dir(store) / f"{run_id}.lock"


def registry_lock_path(store: Path | str) -> Path:
    return _runs_dir(store) / ".registry.lock"


@contextmanager
def _registry_lock(
    store: Path | str,
    *,
    timeout_seconds: float = 2.0,
    stale_seconds: float = 30.0,
):
    directory = _runs_dir(store)
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = registry_lock_path(store)
    deadline = time.monotonic() + timeout_seconds
    fd = None

    while fd is None:
        try:
            fd = os.open(
                lock_path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
            payload = json.dumps(
                {
                    "pid": os.getpid(),
                    "created_at": utc_now(),
                    "kind": "registry",
                },
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
            os.write(fd, payload)
            os.fsync(fd)
        except FileExistsError:
            try:
                age = time.time() - lock_path.stat().st_mtime
            except FileNotFoundError:
                continue
            if age >= stale_seconds:
                try:
                    lock_path.unlink()
                except FileNotFoundError:
                    pass
                continue
            if time.monotonic() >= deadline:
                raise RunLockTimeoutError(
                    "timed out acquiring design harness registry lock"
                )
            time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))

    try:
        yield lock_path
    finally:
        if fd is not None:
            os.close(fd)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


@contextmanager
def _run_write_lock(
    store: Path | str,
    run_id: str,
    *,
    timeout_seconds: float = 2.0,
    stale_seconds: float = 30.0,
):
    if timeout_seconds < 0:
        raise ValidationError("lock timeout must be non-negative")
    if stale_seconds <= 0:
        raise ValidationError("lock stale threshold must be positive")

    directory = _runs_dir(store)
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = run_lock_path(store, run_id)
    deadline = time.monotonic() + timeout_seconds
    fd = None

    while fd is None:
        try:
            fd = os.open(
                lock_path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
            payload = json.dumps(
                {
                    "pid": os.getpid(),
                    "created_at": utc_now(),
                    "run_id": run_id,
                },
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
            os.write(fd, payload)
            os.fsync(fd)
        except FileExistsError:
            try:
                age = time.time() - lock_path.stat().st_mtime
            except FileNotFoundError:
                continue

            if age >= stale_seconds:
                try:
                    lock_path.unlink()
                except FileNotFoundError:
                    pass
                continue

            if time.monotonic() >= deadline:
                raise RunLockTimeoutError(
                    f"timed out acquiring run lock for {run_id}"
                )
            time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))

    try:
        yield lock_path
    finally:
        if fd is not None:
            os.close(fd)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def _run_path(store: Path | str, run_id: str) -> Path:
    return _runs_dir(store) / f"{run_id}.json"


def _append_history(run: Dict[str, Any], event: str, **details: Any) -> None:
    run.setdefault("history", []).append(
        {"at": utc_now(), "event": event, "details": details}
    )


def _canonical_scope(run: Dict[str, Any]) -> str:
    ids = run.get("scope_ids") or []
    joined = ",".join(ids)
    return f'{run["scope_type"]}:{joined}'


def _validate_state(state: str) -> None:
    if state not in PRIMARY_STATES and state not in CONTROL_STATES:
        raise ValidationError(f"unknown state: {state}")


def _state_index(state: str) -> int:
    try:
        return PRIMARY_STATES.index(state)
    except ValueError as exc:
        raise ValidationError(f"state is not a primary progression state: {state}") from exc


def _predecessor(state: str) -> str:
    index = _state_index(state)
    return PRIMARY_STATES[max(0, index - 1)]


def _normalize_evidence(evidence: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    required = {"stage", "status", "producer", "observed_result"}
    missing = sorted(required - set(evidence))
    if missing:
        raise ValidationError(f"evidence missing required fields: {', '.join(missing)}")

    status = evidence["status"]
    if status not in VALID_EVIDENCE_STATUSES:
        raise ValidationError(f"invalid evidence status: {status}")

    stage = evidence["stage"]
    if stage not in EVIDENCE_RESULT_STATE and stage != "correction":
        raise ValidationError(f"invalid evidence stage: {stage}")

    item = deepcopy(evidence)
    item.setdefault("evidence_id", f"evidence_{uuid.uuid4().hex[:12]}")
    item["run_id"] = run_id
    item.setdefault("artifact_ids", [])
    item.setdefault("input_versions", {})
    item.setdefault("limitations", [])
    item.setdefault("timestamp", utc_now())
    item.setdefault("provenance", item.get("producer"))
    item.setdefault("validity", "valid")
    return item


def run_journal_path(store: Path | str, run_id: str) -> Path:
    return _runs_dir(store) / f"{run_id}.events.jsonl"


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _read_journal_events(
    store: Path | str,
    run_id: str,
) -> list[Dict[str, Any]]:
    path = run_journal_path(store, run_id)
    if not path.exists():
        return []
    events = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise JournalIntegrityError(
                f"invalid journal JSON for {run_id} at line {line_number}: {exc}"
            ) from exc
        if not isinstance(item, dict):
            raise JournalIntegrityError(
                f"journal event for {run_id} at line {line_number} is not an object"
            )
        events.append(item)
    return events


def _event_hash_payload(event: Dict[str, Any]) -> Dict[str, Any]:
    payload = deepcopy(event)
    payload.pop("event_hash", None)
    return payload


def _build_journal_event(
    run: Dict[str, Any],
    *,
    previous_revision: int,
    previous_event_hash: Optional[str],
    event_type: str,
) -> Dict[str, Any]:
    snapshot = deepcopy(run)
    event = {
        "journal_version": 1,
        "event_id": f"event_{uuid.uuid4().hex[:12]}",
        "event_type": event_type,
        "run_id": run["run_id"],
        "revision": run["revision"],
        "previous_revision": previous_revision,
        "recorded_at": utc_now(),
        "previous_event_hash": previous_event_hash,
        "snapshot_hash": _sha256_json(snapshot),
        "snapshot": snapshot,
        "cause": (
            (snapshot.get("history") or [{}])[-1].get("event")
            if snapshot.get("history")
            else None
        ),
    }
    event["event_hash"] = hashlib.sha256(
        _canonical_json_bytes(_event_hash_payload(event))
    ).hexdigest()
    return event


def _append_journal_event(
    store: Path | str,
    run_id: str,
    event: Dict[str, Any],
) -> None:
    path = run_journal_path(store, run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        event,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def _bootstrap_journal_if_needed(
    store: Path | str,
    persisted: Optional[Dict[str, Any]],
) -> tuple[int, Optional[str]]:
    if persisted is None:
        return 0, None

    run_id = persisted["run_id"]
    events = _read_journal_events(store, run_id)
    if events:
        latest = events[-1]
        return int(latest["revision"]), latest.get("event_hash")

    revision = int(persisted.get("revision", 0))
    if revision <= 0:
        return 0, None

    bootstrap = _build_journal_event(
        deepcopy(persisted),
        previous_revision=max(0, revision - 1),
        previous_event_hash=None,
        event_type="run.journal-bootstrap",
    )
    _append_journal_event(store, run_id, bootstrap)
    return revision, bootstrap["event_hash"]


def verify_run_journal(
    store: Path | str,
    run_id: str,
) -> Dict[str, Any]:
    path = run_journal_path(store, run_id)
    if not path.exists():
        return {
            "run_id": run_id,
            "valid": False,
            "event_count": 0,
            "latest_revision": None,
            "latest_event_hash": None,
            "errors": ["journal file does not exist"],
        }

    try:
        events = _read_journal_events(store, run_id)
    except JournalIntegrityError as exc:
        return {
            "run_id": run_id,
            "valid": False,
            "event_count": 0,
            "latest_revision": None,
            "latest_event_hash": None,
            "errors": [str(exc)],
        }

    errors = []
    previous = None
    for index, event in enumerate(events):
        line_number = index + 1
        revision = event.get("revision")
        snapshot = event.get("snapshot")
        if event.get("run_id") != run_id:
            errors.append(
                f"line {line_number}: run_id mismatch"
            )
        if not isinstance(revision, int) or revision <= 0:
            errors.append(
                f"line {line_number}: invalid revision {revision}"
            )
            continue
        if not isinstance(snapshot, dict):
            errors.append(
                f"line {line_number}: snapshot missing or invalid"
            )
            continue
        if snapshot.get("run_id") != run_id:
            errors.append(
                f"line {line_number}: snapshot run_id mismatch"
            )
        if snapshot.get("revision") != revision:
            errors.append(
                f"line {line_number}: snapshot revision mismatch"
            )

        expected_snapshot_hash = _sha256_json(snapshot)
        if event.get("snapshot_hash") != expected_snapshot_hash:
            errors.append(
                f"line {line_number}: snapshot hash mismatch"
            )

        expected_event_hash = hashlib.sha256(
            _canonical_json_bytes(_event_hash_payload(event))
        ).hexdigest()
        if event.get("event_hash") != expected_event_hash:
            errors.append(
                f"line {line_number}: event hash mismatch"
            )

        if previous is None:
            if event.get("previous_event_hash") is not None:
                errors.append(
                    f"line {line_number}: first event previous hash must be null"
                )
            if event.get("previous_revision") != revision - 1:
                errors.append(
                    f"line {line_number}: invalid first previous_revision"
                )
        else:
            if revision != previous["revision"] + 1:
                errors.append(
                    f"line {line_number}: revision is not contiguous"
                )
            if event.get("previous_revision") != previous["revision"]:
                errors.append(
                    f"line {line_number}: previous_revision mismatch"
                )
            if event.get("previous_event_hash") != previous.get("event_hash"):
                errors.append(
                    f"line {line_number}: previous event hash mismatch"
                )
        previous = event

    latest = events[-1] if events else None
    return {
        "run_id": run_id,
        "valid": bool(events) and not errors,
        "event_count": len(events),
        "latest_revision": latest.get("revision") if latest else None,
        "latest_event_hash": latest.get("event_hash") if latest else None,
        "errors": errors,
    }


def replay_run_from_journal(
    store: Path | str,
    run_id: str,
) -> Dict[str, Any]:
    result = verify_run_journal(store, run_id)
    if not result["valid"]:
        raise JournalIntegrityError(
            f"cannot replay invalid journal for {run_id}: "
            + "; ".join(result["errors"])
        )
    events = _read_journal_events(store, run_id)
    return deepcopy(events[-1]["snapshot"])


def run_journal_summary(
    store: Path | str,
    run_id: str,
) -> Dict[str, Any]:
    result = verify_run_journal(store, run_id)
    return {
        "run_id": run_id,
        "valid": result["valid"],
        "event_count": result["event_count"],
        "latest_revision": result["latest_revision"],
        "latest_event_hash": result["latest_event_hash"],
        "errors": result["errors"],
        "path": str(run_journal_path(store, run_id)),
    }


def _verified_journal_events(
    store: Path | str,
    run_id: str,
) -> list[Dict[str, Any]]:
    result = verify_run_journal(store, run_id)
    if not result["valid"]:
        raise JournalIntegrityError(
            f"invalid journal for {run_id}: "
            + "; ".join(result["errors"])
        )
    return _read_journal_events(store, run_id)


def run_at_revision(
    store: Path | str,
    run_id: str,
    revision: int,
) -> Dict[str, Any]:
    if not isinstance(revision, int) or revision <= 0:
        raise ValidationError("revision must be a positive integer")

    for event in _verified_journal_events(store, run_id):
        if event.get("revision") == revision:
            return deepcopy(event["snapshot"])

    raise JournalRevisionNotFoundError(
        f"run {run_id} has no journal revision {revision}"
    )


def _json_pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _diff_values(
    before: Any,
    after: Any,
    *,
    path: str,
    changes: list[Dict[str, Any]],
    ignore_volatile: bool,
) -> None:
    volatile_paths = {"/revision", "/updated_at"}
    if ignore_volatile and path in volatile_paths:
        return

    if isinstance(before, dict) and isinstance(after, dict):
        keys = sorted(set(before) | set(after))
        for key in keys:
            child_path = f"{path}/{_json_pointer_escape(str(key))}"
            if key not in before:
                if not (ignore_volatile and child_path in volatile_paths):
                    changes.append(
                        {
                            "path": child_path,
                            "kind": "added",
                            "before": None,
                            "after": deepcopy(after[key]),
                        }
                    )
            elif key not in after:
                if not (ignore_volatile and child_path in volatile_paths):
                    changes.append(
                        {
                            "path": child_path,
                            "kind": "removed",
                            "before": deepcopy(before[key]),
                            "after": None,
                        }
                    )
            else:
                _diff_values(
                    before[key],
                    after[key],
                    path=child_path,
                    changes=changes,
                    ignore_volatile=ignore_volatile,
                )
        return

    if before != after:
        changes.append(
            {
                "path": path or "/",
                "kind": "changed",
                "before": deepcopy(before),
                "after": deepcopy(after),
            }
        )


def diff_run_revisions(
    store: Path | str,
    run_id: str,
    from_revision: int,
    to_revision: int,
    *,
    ignore_volatile: bool = False,
) -> Dict[str, Any]:
    before = run_at_revision(store, run_id, from_revision)
    after = run_at_revision(store, run_id, to_revision)
    changes: list[Dict[str, Any]] = []
    _diff_values(
        before,
        after,
        path="",
        changes=changes,
        ignore_volatile=ignore_volatile,
    )
    return {
        "run_id": run_id,
        "from_revision": from_revision,
        "to_revision": to_revision,
        "ignore_volatile": ignore_volatile,
        "change_count": len(changes),
        "changes": changes,
    }


def run_audit_timeline(
    store: Path | str,
    run_id: str,
    *,
    from_revision: Optional[int] = None,
    to_revision: Optional[int] = None,
) -> list[Dict[str, Any]]:
    if from_revision is not None and from_revision <= 0:
        raise ValidationError("from_revision must be positive")
    if to_revision is not None and to_revision <= 0:
        raise ValidationError("to_revision must be positive")
    if (
        from_revision is not None
        and to_revision is not None
        and from_revision > to_revision
    ):
        raise ValidationError("from_revision cannot exceed to_revision")

    rows = []
    for event in _verified_journal_events(store, run_id):
        revision = event["revision"]
        if from_revision is not None and revision < from_revision:
            continue
        if to_revision is not None and revision > to_revision:
            continue

        snapshot = event["snapshot"]
        rows.append(
            {
                "revision": revision,
                "previous_revision": event.get("previous_revision"),
                "event_type": event.get("event_type"),
                "recorded_at": event.get("recorded_at"),
                "event_hash": event.get("event_hash"),
                "snapshot_hash": event.get("snapshot_hash"),
                "cause": event.get("cause"),
                "state": snapshot.get("state"),
                "profile_id": (snapshot.get("profile") or {}).get("id"),
                "profile_version": (snapshot.get("profile") or {}).get("version"),
                "artifact_count": len(snapshot.get("artifacts") or []),
                "evidence_count": len(snapshot.get("evidence") or []),
                "dispatch_count": len(snapshot.get("dispatches") or []),
                "decision_count": len(snapshot.get("decisions") or []),
                "invalidation_count": len(snapshot.get("invalidations") or []),
            }
        )
    return rows


def _json_pointer_get(
    value: Any,
    pointer: str,
) -> tuple[bool, Any]:
    if pointer == "":
        return True, deepcopy(value)
    if not pointer.startswith("/"):
        raise ValidationError(
            "trace path must be a JSON Pointer starting with '/'"
        )

    current = value
    for raw_part in pointer.split("/")[1:]:
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if part not in current:
                return False, None
            current = current[part]
        elif isinstance(current, list):
            if not part.isdigit():
                return False, None
            index = int(part)
            if index < 0 or index >= len(current):
                return False, None
            current = current[index]
        else:
            return False, None
    return True, deepcopy(current)


def trace_run_path(
    store: Path | str,
    run_id: str,
    path: str,
) -> Dict[str, Any]:
    events = _verified_journal_events(store, run_id)
    changes = []
    previous_exists = None
    previous_value = None

    for event in events:
        snapshot = event["snapshot"]
        exists, value = _json_pointer_get(snapshot, path)
        if (
            previous_exists is None
            or exists != previous_exists
            or value != previous_value
        ):
            changes.append(
                {
                    "revision": event["revision"],
                    "exists": exists,
                    "value": value,
                    "state": snapshot.get("state"),
                    "cause": event.get("cause"),
                    "recorded_at": event.get("recorded_at"),
                    "event_hash": event.get("event_hash"),
                }
            )
            previous_exists = exists
            previous_value = deepcopy(value)

    return {
        "run_id": run_id,
        "path": path,
        "change_count": len(changes),
        "changes": changes,
    }


def _entity_spec(entity_type: str) -> tuple[str, str]:
    spec = ENTITY_COLLECTIONS.get(entity_type)
    if spec is None:
        raise ValidationError(
            "unknown entity type "
            f"{entity_type}; expected one of {', '.join(sorted(ENTITY_COLLECTIONS))}"
        )
    return spec


def _find_entity_in_snapshot(
    snapshot: Dict[str, Any],
    entity_type: str,
    entity_id: str,
) -> Optional[Dict[str, Any]]:
    collection_name, id_field = _entity_spec(entity_type)
    for item in snapshot.get(collection_name) or []:
        if isinstance(item, dict) and item.get(id_field) == entity_id:
            return deepcopy(item)
    return None


def _snapshot_entity_map(
    snapshot: Dict[str, Any],
    entity_type: str,
) -> Dict[str, Dict[str, Any]]:
    collection_name, id_field = _entity_spec(entity_type)
    result: Dict[str, Dict[str, Any]] = {}
    for item in snapshot.get(collection_name) or []:
        if not isinstance(item, dict):
            continue
        entity_id = item.get(id_field)
        if entity_id:
            result[str(entity_id)] = deepcopy(item)
    return result


def _related_invalidation_ids(
    snapshot: Dict[str, Any],
    entity_type: str,
    entity_id: str,
) -> list[str]:
    if entity_type not in {"evidence", "artifact"}:
        return []
    key = "evidence_ids" if entity_type == "evidence" else "artifact_ids"
    ids = []
    for invalidation in snapshot.get("invalidations") or []:
        if entity_id in (invalidation.get(key) or []):
            invalidation_id = invalidation.get("invalidation_id")
            if invalidation_id:
                ids.append(invalidation_id)
    return sorted(set(ids))


def entity_history(
    store: Path | str,
    run_id: str,
    entity_type: str,
    entity_id: str,
) -> Dict[str, Any]:
    _entity_spec(entity_type)
    events = _verified_journal_events(store, run_id)

    changes = []
    previous_exists = False
    previous_entity = None
    seen = False

    for event in events:
        snapshot = event["snapshot"]
        entity = _find_entity_in_snapshot(snapshot, entity_type, entity_id)
        exists = entity is not None

        if not seen and not exists:
            continue

        changed = False
        kind = None
        if exists and not previous_exists:
            changed = True
            kind = "created"
        elif exists and previous_exists and entity != previous_entity:
            changed = True
            kind = "changed"
        elif not exists and previous_exists:
            changed = True
            kind = "removed"

        if changed:
            changes.append(
                {
                    "revision": event["revision"],
                    "kind": kind,
                    "entity": deepcopy(entity) if exists else None,
                    "state": snapshot.get("state"),
                    "cause": event.get("cause"),
                    "recorded_at": event.get("recorded_at"),
                    "event_hash": event.get("event_hash"),
                    "related_invalidation_ids": _related_invalidation_ids(
                        snapshot,
                        entity_type,
                        entity_id,
                    ),
                }
            )

        if exists:
            seen = True
        previous_exists = exists
        previous_entity = deepcopy(entity) if exists else None

    if not seen:
        raise EntityNotFoundError(
            f"{entity_type} entity not found in run {run_id}: {entity_id}"
        )

    latest = None
    latest_revision = None
    for event in reversed(events):
        entity = _find_entity_in_snapshot(
            event["snapshot"], entity_type, entity_id
        )
        if entity is not None:
            latest = entity
            latest_revision = event["revision"]
            break

    return {
        "run_id": run_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "first_revision": changes[0]["revision"] if changes else None,
        "last_changed_revision": (
            changes[-1]["revision"] if changes else None
        ),
        "latest_revision": latest_revision,
        "latest": latest,
        "change_count": len(changes),
        "changes": changes,
    }


def entity_audit_index(
    store: Path | str,
    run_id: str,
) -> Dict[str, Any]:
    events = _verified_journal_events(store, run_id)
    index: Dict[str, list[Dict[str, Any]]] = {
        entity_type: [] for entity_type in ENTITY_COLLECTIONS
    }

    for entity_type in ENTITY_COLLECTIONS:
        records: Dict[str, Dict[str, Any]] = {}
        previous: Dict[str, Dict[str, Any]] = {}

        for event in events:
            revision = event["revision"]
            snapshot = event["snapshot"]
            current = _snapshot_entity_map(snapshot, entity_type)

            for entity_id, entity in current.items():
                record = records.get(entity_id)
                if record is None:
                    record = {
                        "entity_id": entity_id,
                        "first_revision": revision,
                        "last_revision": revision,
                        "last_changed_revision": revision,
                        "change_count": 1,
                        "latest": deepcopy(entity),
                    }
                    records[entity_id] = record
                else:
                    record["last_revision"] = revision
                    record["latest"] = deepcopy(entity)
                    if previous.get(entity_id) != entity:
                        record["last_changed_revision"] = revision
                        record["change_count"] += 1

            previous = current

        index[entity_type] = sorted(
            records.values(),
            key=lambda item: (
                item["first_revision"],
                item["entity_id"],
            ),
        )

    return {
        "run_id": run_id,
        "latest_revision": events[-1]["revision"],
        **index,
    }


def _provenance_edges(
    snapshot: Dict[str, Any],
) -> list[Dict[str, str]]:
    edges: list[Dict[str, str]] = []
    known = {
        entity_type: set(_snapshot_entity_map(snapshot, entity_type))
        for entity_type in ENTITY_COLLECTIONS
    }

    def add_edge(
        source_type: str,
        source_id: Optional[str],
        relation: str,
        target_type: str,
        target_id: Optional[str],
    ) -> None:
        if not source_id or not target_id:
            return
        if source_id not in known.get(source_type, set()):
            return
        if target_id not in known.get(target_type, set()):
            return
        edge = {
            "source_type": source_type,
            "source_id": source_id,
            "relation": relation,
            "target_type": target_type,
            "target_id": target_id,
        }
        if edge not in edges:
            edges.append(edge)

    for dispatch in snapshot.get("dispatches") or []:
        add_edge(
            "dispatch",
            dispatch.get("dispatch_id"),
            "produced-evidence",
            "evidence",
            dispatch.get("evidence_id"),
        )

    for evidence in snapshot.get("evidence") or []:
        evidence_id = evidence.get("evidence_id")
        dispatch_id = evidence.get("dispatch_id")
        if dispatch_id:
            add_edge(
                "dispatch",
                dispatch_id,
                "produced-evidence",
                "evidence",
                evidence_id,
            )
        for artifact_id in evidence.get("artifact_ids") or []:
            add_edge(
                "evidence",
                evidence_id,
                "mentions-artifact",
                "artifact",
                artifact_id,
            )

    for artifact in snapshot.get("artifacts") or []:
        artifact_id = artifact.get("artifact_id")
        for evidence_id in artifact.get("evidence_ids") or []:
            add_edge(
                "artifact",
                artifact_id,
                "supported-by",
                "evidence",
                evidence_id,
            )

    for invalidation in snapshot.get("invalidations") or []:
        invalidation_id = invalidation.get("invalidation_id")
        for evidence_id in invalidation.get("evidence_ids") or []:
            add_edge(
                "invalidation",
                invalidation_id,
                "invalidated-evidence",
                "evidence",
                evidence_id,
            )
        for artifact_id in invalidation.get("artifact_ids") or []:
            add_edge(
                "invalidation",
                invalidation_id,
                "invalidated-artifact",
                "artifact",
                artifact_id,
            )

    return sorted(
        edges,
        key=lambda item: (
            item["source_type"],
            item["source_id"],
            item["relation"],
            item["target_type"],
            item["target_id"],
        ),
    )


def entity_provenance_graph(
    store: Path | str,
    run_id: str,
    entity_type: str,
    entity_id: str,
    *,
    max_depth: int = 2,
) -> Dict[str, Any]:
    _entity_spec(entity_type)
    if not isinstance(max_depth, int) or max_depth < 0:
        raise ValidationError("max_depth must be a non-negative integer")

    events = _verified_journal_events(store, run_id)
    snapshot = events[-1]["snapshot"]
    root = _find_entity_in_snapshot(
        snapshot, entity_type, entity_id
    )
    if root is None:
        raise EntityNotFoundError(
            f"{entity_type} entity not found in latest run snapshot "
            f"{run_id}: {entity_id}"
        )

    all_nodes: Dict[tuple[str, str], Dict[str, Any]] = {}
    for item_type in ENTITY_COLLECTIONS:
        for item_id, entity in _snapshot_entity_map(
            snapshot, item_type
        ).items():
            all_nodes[(item_type, item_id)] = {
                "entity_type": item_type,
                "entity_id": item_id,
                "entity": entity,
            }

    edges = _provenance_edges(snapshot)
    adjacency: Dict[tuple[str, str], set[tuple[str, str]]] = {
        key: set() for key in all_nodes
    }
    for edge in edges:
        source = (edge["source_type"], edge["source_id"])
        target = (edge["target_type"], edge["target_id"])
        adjacency.setdefault(source, set()).add(target)
        adjacency.setdefault(target, set()).add(source)

    root_key = (entity_type, entity_id)
    distances = {root_key: 0}
    queue = [root_key]
    while queue:
        current = queue.pop(0)
        depth = distances[current]
        if depth >= max_depth:
            continue
        for neighbor in sorted(adjacency.get(current, set())):
            if neighbor not in distances:
                distances[neighbor] = depth + 1
                queue.append(neighbor)

    included = set(distances)
    graph_edges = [
        edge
        for edge in edges
        if (edge["source_type"], edge["source_id"]) in included
        and (edge["target_type"], edge["target_id"]) in included
    ]
    nodes = []
    for key in sorted(
        included,
        key=lambda item: (
            distances[item],
            item[0],
            item[1],
        ),
    ):
        node = deepcopy(all_nodes[key])
        node["depth"] = distances[key]
        try:
            history = entity_history(
                store, run_id, key[0], key[1]
            )
            node["first_revision"] = history["first_revision"]
            node["last_changed_revision"] = history[
                "last_changed_revision"
            ]
        except EntityNotFoundError:
            node["first_revision"] = None
            node["last_changed_revision"] = None
        nodes.append(node)

    return {
        "run_id": run_id,
        "revision": events[-1]["revision"],
        "root": {
            "entity_type": entity_type,
            "entity_id": entity_id,
        },
        "max_depth": max_depth,
        "node_count": len(nodes),
        "edge_count": len(graph_edges),
        "nodes": nodes,
        "edges": graph_edges,
    }


def _write_materialized_snapshot(
    path: Path,
    run: Dict[str, Any],
) -> None:
    temp_path = path.with_name(
        f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    )
    try:
        with temp_path.open("w", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    run,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.replace(path)
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


def recover_run_snapshot(
    store: Path | str,
    run_id: str,
    *,
    lock_timeout_seconds: float = 2.0,
    lock_stale_seconds: float = 30.0,
) -> Dict[str, Any]:
    replayed = replay_run_from_journal(store, run_id)
    path = _run_path(store, run_id)

    with _run_write_lock(
        store,
        run_id,
        timeout_seconds=lock_timeout_seconds,
        stale_seconds=lock_stale_seconds,
    ):
        if path.exists():
            try:
                current = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                current = None
            if current is not None:
                current_revision = current.get("revision", 0)
                if (
                    isinstance(current_revision, int)
                    and current_revision > replayed["revision"]
                ):
                    raise JournalRecoveryError(
                        f"materialized snapshot revision {current_revision} "
                        f"is newer than journal revision {replayed['revision']} "
                        f"for {run_id}"
                    )
                if (
                    current_revision == replayed["revision"]
                    and _sha256_json(current) == _sha256_json(replayed)
                ):
                    return deepcopy(current)

        path.parent.mkdir(parents=True, exist_ok=True)
        _write_materialized_snapshot(path, replayed)

    return deepcopy(replayed)


def save_run(
    store: Path | str,
    run: Dict[str, Any],
    *,
    lock_timeout_seconds: float = 2.0,
    lock_stale_seconds: float = 30.0,
) -> Dict[str, Any]:
    if "run_id" not in run:
        raise ValidationError("run_id is required")
    _validate_state(run["state"])

    run_id = run["run_id"]
    expected_revision = run.get("revision", 0)
    if not isinstance(expected_revision, int) or expected_revision < 0:
        raise RunConflictError(
            f"invalid expected revision for {run_id}: {expected_revision}"
        )

    directory = _runs_dir(store)
    directory.mkdir(parents=True, exist_ok=True)
    path = _run_path(store, run_id)

    with _run_write_lock(
        store,
        run_id,
        timeout_seconds=lock_timeout_seconds,
        stale_seconds=lock_stale_seconds,
    ):
        persisted = None
        if path.exists():
            try:
                persisted = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ValidationError(
                    f"invalid persisted run JSON for {run_id}: {exc}"
                ) from exc
            current_revision = persisted.get("revision", 0)
            if not isinstance(current_revision, int) or current_revision < 0:
                raise ValidationError(
                    f"invalid persisted revision for {run_id}: {current_revision}"
                )
            if current_revision != expected_revision:
                raise RunConflictError(
                    f"run revision conflict for {run_id}: "
                    f"expected {expected_revision}, current {current_revision}"
                )
            next_revision = current_revision + 1
        else:
            current_revision = 0
            if expected_revision != 0:
                raise RunConflictError(
                    f"cannot create {run_id} from revision {expected_revision}"
                )
            if run_journal_path(store, run_id).exists():
                raise JournalRecoveryError(
                    f"journal exists without materialized snapshot for {run_id}; "
                    "recover the snapshot before writing"
                )
            next_revision = 1

        journal_revision, previous_event_hash = _bootstrap_journal_if_needed(
            store, persisted
        )
        if journal_revision != current_revision:
            raise JournalRecoveryError(
                f"journal revision {journal_revision} does not match "
                f"materialized revision {current_revision} for {run_id}; "
                "verify and recover before writing"
            )

        stored = deepcopy(run)
        stored["revision"] = next_revision
        stored["updated_at"] = utc_now()

        event = _build_journal_event(
            stored,
            previous_revision=current_revision,
            previous_event_hash=previous_event_hash,
            event_type="run.created" if next_revision == 1 else "run.updated",
        )

        # Journal first: if snapshot replacement fails, replay/recovery can
        # reconstruct the committed revision and future writes will stop until
        # the materialized snapshot is reconciled.
        _append_journal_event(store, run_id, event)
        _write_materialized_snapshot(path, stored)

    run.clear()
    run.update(deepcopy(stored))
    return deepcopy(stored)


def load_run(store: Path | str, run_id: str) -> Dict[str, Any]:
    path = _run_path(store, run_id)
    if not path.exists():
        raise RunNotFoundError(f"run not found: {run_id}")
    run = json.loads(path.read_text(encoding="utf-8"))
    _validate_state(run["state"])
    revision = run.get("revision", 0)
    if not isinstance(revision, int) or revision < 0:
        raise ValidationError(
            f"invalid persisted revision for {run_id}: {revision}"
        )
    run.setdefault("revision", revision)
    return run


def _normalized_scope_ids(scope_ids: Iterable[str]) -> list[str]:
    return sorted({str(item) for item in scope_ids if str(item).strip()})


def _run_summary(run: Dict[str, Any]) -> Dict[str, Any]:
    profile = run.get("profile") or {}
    return {
        "run_id": run["run_id"],
        "revision": run.get("revision", 0),
        "product_id": run.get("product_id"),
        "product_version": run.get("product_version"),
        "surface": run.get("surface"),
        "scope_type": run.get("scope_type"),
        "scope_ids": deepcopy(run.get("scope_ids") or []),
        "scope": _canonical_scope(run),
        "profile_id": profile.get("id"),
        "profile_version": profile.get("version"),
        "state": run.get("state"),
        "parent_run_id": run.get("parent_run_id"),
        "shared_baseline": run.get("shared_baseline"),
        "created_at": run.get("created_at"),
        "updated_at": run.get("updated_at"),
        "archived_at": run.get("archived_at"),
    }


def scan_runs(store: Path | str) -> Dict[str, Any]:
    directory = _runs_dir(store)
    if not directory.exists():
        return {"runs": [], "diagnostics": []}

    runs = []
    diagnostics = []
    for path in sorted(directory.glob("*.json")):
        try:
            run = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(run, dict) or not run.get("run_id"):
                raise ValidationError("run document missing run_id")
            _validate_state(run["state"])
            revision = run.get("revision", 0)
            if not isinstance(revision, int) or revision < 0:
                raise ValidationError(f"invalid revision: {revision}")
            run.setdefault("revision", revision)
            runs.append(run)
        except Exception as exc:
            diagnostics.append(
                {
                    "file": path.name,
                    "error": type(exc).__name__,
                    "message": str(exc),
                }
            )

    runs.sort(
        key=lambda item: (
            item.get("updated_at") or "",
            item.get("created_at") or "",
            item.get("run_id") or "",
        ),
        reverse=True,
    )
    return {"runs": runs, "diagnostics": diagnostics}


def list_runs(store: Path | str) -> list[Dict[str, Any]]:
    return [_run_summary(run) for run in scan_runs(store)["runs"]]


def find_runs(
    store: Path | str,
    *,
    product_id: Optional[str] = None,
    product_version: Optional[str] = None,
    surface: Optional[str] = None,
    scope_type: Optional[str] = None,
    scope_ids: Optional[Iterable[str]] = None,
    profile_id: Optional[str] = None,
    include_terminal: bool = True,
) -> list[Dict[str, Any]]:
    normalized_scope = (
        _normalized_scope_ids(scope_ids) if scope_ids is not None else None
    )
    matches = []

    for run in scan_runs(store)["runs"]:
        profile = run.get("profile") or {}
        if product_id is not None and run.get("product_id") != product_id:
            continue
        if (
            product_version is not None
            and run.get("product_version") != product_version
        ):
            continue
        if surface is not None and run.get("surface") != surface:
            continue
        if scope_type is not None and run.get("scope_type") != scope_type:
            continue
        if (
            normalized_scope is not None
            and _normalized_scope_ids(run.get("scope_ids") or [])
            != normalized_scope
        ):
            continue
        if profile_id is not None and profile.get("id") != profile_id:
            continue
        if not include_terminal and run.get("state") in TERMINAL_STATES:
            continue
        matches.append(_run_summary(run))

    return matches


def find_active_run(
    store: Path | str,
    *,
    product_id: str,
    product_version: str,
    surface: str,
    scope_type: str,
    scope_ids: Iterable[str],
    profile_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    matches = find_runs(
        store,
        product_id=product_id,
        product_version=product_version,
        surface=surface,
        scope_type=scope_type,
        scope_ids=scope_ids,
        profile_id=profile_id,
        include_terminal=False,
    )
    if not matches:
        return None
    if len(matches) > 1:
        raise RunAmbiguityError(
            "multiple active design runs match scope: "
            + ", ".join(item["run_id"] for item in matches)
        )
    return load_run(store, matches[0]["run_id"])


def ensure_run(
    *,
    store: Path | str,
    product_id: str,
    product_version: str,
    surface: str,
    scope_type: str,
    scope_ids: Iterable[str],
    authorities: Optional[Dict[str, str]] = None,
    profile_id: Optional[str] = None,
    run_id: Optional[str] = None,
    lock_timeout_seconds: float = 2.0,
    lock_stale_seconds: float = 30.0,
) -> Dict[str, Any]:
    scope_ids = list(scope_ids)
    with _registry_lock(
        store,
        timeout_seconds=lock_timeout_seconds,
        stale_seconds=lock_stale_seconds,
    ):
        existing = find_active_run(
            store,
            product_id=product_id,
            product_version=product_version,
            surface=surface,
            scope_type=scope_type,
            scope_ids=scope_ids,
            profile_id=profile_id,
        )
        if existing is not None:
            requested_authorities = deepcopy(authorities or {})
            existing_authorities = existing.get("authorities") or {}
            conflicts = {
                key: {
                    "requested": value,
                    "existing": existing_authorities.get(key),
                }
                for key, value in requested_authorities.items()
                if existing_authorities.get(key) != value
            }
            if conflicts:
                details = ", ".join(
                    f"{key}: requested={item['requested']} existing={item['existing']}"
                    for key, item in sorted(conflicts.items())
                )
                raise RunAuthorityConflictError(
                    f"active run authority conflict for {existing['run_id']}: {details}"
                )
            return {"created": False, "run": existing}

        created = start_run(
            store=store,
            product_id=product_id,
            product_version=product_version,
            surface=surface,
            scope_type=scope_type,
            scope_ids=scope_ids,
            authorities=authorities,
            profile_id=profile_id,
            run_id=run_id,
        )
        return {"created": True, "run": created}


def start_run(
    *,
    store: Path | str,
    product_id: str,
    product_version: str,
    surface: str,
    scope_type: str,
    scope_ids: Iterable[str],
    authorities: Optional[Dict[str, str]] = None,
    run_id: Optional[str] = None,
    profile_id: Optional[str] = None,
) -> Dict[str, Any]:
    scope_ids = [str(item) for item in scope_ids if str(item).strip()]
    if not scope_ids:
        raise ValidationError("at least one scope_id is required")
    if not all([product_id, product_version, surface, scope_type]):
        raise ValidationError(
            "product_id, product_version, surface, and scope_type are required"
        )

    run_id = run_id or f"design_{uuid.uuid4().hex[:12]}"
    if _run_path(store, run_id).exists() or run_journal_path(store, run_id).exists():
        raise RunConflictError(f"run or journal already exists: {run_id}")

    profile = None
    stage_plan = []
    stage_cursor = 0
    if profile_id:
        profile_def = load_profile(profile_id)
        if profile_def["entry_mode"] != "start":
            raise ValidationError(
                f"profile {profile_id} cannot start a new run; use its {profile_def['entry_mode']} entry mode"
            )
        authorities = deepcopy(authorities or {})
        missing_authorities = [
            key
            for key in profile_def.get("required_authorities", [])
            if not authorities.get(key)
        ]
        if missing_authorities:
            raise ValidationError(
                f"profile {profile_id} missing required authorities: {', '.join(missing_authorities)}"
            )
        profile = {
            "id": profile_def["id"],
            "version": profile_def["version"],
            "title": profile_def.get("title"),
            "final_gate": profile_def.get("final_gate"),
            "parallel_policy": profile_def.get("parallel_policy"),
            "child_scope": profile_def.get("child_scope"),
        }
        stage_plan = deepcopy(profile_def["stages"])

    now = utc_now()
    run = {
        "schema_version": 1,
        "revision": 0,
        "run_id": run_id,
        "product_id": product_id,
        "product_version": product_version,
        "surface": surface,
        "scope_type": scope_type,
        "scope_ids": scope_ids,
        "parent_run_id": None,
        "children": [],
        "shared_baseline": None,
        "state": "INIT",
        "profile": profile,
        "stage_plan": stage_plan,
        "stage_cursor": stage_cursor,
        "authorities": deepcopy(authorities or {}),
        "artifacts": [],
        "evidence": [],
        "dispatches": [],
        "active_dispatch_id": None,
        "decisions": [],
        "invalidations": [],
        "next_action": None,
        "reconciliation": None,
        "correction": None,
        "created_at": now,
        "updated_at": now,
        "archived_at": None,
        "history": [],
    }
    _append_history(run, "run_started", scope=_canonical_scope(run))
    return save_run(store, run)


def _valid_evidence_ids(run: Dict[str, Any]) -> list[str]:
    return [
        item["evidence_id"]
        for item in run.get("evidence", [])
        if item.get("validity", "valid") == "valid"
    ]


def _valid_artifact_ids(run: Dict[str, Any]) -> list[str]:
    return [
        item["artifact_id"]
        for item in run.get("artifacts", [])
        if item.get("status", "valid") == "valid"
    ]


def _dispatch_inputs(run: Dict[str, Any]) -> Dict[str, Any]:
    authorities = deepcopy(run.get("authorities") or {})
    return {
        "product_id": run["product_id"],
        "product_version": run["product_version"],
        "surface": run["surface"],
        "scope_type": run["scope_type"],
        "scope_ids": deepcopy(run.get("scope_ids") or []),
        "scope": _canonical_scope(run),
        "authorities": authorities,
        "authority_versions": authorities,
        "valid_artifact_ids": _valid_artifact_ids(run),
        "valid_evidence_ids": _valid_evidence_ids(run),
        "parent_run_id": run.get("parent_run_id"),
        "shared_baseline": run.get("shared_baseline"),
    }


def _dispatch_action_for_stage(
    run: Dict[str, Any],
    *,
    evidence_stage: str,
    target_state: str,
    handler: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "kind": "dispatch",
        "handler": handler or DEFAULT_STAGE_HANDLERS.get(evidence_stage, "unknown"),
        "evidence_stage": evidence_stage,
        "target_state": target_state,
        "scope": _canonical_scope(run),
        "inputs": _dispatch_inputs(run),
        "expected_evidence": {
            "stage": evidence_stage,
            "allowed_statuses": sorted(VALID_EVIDENCE_STATUSES),
        },
        "stop_conditions": [
            "blocking-finding",
            "needs-decision",
            "unknown-provider-outcome",
            "human-approval-required",
        ],
    }


def get_next_action(store: Path | str, run_id: str) -> Dict[str, Any]:
    run = load_run(store, run_id)
    state = run["state"]

    active_dispatch_id = run.get("active_dispatch_id")
    if active_dispatch_id:
        active = _find_dispatch(run, active_dispatch_id)
        if active.get("status") == "claimed" and dispatch_lease_expired(active):
            return {
                "kind": "control",
                "handler": "design-harness",
                "operation": "claim-dispatch",
                "dispatch_id": active["dispatch_id"],
                "dispatch_status": active["status"],
                "lease_expired": True,
                "previous_worker_id": active.get("worker_id"),
                "lease_expires_at": active.get("lease_expires_at"),
                "scope": active["scope"],
            }
        if active.get("status") in {"issued", "claimed"}:
            return {
                "kind": "inflight",
                "handler": active["handler"],
                "operation": "complete-dispatch",
                "dispatch_id": active["dispatch_id"],
                "dispatch_status": active["status"],
                "worker_id": active.get("worker_id"),
                "lease_expired": False,
                "lease_expires_at": active.get("lease_expires_at"),
                "evidence_stage": active["evidence_stage"],
                "target_state": active["target_state"],
                "scope": active["scope"],
                "expected_evidence": deepcopy(active["expected_evidence"]),
                "issued_at": active["issued_at"],
                "claimed_at": active.get("claimed_at"),
            }

    if state == "RECONCILING":
        reconciliation = run.get("reconciliation") or {}
        return {
            "kind": "control",
            "handler": "design-harness",
            "operation": "reconcile",
            "scope": _canonical_scope(run),
            "stage": reconciliation.get("stage"),
            "attempts": reconciliation.get("attempts", 0),
            "return_state": reconciliation.get("return_state"),
            "target_state": reconciliation.get("target_state"),
        }

    if state == "BLOCKED":
        return {
            "kind": "control",
            "handler": "human",
            "operation": "resolve-blocker",
            "scope": _canonical_scope(run),
        }

    if state == "CORRECTION":
        return _dispatch_action_for_stage(
            run,
            evidence_stage="correction",
            target_state="CORRECTION",
            handler="ui-continuity",
        )

    if state == "AWAITING_USER_APPROVAL":
        return {
            "kind": "human",
            "handler": "human",
            "operation": "approve",
            "scope": _canonical_scope(run),
        }

    if state == "APPROVED":
        return {
            "kind": "verification",
            "handler": "delivery-verification",
            "operation": "verify",
            "scope": _canonical_scope(run),
            "evidence_stage": "delivery",
            "expected_evidence": {
                "stage": "delivery",
                "allowed_statuses": sorted(VALID_EVIDENCE_STATUSES),
            },
            "inputs": _dispatch_inputs(run),
        }

    if state == "DELIVERY_VERIFIED":
        return {
            "kind": "control",
            "handler": "design-harness",
            "operation": "archive",
            "scope": _canonical_scope(run),
        }

    if state in {"ARCHIVED", "CANCELLED"}:
        return {
            "kind": "done",
            "handler": "design-harness",
            "operation": "none",
            "scope": _canonical_scope(run),
        }

    profile = run.get("profile") or {}
    profile_stage = _profile_next_stage(run) if profile else None
    if profile_stage is not None:
        return _dispatch_action_for_stage(
            run,
            evidence_stage=profile_stage["evidence_stage"],
            target_state=profile_stage["target_state"],
            handler=profile_stage.get("handler"),
        )

    if profile.get("id") == "page-family-batch" and state == "BASELINE_BOUND":
        batch = batch_status(store, run_id)
        if not run.get("children"):
            return {
                "kind": "control",
                "handler": "design-harness",
                "operation": "spawn-children",
                "scope": _canonical_scope(run),
                "shared_baseline": run.get("shared_baseline")
                or run.get("authorities", {}).get("baseline"),
            }
        if batch["ready_for_batch_approval"]:
            return {
                "kind": "human",
                "handler": "human",
                "operation": "batch-approve",
                "scope": _canonical_scope(run),
                "shared_baseline": batch["shared_baseline"],
            }
        return {
            "kind": "control",
            "handler": "design-harness",
            "operation": "batch-status",
            "scope": _canonical_scope(run),
            "overall_state": batch["overall_state"],
            "shared_baseline": batch["shared_baseline"],
        }

    if not profile and state in EXPECTED_TRANSITIONS:
        evidence_stage, target_state = EXPECTED_TRANSITIONS[state]
        return _dispatch_action_for_stage(
            run,
            evidence_stage=evidence_stage,
            target_state=target_state,
            handler=DEFAULT_STAGE_HANDLERS.get(evidence_stage),
        )

    return {
        "kind": "done",
        "handler": "design-harness",
        "operation": "none",
        "scope": _canonical_scope(run),
    }


def _find_dispatch(run: Dict[str, Any], dispatch_id: str) -> Dict[str, Any]:
    for item in run.get("dispatches", []):
        if item.get("dispatch_id") == dispatch_id:
            return item
    raise ValidationError(f"dispatch not found: {dispatch_id}")


def issue_dispatch(store: Path | str, run_id: str) -> Dict[str, Any]:
    run = load_run(store, run_id)

    active_id = run.get("active_dispatch_id")
    if active_id:
        active = _find_dispatch(run, active_id)
        if active.get("status") in {"issued", "claimed"}:
            return deepcopy(active)
        run["active_dispatch_id"] = None

    action = get_next_action(store, run_id)
    if action.get("kind") != "dispatch":
        raise TransitionError(
            f"next action is {action.get('kind')}:{action.get('operation') or action.get('handler')}, not a dispatch"
        )

    profile = run.get("profile") or {}
    dispatch = {
        "contract_version": 1,
        "dispatch_id": f"dispatch_{uuid.uuid4().hex[:12]}",
        "run_id": run_id,
        "profile": {
            "id": profile.get("id"),
            "version": profile.get("version"),
        },
        "stage_cursor": run.get("stage_cursor"),
        "state_at_issue": run["state"],
        "handler": action["handler"],
        "evidence_stage": action["evidence_stage"],
        "target_state": action["target_state"],
        "scope": action["scope"],
        "inputs": action["inputs"],
        "expected_evidence": action["expected_evidence"],
        "stop_conditions": action["stop_conditions"],
        "status": "issued",
        "worker_id": None,
        "claimed_at": None,
        "lease_seconds": None,
        "lease_expires_at": None,
        "heartbeats": [],
        "releases": [],
        "issued_at": utc_now(),
        "completed_at": None,
        "evidence_id": None,
    }
    run.setdefault("dispatches", []).append(dispatch)
    run["active_dispatch_id"] = dispatch["dispatch_id"]
    _append_history(
        run,
        "dispatch_issued",
        dispatch_id=dispatch["dispatch_id"],
        handler=dispatch["handler"],
        evidence_stage=dispatch["evidence_stage"],
    )
    save_run(store, run)
    return deepcopy(dispatch)


def claim_dispatch(
    store: Path | str,
    run_id: str,
    dispatch_id: str,
    *,
    worker_id: str,
    lease_seconds: int = 900,
) -> Dict[str, Any]:
    if not worker_id or not worker_id.strip():
        raise ValidationError("worker_id is required")
    if not isinstance(lease_seconds, int) or lease_seconds <= 0:
        raise ValidationError("lease_seconds must be a positive integer")

    run = load_run(store, run_id)
    if run.get("active_dispatch_id") != dispatch_id:
        raise TransitionError(
            f"dispatch is not active: expected {run.get('active_dispatch_id')}, got {dispatch_id}"
        )

    dispatch = _find_dispatch(run, dispatch_id)
    status = dispatch.get("status")

    if status == "claimed" and not dispatch_lease_expired(dispatch):
        if dispatch.get("worker_id") == worker_id:
            return deepcopy(dispatch)
        raise TransitionError(
            f"dispatch {dispatch_id} is already claimed by {dispatch.get('worker_id')}"
        )

    previous_worker = None
    if status == "claimed":
        if not dispatch_lease_expired(dispatch):
            raise TransitionError(
                f"dispatch {dispatch_id} is already claimed by {dispatch.get('worker_id')}"
            )
        previous_worker = dispatch.get("worker_id")
        dispatch.setdefault("releases", []).append(
            {
                "worker_id": previous_worker,
                "reason": "lease-expired-reclaim",
                "released_at": utc_now(),
                "reclaimed_by": worker_id,
            }
        )
    elif status != "issued":
        raise TransitionError(
            f"dispatch {dispatch_id} cannot be claimed from status {status}"
        )

    dispatch["status"] = "claimed"
    dispatch["worker_id"] = worker_id
    dispatch["claimed_at"] = utc_now()
    dispatch["lease_seconds"] = lease_seconds
    dispatch["lease_expires_at"] = _lease_expiry(lease_seconds)

    if previous_worker is None:
        _append_history(
            run,
            "dispatch_claimed",
            dispatch_id=dispatch_id,
            worker_id=worker_id,
            lease_seconds=lease_seconds,
        )
    else:
        _append_history(
            run,
            "dispatch_reclaimed",
            dispatch_id=dispatch_id,
            previous_worker_id=previous_worker,
            worker_id=worker_id,
            lease_seconds=lease_seconds,
        )

    save_run(store, run)
    return deepcopy(dispatch)


def heartbeat_dispatch(
    store: Path | str,
    run_id: str,
    dispatch_id: str,
    *,
    worker_id: str,
    lease_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    run = load_run(store, run_id)
    if run.get("active_dispatch_id") != dispatch_id:
        raise TransitionError(
            f"dispatch is not active: expected {run.get('active_dispatch_id')}, got {dispatch_id}"
        )

    dispatch = _find_dispatch(run, dispatch_id)
    if dispatch.get("status") != "claimed":
        raise TransitionError(
            f"dispatch {dispatch_id} is not claimed: {dispatch.get('status')}"
        )
    if dispatch.get("worker_id") != worker_id:
        raise TransitionError(
            f"dispatch {dispatch_id} is claimed by {dispatch.get('worker_id')}, not {worker_id}"
        )
    if dispatch_lease_expired(dispatch):
        raise TransitionError(
            f"dispatch {dispatch_id} lease expired; reclaim before heartbeat"
        )

    seconds = lease_seconds if lease_seconds is not None else dispatch.get("lease_seconds")
    if not isinstance(seconds, int) or seconds <= 0:
        raise ValidationError("lease_seconds must be a positive integer")

    previous_expiry = dispatch.get("lease_expires_at")
    heartbeat_at = utc_now()
    dispatch["lease_seconds"] = seconds
    dispatch["lease_expires_at"] = _lease_expiry(seconds)
    dispatch.setdefault("heartbeats", []).append(
        {
            "worker_id": worker_id,
            "heartbeat_at": heartbeat_at,
            "previous_lease_expires_at": previous_expiry,
            "lease_expires_at": dispatch["lease_expires_at"],
        }
    )
    _append_history(
        run,
        "dispatch_heartbeat",
        dispatch_id=dispatch_id,
        worker_id=worker_id,
        lease_seconds=seconds,
    )
    save_run(store, run)
    return deepcopy(dispatch)


def release_dispatch(
    store: Path | str,
    run_id: str,
    dispatch_id: str,
    *,
    worker_id: str,
    reason: str,
) -> Dict[str, Any]:
    if not reason or not reason.strip():
        raise ValidationError("release reason is required")

    run = load_run(store, run_id)
    if run.get("active_dispatch_id") != dispatch_id:
        raise TransitionError(
            f"dispatch is not active: expected {run.get('active_dispatch_id')}, got {dispatch_id}"
        )

    dispatch = _find_dispatch(run, dispatch_id)
    if dispatch.get("status") != "claimed":
        raise TransitionError(
            f"dispatch {dispatch_id} is not claimed: {dispatch.get('status')}"
        )
    if dispatch.get("worker_id") != worker_id:
        raise TransitionError(
            f"dispatch {dispatch_id} is claimed by {dispatch.get('worker_id')}, not {worker_id}"
        )

    dispatch.setdefault("releases", []).append(
        {
            "worker_id": worker_id,
            "reason": reason,
            "released_at": utc_now(),
        }
    )
    dispatch["status"] = "issued"
    dispatch["worker_id"] = None
    dispatch["claimed_at"] = None
    dispatch["lease_seconds"] = None
    dispatch["lease_expires_at"] = None
    _append_history(
        run,
        "dispatch_released",
        dispatch_id=dispatch_id,
        worker_id=worker_id,
        reason=reason,
    )
    save_run(store, run)
    return deepcopy(dispatch)


def complete_dispatch(
    store: Path | str,
    run_id: str,
    dispatch_id: str,
    evidence: Dict[str, Any],
    *,
    worker_id: Optional[str] = None,
) -> Dict[str, Any]:
    run = load_run(store, run_id)
    active_id = run.get("active_dispatch_id")
    if active_id != dispatch_id:
        raise TransitionError(
            f"dispatch is not active: expected {active_id}, got {dispatch_id}"
        )

    dispatch = _find_dispatch(run, dispatch_id)
    dispatch_status = dispatch.get("status")
    if dispatch_status not in {"issued", "claimed"}:
        raise TransitionError(
            f"dispatch {dispatch_id} is not completable: {dispatch_status}"
        )
    if dispatch_status == "claimed":
        if dispatch_lease_expired(dispatch):
            raise TransitionError(
                f"dispatch {dispatch_id} lease expired; reclaim before completion"
            )
        if not worker_id:
            raise TransitionError(
                f"dispatch {dispatch_id} is claimed by {dispatch.get('worker_id')}; worker_id is required"
            )
        if dispatch.get("worker_id") != worker_id:
            raise TransitionError(
                f"dispatch {dispatch_id} is claimed by {dispatch.get('worker_id')}, not {worker_id}"
            )
    if evidence.get("stage") != dispatch["expected_evidence"]["stage"]:
        raise TransitionError(
            f"dispatch {dispatch_id} expects evidence stage {dispatch['expected_evidence']['stage']}, got {evidence.get('stage')}"
        )
    if evidence.get("status") not in dispatch["expected_evidence"]["allowed_statuses"]:
        raise ValidationError(
            f"dispatch {dispatch_id} does not allow evidence status {evidence.get('status')}"
        )

    bound_evidence = deepcopy(evidence)
    bound_evidence["dispatch_id"] = dispatch_id
    advanced = resume_run(store, run_id, bound_evidence)

    run = load_run(store, run_id)
    dispatch = _find_dispatch(run, dispatch_id)
    status = evidence.get("status")
    if status == "pass":
        dispatch["status"] = "completed"
    elif status == "unknown":
        dispatch["status"] = "unknown"
    else:
        dispatch["status"] = "blocked"
    dispatch["completed_at"] = utc_now()

    evidence_item = next(
        (
            item
            for item in reversed(run.get("evidence", []))
            if item.get("dispatch_id") == dispatch_id
        ),
        None,
    )
    if evidence_item:
        dispatch["evidence_id"] = evidence_item["evidence_id"]

    run["active_dispatch_id"] = None
    _append_history(
        run,
        "dispatch_completed",
        dispatch_id=dispatch_id,
        status=dispatch["status"],
        evidence_id=dispatch.get("evidence_id"),
    )
    return save_run(store, run)


def status_run(store: Path | str, run_id: str) -> Dict[str, Any]:
    run = load_run(store, run_id)
    result = deepcopy(run)
    result["profile_next"] = _profile_next_stage(run)
    result["profile_complete"] = bool(run.get("profile")) and result["profile_next"] is None
    result["computed_next_action"] = get_next_action(store, run_id)
    return result


def set_next_action(
    store: Path | str, run_id: str, action: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    run = load_run(store, run_id)
    if action is not None:
        required = {"kind", "target", "expected_evidence"}
        missing = sorted(required - set(action))
        if missing:
            raise ValidationError(
                f"next_action missing required fields: {', '.join(missing)}"
            )
        action = deepcopy(action)
        action.setdefault("required_inputs", [])
    run["next_action"] = action
    _append_history(run, "next_action_set", action=action)
    return save_run(store, run)


def record_artifact(
    store: Path | str, run_id: str, artifact: Dict[str, Any]
) -> Dict[str, Any]:
    run = load_run(store, run_id)
    required = {"artifact_id", "type", "producer", "maturity", "status", "location"}
    missing = sorted(required - set(artifact))
    if missing:
        raise ValidationError(f"artifact missing required fields: {', '.join(missing)}")

    if any(item["artifact_id"] == artifact["artifact_id"] for item in run["artifacts"]):
        raise ValidationError(f'duplicate artifact_id: {artifact["artifact_id"]}')
    if artifact["status"] not in VALID_ARTIFACT_STATUSES:
        raise ValidationError(f'invalid artifact status: {artifact["status"]}')
    if artifact["maturity"] not in VALID_MATURITY:
        raise ValidationError(f'invalid artifact maturity: {artifact["maturity"]}')

    item = deepcopy(artifact)
    item.setdefault("input_versions", {})
    item.setdefault("evidence_ids", [])
    run["artifacts"].append(item)
    _append_history(run, "artifact_recorded", artifact_id=item["artifact_id"])
    return save_run(store, run)


def _append_evidence(run: Dict[str, Any], evidence: Dict[str, Any]) -> Dict[str, Any]:
    item = _normalize_evidence(evidence, run["run_id"])
    run["evidence"].append(item)
    return item


def resume_run(
    store: Path | str, run_id: str, evidence: Dict[str, Any]
) -> Dict[str, Any]:
    run = load_run(store, run_id)
    state = run["state"]

    if state in {"RECONCILING", "BLOCKED", "CANCELLED", "ARCHIVED"}:
        raise TransitionError(f"cannot resume directly from {state}")

    active_dispatch_id = run.get("active_dispatch_id")
    if active_dispatch_id and evidence.get("dispatch_id") != active_dispatch_id:
        raise TransitionError(
            f"run has active dispatch {active_dispatch_id}; complete it with matching dispatch evidence"
        )

    item = _normalize_evidence(evidence, run_id)

    if state == "CORRECTION":
        if item["stage"] != "correction":
            raise TransitionError("CORRECTION requires correction-stage evidence")
        _append_evidence(run, item)
        if item["status"] == "pass":
            resume_from = run["correction"]["resume_from"]
            if run.get("profile"):
                cursor = _profile_cursor_for_state(run, resume_from)
                run["stage_cursor"] = cursor
                run["state"] = (
                    "INIT"
                    if cursor == 0
                    else run["stage_plan"][cursor - 1]["target_state"]
                )
            else:
                run["state"] = _predecessor(resume_from)
            run["correction"]["completed_at"] = utc_now()
            _append_history(run, "correction_completed", resume_from=resume_from)
        elif item["status"] == "unknown":
            run["reconciliation"] = {
                "return_state": "CORRECTION",
                "target_state": "CORRECTION",
                "stage": "correction",
                "attempts": 0,
                "started_at": utc_now(),
            }
            run["state"] = "RECONCILING"
        else:
            run["state"] = "BLOCKED"
            _append_history(run, "correction_blocked", status=item["status"])
        return save_run(store, run)

    profile_stage = _profile_next_stage(run) if run.get("profile") else None
    if profile_stage is not None:
        expected_stage = profile_stage["evidence_stage"]
        target_state = profile_stage["target_state"]
        target_cursor = int(run.get("stage_cursor", 0)) + 1
    else:
        if run.get("profile"):
            raise TransitionError(
                f"profile {run['profile']['id']} has no remaining resumable stages"
            )
        if state not in EXPECTED_TRANSITIONS:
            raise TransitionError(f"state {state} does not accept generic resume evidence")
        expected_stage, target_state = EXPECTED_TRANSITIONS[state]
        target_cursor = None

    if item["stage"] != expected_stage:
        raise TransitionError(
            f"state {state} expects stage {expected_stage}, got {item['stage']}"
        )

    _append_evidence(run, item)
    if item["status"] == "pass":
        run["state"] = target_state
        if target_cursor is not None:
            run["stage_cursor"] = target_cursor
        run["reconciliation"] = None
        _append_history(
            run,
            "stage_advanced",
            from_state=state,
            to_state=target_state,
            evidence_id=item["evidence_id"],
            profile_id=(run.get("profile") or {}).get("id"),
        )
    elif item["status"] == "unknown":
        run["reconciliation"] = {
            "return_state": state,
            "target_state": target_state,
            "target_stage_cursor": target_cursor,
            "stage": expected_stage,
            "attempts": 0,
            "started_at": utc_now(),
        }
        run["state"] = "RECONCILING"
        _append_history(run, "reconciliation_started", stage=expected_stage)
    else:
        run["state"] = "BLOCKED"
        _append_history(run, "stage_blocked", stage=expected_stage, status=item["status"])

    return save_run(store, run)


def reconcile_run(
    store: Path | str,
    run_id: str,
    *,
    resolved: bool,
    note: str,
    outcome: str = "pass",
) -> Dict[str, Any]:
    run = load_run(store, run_id)
    if run["state"] != "RECONCILING" or not run.get("reconciliation"):
        raise TransitionError("reconcile requires RECONCILING state")

    reconciliation = run["reconciliation"]
    reconciliation["attempts"] += 1
    reconciliation.setdefault("probes", []).append(
        {"at": utc_now(), "note": note, "resolved": resolved, "outcome": outcome}
    )

    if resolved:
        if outcome == "pass":
            run["state"] = reconciliation["target_state"]
            if reconciliation.get("target_stage_cursor") is not None:
                run["stage_cursor"] = reconciliation["target_stage_cursor"]
            _append_history(
                run,
                "reconciliation_resolved",
                to_state=run["state"],
                attempts=reconciliation["attempts"],
            )
            run["reconciliation"] = None
        elif outcome in {"fail", "needs-decision"}:
            run["state"] = "BLOCKED"
            _append_history(run, "reconciliation_blocked", outcome=outcome)
        else:
            raise ValidationError("resolved outcome must be pass, fail, or needs-decision")
    elif reconciliation["attempts"] >= 3:
        run["state"] = "BLOCKED"
        _append_history(run, "reconciliation_exhausted", attempts=3)

    return save_run(store, run)


def correct_run(
    store: Path | str,
    run_id: str,
    *,
    affected_state: str,
    reason: str,
    affected_artifact_ids: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    run = load_run(store, run_id)
    if run["state"] in {"ARCHIVED", "CANCELLED", "RECONCILING"}:
        raise TransitionError(f"cannot start correction from {run['state']}")

    affected_index = _state_index(affected_state)
    affected_artifact_ids = set(affected_artifact_ids or [])

    invalidated_evidence_ids = []
    for evidence in run["evidence"]:
        result_state = EVIDENCE_RESULT_STATE.get(evidence["stage"])
        if result_state and _state_index(result_state) >= affected_index:
            if evidence.get("validity") != "invalidated":
                evidence["validity"] = "invalidated"
                invalidated_evidence_ids.append(evidence["evidence_id"])

    invalidated_artifact_ids = []
    for artifact in run["artifacts"]:
        if artifact["artifact_id"] in affected_artifact_ids:
            artifact["status"] = "invalidated"
            invalidated_artifact_ids.append(artifact["artifact_id"])

    invalidation = {
        "invalidation_id": f"invalidation_{uuid.uuid4().hex[:12]}",
        "at": utc_now(),
        "reason": reason,
        "affected_state": affected_state,
        "evidence_ids": invalidated_evidence_ids,
        "artifact_ids": invalidated_artifact_ids,
    }
    run["invalidations"].append(invalidation)
    run["correction"] = {
        "reason": reason,
        "resume_from": affected_state,
        "started_at": utc_now(),
        "invalidation_id": invalidation["invalidation_id"],
    }
    run["state"] = "CORRECTION"
    _append_history(run, "correction_started", **invalidation)
    return save_run(store, run)


def _require_batch_parent(run: Dict[str, Any]) -> None:
    profile = run.get("profile") or {}
    if profile.get("id") != "page-family-batch":
        raise TransitionError("batch operation requires page-family-batch profile")
    if profile.get("parallel_policy") != "shared-baseline":
        raise TransitionError("batch parent must use shared-baseline parallel policy")


def spawn_child_runs(
    store: Path | str,
    parent_run_id: str,
    scope_ids: Iterable[str],
    *,
    authority_overrides: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    parent = load_run(store, parent_run_id)
    _require_batch_parent(parent)
    if parent["state"] not in PRIMARY_STATES or _state_index(parent["state"]) < _state_index("BASELINE_BOUND"):
        raise TransitionError("batch children require parent baseline to be bound")

    child_scope_ids = [str(item) for item in scope_ids if str(item).strip()]
    if not child_scope_ids:
        raise ValidationError("at least one child scope id is required")
    if len(child_scope_ids) != len(set(child_scope_ids)):
        raise ValidationError("duplicate child scope ids in request")

    existing = {item["scope_id"] for item in parent.get("children", [])}
    duplicates = sorted(existing.intersection(child_scope_ids))
    if duplicates:
        raise ValidationError(
            f"child scope already exists: {', '.join(duplicates)}"
        )

    baseline = parent.get("authorities", {}).get("baseline")
    if not baseline:
        raise ValidationError("page-family-batch requires baseline authority")

    overrides = deepcopy(authority_overrides or {})
    if "baseline" in overrides and overrides["baseline"] != baseline:
        raise ValidationError(
            f"child baseline override must match shared baseline {baseline}"
        )

    profile_def = load_profile("page-family-batch")
    child_profile = profile_def.get("child_profile") or "existing-product-next-page"
    created = []

    for scope_id in child_scope_ids:
        authorities = deepcopy(parent.get("authorities") or {})
        authorities.update(overrides)
        authorities["baseline"] = baseline

        child = start_run(
            store=store,
            product_id=parent["product_id"],
            product_version=parent["product_version"],
            surface=parent["surface"],
            scope_type=profile_def.get("child_scope") or "page",
            scope_ids=[scope_id],
            authorities=authorities,
            profile_id=child_profile,
        )
        child["parent_run_id"] = parent_run_id
        child["shared_baseline"] = baseline
        save_run(store, child)

        child = resume_run(
            store,
            child["run_id"],
            {
                "stage": "baseline",
                "status": "pass",
                "producer": "design-harness",
                "observed_result": f"inherited shared baseline {baseline} from parent {parent_run_id}",
                "input_versions": {"baseline": baseline},
                "limitations": [],
            },
        )

        entry = {
            "run_id": child["run_id"],
            "scope_id": scope_id,
            "scope_type": child["scope_type"],
            "profile_id": child_profile,
            "shared_baseline": baseline,
            "created_at": utc_now(),
        }
        parent.setdefault("children", []).append(entry)
        created.append(entry)

    parent["shared_baseline"] = baseline
    _append_history(
        parent,
        "children_spawned",
        child_run_ids=[item["run_id"] for item in created],
        scope_ids=child_scope_ids,
        shared_baseline=baseline,
    )
    return save_run(store, parent)


def batch_status(store: Path | str, parent_run_id: str) -> Dict[str, Any]:
    parent = load_run(store, parent_run_id)
    _require_batch_parent(parent)

    children = []
    counts: Dict[str, int] = {}
    for entry in parent.get("children", []):
        child = load_run(store, entry["run_id"])
        counts[child["state"]] = counts.get(child["state"], 0) + 1
        children.append(
            {
                **deepcopy(entry),
                "state": child["state"],
                "next_action": child.get("next_action"),
                "profile_next": _profile_next_stage(child),
            }
        )

    states = [item["state"] for item in children]
    ready_states = {"AWAITING_USER_APPROVAL", "APPROVED"}
    verified_states = {"DELIVERY_VERIFIED", "ARCHIVED"}
    approved_or_beyond = {"APPROVED", "DELIVERY_VERIFIED", "ARCHIVED"}

    ready_for_batch_approval = bool(states) and all(
        state in ready_states for state in states
    ) and any(state == "AWAITING_USER_APPROVAL" for state in states)
    all_delivery_verified = bool(states) and all(
        state in verified_states for state in states
    )

    if any(state == "BLOCKED" for state in states):
        overall_state = "BLOCKED"
    elif any(state == "RECONCILING" for state in states):
        overall_state = "RECONCILING"
    elif states and all(state == "ARCHIVED" for state in states):
        overall_state = "ARCHIVED"
    elif all_delivery_verified:
        overall_state = "DELIVERY_VERIFIED"
    elif states and all(state in approved_or_beyond for state in states):
        overall_state = "APPROVED"
    elif ready_for_batch_approval:
        overall_state = "READY_FOR_APPROVAL"
    elif not states:
        overall_state = "EMPTY"
    else:
        overall_state = "RUNNING"

    return {
        "parent_run_id": parent_run_id,
        "parent_state": parent["state"],
        "shared_baseline": parent.get("shared_baseline")
        or parent.get("authorities", {}).get("baseline"),
        "children": children,
        "counts": counts,
        "overall_state": overall_state,
        "ready_for_batch_approval": ready_for_batch_approval,
        "all_delivery_verified": all_delivery_verified,
        "total": len(children),
    }


def batch_approve(
    store: Path | str,
    parent_run_id: str,
    *,
    actor: str = "human",
) -> Dict[str, Any]:
    parent = load_run(store, parent_run_id)
    _require_batch_parent(parent)
    status = batch_status(store, parent_run_id)
    if not status["ready_for_batch_approval"]:
        raise TransitionError(
            "batch approval requires every child to be awaiting approval or already approved"
        )

    approved_children = []
    for entry in parent.get("children", []):
        child = load_run(store, entry["run_id"])
        if child["state"] == "AWAITING_USER_APPROVAL":
            child = approve_run(
                store,
                child["run_id"],
                scope=_canonical_scope(child),
                actor=actor,
            )
        approved_children.append(child["run_id"])

    parent = load_run(store, parent_run_id)
    parent["state"] = "APPROVED"
    parent.setdefault("decisions", []).append(
        {
            "decision_id": f"decision_{uuid.uuid4().hex[:12]}",
            "kind": "batch-approval",
            "scope": _canonical_scope(parent),
            "actor": actor,
            "child_run_ids": approved_children,
            "at": utc_now(),
        }
    )
    _append_history(
        parent,
        "batch_approved",
        child_run_ids=approved_children,
        actor=actor,
    )
    return save_run(store, parent)


def approve_run(
    store: Path | str,
    run_id: str,
    *,
    scope: str,
    actor: str = "human",
    expected_scope: Optional[str] = None,
) -> Dict[str, Any]:
    run = load_run(store, run_id)
    if run["state"] != "AWAITING_USER_APPROVAL":
        raise TransitionError("approval requires AWAITING_USER_APPROVAL state")

    expected_scope = expected_scope or _canonical_scope(run)
    if scope != expected_scope:
        raise TransitionError(
            f"approval scope mismatch: expected {expected_scope}, got {scope}"
        )

    decision = {
        "decision_id": f"decision_{uuid.uuid4().hex[:12]}",
        "kind": "approval",
        "scope": scope,
        "actor": actor,
        "at": utc_now(),
    }
    run["decisions"].append(decision)
    run["state"] = "APPROVED"
    _append_history(run, "approved", scope=scope, actor=actor)
    return save_run(store, run)


def verify_run(
    store: Path | str, run_id: str, evidence: Dict[str, Any]
) -> Dict[str, Any]:
    run = load_run(store, run_id)
    if run["state"] != "APPROVED":
        raise TransitionError("delivery verification requires APPROVED state")

    item = _normalize_evidence(evidence, run_id)
    if item["stage"] != "delivery":
        raise ValidationError("verify evidence stage must be delivery")
    _append_evidence(run, item)

    if item["status"] == "pass":
        run["state"] = "DELIVERY_VERIFIED"
        _append_history(run, "delivery_verified", evidence_id=item["evidence_id"])
    elif item["status"] == "unknown":
        run["reconciliation"] = {
            "return_state": "APPROVED",
            "target_state": "DELIVERY_VERIFIED",
            "stage": "delivery",
            "attempts": 0,
            "started_at": utc_now(),
        }
        run["state"] = "RECONCILING"
    else:
        run["state"] = "BLOCKED"
    return save_run(store, run)


def archive_run(store: Path | str, run_id: str) -> Dict[str, Any]:
    run = load_run(store, run_id)
    if run["state"] != "DELIVERY_VERIFIED":
        raise TransitionError("archive requires DELIVERY_VERIFIED state")
    run["state"] = "ARCHIVED"
    run["archived_at"] = utc_now()
    run["next_action"] = None
    _append_history(run, "archived")
    return save_run(store, run)


def _parse_authorities(values: Iterable[str]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValidationError(f"authority must be KEY=VALUE: {value}")
        key, val = value.split("=", 1)
        if not key or not val:
            raise ValidationError(f"authority must be KEY=VALUE: {value}")
        result[key] = val
    return result


def _load_json_arg(value: str) -> Dict[str, Any]:
    if value.startswith("@"):
        return json.loads(Path(value[1:]).read_text(encoding="utf-8"))
    return json.loads(value)


def _print_json(value: Dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="design_harness.py")
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start")
    start.add_argument("--store", required=True)
    start.add_argument("--product-id", required=True)
    start.add_argument("--product-version", required=True)
    start.add_argument("--surface", required=True)
    start.add_argument("--scope-type", required=True)
    start.add_argument("--scope-id", action="append", required=True)
    start.add_argument("--authority", action="append", default=[])
    start.add_argument("--run-id")
    start.add_argument("--profile")

    profiles = sub.add_parser("profiles")
    profile = sub.add_parser("profile")
    profile.add_argument("--name", required=True)

    for name in ["status", "archive"]:
        cmd = sub.add_parser(name)
        cmd.add_argument("--store", required=True)
        cmd.add_argument("--run-id", required=True)

    resume = sub.add_parser("resume")
    resume.add_argument("--store", required=True)
    resume.add_argument("--run-id", required=True)
    resume.add_argument("--evidence-json", required=True)

    reconcile = sub.add_parser("reconcile")
    reconcile.add_argument("--store", required=True)
    reconcile.add_argument("--run-id", required=True)
    group = reconcile.add_mutually_exclusive_group(required=True)
    group.add_argument("--resolved", action="store_true")
    group.add_argument("--unresolved", action="store_true")
    reconcile.add_argument("--outcome", default="pass")
    reconcile.add_argument("--note", required=True)

    correct = sub.add_parser("correct")
    correct.add_argument("--store", required=True)
    correct.add_argument("--run-id", required=True)
    correct.add_argument("--affected-state", required=True)
    correct.add_argument("--reason", required=True)
    correct.add_argument("--artifact-id", action="append", default=[])

    approve = sub.add_parser("approve")
    approve.add_argument("--store", required=True)
    approve.add_argument("--run-id", required=True)
    approve.add_argument("--scope", required=True)
    approve.add_argument("--expected-scope")
    approve.add_argument("--actor", default="human")

    verify = sub.add_parser("verify")
    verify.add_argument("--store", required=True)
    verify.add_argument("--run-id", required=True)
    verify.add_argument("--evidence-json", required=True)

    action = sub.add_parser("set-next-action")
    action.add_argument("--store", required=True)
    action.add_argument("--run-id", required=True)
    action.add_argument("--action-json", required=True)

    artifact = sub.add_parser("record-artifact")
    artifact.add_argument("--store", required=True)
    artifact.add_argument("--run-id", required=True)
    artifact.add_argument("--artifact-json", required=True)

    spawn = sub.add_parser("spawn-children")
    spawn.add_argument("--store", required=True)
    spawn.add_argument("--run-id", required=True)
    spawn.add_argument("--child-scope-id", action="append", required=True)
    spawn.add_argument("--authority", action="append", default=[])

    batch = sub.add_parser("batch-status")
    batch.add_argument("--store", required=True)
    batch.add_argument("--run-id", required=True)

    batch_approval = sub.add_parser("batch-approve")
    batch_approval.add_argument("--store", required=True)
    batch_approval.add_argument("--run-id", required=True)
    batch_approval.add_argument("--actor", default="human")

    next_action = sub.add_parser("next-action")
    next_action.add_argument("--store", required=True)
    next_action.add_argument("--run-id", required=True)

    dispatch = sub.add_parser("dispatch")
    dispatch.add_argument("--store", required=True)
    dispatch.add_argument("--run-id", required=True)

    claim = sub.add_parser("claim-dispatch")
    claim.add_argument("--store", required=True)
    claim.add_argument("--run-id", required=True)
    claim.add_argument("--dispatch-id", required=True)
    claim.add_argument("--worker-id", required=True)
    claim.add_argument("--lease-seconds", type=int, default=900)

    heartbeat = sub.add_parser("heartbeat-dispatch")
    heartbeat.add_argument("--store", required=True)
    heartbeat.add_argument("--run-id", required=True)
    heartbeat.add_argument("--dispatch-id", required=True)
    heartbeat.add_argument("--worker-id", required=True)
    heartbeat.add_argument("--lease-seconds", type=int)

    release = sub.add_parser("release-dispatch")
    release.add_argument("--store", required=True)
    release.add_argument("--run-id", required=True)
    release.add_argument("--dispatch-id", required=True)
    release.add_argument("--worker-id", required=True)
    release.add_argument("--reason", required=True)

    complete = sub.add_parser("complete-dispatch")
    complete.add_argument("--store", required=True)
    complete.add_argument("--run-id", required=True)
    complete.add_argument("--dispatch-id", required=True)
    complete.add_argument("--worker-id")
    complete.add_argument("--evidence-json", required=True)

    runs = sub.add_parser("runs")
    runs.add_argument("--store", required=True)

    find_run = sub.add_parser("find-run")
    find_run.add_argument("--store", required=True)
    find_run.add_argument("--product-id")
    find_run.add_argument("--product-version")
    find_run.add_argument("--surface")
    find_run.add_argument("--scope-type")
    find_run.add_argument("--scope-id", action="append")
    find_run.add_argument("--profile")
    find_run.add_argument("--active-only", action="store_true")

    ensure = sub.add_parser("ensure-run")
    ensure.add_argument("--store", required=True)
    ensure.add_argument("--product-id", required=True)
    ensure.add_argument("--product-version", required=True)
    ensure.add_argument("--surface", required=True)
    ensure.add_argument("--scope-type", required=True)
    ensure.add_argument("--scope-id", action="append", required=True)
    ensure.add_argument("--authority", action="append", default=[])
    ensure.add_argument("--profile")
    ensure.add_argument("--run-id")

    journal = sub.add_parser("journal")
    journal.add_argument("--store", required=True)
    journal.add_argument("--run-id", required=True)

    verify_journal = sub.add_parser("verify-journal")
    verify_journal.add_argument("--store", required=True)
    verify_journal.add_argument("--run-id", required=True)

    replay = sub.add_parser("replay-run")
    replay.add_argument("--store", required=True)
    replay.add_argument("--run-id", required=True)

    recover = sub.add_parser("recover-run")
    recover.add_argument("--store", required=True)
    recover.add_argument("--run-id", required=True)

    snapshot_at = sub.add_parser("snapshot-at")
    snapshot_at.add_argument("--store", required=True)
    snapshot_at.add_argument("--run-id", required=True)
    snapshot_at.add_argument("--revision", required=True, type=int)

    diff_revisions = sub.add_parser("diff-revisions")
    diff_revisions.add_argument("--store", required=True)
    diff_revisions.add_argument("--run-id", required=True)
    diff_revisions.add_argument("--from-revision", required=True, type=int)
    diff_revisions.add_argument("--to-revision", required=True, type=int)
    diff_revisions.add_argument("--ignore-volatile", action="store_true")

    timeline = sub.add_parser("timeline")
    timeline.add_argument("--store", required=True)
    timeline.add_argument("--run-id", required=True)
    timeline.add_argument("--from-revision", type=int)
    timeline.add_argument("--to-revision", type=int)

    trace = sub.add_parser("trace-path")
    trace.add_argument("--store", required=True)
    trace.add_argument("--run-id", required=True)
    trace.add_argument("--path", required=True)

    entity_index = sub.add_parser("entity-index")
    entity_index.add_argument("--store", required=True)
    entity_index.add_argument("--run-id", required=True)

    entity_history_cmd = sub.add_parser("entity-history")
    entity_history_cmd.add_argument("--store", required=True)
    entity_history_cmd.add_argument("--run-id", required=True)
    entity_history_cmd.add_argument("--type", required=True, dest="entity_type")
    entity_history_cmd.add_argument("--id", required=True, dest="entity_id")

    provenance = sub.add_parser("provenance")
    provenance.add_argument("--store", required=True)
    provenance.add_argument("--run-id", required=True)
    provenance.add_argument("--type", required=True, dest="entity_type")
    provenance.add_argument("--id", required=True, dest="entity_id")
    provenance.add_argument("--max-depth", type=int, default=2)

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        if args.command == "start":
            result = start_run(
                store=args.store,
                product_id=args.product_id,
                product_version=args.product_version,
                surface=args.surface,
                scope_type=args.scope_type,
                scope_ids=args.scope_id,
                authorities=_parse_authorities(args.authority),
                run_id=args.run_id,
                profile_id=args.profile,
            )
        elif args.command == "profiles":
            result = {"profiles": list_profiles()}
        elif args.command == "profile":
            result = load_profile(args.name)
        elif args.command == "status":
            result = status_run(args.store, args.run_id)
        elif args.command == "resume":
            result = resume_run(
                args.store, args.run_id, _load_json_arg(args.evidence_json)
            )
        elif args.command == "reconcile":
            result = reconcile_run(
                args.store,
                args.run_id,
                resolved=args.resolved and not args.unresolved,
                outcome=args.outcome,
                note=args.note,
            )
        elif args.command == "correct":
            result = correct_run(
                args.store,
                args.run_id,
                affected_state=args.affected_state,
                reason=args.reason,
                affected_artifact_ids=args.artifact_id,
            )
        elif args.command == "approve":
            result = approve_run(
                args.store,
                args.run_id,
                scope=args.scope,
                expected_scope=args.expected_scope,
                actor=args.actor,
            )
        elif args.command == "verify":
            result = verify_run(
                args.store, args.run_id, _load_json_arg(args.evidence_json)
            )
        elif args.command == "archive":
            result = archive_run(args.store, args.run_id)
        elif args.command == "set-next-action":
            result = set_next_action(
                args.store, args.run_id, _load_json_arg(args.action_json)
            )
        elif args.command == "record-artifact":
            result = record_artifact(
                args.store, args.run_id, _load_json_arg(args.artifact_json)
            )
        elif args.command == "spawn-children":
            result = spawn_child_runs(
                args.store,
                args.run_id,
                args.child_scope_id,
                authority_overrides=_parse_authorities(args.authority),
            )
        elif args.command == "batch-status":
            result = batch_status(args.store, args.run_id)
        elif args.command == "batch-approve":
            result = batch_approve(
                args.store,
                args.run_id,
                actor=args.actor,
            )
        elif args.command == "next-action":
            result = get_next_action(args.store, args.run_id)
        elif args.command == "dispatch":
            result = issue_dispatch(args.store, args.run_id)
        elif args.command == "claim-dispatch":
            result = claim_dispatch(
                args.store,
                args.run_id,
                args.dispatch_id,
                worker_id=args.worker_id,
                lease_seconds=args.lease_seconds,
            )
        elif args.command == "heartbeat-dispatch":
            result = heartbeat_dispatch(
                args.store,
                args.run_id,
                args.dispatch_id,
                worker_id=args.worker_id,
                lease_seconds=args.lease_seconds,
            )
        elif args.command == "release-dispatch":
            result = release_dispatch(
                args.store,
                args.run_id,
                args.dispatch_id,
                worker_id=args.worker_id,
                reason=args.reason,
            )
        elif args.command == "complete-dispatch":
            result = complete_dispatch(
                args.store,
                args.run_id,
                args.dispatch_id,
                _load_json_arg(args.evidence_json),
                worker_id=args.worker_id,
            )
        elif args.command == "runs":
            result = {"runs": list_runs(args.store)}
        elif args.command == "find-run":
            result = {
                "runs": find_runs(
                    args.store,
                    product_id=args.product_id,
                    product_version=args.product_version,
                    surface=args.surface,
                    scope_type=args.scope_type,
                    scope_ids=args.scope_id,
                    profile_id=args.profile,
                    include_terminal=not args.active_only,
                )
            }
        elif args.command == "ensure-run":
            result = ensure_run(
                store=args.store,
                product_id=args.product_id,
                product_version=args.product_version,
                surface=args.surface,
                scope_type=args.scope_type,
                scope_ids=args.scope_id,
                authorities=_parse_authorities(args.authority),
                profile_id=args.profile,
                run_id=args.run_id,
            )
        elif args.command == "journal":
            result = run_journal_summary(args.store, args.run_id)
        elif args.command == "verify-journal":
            result = verify_run_journal(args.store, args.run_id)
        elif args.command == "replay-run":
            result = replay_run_from_journal(args.store, args.run_id)
        elif args.command == "recover-run":
            result = recover_run_snapshot(args.store, args.run_id)
        elif args.command == "snapshot-at":
            result = run_at_revision(
                args.store,
                args.run_id,
                args.revision,
            )
        elif args.command == "diff-revisions":
            result = diff_run_revisions(
                args.store,
                args.run_id,
                args.from_revision,
                args.to_revision,
                ignore_volatile=args.ignore_volatile,
            )
        elif args.command == "timeline":
            result = {
                "run_id": args.run_id,
                "timeline": run_audit_timeline(
                    args.store,
                    args.run_id,
                    from_revision=args.from_revision,
                    to_revision=args.to_revision,
                ),
            }
        elif args.command == "trace-path":
            result = trace_run_path(
                args.store,
                args.run_id,
                args.path,
            )
        elif args.command == "entity-index":
            result = entity_audit_index(
                args.store,
                args.run_id,
            )
        elif args.command == "entity-history":
            result = entity_history(
                args.store,
                args.run_id,
                args.entity_type,
                args.entity_id,
            )
        elif args.command == "provenance":
            result = entity_provenance_graph(
                args.store,
                args.run_id,
                args.entity_type,
                args.entity_id,
                max_depth=args.max_depth,
            )
        else:
            parser.error(f"unknown command: {args.command}")
            return 2

        _print_json(result)
        return 0
    except DesignHarnessError as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
