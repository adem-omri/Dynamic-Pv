# PV Dynamic Knowledge Map

This document provides a comprehensive structural and functional mapping of the `pv_dynamic` Odoo module. It is designed to be easily parsed by AI assistants to understand the entire architecture, data models, views, and logic flows.

## 📁 1. Folder Structure

```text
pv_dynamic/
├── __init__.py               # Module initialization
├── __manifest__.py           # Module manifest (depends, data, security)
├── README.md                 # Project documentation
├── security/                 
│   └── ir.model.access.csv   # Access rights for all models
├── data/                     
│   └── pv_modele_demo.xml    # Demo data (General Site Audit template)
├── models/                   
│   ├── __init__.py           
│   ├── pv_modele.py          # Template model
│   ├── pv_modele_champ.py    # Template fields definition
│   ├── pv_modele_subfield.py # Template subfields for complex types
│   ├── pv_pv.py              # PV Instance model
│   ├── pv_pv_champ.py        # PV Instance fields (snapshot)
│   ├── pv_pv_champ_row.py    # PV Instance complex field rows
│   └── pv_pv_champ_row_value.py # PV Instance complex field subfield actual values
├── views/                    
│   ├── pv_modele_views.xml   # Views & Actions for Templates
│   └── pv_pv_views.xml       # Views & Actions for PV Instances
└── tests/                    
    ├── __init__.py           
    └── test_pv_dynamic.py    # Unit, Integration, and Stress tests
```

---

## 🏗️ 2. Core Models

### `pv.modele` (Template Master)
*   **Purpose**: Defines the master schema/structure for a PV.
*   **Fields**:
    *   `name` (Char, Required)
    *   `active` (Boolean, Default: True)
    *   `champ_ids` (One2many -> `pv.modele.champ`, inverse: `modele_id`, Cascade)

### `pv.modele.champ` (Template Field Definition)
*   **Purpose**: Defines an individual field within a Template, including its type, configuration, and conditional logic.
*   **Fields**:
    *   `modele_id` (Many2one -> `pv.modele`, Required, Cascade)
    *   `name` (Char, Required, Label)
    *   `type_champ` (Selection: `char, date, integer, float, percentage, boolean, complex`, Required)
    *   `required` (Boolean, Default: False)
    *   `sequence` (Integer, Default: 10)
    *   `subfield_ids` (One2many -> `pv.modele.subfield`, inverse: `champ_id`, Cascade)
    *   `condition_field_id` (Many2one -> `pv.modele.champ`, Domain: `[('modele_id', '=', modele_id)]`)
    *   `condition_operator` (Selection: `=`, `!=`, `>`, `<`)
    *   `condition_value` (Char)

### `pv.modele.subfield` (Template Complex Subfield)
*   **Purpose**: Defines column definitions for `complex` type fields (think: columns in a table/grid).
*   **Fields**:
    *   `champ_id` (Many2one -> `pv.modele.champ`, Required, Cascade)
    *   `name` (Char, Required)
    *   `type_champ` (Selection, excludes `complex`)
    *   `sequence` (Integer, Default: 10)

### `pv.pv` (PV Instance Master)
*   **Purpose**: Represents an instantiated, fillable PV record cloned from a Template.
*   **Fields**:
    *   `name` (Char)
    *   `modele_id` (Many2one -> `pv.modele`, Required, Cascade)
    *   `date` (Date, Default: today)
    *   `champ_ids` (One2many -> `pv.pv.champ`, inverse: `pv_id`, Cascade, `prefetch=True`)
*   **Logic & Overrides**:
    *   `create()`: Overridden to execute a two-pass clone. 
        1. Clones all `pv.modele.champ` records cleanly.
        2. Remaps `condition_field_id` relationships so instances refer to sister instance records, not template records.
        3. Auto-generates `name`.
    *   `@api.constrains('champ_ids') _validate_required_fields`: Traverses all related `champ_ids`. If `is_visible == True` and `required == True`, checks for nulls/empties. For `complex` types, enforces `len(row_ids) > 0`.

