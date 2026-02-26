# README AUDIT - STEP 7: Testing & QA

This document audits the automated testing scenarios executed for the `pv_dynamic` module natively using the Odoo Testing framework. 

All tests run via: `python odoo-bin -i pv_dynamic --test-enable`

## 🧪 1. Unit Tests

### `test_01_unit_pv_creation`
- **Goal**: Verify that instantiating a `pv.pv` clones all fields correctly from the template and applies the correct naming convention.
- **Assertions**:
  - Name is dynamically generated as `PV - [Template Name] - [Date]`.
  - Number of fields matched `pv.modele`.
  - `type_champ`, `required`, and `sequence` properties are exact clones.
  - Complex fields initialized with exactly `0` rows.
- **Result**: **PASS**

### `test_02_unit_conditional_visibility`
- **Goal**: Verify `is_visible` topology logic dynamically hides/shows fields cleanly.
- **Scenario**: 
  - `Toggle (Boolean)` -> `Dep 1 (Char, visible if Toggle='True')` -> `Dep 2 (Char, visible if Dep 1='Show')`.
- **Assertions**:
  - Initial generation: Toggle is True, Dep 1 False, Dep 2 False.
  - Toggling boolean: Dep 1 True, Dep 2 False.
  - Entering 'Show' into Dep 1: Dep 2 becomes True.
- **Result**: **PASS** *(Fix applied to python string coercion for `True`/`False`)*.

### `test_03_unit_validation_enforcement`
- **Goal**: Verify the central `@api.constrains` block strictly enforces validation rules but respects visibility.
- **Assertions**:
  - Empty required atomic field triggers `ValidationError`.
  - Empty required complex field (0 rows) triggers `ValidationError`.
  - Adding 1 row to the complex field allows the save to pass.
  - If a required field is hidden (`is_visible=False`), validation is safely bypassed.
- **Result**: **PASS**

## 🔗 2. Integration Tests

### `test_04_integration_template_deletion_cascade`
- **Goal**: Ensure the destruction of a master template cleanly cascades down and wipes all derived PVs to prevent orphan schema records.
- **Assertions**:
  - Delete `pv.modele`.
  - Query `pv.pv`, `pv.pv.champ` count is exactly 0.
- **Result**: **PASS**

### `test_05_integration_structural_modification_invalidation`
- **Goal**: Verify the "Destructive Sync" rule (Step 3). Changing a template instantly invalidates old PVs.
- **Assertions**:
  - Create Template -> Create PV.
  - Modify `required` attribute on a template field.
  - Query PV instance: The instance is destroyed.
- **Result**: **PASS**

## 🏋️ 3. Stress / Performance Tests

### `test_06_stress_large_template`
- **Goal**: Verify large database transactions during generation and deletion do not exceed limits or cause recursive ORM loop limits.
- **Scenario**:
  - Template with 50 atomic fields and 10 complex fields (each with 5 subfields).
  - Bulk generate 5 PVs simultaneously.
- **Assertions**:
  - 5 PVs generated.
  - Each PV correctly houses 60 fields instantly.
  - Mass deletion of template correctly deletes 1 Template, 5 PVs, 300 Fields, and cleans data layer without deadlock.
- **Result**: **PASS**

## 📌 Conclusion
Module `pv_dynamic` strictly adheres to the requested architecture:
1. **Structural Strictness**: Immutability enforced.
2. **Conditional Flexibility**: Topology correctly triggers visibility.
3. **Data Safety**: Odoo Cascade destroys cleanly without orphans.
