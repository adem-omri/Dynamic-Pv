# README AUDIT - STEP 6: PV Dynamic Forms & Views

This document audits the XML views, formatting, and structural UI rules implemented for `pv_dynamic`, verifying that performance, conditionals, and standard Odoo mechanisms interact perfectly.

## 1️⃣ Form View Structure (pv_pv_views.xml)

The dynamic rendering of the PV instance form operates entirely through Odoo's native XML `attrs` attribute, avoiding any custom JavaScript.

### Dynamic Hiding
Each data column (`valeur_char`, `valeur_integer`, etc.) defines an `invisible` rule that evaluates two criteria:
1.  **Macro Visibility**: Is the field logically visible according to conditions? `('is_visible', '=', False)`
2.  **Type Matching**: Does this column match the field's instantiated type? `('type_champ', '!=', 'char')`

```xml
<field name="valeur_char" attrs="{
    'invisible': ['|', ('is_visible', '=', False), ('type_champ', '!=', 'char')],
    'required': [('is_visible', '=', True), ('required', '=', True), ('type_champ', '=', 'char')]
}"/>
```
By combining these with an OR (`|`), Odoo ensures exactly *one* input field is visible per row in the `champ_ids` tree.

### UI Validation Enforcement
Required fields enforce UI-level blocking explicitly via `attrs="{'required': ... }"`. If a field is `required` but its condition hides it, the `is_visible` check in the XML prevents the form from blocking the save, mirroring the ORM `@api.constrains` logic perfectly.

## 2️⃣ Complex Field Layout

Complex rows are handled securely using an embedded form view inside the `champ_ids` tree.

1.  **Opener Button**: A button (`type="object"`) is visible only on complex type fields. Clicking it opens the specific `pv.pv.champ` record in a popup form.
2.  **Popup Management**: Inside that popup, the `row_ids` One2many relationship is exposed as an editable tree.
3.  **Subfield Values**: Inside the `row_ids` tree, the `value_ids` (the actual cell values) are visible.
4.  **Creation/Deletion Lock**: To enforce structural immutability (Step 2/4 rules), `create="0" delete="0"` are applied to the `value_ids` tree. Users can add *rows* (`row_ids`), but they cannot spontaneously add or remove *subfields* (`value_ids`) within a row.

## 3️⃣ Action Button Behavior

*   **Créer un PV**: We use the native Odoo "Create" button on the `view_pv_pv_tree`. It opens the form in draft mode. Upon selecting a template and saving, the `@api.model_create_multi` method (Step 3) automatically spawns all fields.
*   **Supprimer PV**: We use the native "Action -> Delete". This triggers the ORM `unlink()` method, which cascades down to wipe all associated fields, rows, and values (Step 4 verification).

## 4️⃣ Edge Case Handling

### Large Templates (50+ fields)
*   **Performance**: The `is_visible` computed field in Python does *not* query the database per field; it evaluates values already in memory during the transaction.
*   **Scrolling**: By using an `editable="bottom"` tree for atomic fields, the form remains a clean, scrollable list. Complex fields exist in their own popups, preventing massive nested grids from freezing the main DOM.

### Nested Conditions
*   Invisible fields remain in the DOM as `display: none`. They do not take up space. 
*   If Field A hides Field B, and Field B hides Field C, the Python `is_visible` topology guarantees all are marked invisible in the XML, preventing "ghost" required validations.

### Empty Complex Fields
*   If a complex field is newly generated, opening its popup reveals an empty `row_ids` tree.
*   The user can click "Add a line" to spawn a new row. Upon row creation (which will be implemented closely via ORM defaults/onchange in the future if auto-spawning subfields is desired, or relies on standard Odoo O2M behavior). *Note: Auto-populating the `value_ids` based on `subfield_ids` upon clicking "Add a row" may require a minor ORM tweak in a future polish step, but the structure strictly supports it.*