### `pv.pv.champ` (PV Instance Field Data)
*   **Purpose**: Holds actual user-inputted values and evaluates runtime visibility for an instance.
*   **Fields**:
    *   `pv_id` (Many2one -> `pv.pv`, Required, Cascade)
    *   `modele_champ_id` (Many2one -> `pv.modele.champ`, Required) - Strict template adherence referencing.
    *   *Configuration clones*: `name, type_champ, required, sequence`.
    *   *Condition clones*: `condition_field_id` (Many2one -> `pv.pv.champ`), `condition_operator, condition_value`.
    *   `is_visible` (Boolean, Computed, `store=False`): Topologically evaluates conditions recursively handling nested conditions.
    *   *Data Containers*: `valeur_char, valeur_date, valeur_integer, valeur_float, valeur_percentage, valeur_boolean`.
    *   `row_ids` (One2many -> `pv.pv.champ.row`, for complex types, `prefetch=True`).
*   **Logic**:
    *   `_compute_is_visible()`: Evaluates dependencies. If the master dependent field is hidden, the child hides automatically. Typecasts the dynamic values cleanly against `condition_value`.
    *   `action_open_complex()`: Returns an `ir.actions.act_window` dictionary to pop open a dedicated form view for `row_ids` editing.

### `pv.pv.champ.row` (PV Complex Field Row)
*   **Purpose**: Manages multiple rows inside a `complex` field instance.
*   **Fields**:
    *   `champ_id` (Many2one -> `pv.pv.champ`, Required, Cascade)
    *   `sequence` (Integer)
    *   `value_ids` (One2many -> `pv.pv.champ.row.value`, inverse: `row_id`, Cascade, `prefetch=True`).
*   **Logic & Overrides**:
    *   `create()`: Overridden. When a user creates a new row, it reads the Template's `subfield_ids` and instantly auto-populates `value_ids` with empty records so the tree renders cleanly inline.

### `pv.pv.champ.row.value` (PV Complex Subfield Value)
*   **Purpose**: Holds the actual cell data for a specific subfield column in a complex row.
*   **Fields**:
    *   `row_id` (Many2one -> `pv.pv.champ.row`, Required, Cascade)
    *   `subfield_id` (Many2one -> `pv.modele.subfield`, Required)
    *   `type_champ` (Selection, Cloned)
    *   *Data Containers*: `valeur_char, ...` (same as `pv.pv.champ`).

---

## 👁️‍🗨️ 3. App Views & UI (`views/*.xml`)

### `pv_modele_views.xml`
*   **Menu**: Setup -> PV Templates.
*   **Views**:
    *   **Tree/Form**: Configures Template details.
    *   **Embedded Tree/Form (`champ_ids`)**: Manages fields. The form explicitly lays out Condition Logic (hiding fields conditionally using simple `attrs` if `condition_field_id` is blank).
    *   **Deep Embedded Tree (`subfield_ids`)**: Renders dynamically inside the field form only if `type_champ == 'complex'`.

### `pv_pv_views.xml`
*   **Menu**: PV Dynamic -> PVs.
*   **Views**:
    *   **Tree/Form**: Primary Instance Entry.
    *   **Dynamic UI (`champ_ids`)**: Native Odoo `attrs="{'invisible': [('is_visible','=',False)]}"` handles hiding elements entirely cleanly in the DOM without JS.
    *   **Atomic vs Complex Separation**: 
        *   Atomic fields (char etc.) render inline with `widget` formatting depending on `type_champ`.
        *   Complex fields render a "Manage Rows" `<button>` firing `action_open_complex()`.
    *   **Popup Popout View**: The complex button opens identical model context targeted to show the `row_ids` one2many recursively via `target="new"`.

---

