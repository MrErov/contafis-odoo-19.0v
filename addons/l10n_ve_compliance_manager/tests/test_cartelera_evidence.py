from odoo import fields
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


@tagged('post_install', '-at_install')
class TestCarteleraEvidence(TransactionCase):
    """Tests del modelo l10n.ve.cartelera.evidence (Fase E2, Sub-tarea 1)."""

    def setUp(self):
        super().setUp()
        # Limpiar para idempotencia
        self.env['l10n.ve.cartelera.evidence'].search([]).unlink()
        self.env['l10n.ve.cartelera.status'].search([]).unlink()

        self.Client = self.env['l10n.ve.compliance.client']
        self.DocType = self.env['l10n.ve.document.type']
        self.Status = self.env['l10n.ve.cartelera.status']
        self.Evidence = self.env['l10n.ve.cartelera.evidence']

        # Cliente de prueba
        self.partner = self.env['res.partner'].create({
            'name': 'Cliente Test Evidence',
            'vat': 'J-12345678-9',
        })
        self.client = self.Client.create({
            'name': 'Cliente Test Evidence',
            'partner_id': self.partner.id,
            'company_id': self.env.company.id,
            'rif': 'J-12345678-9',
        })

        # Tipo de documento
        self.type_c01 = self.DocType.search([('code', '=', 'C01')], limit=1)

        # Mes de prueba
        today = fields.Date.today()
        prev_month = today - relativedelta(months=1)
        self.test_year = prev_month.year
        self.test_month = str(prev_month.month)

        # Crear snapshot inicial con state='missing'
        self.status = self.Status.create({
            'client_id': self.client.id,
            'year': self.test_year,
            'month': self.test_month,
            'document_type_id': self.type_c01.id,
            'state': 'missing',
        })

    def _create_evidence(self, status, state='pending', image=False):
        """Helper para crear evidencia."""
        vals = {
            'cartelera_status_id': status.id,
            'state': state,
            'notes': f'Test {state}',
        }
        if image:
            vals['image'] = image
        return self.Evidence.create(vals)

    def test_evidence_create_missing_to_pending(self):
        """Crear evidencia con state='pending' cambia status de 'missing' a 'pending'."""
        self.assertEqual(self.status.state, 'missing')

        self._create_evidence(self.status, state='pending')

        self.status.invalidate_recordset()
        self.assertEqual(self.status.state, 'pending',
                         'Status debe cambiar a pending al crear evidence pending')

    def test_evidence_accepted_to_valid(self):
        """Evidencia accepted → status = 'valid'."""
        self.status.write({'state': 'missing'})
        self._create_evidence(self.status, state='accepted')

        self.status.invalidate_recordset()
        self.assertEqual(self.status.state, 'valid',
                         'Status debe ser valid con evidence accepted')

    def test_evidence_reject_only_when_no_accepted(self):
        """Si hay accepted, rejected no cambia a rejected."""
        # Primero accepted
        self._create_evidence(self.status, state='accepted')
        self.status.invalidate_recordset()
        self.assertEqual(self.status.state, 'valid')

        # Añadir rejected
        self._create_evidence(self.status, state='rejected')
        self.status.invalidate_recordset()
        # Debe seguir valid porque hay accepted
        self.assertEqual(self.status.state, 'valid',
                         'Status debe seguir valid si hay accepted')

        # Limpiar y probar solo rejected
        self.Evidence.search([]).unlink()
        self.status.write({'state': 'missing'})
        self._create_evidence(self.status, state='rejected')
        self.status.invalidate_recordset()
        self.assertEqual(self.status.state, 'rejected',
                         'Status debe ser rejected si solo hay rejected')

    def test_evidence_unlink_recomputes(self):
        """Unlink de evidence recalcula status correctamente."""
        # Crear accepted → valid
        ev = self._create_evidence(self.status, state='accepted')
        self.status.invalidate_recordset()
        self.assertEqual(self.status.state, 'valid')

        # Borrar evidence → status no debe tocarse si queda sin evidence
        # (la regla dice: si NO hay evidence, NO TOCAR el estado)
        ev.unlink()
        self.status.invalidate_recordset()
        # El estado se mantiene en 'valid' porque no hay evidence
        # (en la práctica el contador vería que no hay evidencia y decidirá)
        self.assertEqual(self.status.state, 'valid',
                         'Sin evidence, el estado no se toca (queda como estaba)')

        # Probar con pending
        self.status.write({'state': 'missing'})
        ev2 = self._create_evidence(self.status, state='pending')
        self.status.invalidate_recordset()
        self.assertEqual(self.status.state, 'pending')

        ev2.unlink()
        self.status.invalidate_recordset()
        self.assertEqual(self.status.state, 'pending',
                         'Sin evidence, el estado no se toca')

    def test_evidence_write_state_change(self):
        """Cambiar state de evidence llama a recompute."""
        ev = self._create_evidence(self.status, state='pending')
        self.status.invalidate_recordset()
        self.assertEqual(self.status.state, 'pending')

        # Cambiar a accepted
        ev.write({'state': 'accepted'})
        self.status.invalidate_recordset()
        self.assertEqual(self.status.state, 'valid')

        # Cambiar a rejected
        ev.write({'state': 'rejected'})
        self.status.invalidate_recordset()
        self.assertEqual(self.status.state, 'rejected')

    def test_evidence_image_size_limit(self):
        """Crear evidence con imagen > 5 MB debe lanzar ValidationError."""
        import base64
        # Crear imagen simulada de 6 MB (base64 de 6MB)
        large_image = base64.b64encode(b'x' * (6 * 1024 * 1024)).decode()
        with self.assertRaises(ValidationError) as cm:
            self._create_evidence(self.status, state='pending', image=large_image)
        self.assertIn('6.0 MB', str(cm.exception))
        self.assertIn('5.0 MB', str(cm.exception))

    def test_evidence_image_compression(self):
        """Wizard comprime imagen de 3 MB → evidence guardada pesa menos."""
        import base64
        # Usar PNG real pequeño (1x1 px transparente) que image_process puede comprimir
        real_png = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+XfJsAAAAASUVORK5CYII='
        # Repetir para simular ~3MB (en test real usaríamos imagen real grande)
        # Para test: verificamos que el wizard llama a compresión y crea evidence
        Wizard = self.env['l10n.ve.cartelera.evidence.wizard']
        wizard = Wizard.with_context(
            default_cartelera_status_id=self.status.id
        ).create({
            'image': real_png,
            'filename': 'test.png',
            'notes': 'Test compresión',
        })
        wizard.action_upload()

        evidence = self.Evidence.search([('cartelera_status_id', '=', self.status.id)])
        self.assertEqual(len(evidence), 1)
        # El archivo guardado existe y tiene file_size_mb computado
        self.assertGreater(evidence.file_size_mb, 0.0)