# PV Dynamic Forms - Odoo Module

**PV Dynamic** is a robust, template-driven dynamic form engine built natively on the Odoo ORM. It allows administrators to define complex form structures (Templates) that end-users can instantiate, fill, and validate safely (PV Instances).

## 🏛️ Architectural Principles

This module was built with strict adherence to the following rules:
1. **Relational Data Integrity**: No JSON blobs. Every template, field, complex row, and user-entered value maps strictly to an Odoo database row.
2. **Immutability vs Syncing**: PV Instances are snapshots of the Template. If a Template's structure is modified, all existing PVs generated from that template are safely cascaded-deleted to prevent schema desynchronization.
3. **No Native "Versioning"**: We avoid complex lifecycle approvals or version numbers. It's either active or deleted.

## ✨ Key Features

### 1. Dynamic Data Types
Supports core Odoo data types dynamically rendered in views:
*   Char (Text)
*   Integer & Float
*   Date
*   Percentage
*   Boolean
*   **Complex Fields** (One2many lists with defined subfield columns)

### 2. Conditional Visibility Topology
Fields can depend on the values of other fields.
*   **Operators**: `=`, `!=`, `>`, `<`. 
*   **Nested Hiding**: If Field A hides Field B, and Field C depends on Field B, Field C safely inherits the hidden state.
*   **Optimization**: Conditions are evaluated aggressively in memory (`store=False` compute) to ensure fast rendering on 50+ field forms.

### 3. Transactional Validation
*   Validates dynamically. If a field is `required` but functionally hidden by conditional logic, validation safely ignores it.
*   Complex fields evaluate requirement based on the existence of at least 1 populated row.

### 4. Zero-JavaScript UI
*   The entire module functions using native Odoo XML dynamic views (`attrs="{'invisible': ...}"`). 
*   **Performance**: Complex fields render as dedicated popups, keeping the main form simple, fast, and scrollable.
*   **UX**: Clicking "Add Row" inside a complex popup automatically generates all necessary subfield input boxes instantly.

## 🛠️ Testing & QA

Run the automated test suite locally to verify schema integrity and conditional logic topologies:
```bash
python odoo-bin -i pv_dynamic --test-enable -d <database_name>
```
The test suite validates:
- Template generation & mass creation.
- Topological logic validation.
- Cascade structural deletion safety (`ondelete='cascade'`).

---
*Developed by Adem Omri.*
