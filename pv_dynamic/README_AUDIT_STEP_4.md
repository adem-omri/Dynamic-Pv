# README AUDIT - STEP 4: PV Instance Value Management

This document audits the implementation of the PV data layer, verifying how user input is stored, managed, and deleted within the strict structural rules of the `pv_dynamic` module.

> **Note**: The relational structures supporting this step were fully implemented during Step 2. This document serves to explain how that structure satisfies the Step 4 requirements for value management.

## 1️⃣ Step-by-Step PV Creation & Transaction Flow

When a user initiates the creation of a new PV instance, the following deterministic flow occurs within a single ORM transaction:

1.  **Template Selection**: The user selects a `pv.modele` (Template). This is the only mandatory input.
2.  **`pv.pv.create()` is triggered**:
    *   **Auto-Naming**: If no name is provided, the system calculates and assigns `PV - {Template Name} - {YYYY-MM-DD}`.
    *   **Root Record Creation**: The `pv.pv` record is inserted into the database.
3.  **Field Cloning Loop**:
    *   The system iterates over `pv.modele_id.champ_ids`.
    *   For each template field, a `pv.pv.champ` record is created.
4.  **Transaction Commit**: All records (`pv.pv` and multiple `pv.pv.champ`) are committed simultaneously.

**Rollback Behavior**: Because this process occurs within a standard Odoo `@api.model_create_multi` override, any failure (e.g., database lock, constraint violation) will rollback the entire transaction. No partial PVs or orphaned fields can be created.

## 2️⃣ Data Storage Mechanics

### Atomic Fields
Stored directly on the cloned `pv.pv.champ` record.

*   `char` enters `valeur_char`
*   `date` enters `valeur_date`
*   `integer` enters `valeur_integer`
*   `float` enters `valeur_float`
*   `percentage` enters `valeur_percentage`
*   `boolean` enters `valeur_boolean`

### Complex Fields
Stored hierarchically. 
When a user adds a row to a grid:

1.  **Row Creation**: A `pv.pv.champ.row` is created, linked via `champ_id` to the parent complex `pv.pv.champ`.
2.  **Cell Values**: Multiple `pv.pv.champ.row.value` records are created, one for each subfield in the blueprint.
3.  **Cell Storage**: These value records use the exact same `valeur_*` columns based on their `type_champ`.

## 3️⃣ Interaction Rules

*   **No Structural Editing**: Users interact with the `pv.pv.champ` records purely for data entry. They cannot create new `pv.pv.champ` records manually, nor can they delete them (enforced by lack of UI mechanisms and structural immutability rules).
*   **Sequential Immutability**: The `sequence` field on `pv.pv.champ` is a static clone from the template. Reordering fields requires modifying the template (which deletes the PV per Step 3).
*   **Row Management**: Users *can* add and delete `pv.pv.champ.row` records. This is standard data entry, not structural modification.

## 4️⃣ Cascading Deletion Map

Integrity is guaranteed by `ondelete='cascade'` at every layer of the PV instance.

If a PV is deleted (`pv.pv.unlink()`):
1.  **`pv.pv`** acts as the root. Wiped.
2.  **`pv.pv.champ`** (where `pv_id` = PV). Wiped.
3.  **`pv.pv.champ.row`** (where `champ_id` = wiped fields). Wiped automatically by the DB.
4.  **`pv.pv.champ.row.value`** (where `row_id` = wiped rows). Wiped automatically by the DB.

No orphan records can survive a PV deletion.

## 5️⃣ Edge Case Simulation

1.  **Create PV without Template**: Denied by ORM (`modele_id` is structurally `required=True`).
2.  **Add Atomic Field Values**: The user edits the `valeur_char` of a specific field. Changes are saved to that exact scalar column.
3.  **Complex Field with Zero Rows**: Allowed. The system creates the `pv.pv.champ` with `type_champ='complex'`, but the `row_ids` One2many relation remains empty until the user specifically acts.
4.  **Delete PV**: 
    *   Given PV "A" with 5 fields, one complex field having 3 rows and 4 subfields per row.
    *   When "A" is deleted: 1 PV record + 5 PV Champ records + 3 Row records + 12 Value records are deleted simultaneously via SQL cascade constraints. The database remains perfectly clean.
