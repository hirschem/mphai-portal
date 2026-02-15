# Manual Test Procedure: Invoice Wrap Boundary & Debug Logic

**Location:** `apps/api/TESTING_INVOICE_WRAP_BOUNDARY.md`

This document provides a step-by-step, copy/paste-friendly manual procedure to validate the invoice table wrap boundary logic, debug output, and edge-case handling. No code changes are required to follow these steps.

---

## A) Normal Session Test (Non-Stress)

**Session ID:** `dev_check_001`

**Steps:**
1. Ensure the debug flag is **OFF** (unset or `STRESS_TEST_DEBUG=0`).
2. Run the invoice export using your normal method (endpoint, CLI, or script). For example, if using the stress runner:
   ```sh
   python apps/api/run_stress_test.py
   ```
   (Or use your normal export flow, but set `session_id = dev_check_001`.)
3. Locate the output PDF:
   - `apps/data/sessions/dev_check_001/invoice.pdf`

**Expected Results:**
- PDF contains only normal items (no edge-case rows).
- No debug logs are printed to the console.
- No magenta guide lines appear in the PDF.

---

## B) Stress Session Test (Stress Prefix, Debug OFF)

**Session ID:** `stress_test_001`

**Steps:**
1. Ensure the debug flag is **OFF** (unset or `STRESS_TEST_DEBUG=0`).
2. Run the invoice export with the stress session ID:
   ```sh
   python apps/api/run_stress_test.py
   ```
   (Or use your normal export flow, but set `session_id = stress_test_001`.)
3. Locate the output PDF:
   - `apps/data/sessions/stress_test_001/invoice.pdf`

**Expected Results:**
- PDF contains the following edge-case rows:
  - Long description + amount
  - No amount row with long description
  - Very large amount row (e.g. 1234567.89)
  - Short description + amount
- No debug logs are printed to the console.
- No magenta guide lines appear in the PDF.

---

## C) Stress Session Test with Debug ON

**Session ID:** `stress_test_002`

**Steps:**
1. Enable the debug flag (set `STRESS_TEST_DEBUG=1`). For example:
   ```sh
   $env:STRESS_TEST_DEBUG="1"; python apps/api/run_stress_test.py
   ```
   (Or use your normal export flow, but set `session_id = stress_test_002` and enable the debug flag as above.)
2. Locate the output PDF:
   - `apps/data/sessions/stress_test_002/invoice.pdf`

**Expected Results:**
- PDF contains the same edge-case rows as in (B).
- Console output includes per-row debug logs showing:
  - `divider_x`, `amount_right_x`, `amount_left_x` (when applicable), `wrap_limit_x`, and the rule used (`amount_rule` vs `divider_rule`).
- Magenta debug guide lines appear in the PDF ONLY when debug is enabled.

---

## D) Wrap-Boundary Visual Proof Checklist

- For the **NO AMOUNT** row: description wraps based on `divider_x - DESC_PAD_R` (**divider_rule**).
- For the **VERY LARGE AMOUNT** row: description wraps earlier because `amount_left_x` shifts left (**amount_rule**).
- **No overlap** between description and amount column on any row.

---

## E) `compute_pg1_layout_positions()` Call Verification

**Steps:**
1. Open `apps/api/app/services/export_service.py` in your editor.
2. Search for:
   ```
   compute_pg1_layout_positions(
   ```
3. Confirm that there is **only one call** to this function in the invoice Page 1 render path.
   - (If optional debug instrumentation exists, it will be behind the debug flag and will be described in the debug output.)

---

## Notes
- To run these tests, use the same command, endpoint, or stress runner you already use to produce `apps/data/sessions/{session_id}/invoice.pdf`.
- No code changes are required to follow this procedure.
- If you have a different export flow, adapt the session_id and debug flag as described above.

---

**This procedure ensures that edge-case handling, debug output, and wrap-boundary logic are all working as intended, and that production behavior is unaffected.**
