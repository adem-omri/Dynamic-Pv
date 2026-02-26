from odoo import models, fields, api

class PvModele(models.Model):
    _name = 'pv.modele'
    _description = 'Template for PV'

    name = fields.Char(string='Name', required=True)
    champ_ids = fields.One2many('pv.modele.champ', 'modele_id', string='Fields', copy=True)
    active = fields.Boolean(string='Active', default=True)

    def unlink(self):
        for template in self:
            # Explicitly delete all PVs using this template
            pvs = self.env['pv.pv'].search([('modele_id', '=', template.id)])
            pvs.unlink()
        return super(PvModele, self).unlink()


