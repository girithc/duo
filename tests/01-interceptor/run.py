#!/usr/bin/env python3
"""Run every test-*.py in tests/: form the contract, then drive SubQ selection.

Per test file:
  1. Form the contract state from its three inputs
     (TICKET, SIGNATURES_SKELETON, FILE_MANIFEST) — the run file owns
     contract formation, test files hold data only.
  2. Pass 1 — send the 24 higher-level family noul gates in one request.
  3. Pass 2 — pool granular types of selected families, batch at 128
     questions per request, merge answers.
  4. Emit the curated, severity-ordered test-type list the generator
     should produce (printed + saved to tests/01-interceptor/output/).

Catalog + question builders: 01-intercept/inputs/tests.py

Usage (from project root):
    python3 tests/01-interceptor/run.py              # run all test files
    python3 tests/01-interceptor/run.py test-1.py    # run a single file

Per rule.md: no mocks, no placeholders, all errors returned (fail loudly).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent           # tests/01-interceptor
ROOT = TESTS_DIR.parent.parent              # repo root
ENGINE = ROOT / "engine"                    # stage implementations + clients
OUTPUT_DIR = TESTS_DIR / "output"

sys.path.insert(0, str(ENGINE))  # so `client.subq` imports

from client.subq import SubQClient  # noqa: E402

import bus  # noqa: E402

CATALOG_PATH = ENGINE / "01-intercept" / "inputs" / "tests.py"
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
REQUIRED_INPUTS = ("TICKET", "SIGNATURES_SKELETON", "FILE_MANIFEST")


def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discover_test_files(requested: list[str] | None = None) -> list[Path]:
    if requested:
        files = [TESTS_DIR / name for name in requested]
        missing = [str(f) for f in files if not f.is_file()]
        if missing:
            raise FileNotFoundError(f"test file(s) not found: {missing}")
        return files
    files = sorted(p for p in TESTS_DIR.glob("test*.py") if p.name != Path(__file__).name)
    if not files:
        raise FileNotFoundError(f"no test files found in {TESTS_DIR}")
    return files


def form_contract(module) -> dict:
    """Contract state every test file must provide. Missing input = loud failure."""
    missing = [name for name in REQUIRED_INPUTS if not hasattr(module, name)]
    if missing:
        raise AttributeError(
            f"test file '{module.__name__}' is missing required inputs: {missing}"
        )
    return {
        "ticket": module.TICKET,
        "signatures_skeleton": module.SIGNATURES_SKELETON,
        "file_manifest": module.FILE_MANIFEST,
    }


def run_one(test_path: Path, catalog, client) -> dict:
    module = load_module(test_path.stem.replace("-", "_"), test_path)
    state = form_contract(module)
    input_tokens = 0

    # Pass 1 — higher-level categories: 24 noul gates, one request.
    pass1_answers = client.decide_full(state, catalog.pass1_questions())
    input_tokens += pass1_answers["usage"]["input_tokens"]
    selected_family_ids = sorted(
        int(qname[3:])  # "fam07" -> 7
        for qname, ans in pass1_answers["answers"].items()
        if ans.get("noul", 0.0) >= catalog.CONFIDENCE_FLOOR
    )
    for qname, ans in sorted(pass1_answers["answers"].items()):
        bus.publish("family_gate", family=qname,
                    noul=round(ans.get("noul", 0.0), 3),
                    selected=int(qname[3:]) in selected_family_ids)

    # Pass 2 — granular types of selected families, pooled and batched at 128.
    curated: list[dict] = []
    batches = catalog.pass2_questions(set(selected_family_ids))
    for batch in batches:
        pass2_answers = client.decide_full(state, batch)
        input_tokens += pass2_answers["usage"]["input_tokens"]
        for qname, ans in pass2_answers["answers"].items():
            confidence = ans.get("noul", 0.0)
            leaf_id = qname.split("__", 1)[1]
            if confidence < catalog.CONFIDENCE_FLOOR:
                bus.publish("type_verdict", leaf_id=leaf_id,
                            confidence=round(confidence, 3),
                            selected=False, band="dropped")
                continue
            fam, leaf = catalog.leaf_index()[leaf_id]
            bus.publish("type_verdict", leaf_id=leaf_id,
                        confidence=round(confidence, 3), selected=True,
                        band=catalog.confidence_band(confidence))
            curated.append({
                "family_id": fam.id,
                "family": fam.name,
                "leaf_id": leaf.id,
                "definition": leaf.definition,
                "severity": leaf.severity,
                "tool": leaf.tool,
                "confidence": confidence,
                "band": catalog.confidence_band(confidence),
            })

    curated.sort(key=lambda row: (SEVERITY_ORDER[row["severity"]], -row["confidence"]))

    return {
        "test": test_path.name,
        "selected_families": selected_family_ids,
        "pass2_batches": len(batches),
        "input_tokens": input_tokens,
        "curated_test_types": curated,
    }


def main() -> int:
    requested = sys.argv[1:] or None
    test_files = discover_test_files(requested)
    catalog = load_module("duo_test_catalog", CATALOG_PATH)
    client = SubQClient()  # fails loudly if SUBQ_API_KEY is not set

    OUTPUT_DIR.mkdir(exist_ok=True)

    results, errors = [], []
    for test_path in test_files:
        try:
            results.append(run_one(test_path, catalog, client))
        except Exception as exc:  # rule.md #3: collect ALL errors, report them all
            errors.append((test_path.name, exc))

    for result in results:
        out_path = OUTPUT_DIR / f"{result['test']}_curated.json"
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    if errors:
        print("\n!!! FAILURES (all returned, none filtered):", file=sys.stderr)
        for name, exc in errors:
            print(f"  {name}: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
