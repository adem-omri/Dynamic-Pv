# README AUDIT - STEP 3: Cloning + Structural Integrity Enforcement

This document audits the lifecycle control logic implemented in Step 3, ensuring that PV instances are perfectly synchronized with their templates and that structural integrity is maintained through destructive synchronization.

## 1️⃣ Cloning Process Walkthrough

When a `pv.pv` record is created, the system executes the following steps:

1.  **Placeholder Name Generation**: The `create()` method in `pv.pv` checks if a name is provided. If empty, it fetches the template name and current date to generate a standard name: `PV - {Template Name} - {YYYY-MM-DD}`.
2.  **Parent Record Creation**: The `super().create()` call is executed to create the `pv.pv` record in the database.
3.  **Field Snapshot (Cloning)**: 
    *   The system iterates through all `pv.modele.champ` associated with the template.
    *   For each template field, a new `pv.pv.champ` record is created.
    *   **Data Snapshot**: All structural attributes (`name`, `type_champ`, `required`, `sequence`) and the reference to the original `modele_champ_id` are copied.
4.  **Complex Field Handling**: If a field type is `complex`, the record is created but no rows are generated. This matches the requirement that rows are manual user input.

**Deterministic Behavior**: The entire process happens within a single database transaction. If any part of the cloning fails, the whole PV creation is rolled back, preventing partial copies.

## 2️⃣ Structural Destruction Map

The system enforces a "Destructive Sync" policy. Any change to the structural definition of a template results in the immediate deletion of all derived PVs.

### Template Deletion
*   **Method Overridden**: `unlink()` in `pv.modele`.
*   **Logic**: Before the template is destroyed, the system performs a search for all `pv.pv` records linked to that template ID and calls `unlink()` on them. This ensures that PVs are cleaned up explicitly before the parent template disappears.

### Template Field Modification
*   **Methods Overridden**: `create()`, `write()`, `unlink()` in `pv.modele.champ`.
*   **Logic**: 
    *   Adding a new field, deleting an existing one, or changing ANY attribute of a template field (name, type, required, sequence) triggers the `_invalidate_pvs()` helper.
    *   This helper finds and deletes all `pv.pv` records associated with the current field's parent `modele_id`.

### Subfield Modification
*   **Methods Overridden**: `create()`, `write()`, `unlink()` in `pv.modele.subfield`.
*   **Logic**: Similar to field modification, but the system must navigate up one level (`subfield -> champ -> modele`) to find the root template and delete all its associated PVs.

## 3️⃣ Safety Mechanisms

*   **Transactional Rollback**: By using Odoo's standard ORM overrides, if a deletion of a PV fails (e.g., due to a lock), the modification of the template field will also fail, keeping the system in a consistent state.
*   **Orphan Prevention**: `ondelete='cascade'` is set on all `Many2one` relations from PV Field -> PV and Row -> PV Field. Even if our explicit code missed a corner case, the database ensures that deleting a PV automatically wipes all its subsidiary data (champs, rows, values).
*   **Deterministic Destruction**: There is no partial update logic. The rule is absolute: if the blueprint is touched, all existing houses are demolished.

## 4️⃣ Edge Case Simulation

*   **Scenario**: User creates Template "A" with two fields. User creates PV "A-1".
*   **Action**: User changes the type of Field 2 in Template "A" from `integer` to `float`.
*   **Observed Behavior**: The `write()` method on `pv.modele.champ` for Field 2 fires. It calls `_invalidate_pvs()`. PV "A-1" is deleted. The type change is then committed to the template.
*   **Result**: The system is clean. No PV exists with a type mismatch.

## 5️⃣ Confirm What Is STILL NOT IMPLEMENTED

*   **No Validation Logic**: Required fields in PVs do not yet block saving if empty.
*   **No Conditional Logic**: Visibility rules on champs based on other field values are not evaluated.
*   **No UI Logic**: All operations are currently at the ORM level. No views or action buttons have been defined.
*   **No Complex Row Validation**: Complex fields do not yet enforce the "at least one row" rule.
