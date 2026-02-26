# README AUDIT - STEP 5: Conditional Visibility & Validation

This document audits the implementation of conditional logic and required field validation for `pv_dynamic`, verifying that validation constraints cleanly respect visibility rules without compromising transactional safety.

## 1️⃣ Conditional Evaluation Flow

Visibility is determined dynamically at runtime via the `is_visible` computed field on `pv.pv.champ`.

1.  **Condition Definition**: In the Template (`pv.modele.champ`), a field can be configured to depend on another field (`condition_field_id`), evaluating with an operator (`=, !=, >, <`) against a `condition_value`.
2.  **Snapshotting**: During PV creation (Step 3/4), these condition properties are structurally cloned to the `pv.pv.champ` records. Crucially, a two-pass clone ensures that `condition_field_id` correctly points to the *newly cloned* instance field, not the template field.
3.  **Runtime Evaluation**: The `is_visible` field uses `@api.depends` to monitor changes in the target condition field's values (`valeur_char`, `valeur_integer`, etc.) and its `is_visible` state.
4.  **Topological Resolution**: If Field C depends on Field B, and Field B depends on Field A:
    *   If Field A hides Field B...
    *   Field C explicitly checks `if not rec.condition_field_id.is_visible: rec.is_visible = False`.
    *   This guarantees that nested dependencies resolve correctly without infinite loops or deep recursion.

## 2️⃣ Validation Rules

Validation is enforced centrally via `@api.constrains('champ_ids')` on the `pv.pv` model. This triggers immediately before the database commit.

### Rule Enforcement Check
For every field in the PV, the system checks:
`if champ.is_visible and champ.required:`

*   **Rule 1 - Hidden Fields Bypass Validation**: If `is_visible` evaluates to `False`, the required check is entirely skipped. Hidden required fields do *not* block the save.
*   **Rule 2 - Atomic Fields**: If visible and required, the system checks the specific `valeur_*` column based on the field type. If it is `None` or `''` (empty string), it raises a `ValidationError`. (Note: `boolean` fields are treated specially since `False` is usually a valid answer; they bypass the strict emptiness check).
*   **Rule 3 - Complex Fields**: If visible and required, the system checks the `row_ids` relationship. If `not champ.row_ids`, it raises a `ValidationError`, enforcing the "at least one row" rule.

## 3️⃣ Transactional Enforcement

*   **Before Commit**: The `@api.constrains` decorator ensures validation happens at the ORM layer before the SQL `COMMIT`.
*   **Safe Rollback**: If a `ValidationError` is raised, Odoo automatically aborts the current transaction.
    *   This prevents partial saves.
    *   Because it is isolated to the current `pv.pv` transaction, it cannot corrupt other distinct PV records or template structures.
*   **Structural Integrity**: Since users cannot directly create/unlink `pv.pv.champ` records (Step 4), validation only concerns itself with data correctness, not structural manipulation.

## 4️⃣ Edge Case Simulation

### Case A: Nested Conditions
*   **Setup**: Field 1 (Boolean) -> Field 2 (Required, shows if Field 1 = True) -> Field 3 (Required, shows if Field 2 = 'Yes').
*   **Action**: User unchecks Field 1.
*   **Result**: 
    1. Field 1 changes.
    2. Field 2 `is_visible` becomes False.
    3. Field 3 `is_visible` evaluates Field 2's visibility, sees False, and becomes False.
    4. Validation runs. Field 2 and 3 are ignored. Save succeeds.

### Case B: Zero-Row Complex Fields
*   **Setup**: Field "Team Members", type `complex`, `required=True`.
*   **Action**: User attempts to save the PV without adding any rows.
*   **Result**: Validation triggers. `is_visible` is True, `required` is True. `if not champ.row_ids` evaluates to True. `ValidationError("The complex field 'Team Members' requires at least one row.")` is raised. Save is blocked.

### Case C: Mixed Visible/Hidden Required Fields
*   **Setup**: Field A (Required, Visible, Empty), Field B (Required, Hidden, Empty).
*   **Action**: User saves.
*   **Result**: Validation ignores Field B. Validation catches Field A and raises `ValidationError("The field 'Field A' is required and cannot be empty.")`.

## 5️⃣ Confirm What Is STILL NOT IMPLEMENTED

*   **No UI/Frontend Views**: All logic exists entirely in the Python ORM. There are no XML views to define how these fields render, how conditions dynamically hide DOM elements in the browser, or how the complex grid is displayed.
*   **No Business Workflows**: There are no states (Draft, Approved) or approval lifecycles, as dictated by the strict "No workflow states" rule.
