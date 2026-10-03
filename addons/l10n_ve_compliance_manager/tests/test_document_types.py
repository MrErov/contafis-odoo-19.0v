import re

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDocumentTypesCartelera(TransactionCase):
    """
    Tests de los 36 tipos de documento de la cartelera fiscal
    (data/document_type_cartelera.xml, noupdate=1).
    """

    def _cartelera_types(self):
        """Document types con code C01..C36 (formato ^C\\d{2}$)."""
        types = self.env['l10n.ve.document.type'].search([])
        return types.filtered(
            lambda t: t.code and re.match(r'^C\d{2}$', t.code)
        )

    def test_cartelera_types_loaded(self):
        """36 tipos con códigos C01..C36 exactos."""
        types = self._cartelera_types()
        self.assertEqual(len(types), 36)
        expected = {'C%02d' % i for i in range(1, 37)}
        self.assertEqual(set(types.mapped('code')), expected)

    def test_codes_unique(self):
        """No hay códigos duplicados (global y por institución)."""
        types = self._cartelera_types()
        codes = types.mapped('code')
        self.assertEqual(len(codes), len(set(codes)))
        pairs = [(t.institution_id.id, t.code) for t in types]
        self.assertEqual(len(pairs), len(set(pairs)))

    def test_counts_by_institution(self):
        """municipal=11, seniat=8, ivss=5, inces=2, banavih=4, mintra=6."""
        types = self._cartelera_types()
        expected = {
            'municipal': 11,
            'seniat': 8,
            'ivss': 5,
            'inces': 2,
            'banavih': 4,
            'mintra': 6,
        }
        for inst_type, count in expected.items():
            filtered = types.filtered(
                lambda t, it=inst_type: t.institution_id.type == it
            )
            self.assertEqual(
                len(filtered), count,
                'Institución %s: esperados %d, encontrados %d' % (
                    inst_type, count, len(filtered),
                ),
            )

    def test_validity_days_correct(self):
        """C06-C11=30, C12=365, C05=0, C29=0, C31=0."""
        types = self._cartelera_types()
        by_code = {t.code: t for t in types}
        for code in ('C06', 'C07', 'C08', 'C09', 'C10', 'C11'):
            self.assertEqual(
                by_code[code].validity_days, 30,
                'Código %s debe tener 30 días' % code,
            )
        self.assertEqual(by_code['C12'].validity_days, 365)
        for code in ('C05', 'C29', 'C31'):
            self.assertEqual(
                by_code[code].validity_days, 0,
                'Código %s debe ser permanente (0)' % code,
            )

    def test_mintra_institution_exists(self):
        """La institución MINTRA existe con type='mintra'."""
        mintra = self.env['l10n.ve.institution'].search([
            ('type', '=', 'mintra'),
        ])
        self.assertEqual(len(mintra), 1)
        self.assertTrue(mintra.name)
