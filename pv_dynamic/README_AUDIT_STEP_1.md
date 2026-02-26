# README AUDIT - STEP 1: Base Module Structure

This document serves as an audit of the initial structure created for the `pv_dynamic` Odoo module, ensuring alignment with the non-negotiable architectural rules.

## 1️⃣ Folder Structure Tree

The following structure has been established:

```text
pv_dynamic/
├── __init__.py
├── __manifest__.py
├── README_AUDIT_STEP_1.md
├── models/
│   ├── __init__.py
│   ├── pv_modele.py
│   ├── pv_modele_champ.py
│   ├── pv_modele_subfield.py
│   ├── pv_pv.py
│   ├── pv_pv_champ.py
│   ├── pv_pv_champ_row.py
│   └── pv_pv_champ_row_value.py
└── security/
    └── ir.model.access.csv
```

## 2️⃣ File-by-File Explanation

### Root Files
| File | Purpose | Future Content |
| :--- | :--- | :--- |
| `__init__.py` | Python package initialization. | Imports the `models` directory. |
| `__manifest__.py` | Odoo module metadata. | Module description, dependencies, and data file declarations. |

### Models Directory (`models/`)
| File | Purpose | Future Content |
| :--- | :--- | :--- |
| `__init__.py` | Models package initialization. | Imports all model files. |
| `pv_modele.py` | Defininition of PV Templates (Structures). | Fields to define name, sequence, and relation to fields. |
| `pv_modele_champ.py` | Definition of fields within a Template. | Configuration of field type, label, and required constraints. |
| `pv_modele_subfield.py` | Definition of sub-structure for complex fields. | Structure for multi-column rows in complex list fields. |
| `pv_pv.py` | The actual PV instance (Data). | Reference to the template and immutable structural copy. |
| `pv_pv_champ.py` | Instance of a field within a PV. | Value storage or link to rows for complex fields. |
| `pv_pv_champ_row.py` | Storage for a row in a complex field. | Links to individual value records for each subfield. |
| `pv_pv_champ_row_value.py` | Atomic value storage for complex subfields. | The actual data value for a subfield cell. |

### Security Directory (`security/`)
| File | Purpose | Future Content |
| :--- | :--- | :--- |
| `ir.model.access.csv` | ACL definition. | Permission grants for the defined models. |

## 3️⃣ Architectural Interpretation

The system is designed as a **Template-to-Instance Relational Model**. 

*   **Structure vs. Data**: `pv.modele` and related sub-models define the "Blueprints". These are purely structural. `pv.pv` and its sub-models are the "Actual Houses" built from those blueprints.
*   **Immutability**: Once a `pv.pv` is created, it is a structural snapshot. Even if the `pv.modele` changes later, the existing `pv.pv` remains tied to the structure it was born with.
*   **Destructive Sync**: The system favors structural integrity over history. If a blueprint (Template) is altered or destroyed, all houses (PVs) built from it are invalidated and removed. There is no "grandfathering" of old structures into new logic.
*   **Relational Persistence**: Data is not stored in JSON blobs; it is fully decomposed into rows and values (`pv.pv.champ.row.value`), ensuring Odoo ORM compatibility, standard search/filtering capabilities (within Odoo limits), and robust validation.

## 4️⃣ Risk Points Identified

*   **Performance on Deletion**: Since deleting a template triggers a cascade deletion of all related PVs, and each PV might have dozens of fields and hundreds of row values, a single template deletion could trigger a massive DB operation.
*   **Data Loss Impact**: The rule "Modify template structure -> Delete related PVs" is extremely high-risk for production data. One accidental field change in a template could wipe out years of PV data.
*   **Validation Complexity**: Ensuring "Hidden required fields must not block validation" while "Complex fields require at least one row" requires careful override of Odoo's standard `_constraints` or `_validate` methods to respect visibility logic over schema requirements.
*   **Structure Mimicry**: The "clone structure at creation" logic must be perfect. Any failure to deeply copy the field definitions (options, subfields, constraints) into the PV instance models will lead to inconsistent behavior between the template preview and the actual PV.
*   **Storage Overhead**: Storing every single cell value of a complex field as a separate record (`pv.pv.champ.row.value`) is clean for the ORM but can lead to very large table sizes quickly compared to JSONB storage.
