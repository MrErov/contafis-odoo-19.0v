from odoo import fields
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError
from odoo.tools import mute_logger
import psycopg2


@tagged('post_install', '-at_install')
class TestVatBookLine(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Proveedor Test'})
        self.company = self.env.company

    def test_vat_book_line_create_purchase(self):
        """Crear línea de libro para compra."""
        line = self.env['l10n.ve.vat.book.line'].create({
            'book_type': 'purchase',
            'period_month': '2026-08',
            'partner_id': self.partner.id,
            'invoice_number': 'FAC-001',
            'control_number': 'CTRL-001',
            'operation_code': '33',
            'base_general': 1000.0,
            'vat_general': 160.0,
            'company_id': self.company.id,
        })
        self.assertEqual(line.book_type, 'purchase')
        self.assertEqual(line.base_general, 1000.0)
        self.assertEqual(line.vat_general, 160.0)

    def test_vat_book_line_create_sale(self):
        """Crear línea de libro para venta."""
        line = self.env['l10n.ve.vat.book.line'].create({
            'book_type': 'sale',
            'period_month': '2026-08',
            'partner_id': self.partner.id,
            'invoice_number': 'FAC-002',
            'control_number': 'CTRL-002',
            'operation_code': '42',
            'base_general': 2000.0,
            'vat_general': 320.0,
            'company_id': self.company.id,
        })
        self.assertEqual(line.book_type, 'sale')
        self.assertEqual(line.operation_code, '42')

    def test_vat_book_line_unique_constraint(self):
        """Constraint único evita duplicados - verifica que el constraint SQL existe en el modelo."""
        # Verificar que el constraint SQL está definido en el modelo
        model = self.env['l10n.ve.vat.book.line']
        constraints = model._sql_constraints
        constraint_names = [c[0] for c in constraints]
        self.assertIn('unique_line', constraint_names)
        
        # Verificar la definición del constraint
        unique_constraint = next(c for c in constraints if c[0] == 'unique_line')
        self.assertIn('partner_id', unique_constraint[1])
        self.assertIn('invoice_number', unique_constraint[1])
        self.assertIn('control_number', unique_constraint[1])
        self.assertIn('period_month', unique_constraint[1])
        self.assertIn('company_id', unique_constraint[1])

    def test_get_operation_code_for_rate(self):
        """Verifica mapeo de tasas a códigos SENIAT."""
        # Ventas
        self.assertEqual(
            self.env['l10n.ve.vat.book.line']._get_operation_code_for_rate(16, 'sale'),
            '42'
        )
        self.assertEqual(
            self.env['l10n.ve.vat.book.line']._get_operation_code_for_rate(8, 'sale'),
            '443'
        )
        self.assertEqual(
            self.env['l10n.ve.vat.book.line']._get_operation_code_for_rate(18, 'sale'),
            '442'
        )
        self.assertEqual(
            self.env['l10n.ve.vat.book.line']._get_operation_code_for_rate(0, 'sale'),
            '40'
        )
        # Compras
        self.assertEqual(
            self.env['l10n.ve.vat.book.line']._get_operation_code_for_rate(16, 'purchase'),
            '33'
        )
        self.assertEqual(
            self.env['l10n.ve.vat.book.line']._get_operation_code_for_rate(8, 'purchase'),
            '333'  # Base reducida (item_333), no 343 que es el IVA
        )
        self.assertEqual(
            self.env['l10n.ve.vat.book.line']._get_operation_code_for_rate(18, 'purchase'),
            '332'
        )
        self.assertEqual(
            self.env['l10n.ve.vat.book.line']._get_operation_code_for_rate(0, 'purchase'),
            '30'
        )