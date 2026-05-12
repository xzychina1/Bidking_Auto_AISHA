from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SHADOW_PROJECT_ROOT = REPO_ROOT / "bidking_shadow"


def _shadow_project_root(config: dict[str, Any]) -> Path:
    bridge = config.get("pricing", {}).get("shadow_bridge", {})
    raw_path = bridge.get("project_path")
    if raw_path in (None, ""):
        return DEFAULT_SHADOW_PROJECT_ROOT
    path = Path(str(raw_path))
    if not path.is_absolute():
        return (REPO_ROOT / path).resolve()
    return path


def _shadow_log_path(config: dict[str, Any], project_root: Path) -> Path:
    bridge = config.get("pricing", {}).get("shadow_bridge", {})
    raw_path = bridge.get("log_path")
    if raw_path not in (None, ""):
        path = Path(str(raw_path))
        if not path.is_absolute():
            return project_root / path
        return path

    try:
        _ensure_shadow_import_path(project_root)
        with _shadow_working_directory(project_root):
            from bidking_shadow.getlog.constants import DEFAULT_GAME_LOG

        return Path(DEFAULT_GAME_LOG)
    except Exception:
        return project_root / "Player.log"


def _shadow_csv_path(config: dict[str, Any], project_root: Path) -> Path:
    bridge = config.get("pricing", {}).get("shadow_bridge", {})
    raw_path = bridge.get("csv_path")
    if raw_path not in (None, ""):
        path = Path(str(raw_path))
        if not path.is_absolute():
            return project_root / path
        return path

    try:
        _ensure_shadow_import_path(project_root)
        with _shadow_working_directory(project_root):
            from bidking_shadow.getlog.constants import CSV_PATH

        return Path(CSV_PATH)
    except Exception:
        return project_root / "item_prices.csv"


def _ensure_shadow_import_path(project_root: Path) -> None:
    root = str(project_root.parent)
    if root not in sys.path:
        sys.path.insert(0, root)


@contextmanager
def _shadow_working_directory(project_root: Path):
    previous = Path.cwd()
    try:
        os.chdir(project_root)
        yield
    finally:
        os.chdir(previous)


@lru_cache(maxsize=1)
def _shadow_runtime(project_root: str):
    root = Path(project_root)
    _ensure_shadow_import_path(root)
    with _shadow_working_directory(root):
        from bidking_shadow.getlog.constants import DEFAULT_GAME_LOG, CSV_PATH
        from bidking_shadow.getlog.item_db import _filter_candidates, candidate_probabilities, load_csv
        from bidking_shadow.getlog.posterior_estimator import (
            WeightedValue,
            estimate_total_posterior,
            price_likelihood,
        )
        from bidking_shadow.getlog.runner import parse_last_game_state_from_tail
        from bidking_shadow.getlog.grid_view_shared import GRID_COLS, GRID_ROWS, MIN_ROUND_SHOW_EMPTY

    return {
        "DEFAULT_GAME_LOG": DEFAULT_GAME_LOG,
        "CSV_PATH": CSV_PATH,
        "GRID_COLS": GRID_COLS,
        "GRID_ROWS": GRID_ROWS,
        "MIN_ROUND_SHOW_EMPTY": MIN_ROUND_SHOW_EMPTY,
        "WeightedValue": WeightedValue,
        "estimate_total_posterior": estimate_total_posterior,
        "price_likelihood": price_likelihood,
        "candidate_probabilities": candidate_probabilities,
        "_filter_candidates": _filter_candidates,
        "load_csv": load_csv,
        "parse_last_game_state_from_tail": parse_last_game_state_from_tail,
    }


def _shape_wh(shape: Any) -> tuple[int, int]:
    if shape is None:
        return 1, 1
    text = str(shape)
    if len(text) == 2 and text.isdigit():
        return int(text[0]), int(text[1])
    return 1, 1


def _compute_empty_zone_count(state: Any, grid_cols: int, grid_rows: int, min_round_show_empty: int) -> int | None:
    if getattr(state, "current_round", 0) < min_round_show_empty:
        return None

    max_box_id = -1
    occupied: set[tuple[int, int]] = set()
    for k in getattr(state, "items", {}).values():
        box_id = getattr(k, "box_id", None)
        if box_id is None or not getattr(k, "box_id_confirmed", False):
            continue
        max_box_id = max(max_box_id, int(box_id))
        row = int(box_id) // grid_cols
        col = int(box_id) % grid_cols
        width, height = _shape_wh(getattr(k, "shape", None))
        for dr in range(height):
            for dc in range(width):
                occupied.add((row + dr, col + dc))

    if max_box_id < 0:
        return None

    count = 0
    for box_id in range(min(max_box_id, grid_cols * grid_rows - 1) + 1):
        row = box_id // grid_cols
        col = box_id % grid_cols
        if (row, col) not in occupied:
            count += 1
    return count


