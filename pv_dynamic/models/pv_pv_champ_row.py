from odoo import models, fields, api

class PvPvChampRow(models.Model):
    _name = 'pv.pv.champ.row'
    _description = 'Row in a Complex Field'
    _order = 'sequence'

    champ_id = fields.Many2one('pv.pv.champ', string='Parent Complex Field', required=True, ondelete='cascade')
    value_ids = fields.One2many('pv.pv.champ.row.value', 'row_id', string='Values', copy=True, prefetch=True)
    sequence = fields.Integer(string='Sequence', default=10)

    @api.onchange('champ_id')
    def _onchange_champ_id(self):
        """Auto-populate subfield rows in the UI when a new row is added."""
        if self.champ_id and self.champ_id.modele_champ_id and not self.value_ids:
            vals = []
            for subfield in self.champ_id.modele_champ_id.subfield_ids:
                vals.append((0, 0, {
                    'subfield_id': subfield.id,
                    'type_champ': subfield.type_champ,
                }))
            self.value_ids = vals

    @api.model_create_multi
    def create(self, vals_list):
        rows = super().create(vals_list)
        value_env = self.env['pv.pv.champ.row.value']
        for row in rows:
            # Auto-populate subfield value records if not already populated (fallback)
            if row.champ_id and row.champ_id.modele_champ_id and row.champ_id.modele_champ_id.subfield_ids:
                if not row.value_ids:
                    for subfield in row.champ_id.modele_champ_id.subfield_ids:
                        value_env.create({
                            'row_id': row.id,
                            'subfield_id': subfield.id,
                            'type_champ': subfield.type_champ
                        })
        return rows
