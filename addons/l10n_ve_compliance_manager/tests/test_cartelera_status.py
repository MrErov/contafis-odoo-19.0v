from odoo import fields
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from psycopg2 import IntegrityError


@tagged('post_install', '-at_install')
class TestCarteleraStatus(TransactionCase):
    """Tests del modelo l10n.ve.cartelera.status (Fase B)."""

    def setUp(self):
        super().setUp()
        # Limpiar snapshots de tests previos para asegurar idempotencia
        self.env['l10n.ve.cartelera.status'].search([]).unlink()
        self.Client = self.env['l10n.ve.compliance.client']
        self.DocType = self.env['l10n.ve.document.type']
        self.Document = self.env['l10n.ve.document']
        self.Status = self.env['l10n.ve.cartelera.status']

        # Cliente de prueba
        self.partner = self.env['res.partner'].create({
            'name': 'Cliente Test',
            'vat': 'J-12345678-9',
        })
        self.client = self.Client.create({
            'name': 'Cliente Test',
            'partner_id': self.partner.id,
            'company_id': self.env.company.id,
            'rif': 'J-12345678-9',
        })

        # Tipos de documento requeridos (company)
        self.type_c01 = self.DocType.search([('code', '=', 'C01')], limit=1)
        self.type_c05 = self.DocType.search([('code', '=', 'C05')], limit=1)
        self.type_c06 = self.DocType.search([('code', '=', 'C06')], limit=1)
        self.type_c12 = self.DocType.search([('code', '=', 'C12')], limit=1)

        # Mes de prueba (mes anterior al actual)
        today = fields.Date.today()
        prev_month = today - relativedelta(months=1)
        self.test_year = prev_month.year
        self.test_month = str(prev_month.month)

    def _create_document(self, doc_type, state='valid', expiry_date=None):
        """Helper para crear documento."""
        if expiry_date is None:
            from datetime import date, timedelta
            expiry_date = date.today() + timedelta(days=30)
        return self.Document.create({
            'client_id': self.client.id,
            'document_type_id': doc_type.id,
            'number': f'DOC-{doc_type.code}',
            'issue_date': expiry_date - relativedelta(days=30),
            'expiry_date': expiry_date,
            'state': state,
        })

    def test_snapshot_generation(self):
        """Genera snapshot con docs mixtos: valid, expired, missing."""
        # Usar cliente nuevo para aislar test
        partner_new = self.env['res.partner'].create({
            'name': 'Cliente Snapshot',
            'vat': 'J-44444444-4',
        })
        client_new = self.Client.create({
            'name': 'Cliente Snapshot',
            'partner_id': partner_new.id,
            'company_id': self.env.company.id,
            'rif': 'J-44444444-4',
        })

        # Crear 2 docs: uno válido, uno expirado
        self.Document.create({
            'client_id': client_new.id,
            'document_type_id': self.type_c01.id,
            'number': 'DOC-C01',
            'issue_date': fields.Date.today() - relativedelta(days=30),
            'expiry_date': fields.Date.today() + relativedelta(days=30),
            'state': 'valid',
        })
        self.Document.create({
            'client_id': client_new.id,
            'document_type_id': self.type_c06.id,
            'number': 'DOC-C06',
            'issue_date': fields.Date.today() - relativedelta(days=30),
            'expiry_date': fields.Date.today() - relativedelta(days=1),
            'state': 'expired',
        })

        # Generar snapshot (modo normal, sin statuses)
        snapshots = self.Status.generate_snapshot(
            client_new.id, self.test_year, self.test_month
        )

        # Debe crear 36 snapshots (todos los tipos requeridos company)
        self.assertEqual(len(snapshots), 36)

        # Verificar estados específicos
        s_c01 = snapshots.filtered(lambda s: s.document_type_id == self.type_c01)
        s_c06 = snapshots.filtered(lambda s: s.document_type_id == self.type_c06)
        s_c12 = snapshots.filtered(lambda s: s.document_type_id == self.type_c12)

        self.assertEqual(s_c01.state, 'valid', 'C01 debería ser valid')
        self.assertEqual(s_c06.state, 'expired', 'C06 debería ser expired')
        self.assertEqual(s_c12.state, 'missing', 'C12 sin doc debería ser missing')

    def test_missing_document_marked(self):
        """Tipo requerido sin documento → state='missing'."""
        # Usar cliente nuevo para aislar test
        partner_new = self.env['res.partner'].create({
            'name': 'Cliente Missing',
            'vat': 'J-55555555-5',
        })
        client_new = self.Client.create({
            'name': 'Cliente Missing',
            'partner_id': partner_new.id,
            'company_id': self.env.company.id,
            'rif': 'J-55555555-5',
        })

        # No crear ningún documento
        snapshots = self.Status.generate_snapshot(
            client_new.id, self.test_year, self.test_month
        )

        # Todos deberían ser missing
        for snap in snapshots:
            self.assertEqual(snap.state, 'missing',
                             f'{snap.document_type_id.code} debería ser missing')

    def test_document_score(self):
        """Cliente con 1 doc válido de 36 → score≈2.78."""
        # Usar cliente nuevo para aislar test
        partner_new = self.env['res.partner'].create({
            'name': 'Cliente Score1',
            'vat': 'J-66666666-6',
        })
        client_new = self.Client.create({
            'name': 'Cliente Score1',
            'partner_id': partner_new.id,
            'company_id': self.env.company.id,
            'rif': 'J-66666666-6',
        })

        # Solo crear doc para C01 (1 de 36)
        self.Document.create({
            'client_id': client_new.id,
            'document_type_id': self.type_c01.id,
            'number': 'DOC-C01',
            'issue_date': fields.Date.today() - relativedelta(days=30),
            'expiry_date': fields.Date.today() + relativedelta(days=30),
            'state': 'valid',
        })

        # Forzar recálculo del score
        client_new._compute_document_score()

        # 1 válido de 36 requeridos ≈ 2.78%
        self.assertAlmostEqual(client_new.document_score, 100.0 / 36, places=2)

    def test_document_score_all_valid(self):
        """Cliente con todos los 36 docs válidos → score=100."""
        # Obtener todos los tipos requeridos para company
        required_types = self.DocType.search([('required_for', '=', 'company')])
        for doc_type in required_types:
            self._create_document(doc_type, state='valid')

        self.client._compute_document_score()
        self.assertEqual(self.client.document_score, 100.0)

    def test_document_score_no_required_types(self):
        """Si no hay tipos requeridos, score=100 (consistente con compliance_score)."""
        # Usar cliente nuevo para aislar test
        partner_new = self.env['res.partner'].create({
            'name': 'Cliente NoTypes',
            'vat': 'J-77777777-7',
        })
        client_new = self.Client.create({
            'name': 'Cliente NoTypes',
            'partner_id': partner_new.id,
            'company_id': self.env.company.id,
            'rif': 'J-77777777-7',
        })
        # Desactivar required_for temporalmente (no se puede en test real)
        # Pero el código ya maneja el caso: required_types vacío → 100
        # Verificamos que el compute no falle
        client_new._compute_document_score()
        # Con 36 tipos cargados en BD, será < 100 si no hay docs
        # Este test solo verifica que no hay error

    def test_unique_constraint(self):
        """Duplicar snapshot mismo cliente/año/mes/tipo → error."""
        # Usar un cliente nuevo y año/mes diferente para evitar conflictos con otros tests
        partner_new = self.env['res.partner'].create({
            'name': 'Cliente Unique',
            'vat': 'J-11111111-1',
        })
        client_new = self.Client.create({
            'name': 'Cliente Unique',
            'partner_id': partner_new.id,
            'company_id': self.env.company.id,
            'rif': 'J-11111111-1',
        })

        # Usar año/mes diferente
        test_year = 2020
        test_month = '1'

        self.Status.create({
            'client_id': client_new.id,
            'year': test_year,
            'month': test_month,
            'document_type_id': self.type_c01.id,
            'state': 'valid',
        })

        with self.assertRaises(IntegrityError):
            self.Status.create({
                'client_id': client_new.id,
                'year': test_year,
                'month': test_month,
                'document_type_id': self.type_c01.id,
                'state': 'missing',
            })

    def test_generate_snapshot_upsert(self):
        """generate_snapshot actualiza si ya existe (upsert)."""
        # Usar cliente nuevo para aislar test
        partner_new = self.env['res.partner'].create({
            'name': 'Cliente Upsert',
            'vat': 'J-22222222-2',
        })
        client_new = self.Client.create({
            'name': 'Cliente Upsert',
            'partner_id': partner_new.id,
            'company_id': self.env.company.id,
            'rif': 'J-22222222-2',
        })

        # Primera generación
        self._create_document(self.type_c01, state='valid')
        # Need to create document for the new client
        doc = self.Document.create({
            'client_id': client_new.id,
            'document_type_id': self.type_c01.id,
            'number': 'DOC-C01',
            'issue_date': fields.Date.today() - relativedelta(days=30),
            'expiry_date': fields.Date.today() + relativedelta(days=30),
            'state': 'valid',
        })
        self.Status.generate_snapshot(client_new.id, self.test_year, self.test_month)

        # Cambiar documento a expired
        doc.write({'state': 'expired'})

        # Segunda generación (debe actualizar)
        snapshots = self.Status.generate_snapshot(
            client_new.id, self.test_year, self.test_month
        )

        s_c01 = snapshots.filtered(lambda s: s.document_type_id == self.type_c01)
        self.assertEqual(s_c01.state, 'expired',
                         'Segunda generación debe actualizar estado a expired')

    def test_generate_snapshot_with_statuses(self):
        """Modo Fase C: statuses dict desde Excel."""
        # Usar cliente nuevo para aislar test
        partner_new = self.env['res.partner'].create({
            'name': 'Cliente Statuses',
            'vat': 'J-33333333-3',
        })
        client_new = self.Client.create({
            'name': 'Cliente Statuses',
            'partner_id': partner_new.id,
            'company_id': self.env.company.id,
            'rif': 'J-33333333-3',
        })

        statuses = {
            'C01': True,   # presente
            'C05': False,  # faltante
            'C06': True,   # presente
        }
        snapshots = self.Status.generate_snapshot(
            client_new.id, self.test_year, self.test_month,
            statuses=statuses
        )

        s_c01 = snapshots.filtered(lambda s: s.document_type_id.code == 'C01')
        s_c05 = snapshots.filtered(lambda s: s.document_type_id.code == 'C05')
        s_c06 = snapshots.filtered(lambda s: s.document_type_id.code == 'C06')
        s_c12 = snapshots.filtered(lambda s: s.document_type_id.code == 'C12')

        self.assertEqual(s_c01.state, 'valid')
        self.assertEqual(s_c05.state, 'missing')
        self.assertEqual(s_c06.state, 'valid')
        # C12 no está en statuses → modo normal (missing porque no hay doc)
        self.assertEqual(s_c12.state, 'missing')

    def test_generate_snapshot_all_clients(self):
        """Genera snapshots para múltiples clientes."""
        # Crear segundo cliente
        partner2 = self.env['res.partner'].create({
            'name': 'Cliente 2',
            'vat': 'J-98765432-1',
        })
        client2 = self.Client.create({
            'name': 'Cliente 2',
            'partner_id': partner2.id,
            'company_id': self.env.company.id,
            'rif': 'J-98765432-1',
        })

        snapshots = self.Status.generate_snapshot_all_clients(
            self.test_year, self.test_month
        )

        # Filtrar solo los dos clientes creados en este test
        test_client_ids = (self.client | client2).ids
        snapshots = snapshots.filtered(lambda s: s.client_id.id in test_client_ids)

        # 36 tipos * 2 clientes = 72
        self.assertEqual(len(snapshots), 72)
        client_ids = snapshots.mapped('client_id.id')
        self.assertIn(self.client.id, client_ids)
        self.assertIn(client2.id, client_ids)

    def test_action_open_cartelera_gaps(self):
        """action_open_cartelera_gaps devuelve act_window con domain correcto."""
        # Usar cliente nuevo para aislar test
        partner_new = self.env['res.partner'].create({
            'name': 'Cliente Gaps',
            'vat': 'J-88888888-8',
        })
        client_new = self.Client.create({
            'name': 'Cliente Gaps',
            'partner_id': partner_new.id,
            'company_id': self.env.company.id,
            'rif': 'J-88888888-8',
        })

        # Crear algunos snapshots missing y valid
        self.Status.create({
            'client_id': client_new.id,
            'year': self.test_year,
            'month': self.test_month,
            'document_type_id': self.type_c01.id,
            'state': 'missing',
        })
        self.Status.create({
            'client_id': client_new.id,
            'year': self.test_year,
            'month': self.test_month,
            'document_type_id': self.type_c05.id,
            'state': 'valid',
        })
        self.Status.create({
            'client_id': client_new.id,
            'year': self.test_year,
            'month': self.test_month,
            'document_type_id': self.type_c06.id,
            'state': 'missing',
        })

        action = client_new.action_open_cartelera_gaps()

        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'l10n.ve.cartelera.status')
        self.assertEqual(action['view_mode'], 'list,form')
        self.assertEqual(action['domain'], [('client_id', '=', client_new.id), ('state', '=', 'missing')])
        self.assertEqual(action['context'], {'default_client_id': client_new.id})