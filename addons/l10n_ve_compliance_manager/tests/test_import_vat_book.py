from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestImportVatBook(TransactionCase):
    """Tests para importación de Libro de Compras/Ventas (Fase G)."""

    def setUp(self):
        super().setUp()
        self.Wizard = self.env['l10n.ve.import.wizard']

    def test_import_types_exist(self):
        """Verifica que los nuevos import_type están en la selección."""
        wizard = self.env['l10n.ve.import.wizard']
        types = dict(wizard._fields['import_type'].selection)
        self.assertIn('vat_book_purchase', types)
        self.assertIn('vat_book_sale', types)
        self.assertEqual(types['vat_book_purchase'], 'Libro de Compras (IVA)')
        self.assertEqual(types['vat_book_sale'], 'Libro de Ventas (IVA)')

    def test_wizard_has_vat_book_fields(self):
        """Verifica que el wizard tiene los campos period_month y sheet_name."""
        wizard = self.Wizard.create({
            'import_type': 'vat_book_purchase',
        })
        # Los campos deben existir en el modelo
        self.assertTrue('period_month' in wizard._fields)
        self.assertTrue('sheet_name' in wizard._fields)
        # period_month es Char
        self.assertEqual(wizard._fields['period_month'].type, 'char')
        # sheet_name es Char readonly
        self.assertEqual(wizard._fields['sheet_name'].type, 'char')
        self.assertTrue(wizard._fields['sheet_name'].readonly)
