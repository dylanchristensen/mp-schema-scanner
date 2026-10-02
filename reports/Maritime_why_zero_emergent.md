# Why the Maritime Model Yields Zero Emergent Behaviors — 2026-07-21

Question: is the maritime zero a true "schema completeness" result (the paper's
claim), or an artifact of the model's own bugs deleting the regions of the
trace space where emergence would live?

Method: counterfactual enumeration with the validated closed-form enumerator
(`mp_enumerate.py`), on the local 12-REJECT revision (45,836 traces — the
pre-weather space; its 136 trends match the paper's pre-revision figure
exactly).

| Variant | Change | Traces | Trends |
|---|---|---:|---:|
| V0 | as modeled | 45,836 | 136 |
| V1 | restore the 3 ordering-deleted workflows (VTS warning×give-way, allocated×moored, give-way×altering) | 49,026 | 152 |
| V2 | V1 + revive cargo ops (drop the sibling-contradiction REJECT) | 49,656 | 158 |

## Answer: the zero is real. Three findings.

### 1. The suppressed workflows were not masking emergence
V1 restores 3,190 deleted traces and produces 28 new trends — every one of
them weak (max |log OR| = 0.16, barely over the CI gate at N≈49k). These are
base-rate ripples from re-weighting the space, not hidden dependencies. If a
genuine emergent association had been buried under the ordering deletions, it
would appear here. Nothing does.

### 2. Reviving cargo ops shows rule-CHAINS manufacturing significance
V2 makes `cargo_ops_active` reachable (630 traces) and immediately produces
strong trends (|log OR| up to 8.1) — all of them two-hop consequences of the
surviving rules: cargo requires moored; moored requires tugs assisting; hence
cargo↔tugs_assisting at +8.09 and cargo-excludes-everything-else at −4 to −6.
None of these pairs is named together by any single REJECT — a **single-rule
schema filter misses all of them**. This is direct evidence for the paper's
Section-4 thesis and sharpens it: the schema-aware filter must compute
**transitive rule implication**, not per-rule mention.

### 3. Where maritime's unwritten assumptions actually are
The statistical flag finds nothing because the domain's cross-component
dependencies are almost all *written down* (12 REJECTs spanning COLREGs
coupling, the GNSS→AIS→ECDIS chain, tug/pilot/tide requirements). What remains
unwritten surfaces on the **symbolic** side instead: the scanner's candidates
(`tugs_assisting` requires `tugs_dispatched`; `vessel_moored` requires
`berth_allocated`) are real unstated assumptions — and the model's own
ordering bugs are themselves unwritten-assumption violations (the orderings
assume coordination that the schema never establishes). Maritime's yield is
zero *statistical* emergents, not zero findings.

Note: the old pipeline report's "genuine" candidate (gnss_jammed ↔
ais_offline/ais_rx_only, lift 1.91) resolves as schema-induced under the
formal criterion: the `tx_msg1_dynamic × gnss_jammed` REJECT forbids both
transmitting AIS states under jamming, forcing AIS ∈ {rx_only, offline}.

## Implications for the paper

- The maritime section's claim survives scrutiny and gets stronger: the zero
  is robust to repairing every suppression bug in the model, which rules out
  the obvious objection that the null result is self-inflicted.
- The V2 experiment is a compact, quotable demonstration that schema-induced
  significance propagates through rule chains — motivating the transitive
  schema-aware filter as future work with data instead of assertion.
- Complementarity framing: on intent-complete models, unwritten assumptions
  surface structurally (scanner, ordering audits), not statistically. The two
  flag families are not redundant; they cover opposite ends of the
  schema-completeness spectrum.

Artifacts: `/tmp` variant schemas + DBs regenerable via `mp_enumerate.py`;
variant construction documented in this analysis (drop ENSURE 1/3/4; drop the
cargo×berth_occupied REJECT).
