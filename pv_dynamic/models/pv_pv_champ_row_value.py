from odoo import models, fields, api
from odoo.exceptions import ValidationError

TYPE_CHAMP_SUB_SELECTION = [
    ('char', 'Char'),
    ('date', 'Date'),
    ('integer', 'Integer'),
    ('float', 'Float'),
    ('percentage', 'Percentage'),
    ('boolean', 'Boolean'),
]

class PvPvChampRowValue(models.Model):
    _name = 'pv.pv.champ.row.value'
    _description = 'Specific value for a subfield within a row'

    row_id = fields.Many2one('pv.pv.champ.row', string='Parent Row', required=True, ondelete='cascade')
    subfield_id = fields.Many2one('pv.modele.subfield', string='Template Subfield', required=True)
    type_champ = fields.Selection(TYPE_CHAMP_SUB_SELECTION, string='Subfield Type', required=True)

    def name_get(self):
        result = []
        for rec in self:
            label = rec.subfield_id.name if rec.subfield_id else 'Value'
            val = ''
            if rec.type_champ == 'char' and rec.valeur_char:
                val = rec.valeur_char
            elif rec.type_champ == 'integer' and rec.valeur_integer:
                val = str(rec.valeur_integer)
            elif rec.type_champ == 'float' and rec.valeur_float:
                val = str(rec.valeur_float)
            elif rec.type_champ == 'percentage' and rec.valeur_percentage:
                val = str(rec.valeur_percentage) + '%'
            elif rec.type_champ == 'boolean':
                val = 'Yes' if rec.valeur_boolean else 'No'
            elif rec.type_champ == 'date' and rec.valeur_date:
                val = str(rec.valeur_date)
            if val:
                name = '%s: %s' % (label, val)
            else:
                name = label
            result.append((rec.id, name))
        return result

    # Value fields
    valeur_char = fields.Char(string='Char Value')
    valeur_date = fields.Date(string='Date Value')
    valeur_integer = fields.Integer(string='Integer Value')
    valeur_float = fields.Float(string='Float Value')
    valeur_percentage = fields.Float(string='Percentage Value')
    valeur_boolean = fields.Boolean(string='Boolean Value')

    value_input = fields.Char(string='Value', compute='_compute_value_input', inverse='_inverse_value_input', store=False)

    @api.depends('valeur_char', 'valeur_date', 'valeur_integer', 'valeur_float', 'valeur_percentage', 'valeur_boolean', 'type_champ')
    def _compute_value_input(self):
        for rec in self:
            if rec.type_champ == 'char': rec.value_input = rec.valeur_char
            elif rec.type_champ == 'integer': 
                rec.value_input = str(rec.valeur_integer) if rec.valeur_integer or rec.valeur_integer == 0 else ''
            elif rec.type_champ == 'float': 
                rec.value_input = str(rec.valeur_float) if rec.valeur_float or rec.valeur_float == 0.0 else ''
            elif rec.type_champ == 'percentage': 
                rec.value_input = str(rec.valeur_percentage) if rec.valeur_percentage or rec.valeur_percentage == 0.0 else ''
            elif rec.type_champ == 'boolean': 
                rec.value_input = 'True' if rec.valeur_boolean else 'False'
            elif rec.type_champ == 'date': 
                rec.value_input = str(rec.valeur_date) if rec.valeur_date else ''
            else:
                rec.value_input = ''

    def _inverse_value_input(self):
        for rec in self:
            val = (rec.value_input or '').strip()
            if not val:
                rec.valeur_char = False
                rec.valeur_integer = 0
                rec.valeur_float = 0.0
                rec.valeur_percentage = 0.0
                rec.valeur_boolean = False
                rec.valeur_date = False
                continue

            try:
                if rec.type_champ == 'char':
                    rec.valeur_char = val
                elif rec.type_champ == 'integer':
                    rec.valeur_integer = int(val)
                elif rec.type_champ == 'float':
                    rec.valeur_float = float(val)
                elif rec.type_champ == 'percentage':
                    rec.valeur_percentage = float(val)
                elif rec.type_champ == 'boolean':
                    if val.lower() not in ['true', 'false', '0', '1', 'yes', 'no', 'vrai', 'faux', 'y', 'n', 't', 'f']:
                        raise ValueError()
                    rec.valeur_boolean = val.lower() in ['true', '1', 'yes', 'vrai', 'y', 't']
                elif rec.type_champ == 'date':
                    rec.valeur_date = fields.Date.to_date(val)
            except Exception:
                raise ValidationError(f"Data Entry Error: The value '{val}' is not a valid {rec.type_champ.capitalize()}.")
