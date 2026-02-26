from odoo import models, fields, api

TYPE_CHAMP_SUB_SELECTION = [
    ('char', 'Char'),
    ('date', 'Date'),
    ('integer', 'Integer'),
    ('float', 'Float'),
    ('percentage', 'Percentage'),
    ('boolean', 'Boolean'),
]

class PvModeleSubfield(models.Model):
    _name = 'pv.modele.subfield'
    _description = 'Subfield structure for complex types'
    _order = 'sequence'

    champ_id = fields.Many2one('pv.modele.champ', string='Parent Complex Field', required=True, ondelete='cascade')
    name = fields.Char(string='Subfield Label', required=True)
    type_champ = fields.Selection(TYPE_CHAMP_SUB_SELECTION, string='Subfield Type', required=True)
    required = fields.Boolean(string='Required', default=False)
    sequence = fields.Integer(string='Sequence', default=10)

    def _invalidate_pvs(self):
        for rec in self:
            if rec.champ_id and rec.champ_id.modele_id:
                pvs = self.env['pv.pv'].search([('modele_id', '=', rec.champ_id.modele_id.id)])
                pvs.unlink()

    @api.model_create_multi
    def create(self, vals_list):
        res = super(PvModeleSubfield, self).create(vals_list)
        res._invalidate_pvs()
        return res

    def write(self, vals):
        res = super(PvModeleSubfield, self).write(vals)
        self._invalidate_pvs()
        return res

    def unlink(self):
        self._invalidate_pvs()
        return super(PvModeleSubfield, self).unlink()


