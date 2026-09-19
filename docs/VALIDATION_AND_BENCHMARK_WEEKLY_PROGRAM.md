# Validation and Benchmark Weekly Program

**Repository:** Advocate-Chambers  
**Scope:** Evidence-based validation after the Week 1–20 architectural enrichment  
**Status:** Planned execution program  
**Primary objective:** Prove that the planning system detects dangerous architectural defects, produces findings that professionals can reproduce, and performs predictably across project sizes.

This program validates the software; it does not replace review by a licensed
architect, structural engineer, MEP consultant, accessibility professional,
fire/life-safety professional, surveyor, or local authority.

## Definition of success

The program is successful only when all of the following are true:

1. The adversarial benchmark detects **100% of known critical defects**.
2. The benchmark records **zero dangerous false negatives**.
3. Every critical finding identifies the correct rule, geometry, evidence, and suggested correction.
4. Independent professionals can classify blinded plans and reproduce the important findings.
5. Small, medium, and large workload benchmarks complete without silent timeout, out-of-memory failure, data loss, or nondeterministic results.
6. A failed generation never replaces the last valid revision.
7. The combined quality gate clearly reports `PASS`, `REVIEW_REQUIRED`, `BLOCKED`, or `INCOMPLETE`.

No numerical score may override a failed hard gate.

## Weekly delivery plan

### Week 21 — Quality-gate contract and baseline

**Objective:** Establish one machine-readable contract for the three validation
tracks and record the current baseline before changing the system.

**Deliverables:**

- `scripts/quality_gate.py`
- `tests/test_quality_gate.py`
- `bar-association-hall/standard/quality-gate-report.json`
- JSON schemas for adversarial, professional-review, and performance results
- Baseline record for the existing 69-test regression suite

**Required quality-gate states:**

```text
PASS
REVIEW_REQUIRED
BLOCKED
INCOMPLETE
```

**Acceptance gate:**

- A missing benchmark result produces `INCOMPLETE`.
- A critical false negative produces `BLOCKED`.
- Professional uncertainty produces `REVIEW_REQUIRED`, not `PASS`.
- All existing tests continue to pass.

### Week 22 — Adversarial fixture foundation

**Objective:** Build the first intentionally defective planning corpus and
connect each defect to an expected finding contract.

**Deliverables:**

- At least 15 defective fixtures
- Valid source fixture paired with each defective fixture
- Expected rule ID, severity, affected object, evidence, and correction
- Fixture metadata schema
- Automated fixture discovery and execution

**Initial defect families:**

- Inaccessible first-floor room
- Door opening into a wall
- Door opening into a private or locked room
- Corridor blocked by furniture
- Door swing blocking circulation
- Stair without landing
- Disconnected second floor
- Invalid external door
- Missing fire access
- Invalid setback
- Poor daylight or ventilation
- Wet-area coordination failure

**Acceptance gate:**

- Every fixture has a deterministic expected result.
- Every critical fixture fails for the intended rule.
- The report identifies the affected room, opening, stair, route, furniture, or site geometry.

### Week 23 — Adversarial benchmark expansion and hardening

**Objective:** Expand the corpus to 30–50 fixtures and prove that the system
does not only pass happy-path examples.

**Deliverables:**

- 30 fixtures minimum; 50 fixtures preferred
- Valid, invalid, and incomplete-input fixture groups
- False-positive and false-negative report
- Mutation cases for geometry, openings, routes, furniture, levels, and site data
- Regression test for every defect discovered during the benchmark

**Required measurements:**

```text
critical defects
detected defects
missed defects
false positives
false negatives
rule-ID accuracy
affected-geometry accuracy
suggested-correction completeness
```

**Acceptance gate:**

- 100% of known critical defects are detected.
- Zero dangerous false negatives.
- No critical false positive remains unexplained.
- Every failure includes a rule, evidence, affected geometry, and correction.

If this gate fails, the release status is `BLOCKED` and the next week is spent
fixing the detection contract before adding more features.

### Week 24 — Independent professional review package

**Objective:** Test whether independent professionals find the same important
problems and can reproduce the software's reasoning.

**Deliverables:**

- Blinded review pack containing:
  - 10 valid plans
  - 10 intentionally defective plans
  - 5 borderline or incomplete-input plans
- Reviewer instructions
- Standard review form
- Reviewer finding and disagreement schema
- Anonymized review results

**Reviewer scorecard:**

- Usable / not usable / uncertain
- Access correctness
- Room adjacency quality
- Dimensional credibility
- Stair and exit quality
- Drawing clarity
- Furniture and circulation quality
- Missing assumptions
- Reproducibility of software findings
- Reviewer confidence

**Acceptance gate:**

- At least two independent reviewers participate.
- At least 90% agreement is achieved for usable/not-usable classification.
- No critical defect is accepted as usable by both reviewers.
- Every critical disagreement is documented.
- Reviewers can reproduce each critical software finding from the model, rule ID, geometry, and calculation.

