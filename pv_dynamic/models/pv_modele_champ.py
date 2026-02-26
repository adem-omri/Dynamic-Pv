from odoo import models, fields, api

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

class PvModeleChamp(models.Model):
    _name = 'pv.modele.champ'
    _description = 'Champ within a PV Template'
    _order = 'sequence'

    modele_id = fields.Many2one('pv.modele', string='PV Template', ondelete='cascade')
    name = fields.Char(string='Field Label', required=True)
    type_champ = fields.Selection(TYPE_CHAMP_SELECTION, string='Field Type', required=True)
    required = fields.Boolean(string='Required', default=False)
    sequence = fields.Integer(string='Sequence', default=10)
    subfield_ids = fields.One2many('pv.modele.subfield', 'champ_id', string='Subfields', copy=True)
    
    # Conditional Visibility Logic
    condition_field_id = fields.Many2one('pv.modele.champ', string='Depends On', domain="[('modele_id', '=', modele_id), ('id', '!=', id)]")
    condition_operator = fields.Selection(COND_OPERATOR_SELECTION, string='Operator')
    condition_value = fields.Char(string='Condition Value')

    def _invalidate_pvs(self):

        for rec in self:
            if rec.modele_id:
                pvs = self.env['pv.pv'].search([('modele_id', '=', rec.modele_id.id)])
                pvs.unlink()

    @api.model_create_multi
    def create(self, vals_list):
        res = super(PvModeleChamp, self).create(vals_list)
        res._invalidate_pvs()
        return res

    def write(self, vals):
        # Any change to a template field is considered structural in this system
        res = super(PvModeleChamp, self).write(vals)
        self._invalidate_pvs()
        return res

    def unlink(self):
        self._invalidate_pvs()
        return super(PvModeleChamp, self).unlink()


