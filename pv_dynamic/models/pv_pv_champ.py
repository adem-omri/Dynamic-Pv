from odoo import models, fields, api
from odoo.exceptions import ValidationError

TYPE_CHAMP_SELECTION = [
    ('char', 'Char'),
    ('date', 'Date'),
    ('integer', 'Integer'),
    ('float', 'Float'),
    ('percentage', 'Percentage'),
    ('boolean', 'Boolean'),
    ('complex', 'Complex'),
]

COND_OPERATOR_SELECTION = [
    ('=', 'Equals'),
    ('!=', 'Not Equals'),
    ('>', 'Greater Than'),
    ('<', 'Less Than'),
]

class PvPvChamp(models.Model):
    _name = 'pv.pv.champ'
    _description = 'Champ within a PV Instance'
    _order = 'sequence'

    pv_id = fields.Many2one('pv.pv', string='PV Instance', required=True, ondelete='cascade')
    modele_champ_id = fields.Many2one('pv.modele.champ', string='Template Field')
    name = fields.Char(string='Field Label')
    type_champ = fields.Selection(TYPE_CHAMP_SELECTION, string='Field Type')
    required = fields.Boolean(string='Required', default=False)
    sequence = fields.Integer(string='Sequence', default=10)

    # Conditional Visibility Logic (Snapshots via create)
    condition_field_id = fields.Many2one('pv.pv.champ', string='Depends On')
    condition_operator = fields.Selection(COND_OPERATOR_SELECTION, string='Operator')
    condition_value = fields.Char(string='Condition Value')
    
    is_visible = fields.Boolean(
        string='Is Visible', 
        compute='_compute_is_visible', 
        store=False, # Evaluated at runtime
        help="Evaluates conditional logic to determine if this field should be shown/validated."
    )

    # Value fields for non-complex types
    valeur_char = fields.Char(string='Char Value')
    valeur_date = fields.Date(string='Date Value')
    valeur_integer = fields.Integer(string='Integer Value')
    valeur_float = fields.Float(string='Float Value')
    valeur_percentage = fields.Float(string='Percentage Value')
    valeur_boolean = fields.Boolean(string='Boolean Value')

    value_input = fields.Char(string='Value', compute='_compute_value_input', inverse='_inverse_value_input', store=False)

    # For complex type
    row_ids = fields.One2many('pv.pv.champ.row', 'champ_id', string='Rows', copy=True, prefetch=True)

    @api.depends('valeur_char', 'valeur_date', 'valeur_integer', 'valeur_float', 'valeur_percentage', 'valeur_boolean', 'type_champ')
    def _compute_value_input(self):
        for rec in self:
            if rec.type_champ == 'char':
                rec.value_input = rec.valeur_char
            elif rec.type_champ == 'integer':
                rec.value_input = str(rec.valeur_integer) if rec.valeur_integer is not None else ''
            elif rec.type_champ == 'float':
                rec.value_input = str(rec.valeur_float) if rec.valeur_float is not None else ''
            elif rec.type_champ == 'percentage':
                rec.value_input = str(rec.valeur_percentage) if rec.valeur_percentage is not None else ''
            elif rec.type_champ == 'boolean':
                rec.value_input = rec.valeur_boolean
            elif rec.type_champ == 'date':
                rec.value_input = rec.valeur_date
            else:
                rec.value_input = ''

    def _inverse_value_input(self):
        for rec in self:
            if rec.type_champ == 'char':
                rec.valeur_char = rec.value_input
            elif rec.type_champ == 'integer':
                rec.valeur_integer = int(rec.value_input) if rec.value_input else None
            elif rec.type_champ == 'float':
                rec.valeur_float = float(rec.value_input) if rec.value_input else None
            elif rec.type_champ == 'percentage':
                rec.valeur_percentage = float(rec.value_input) if rec.value_input else None
            elif rec.type_champ == 'boolean':
                rec.valeur_boolean = bool(rec.value_input)
            elif rec.type_champ == 'date':
                rec.valeur_date = rec.value_input
    @api.depends('condition_field_id.valeur_char', 'condition_field_id.valeur_integer', 
                 'condition_field_id.valeur_float', 'condition_field_id.valeur_percentage', 
                 'condition_field_id.valeur_boolean', 'condition_field_id.is_visible')
    def _compute_is_visible(self):
        for rec in self:
            # Base case: no condition means visible
            if not rec.condition_field_id or not rec.condition_operator or rec.condition_value is None:
                rec.is_visible = True
                continue
            
            # If the field it depends on is itself hidden, this field hides.
            # This handles nested dependencies topologically.
            if not rec.condition_field_id.is_visible:
                rec.is_visible = False
                continue

            # Fetch the actual value based on the type of the target condition field
            target_field = rec.condition_field_id
            t_type = target_field.type_champ
            
            actual_val = None
            if t_type == 'char': actual_val = target_field.valeur_char
            elif t_type == 'integer': actual_val = target_field.valeur_integer
            elif t_type == 'float': actual_val = target_field.valeur_float
            elif t_type == 'percentage': actual_val = target_field.valeur_percentage
            elif t_type == 'boolean': actual_val = str(target_field.valeur_boolean)
            elif t_type == 'date': actual_val = target_field.valeur_date and str(target_field.valeur_date) or ''
            
            
            # Normalize for comparison
            actual_val_str = str(actual_val) if actual_val is not None and str(actual_val) != 'False' else ''
            cond_val_str = str(rec.condition_value)

            # Evaluate
            is_vis = False
            try:
                if rec.condition_operator == '=':
                    is_vis = (actual_val_str == cond_val_str)
                elif rec.condition_operator == '!=':
                    is_vis = (actual_val_str != cond_val_str)
                elif rec.condition_operator == '>':
                    is_vis = (float(actual_val_str) > float(cond_val_str))
                elif rec.condition_operator == '<':
                    is_vis = (float(actual_val_str) < float(cond_val_str))
            except ValueError:
                # Type mismatch during float casting mostly. Safe fallback is False.
                is_vis = False
                
            rec.is_visible = is_vis

    def action_open_complex(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Manage Rows: %s' % self.name,
            'view_mode': 'form',
            'res_model': 'pv.pv.champ',
            'res_id': self.id,
            'views': [(self.env.ref('pv_dynamic.view_pv_champ_complex_form').id, 'form')],
            'target': 'new',
        }