Professional review results must not be stored as an automatic approval or
permit decision.

### Week 25 — Performance benchmark harness

**Objective:** Measure runtime behavior for representative project sizes and
establish evidence-based performance limits.

**Workload profiles:**

| Profile | Floors | Rooms | Openings | Furniture |
|---|---:|---:|---:|---:|
| Small | 1–2 | Up to 15 | Up to 25 | Up to 30 |
| Medium | 2–3 | 16–50 | 26–100 | 31–150 |
| Large | 4+ | 51–150 | 101–400 | 151–600 |

**Deliverables:**

- `benchmarks/run_benchmark.py`
- `benchmarks/README.md`
- Small, medium, and large workload fixtures
- JSON results with machine, commit, rule-pack, and input signatures
- p50 and p95 measurements

**Record:**

- Model-generation time
- Validation time
- Site-feasibility time
- Furniture and clearance time
- Technical PDF export time
- Coloured presentation export time
- DXF export time
- API p50 and p95 latency
- Peak memory
- CPU time
- Maximum supported rooms, floors, openings, and furniture
- Timeout and out-of-memory count
- Failure recovery time

**Initial engineering targets:**

| Operation | Small p95 | Medium p95 | Large p95 |
|---|---:|---:|---:|
| Model generation | 5 sec | 15 sec | 60 sec |
| Validation | 5 sec | 15 sec | 60 sec |
| Technical export | 10 sec | 30 sec | 120 sec |

The first run establishes the baseline. Any revised target must be recorded
with its reason rather than silently changing the threshold.

**Acceptance gate:**

- No silent timeout.
- No out-of-memory failure.
- No loss of the last valid revision.
- Repeated identical inputs produce identical model and validation signatures.

### Week 26 — Reproducibility and failure recovery

**Objective:** Prove that another workspace can verify, restore, and reproduce
the same planning result.

**Deliverables:**

- Reproducibility runner
- Failure-injection tests
- Restore verification report
- Tampered-manifest test cases
- Partial-export and missing-artifact test cases
- Revision comparison report

**Required checks:**

1. Save input model hash.
2. Save application commit.
3. Save rule-pack version.
4. Save model signature.
5. Save validation signature.
6. Save artifact manifest.
7. Re-run the same input.
8. Compare all signatures and findings.

**Acceptance gate:**

- Tampered manifests are rejected.
- Missing artifacts remain explicitly marked missing.
- Partial generation cannot replace the current valid revision.
- Soft archive and restore preserve the current revision.
- A second workspace can verify the package independently.

### Week 27 — Integrated release decision and remediation

**Objective:** Combine all evidence into one release decision and turn every
unresolved issue into a tracked engineering or professional-review item.

**Deliverables:**

- Final `quality-gate-report.json`
- Human-readable validation report
- Adversarial benchmark summary
- Professional-review summary
- Performance benchmark summary
- Known-limitations register
- Remediation backlog
- Release decision recorded in the README and changelog

**Release classifications:**

| Classification | Meaning |
|---|---|
| `BLOCKED` | A critical defect was missed, data was lost, or reproducibility failed |
| `REVIEW_REQUIRED` | Automated checks pass but professional or site evidence is incomplete |
| `PRELIMINARY_COORDINATION_READY` | Automated hard gates and independent review pass |
| `ISSUABLE` | Only after explicit professional and authority sign-off; never automatic |

**Acceptance gate:**

- No unresolved dangerous false negative.
- All unknowns are visible.
- All reviewer disagreements are recorded.
- Performance results are reproducible.
- Archive and revision verification pass.
- The README uses the correct release classification.

## Proposed repository layout

```text
docs/
  VALIDATION_AND_BENCHMARK_WEEKLY_PROGRAM.md
  PROFESSIONAL_REVIEW_PROTOCOL.md

tests/
  fixtures/
    adversarial/
      valid/
      defective/
      incomplete/
  test_adversarial_architecture.py
  test_quality_gate.py

benchmarks/
  README.md
  run_benchmark.py
  workloads/
    small/
    medium/
    large/
  results/

review/
  blinded/
  forms/
  anonymized-results/

bar-association-hall/standard/
  quality-gate-report.json
  adversarial-benchmark-report.json
  professional-review-report.json
  performance-benchmark-report.json
```

## Weekly report template

Every weekly change must record:

```text
Week:
Objective:
Commit:
Fixtures added:
Tests added:
Automated result:
Professional-review result:
Performance result:
Unknowns:
Blockers:
Evidence paths:
Next decision:
```

## Final success statement

> The application detects all known critical architectural defects in the
> benchmark corpus, produces explainable and reproducible findings, survives
> independent professional review, meets documented performance limits, and
> never loses or corrupts a valid project revision.