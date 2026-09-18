#!/usr/bin/env python3
"""Minimal persistent runtime for design-harness SOP execution.

Pure-stdlib by design so the skill can run in most agent environments.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from copy import deepcopy
from datetime import datetime, timezone
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

VALID_EVIDENCE_STATUSES = {"pass", "fail", "unknown", "needs-decision"}
VALID_ARTIFACT_STATUSES = {"valid", "invalidated", "superseded", "unknown"}
VALID_MATURITY = {
    "candidate",
    "preferred",
    "approved-master",
    "verified-delivery",
    "archived",
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


def _runs_dir(store: Path | str) -> Path:
    return Path(store) / "runs"


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


def save_run(store: Path | str, run: Dict[str, Any]) -> Dict[str, Any]:
    if "run_id" not in run:
        raise ValidationError("run_id is required")
    _validate_state(run["state"])

    directory = _runs_dir(store)
    directory.mkdir(parents=True, exist_ok=True)
    path = _run_path(store, run["run_id"])
    run["updated_at"] = utc_now()
    temp_path = path.with_suffix(".json.tmp")
    temp_path.write_text(
        json.dumps(run, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)
    return deepcopy(run)


def load_run(store: Path | str, run_id: str) -> Dict[str, Any]:
    path = _run_path(store, run_id)
    if not path.exists():
        raise RunNotFoundError(f"run not found: {run_id}")
    run = json.loads(path.read_text(encoding="utf-8"))
    _validate_state(run["state"])
    return run


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
    if _run_path(store, run_id).exists():
        raise ValidationError(f"run already exists: {run_id}")

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


def status_run(store: Path | str, run_id: str) -> Dict[str, Any]:
    run = load_run(store, run_id)
    result = deepcopy(run)
    result["profile_next"] = _profile_next_stage(run)
    result["profile_complete"] = bool(run.get("profile")) and result["profile_next"] is None
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
