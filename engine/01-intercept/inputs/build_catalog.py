#!/usr/bin/env python3
"""Regenerate tests.py (importable catalog) from tests.md (human-readable doc).

Run after any catalog edit:
    python3 build_catalog.py
"""
import re
from pathlib import Path

HERE = Path(__file__).parent
MD = HERE / "tests.md"
OUT = HERE / "tests.py"

FAM_RE = re.compile(r"^## (\d+)\. (.+?)\s*$")
BELT_RE = re.compile(r"^Tool belt:\s*(.+)$")
LEAF_RE = re.compile(
    r"^- `([\w-]+)`\s*[—–-]\s*(.+?)\.\s*Trigger:\s*(.+?)\.\s*Sev:\s*"
    r"(critical|high|medium|low)\.\s*Tool:\s*`([^`]+)`\s*\.?\s*$"
)


def parse(md_text: str):
    families, cur, skipped = [], None, []
    for lineno, raw in enumerate(md_text.splitlines(), 1):
        line = raw.rstrip()
        m = FAM_RE.match(line)
        if m:
            cur = {
                "id": int(m.group(1)),
                "name": m.group(2),
                "scope": "",
                "tools": [],
                "leaves": [],
            }
            families.append(cur)
            continue
        if cur is None or not line or line.startswith("---"):
            continue
        if line.startswith("## "):  # non-family H2 ends the current family section
            cur = None
            continue
        m = BELT_RE.match(line)
        if m:
            cur["tools"] = re.findall(r"`([^`]+)`", m.group(1))
            continue
        m = LEAF_RE.match(line)
        if m:
            cur["leaves"].append(m.groups())
            continue
        if line.startswith("- `"):  # looks like a leaf but did not parse
            skipped.append((lineno, line[:100]))
            continue
        if not cur["scope"] and not line.startswith("#"):
            cur["scope"] = line.strip()
    return families, skipped


HEADER = '''"""Duo test-type catalog — the frozen SubQ selection yardstick.

24 families -> {n_leaves} granular leaf types (Python ecosystem).
Regenerate from tests.md edits with:  python3 build_catalog.py

SubQ flow (Decisions API, model=subq-snap-1.1, POST /v1/systemone):
  Pass 1: pass1_questions() -> 24 noul gates, one per family.
  Pass 2: pass2_questions(selected_family_ids) -> pooled leaves,
          deduplicated, chunked into batches of <=128 noul questions,
          question names "famNN__leaf-id" for traceability.
  Merge:  union batches, drop confidence < CONFIDENCE_FLOOR (insignificant),
          sort by severity then confidence -> curated list for the
          Stage 02 test generator.
"""
from dataclasses import dataclass

'''

# Emitted verbatim after HEADER (never passed through .format — contains braces).
CONSTANTS = '''MODEL = "subq-snap-1.1"
# Confidence bands: <0.50 insignificant (dropped), 0.50-0.65 very low,
# 0.65-0.70 low, 0.70-0.85 medium, 0.85-1.0 high.
CONFIDENCE_FLOOR = 0.5  # below this = insignificant, dropped
PASS2_MAX_QUESTIONS = 128  # Decisions API limit: 1-128 questions per request


def confidence_band(p: float) -> str:
    if p >= 0.85:
        return "high"
    if p >= 0.70:
        return "medium"
    if p >= 0.65:
        return "low"
    if p >= 0.50:
        return "very_low"
    raise ValueError(f"confidence {p} is insignificant (<0.50) — drop, don't band")


'''


