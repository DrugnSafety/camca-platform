---
name: gina-2024-reference
description: |
  Summary of GINA 2024 (Global Strategy for Asthma Management and Prevention) sections relevant to inhaler technique assessment. Includes Box 3-6 common errors mapped to CAMCA critical error IDs, recommended training intervals, and ready-to-use citation strings for evaluation rationales and patient-facing reports. Use when an evaluator needs the authoritative GINA-aligned criterion for a scoring decision.
---

# GINA 2024 — Inhaler Technique Reference

## Source

> Global Initiative for Asthma. *Global Strategy for Asthma Management and Prevention*, 2024. Available from www.ginasthma.org

Short citation form for use in rationales: **GINA 2024**
Long citation form for use in reports/papers: *Global Initiative for Asthma. Global Strategy for Asthma Management and Prevention, 2024. www.ginasthma.org*

## Relevant GINA 2024 Sections

### Chapter 3 — Treating asthma to control symptoms and minimize risk

Key recommendation: **"Check inhaler technique at every visit, particularly if asthma is not well controlled."**

Practice points:
- Most patients (up to 70-80%) cannot use their inhaler correctly
- Health professionals often cannot demonstrate inhaler technique correctly either (Plaza 2018)
- Brief training (2-3 minutes per visit) significantly improves technique and outcomes
- Re-demonstration at every visit, not just at start of therapy

### Box 3-6 — Common errors in inhaler use (GINA 2024)

GINA 2024 lists the following common errors. Mapped to CAMCA critical error IDs:

| GINA Box 3-6 Error | CAMCA Critical Error ID | Device |
|---|---|---|
| Failure to remove cap | CRIT-pMDI-02 | pMDI |
| Failure to shake | CRIT-pMDI-01 | pMDI (suspension) |
| Failure to exhale before actuation | CRIT-UNIV-01 / CRIT-pMDI-03 | pMDI, DPI |
| Failure to time inhalation with actuation | CRIT-pMDI-04, CRIT-pMDI-05 | pMDI |
| Slow inhalation through DPI | CRIT-TBH-05, CRIT-TBH-06 | DPI |
| Failure to inhale deeply and forcefully (DPI) | CRIT-TBH-05 to -07 | DPI |
| Inhaling too fast through pMDI | CRIT-pMDI-06 | pMDI |
| Failure to breath-hold after inhalation | CRIT-pMDI-08, CRIT-TBH-08 | All |
| Repeated actuation in one breath (pMDI) | (not yet mapped — consider CRIT-pMDI-10 future) | pMDI |
| Exhaling through inhaler (DPI) | CRIT-TBH-04 | DPI |

### Recommended Training Intervals (GINA 2024)

| Patient situation | Recommended technique check |
|---|---|
| New inhaler prescription | At prescription, again at 1-month follow-up |
| Step-up in therapy | At each step-up visit |
| Uncontrolled asthma despite adequate therapy | At every visit until controlled |
| Stable, well-controlled | At least annually |
| Severe asthma | Every visit |

**Implication for CAMCA**: Re-evaluation schedule in patient-facing PDF report should default to these intervals based on patient context (provided as input metadata).

## GINA 2024 — Patient-Centered Communication Recommendations

When delivering technique feedback to patients, GINA 2024 emphasizes:

1. **Show, don't just tell** — physical demonstration outperforms verbal instruction
2. **Watch the patient, then correct one step at a time** — avoid overwhelming feedback
3. **Use the patient's own device** — generic placebo devices are less effective
4. **Repeat at intervals** — technique decays within weeks without reinforcement
5. **Provide written instructions in patient's language** — particularly for non-native speakers

These principles guide the `patient-feedback-templates-ko` skill design.

## Citation Strings Ready to Embed

For use in `rationale` fields of evaluator output:

- "Per GINA 2024 Chapter 3, this step is critical for asthma control."
- "GINA 2024 Box 3-6 identifies this as a common inhaler error."
- "Inadequate technique on this step has been associated with worse asthma outcomes (GINA 2024; Price 2017)."

For use in patient PDF Korean reports (translated):
- "이는 GINA 2024 글로벌 천식 진료 지침에서 권고하는 표준 흡입 동작입니다."
- "GINA 2024는 이 단계의 오류가 천식 조절 악화와 연관됨을 명시하고 있습니다."

## Cross-References to Other Guidelines

GINA 2024 aligns with but is distinct from:

- **GOLD 2025** — for COPD (less detail on technique, more on device selection)
- **ATS/ERS** — for U.S./European pulmonary societies
- **EAACI** — for European allergy society guidance

When CAMCA is deployed in COPD context, use `gold-2025-reference` skill (future) instead.

## TODO

- [ ] Full GINA 2024 Box 3-6 verbatim quotes for direct citation (requires access to PDF)
- [ ] GOLD 2025 reference skill creation
- [ ] Evidence grade table (GINA uses A/B/C/D evidence levels for each recommendation)
