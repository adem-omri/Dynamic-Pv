from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PvPv(models.Model):
    _name = 'pv.pv'
    _description = 'Instances of PV'

    name = fields.Char(string='Name')
    modele_id = fields.Many2one('pv.modele', string='Template', required=True, ondelete='cascade')
    champ_ids = fields.One2many('pv.pv.champ', 'pv_id', string='Fields', copy=True, prefetch=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)

    @api.onchange('modele_id')
    def _onchange_modele_id(self):
        if self.modele_id:
            # Clear existing and preview new fields
            champ_commands = [(5, 0, 0)]
            for template_champ in self.modele_id.champ_ids:
                champ_commands.append((0, 0, {
                    'modele_champ_id': template_champ.id,
                    'name': template_champ.name,
                    'type_champ': template_champ.type_champ,
                    'required': template_champ.required,
                    'sequence': template_champ.sequence,
                    'condition_operator': template_champ.condition_operator,
                    'condition_value': template_champ.condition_value,
                }))
            self.champ_ids = champ_commands

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') and vals.get('modele_id'):
                template = self.env['pv.modele'].browse(vals['modele_id'])
                date_str = fields.Date.today().strftime('%Y-%m-%d')
                vals['name'] = f"PV - {template.name} - {date_str}"
        
        pvs = super().create(vals_list)
        
        for pv in pvs:
            # Check if fields were provided by the UI (onchange) or programmatic creation
            if not pv.champ_ids and pv.modele_id:
                # Programmatic creation without onchange data: Fallback to manual pass 1 clone
                for template_champ in pv.modele_id.champ_ids:
                    self.env['pv.pv.champ'].create({
                        'pv_id': pv.id,
                        'modele_champ_id': template_champ.id,
                        'name': template_champ.name,
                        'type_champ': template_champ.type_champ,
                        'required': template_champ.required,
                        'sequence': template_champ.sequence,
                        'condition_operator': template_champ.condition_operator,
                        'condition_value': template_champ.condition_value,
                    })

            # Pass 2: Link condition_field_id cleanly mapping instances together
            template_to_pv_map = {champ.modele_champ_id.id: champ.id for champ in pv.champ_ids}
            for champ in pv.champ_ids:
                if champ.modele_champ_id.condition_field_id:
                    target_id = template_to_pv_map.get(champ.modele_champ_id.condition_field_id.id)
                    if target_id and not champ.condition_field_id:
                        champ.condition_field_id = target_id
                        
        return pvs

    @api.constrains('champ_ids')
    def _validate_required_fields(self):
        for pv in self:
            for champ in pv.champ_ids:
                # Validation only applies if the field is visible and marked as required
                if champ.is_visible and champ.required:
                    if champ.type_champ == 'complex':
                        # Complex fields: rows are optional, no validation needed
                        continue
                    else:
                        # Atomic fields require a value
                        val = None
                        if champ.type_champ == 'char': val = champ.valeur_char
                        elif champ.type_champ == 'integer': val = champ.valeur_integer
                        elif champ.type_champ == 'float': val = champ.valeur_float
                        elif champ.type_champ == 'percentage': val = champ.valeur_percentage
                        elif champ.type_champ == 'boolean': val = champ.valeur_boolean  # Boolean False is a value, but UI might treat empty differently. Assuming False is valid if just checking empty.
                        elif champ.type_champ == 'date': val = champ.valeur_date

                        # For boolean, we might want to ensure it's not literally None if required, but in Odoo Boolean is usually False.
                        # For other types, check if it evaluates to False (0, '', None)
                        # Specific check for 0 since 0 might be a valid entry for Integer/Float.
                        if val is False and champ.type_champ == 'boolean':
                            continue # Boolean False is normally considered a valid "value" unless explicitly meant to be unanswered.
                        
                        if val is None or val == '':
                            raise ValidationError(f"The field '{champ.name}' is required and cannot be empty.")