def emit(families) -> str:
    n_leaves = sum(len(f["leaves"]) for f in families)
    out = [HEADER.format(n_leaves=n_leaves), CONSTANTS]
    out.append("@dataclass(frozen=True)\nclass Leaf:\n    id: str\n    definition: str\n    trigger: str\n    severity: str\n    tool: str\n\n\n")
    out.append("@dataclass(frozen=True)\nclass Family:\n    id: int\n    name: str\n    scope: str\n    tools: tuple[str, ...]\n    leaves: tuple[Leaf, ...]\n\n\n")
    out.append("CATALOG: tuple[Family, ...] = (\n")
    for f in families:
        out.append("    Family(\n")
        out.append(f"        id={f['id']},\n")
        out.append(f"        name={f['name']!r},\n")
        out.append(f"        scope={f['scope']!r},\n")
        out.append(f"        tools={tuple(f['tools'])!r},\n")
        out.append("        leaves=(\n")
        for lid, definition, trigger, sev, tool in f["leaves"]:
            out.append(
                f"            Leaf(id={lid!r}, definition={definition!r}, "
                f"trigger={trigger!r}, severity={sev!r}, tool={tool!r}),\n"
            )
        out.append("        ),\n    ),\n")
    out.append(")\n\n")
    out.append(HELPERS)
    return "".join(out)


HELPERS = '''

def leaf_index() -> dict[str, tuple[Family, Leaf]]:
    """Map leaf-id -> (family, leaf). First family wins on duplicate ids."""
    idx: dict[str, tuple[Family, Leaf]] = {}
    for fam in CATALOG:
        for leaf in fam.leaves:
            idx.setdefault(leaf.id, (fam, leaf))
    return idx


def pass1_questions() -> dict[str, dict]:
    """Pass 1: 24 noul gates, one per family, in a single request."""
    qs = {}
    for fam in CATALOG:
        qs[f"fam{fam.id:02d}"] = {
            "type": "noul",
            "instructions": (
                f"Is the '{fam.name}' family relevant for testing this change? "
                f"Family scope: {fam.scope}"
            ),
            "criteria": {
                "true": f"Ticket/skeleton/manifest signals work in scope of: {fam.scope}",
                "false": "No signal in this family's scope",
            },
        }
    return qs


def pass2_questions(selected_family_ids: set[int]) -> list[dict[str, dict]]:
    """Pass 2: pool leaves of selected families, dedupe, chunk <=128 per request.

    Returns a list of question dicts; question names are 'famNN__leaf-id'.
    """
    pool, seen = [], set()
    for fam in CATALOG:
        if fam.id not in selected_family_ids:
            continue
        for leaf in fam.leaves:
            if leaf.id in seen:
                continue
            seen.add(leaf.id)
            pool.append((fam, leaf))
    batches = []
    for i in range(0, len(pool), PASS2_MAX_QUESTIONS):
        chunk = pool[i : i + PASS2_MAX_QUESTIONS]
        qs = {}
        for fam, leaf in chunk:
            qs[f"fam{fam.id:02d}__{leaf.id}"] = {
                "type": "noul",
                "instructions": (
                    f"Should the test generator cover '{leaf.definition}' "
                    f"for this change? Applies when: {leaf.trigger}."
                ),
                "criteria": {
                    "true": "Ticket/contract signals this risk",
                    "false": "Not signaled for this change",
                },
            }
        batches.append(qs)
    return batches


if __name__ == "__main__":
    import json

    all_ids = {f.id for f in CATALOG}
    print(f"families: {len(CATALOG)}")
    print(f"leaves:   {sum(len(f.leaves) for f in CATALOG)}")
    p1 = pass1_questions()
    print(f"pass1:    {len(p1)} questions")
    batches = pass2_questions(all_ids)
    print(f"pass2 (all families selected): {len(batches)} batches, "
          f"sizes {[len(b) for b in batches]}")
    json.dumps(p1)
    json.dumps(batches)
    print("json-serializable: ok")
'''


def main():
    families, skipped = parse(MD.read_text(encoding="utf-8"))
    OUT.write_text(emit(families), encoding="utf-8")
    counts = {f["id"]: len(f["leaves"]) for f in families}
    print(f"wrote {OUT} — {len(families)} families, "
          f"{sum(counts.values())} leaves")
    if skipped:
        print(f"WARNING: {len(skipped)} unparseable leaf lines:")
        for lineno, text in skipped[:10]:
            print(f"  line {lineno}: {text}")


if __name__ == "__main__":
    main()