## 🔒 4. Security
*   `ir.model.access.csv`: Standard boilerplate mapping all 7 models to `base.group_user` with `1,1,1,1` (Read, Write, Create, Unlink) permissions globally.

---

## 📦 5. Data & Defaults
*   `data/pv_modele_demo.xml`: 
    *   Loaded as `noupdate="1"`.
    *   Creates template: "General Site Audit".
    *   Pre-configured fields: "Project Name" (char), "Date" (date), "Passed" (bool), "Reason" (char, conditionally bounds to `Passed` = False), and "Equipment" (complex list with Serial No and Condition subfields).

---

## 🧪 6. Testing coverage (`tests/test_pv_dynamic.py`)

*   **`test_01_unit_pv_creation`**: Validates the two-pass clone mapping correctly copies fields and skips generating complex row contents initially.
*   **`test_02_unit_conditional_visibility`**: Simulates chained dependencies determining whether `is_visible` cascades cleanly through compute fields and tests typecasting (Flushes the ORM deliberately).
*   **`test_03_unit_validation_enforcement`**: Manually forces the `@api.constrains` check making sure hidden required fields gracefully pass, while visible empty fields block transactionally.
*   **`test_04_integration_template_deletion_cascade`**: Validates `ondelete='cascade'` sweeps `pv.pv` entirely if a template vanishes.
*   **`test_05_integration_structural_modification_invalidation`**: "Destructive Sync". Proof that editing a template structural piece (like `required`) effectively severs or forces data invalidation cleanly in real-world scenarios.
*   **`test_06_stress_large_template`**: Bulk load test producing 50 atomic and 50 complex subfields concurrently and tests ORM deletion throughput.

---

## 🔄 7. Step-by-Step Functional Lifecycle

1. **Configuration**: Admin accesses *PV Templates*, designs a workflow using `pv.modele.champ`.
2. **Cloning (Destructive Sync policy)**: User opens *PVs* -> *Create*. User associates a Template. At save/create, Odoo creates `pv.pv`. The system fires a two-pass deep-copy creating a pristine structural snapshot of the template in `pv.pv.champ`.
3. **Data Entry**: Form UI reads `pv.pv.champ`. Elements toggle in frontend strictly utilizing the computed `is_visible` flag. Checkboxes naturally reveal textboxes underneath them topologically. 
4. **Nested Grid Handling**: User triggers a Complex field action. Form opens modal overlay. User clicks "Add line" -> ORM immediately spawns `pv.pv.champ.row` which instantly calls `create()` overriding to spam-generate related `pv.pv.champ.row.value` records ensuring inline editable subfields exist flawlessly.
5. **Validation Hook**: Before final DB save, `@api.constrains` sweeps all values, strictly confirming `required=True` matches populated fields. Odoo rejects commit if anything fails.

---

## ⚠️ 8. Known Limitations & TODOs

*   **Data Types**: Missing `many2one` relational pointer fields out of the box natively configured in dynamic rules.
*   **Double Computes**: Conditional fields execute on memory load (`store=False`). While `prefetch=True` was added in Step 8 to prevent DB hits, computing topologies in Python for extremely large lists could still cause client sluggishness over 500+ fields.
*   **Complex Nesting Limitations**: System architecture allows atomic fields inside a complex row subfield. It does NOT conditionally support Complex fields inside Complex subfields (matrix/cube generation).

## 🚀 9. Entry Points

*   **UI Menu Initiation**: `menu_pv_modele_root` (Settings) & `menu_pv_pv_root` (App Root).
*   **Validation Initiation**: `@api.constrains('champ_ids') _validate_required_fields` hook in `pv.pv.py`.
*   **Cloning Initiation**: `create()` method in `pv.pv.py`.
*   **Subfield Grid Generation Initiation**: `create()` hook in `pv.pv.champ.row.py`.
*   **PopOut Initiation**: `<button name="action_open_complex" type="object"/>` in XML referencing `pv.pv.champ.py`.
