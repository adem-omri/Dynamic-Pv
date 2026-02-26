from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestPvDynamic(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestPvDynamic, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Setup basic template
        cls.template = cls.env['pv.modele'].create({
            'name': 'Test Template',
            'champ_ids': [
                (0, 0, {'name': 'Field 1 (Char)', 'type_champ': 'char', 'required': True, 'sequence': 10}),
                (0, 0, {'name': 'Field 2 (Int)', 'type_champ': 'integer', 'required': False, 'sequence': 20}),
                (0, 0, {'name': 'Field 3 (Complex)', 'type_champ': 'complex', 'required': True, 'sequence': 30,
                        'subfield_ids': [
                            (0, 0, {'name': 'Sub 1', 'type_champ': 'char'}),
                            (0, 0, {'name': 'Sub 2', 'type_champ': 'integer'}),
                        ]}),
            ]
        })
        cls.field_char = cls.template.champ_ids.filtered(lambda c: c.type_champ == 'char')
        cls.field_int = cls.template.champ_ids.filtered(lambda c: c.type_champ == 'integer')
        cls.field_complex = cls.template.champ_ids.filtered(lambda c: c.type_champ == 'complex')

        # Conditional Template
        cls.cond_template = cls.env['pv.modele'].create({
            'name': 'Cond Template',
        })
        cls.f_bool = cls.env['pv.modele.champ'].create({
            'modele_id': cls.cond_template.id, 'name': 'Toggle', 'type_champ': 'boolean', 'sequence': 1
        })
        cls.f_dep1 = cls.env['pv.modele.champ'].create({
            'modele_id': cls.cond_template.id, 'name': 'Dep 1', 'type_champ': 'char', 'required': True, 'sequence': 2,
            'condition_field_id': cls.f_bool.id, 'condition_operator': '=', 'condition_value': 'True'
        })
        cls.f_dep2 = cls.env['pv.modele.champ'].create({
            'modele_id': cls.cond_template.id, 'name': 'Dep 2', 'type_champ': 'char', 'required': True, 'sequence': 3,
            'condition_field_id': cls.f_dep1.id, 'condition_operator': '=', 'condition_value': 'Show'
        })

    def test_01_unit_pv_creation(self):
        """Test PV creation, field cloning accuracy, and zero initial rows for complex fields."""
        pv = self.env['pv.pv'].create({'modele_id': self.template.id})
        
        # Check auto-naming
        self.assertTrue(pv.name.startswith("PV - Test Template -"))
        
        # Check cloned fields count matches template
        self.assertEqual(len(pv.champ_ids), 3)
        
        # Check cloned field properties
        for t_champ in self.template.champ_ids:
            pv_champ = pv.champ_ids.filtered(lambda c: c.name == t_champ.name)
            self.assertTrue(pv_champ)
            self.assertEqual(pv_champ.type_champ, t_champ.type_champ)
            self.assertEqual(pv_champ.required, t_champ.required)
            self.assertEqual(pv_champ.sequence, t_champ.sequence)
            
            if pv_champ.type_champ == 'complex':
                # Assert zero rows initially
                self.assertEqual(len(pv_champ.row_ids), 0)

    def test_02_unit_conditional_visibility(self):
        """Test conditional visibility logic and topological resolution."""
        pv = self.env['pv.pv'].create({'modele_id': self.cond_template.id})
        
        pv_f_bool = pv.champ_ids.filtered(lambda c: c.name == 'Toggle')
        pv_f_dep1 = pv.champ_ids.filtered(lambda c: c.name == 'Dep 1')
        pv_f_dep2 = pv.champ_ids.filtered(lambda c: c.name == 'Dep 2')
        
        # Initial state: Toggle is False -> Dep1 invisible -> Dep2 invisible
        self.assertTrue(pv_f_bool.is_visible)
        self.assertFalse(pv_f_dep1.is_visible)
        self.assertFalse(pv_f_dep2.is_visible)
        
        # Toggle True -> Dep 1 visible, Dep 1 value is empty (!= Show) -> Dep 2 invisible
        pv_f_bool.write({'valeur_boolean': True})
        self.env.flush_all()
        pv_f_dep1.invalidate_recordset()
        
        self.assertTrue(pv_f_dep1.is_visible)
        self.assertFalse(pv_f_dep2.is_visible)
        
        # Dep 1 = Show -> Dep 2 visible
        pv_f_dep1.write({'valeur_char': 'Show'})
        self.env.flush_all()
        pv_f_dep2.invalidate_recordset()
        
        self.assertTrue(pv_f_dep2.is_visible)

    def test_03_unit_validation_enforcement(self):
        """Test validation enforcement (atomic required, complex required, hidden bypass)."""
        pv = self.env['pv.pv'].create({'modele_id': self.template.id})
        pv_char = pv.champ_ids.filtered(lambda c: c.type_champ == 'char')
        pv_complex = pv.champ_ids.filtered(lambda c: c.type_champ == 'complex')

        # Both are required and empty, save should fail validation
        with self.assertRaises(ValidationError):
            pv._validate_required_fields()
            
        # Fill atomic, leave complex empty -> fail
        pv_char.valeur_char = 'Test'
        with self.assertRaises(ValidationError):
            pv._validate_required_fields()
            
        # Add a row to complex
        self.env['pv.pv.champ.row'].create({'champ_id': pv_complex.id})
        
        # Now it should pass
        pv._validate_required_fields()
        self.assertTrue(True) # Reached here means no exception

        # Test hidden bypass
        pv_cond = self.env['pv.pv'].create({'modele_id': self.cond_template.id})
        # Fills nothing. Both Dep1 and Dep2 are required but hidden initially.
        pv_cond._validate_required_fields() # Should pass because they are hidden
        self.assertTrue(True)

    def test_04_integration_template_deletion_cascade(self):
        """Test template deletion cascades (no orphans)."""
        t = self.env['pv.modele'].create({'name': 'To Delete'})
        c = self.env['pv.modele.champ'].create({'modele_id': t.id, 'name': 'C1', 'type_champ': 'char'})
        pv1 = self.env['pv.pv'].create({'modele_id': t.id})
        pv2 = self.env['pv.pv'].create({'modele_id': t.id})
        
        self.assertEqual(self.env['pv.pv'].search_count([('modele_id', '=', t.id)]), 2)
        
        t.unlink()
        
        # Assert PVs are gone
        self.assertEqual(self.env['pv.pv'].search_count([('name', 'ilike', 'To Delete')]), 0)

    def test_05_integration_structural_modification_invalidation(self):
        """Test structural modification invalidation."""
        t = self.env['pv.modele'].create({'name': 'To Modify'})
        c = self.env['pv.modele.champ'].create({'modele_id': t.id, 'name': 'C1', 'type_champ': 'char'})
        pv1 = self.env['pv.pv'].create({'modele_id': t.id})
        
        self.assertEqual(len(self.env['pv.pv'].search([('modele_id', '=', t.id)])), 1)
        
        # Modify field required status
        c.write({'required': True})
        
        # PV should be deleted
        self.assertEqual(len(self.env['pv.pv'].search([('modele_id', '=', t.id)])), 0)

    def test_06_stress_large_template(self):
        """Test large template generation."""
        # Create massive template
        champ_vals = []
        for i in range(50):
            champ_vals.append((0, 0, {'name': f'F {i}', 'type_champ': 'char'}))
        for i in range(10):
            champ_vals.append((0, 0, {'name': f'C {i}', 'type_champ': 'complex', 
                                      'subfield_ids': [(0,0,{'name': f'S {j}', 'type_champ': 'char'}) for j in range(5)]}))
                                      
        t = self.env['pv.modele'].create({
            'name': 'Massive',
            'champ_ids': champ_vals
        })
        
        # Generate PVs
        pvs = self.env['pv.pv'].create([{'modele_id': t.id} for _ in range(5)])
        
        self.assertEqual(len(pvs), 5)
        self.assertEqual(len(pvs[0].champ_ids), 60)
        
        # Mass deletion verify
        t.unlink()
        self.assertEqual(self.env['pv.pv'].search_count([('modele_id', '=', t.id)]), 0)