def _posterior_distribution_for_item(
    uid: str,
    k: Any,
    csv_index: dict[int, Any],
    csv_items: list[Any],
    map_category_weights: dict[int, float] | None,
    map_id: int,
    runtime: dict[str, Any],
) -> list[Any]:
    if getattr(k, "price", None) is not None and getattr(k, "item_cid", None):
        item = csv_index.get(int(k.item_cid))
        quality = item.quality if item is not None else getattr(k, "quality", None)
        cells = _shape_wh(item.shape)[0] * _shape_wh(item.shape)[1] if item is not None else 1
        return [runtime["WeightedValue"](float(k.price), 1.0, quality, cells)]

    item_cid = getattr(k, "item_cid", None)
    if item_cid in csv_index:
        item = csv_index[int(item_cid)]
        return [
            runtime["WeightedValue"](
                float(item.base_value),
                1.0,
                item.quality,
                _shape_wh(item.shape)[0] * _shape_wh(item.shape)[1],
            )
        ]

    candidates = runtime["_filter_candidates"](
        getattr(k, "shape", None),
        getattr(k, "quality", None),
        set(getattr(k, "categories", set())),
        item_cid,
        csv_index,
        csv_items,
        getattr(k, "excluded_categories", None),
        getattr(k, "excluded_qualities", None),
    )
    if not candidates:
        return []

    if len(candidates) == 1:
        item = candidates[0]
        return [
            runtime["WeightedValue"](
                float(item.base_value),
                1.0,
                item.quality,
                _shape_wh(item.shape)[0] * _shape_wh(item.shape)[1],
            )
        ]

    probs = runtime["candidate_probabilities"](
        candidates,
        map_category_weights,
        map_id,
    )
    observed_price = float(k.price) if getattr(k, "price", None) is not None else None
    return [
        runtime["WeightedValue"](
            float(item.base_value),
            probs.get(item.item_id, 0.0)
            * runtime["price_likelihood"](float(item.base_value), observed_price),
            item.quality,
            _shape_wh(item.shape)[0] * _shape_wh(item.shape)[1],
        )
        for item in candidates
    ]


def _confidence_from_estimate(estimate: Any) -> float:
    item_count = max(0, int(getattr(estimate, "item_count", 0) or 0))
    unresolved_count = max(0, int(getattr(estimate, "unresolved_count", 0) or 0))
    cv = max(0.0, float(getattr(estimate, "cv", 0.0) or 0.0))
    total = max(1, item_count + unresolved_count)
    unresolved_ratio = unresolved_count / total
    score = 1.0 - (unresolved_ratio * 0.45) - min(0.35, cv * 0.20)
    return max(0.05, min(0.99, score))


def build_shadow_snapshot(
    config: dict[str, Any],
    parsed_patch: dict[str, Any],
    round_no: int,
    price_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    project_root = _shadow_project_root(config)
    if not project_root.exists():
        snapshot = {
            "available": False,
            "expected_value": 0.0,
            "empty_cell_count": 0,
            "confidence": 0.0,
            "source": "getlog",
            "reason": f"shadow project not found: {project_root}",
        }
        return snapshot

    runtime = _shadow_runtime(str(project_root.resolve()))
    log_path = _shadow_log_path(config, project_root)
    csv_path = _shadow_csv_path(config, project_root)
    if not log_path.exists():
        return {
            "available": False,
            "expected_value": 0.0,
            "empty_cell_count": 0,
            "confidence": 0.0,
            "source": "getlog",
            "reason": f"log not found: {log_path}",
        }
    if not csv_path.exists():
        return {
            "available": False,
            "expected_value": 0.0,
            "empty_cell_count": 0,
            "confidence": 0.0,
            "source": "getlog",
            "reason": f"csv not found: {csv_path}",
        }

    csv_index, csv_items = runtime["load_csv"](str(csv_path))
    state = runtime["parse_last_game_state_from_tail"](str(log_path), csv_index, csv_items)
    if state is None or not getattr(state, "items", None):
        return {
            "available": False,
            "expected_value": 0.0,
            "empty_cell_count": 0,
            "confidence": 0.0,
            "source": "getlog",
            "reason": f"no parsed game state from {log_path}",
        }

    map_category_weights = None
    if price_config and isinstance(price_config.get("category_weights"), dict):
        map_category_weights = {
            int(str(key)[3:]): float(value)
            for key, value in price_config.get("category_weights", {}).items()
            if str(key).startswith("cat")
        }

    item_rows = list(getattr(state, "items", {}).items())
    distributions = [
        _posterior_distribution_for_item(
            uid,
            k,
            csv_index,
            csv_items,
            map_category_weights,
            getattr(state, "map_id", 0),
            runtime,
        )
        for uid, k in item_rows
    ]
    estimate = runtime["estimate_total_posterior"](distributions)
    empty_cell_count = _compute_empty_zone_count(
        state,
        runtime["GRID_COLS"],
        runtime["GRID_ROWS"],
        runtime["MIN_ROUND_SHOW_EMPTY"],
    )
    confidence = _confidence_from_estimate(estimate)
    min_confidence = 0.0
    try:
        min_confidence = float(config.get("pricing", {}).get("shadow_bridge", {}).get("min_confidence", 0.0))
    except Exception:
        min_confidence = 0.0
    if confidence < min_confidence:
        return {
            "available": False,
            "expected_value": float(getattr(estimate, "estimate", 0.0) or 0.0),
            "empty_cell_count": int(empty_cell_count or 0),
            "confidence": float(confidence),
            "source": "getlog",
            "reason": f"shadow confidence {confidence:.3f} below threshold {min_confidence:.3f}",
        }
    reason = (
        f"getlog snapshot round={getattr(state, 'current_round', round_no)} "
        f"items={getattr(estimate, 'item_count', 0)}/{len(item_rows)} "
        f"cv={float(getattr(estimate, 'cv', 0.0) or 0.0):.3f}"
    )
    if empty_cell_count is None:
        empty_cell_count = 0
        reason += "; empty cells unavailable"
    else:
        reason += f"; empty={empty_cell_count}"

    snapshot = {
        "available": True,
        "expected_value": float(getattr(estimate, "estimate", 0.0) or 0.0),
        "empty_cell_count": int(empty_cell_count),
        "confidence": float(confidence),
        "source": "getlog",
        "reason": reason,
    }
    return snapshot