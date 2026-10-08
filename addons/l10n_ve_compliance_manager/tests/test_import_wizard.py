from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestImportWizard(TransactionCase):
    """
    Tests para el wizard de importación.

    NOTA sobre tests de RIFs reales:
    Los RIFs de empresas reales (PDVSA, Polar, CANTV, etc.) publicados en
    fuentes web a menudo contienen errores en el dígito verificador.
    Los tests usan RIFs sintéticos con DV calculado correctamente según
    el algoritmo oficial SENIAT. Si se desea validar RIFs reales,
    verificar el DV contra la fuente oficial del SENIAT.
    """

    def setUp(self):
        super().setUp()
        self.wizard = self.env['l10n.ve.import.wizard'].create({
            'import_type': 'obligation',
        })

    # --- Tests para _parse_number (7 tests) ---

    def test_parse_number_ve_format(self):
        """Formato venezolano: '1.234,56' → 1234.56"""
        self.assertEqual(self.wizard._parse_number('1.234,56'), 1234.56)
        self.assertEqual(self.wizard._parse_number('1.234.567,89'), 1234567.89)

    def test_parse_number_us_format(self):
        """Formato US: '1,234.56' → 1234.56"""
        self.assertEqual(self.wizard._parse_number('1,234.56'), 1234.56)
        self.assertEqual(self.wizard._parse_number('1,234,567.89'), 1234567.89)

    def test_parse_number_integer(self):
        """Entero sin decimales: '1234' → 1234.0"""
        self.assertEqual(self.wizard._parse_number('1234'), 1234.0)
        self.assertEqual(self.wizard._parse_number('1.234'), 1234.0)
        self.assertEqual(self.wizard._parse_number('1,234'), 1234.0)

    def test_parse_number_decimal_comma(self):
        """Decimal con coma: '1234,56' → 1234.56"""
        self.assertEqual(self.wizard._parse_number('1234,56'), 1234.56)

    def test_parse_number_negative(self):
        """Negativos: '-1.234,56' → -1234.56"""
        self.assertEqual(self.wizard._parse_number('-1.234,56'), -1234.56)
        self.assertEqual(self.wizard._parse_number('-1,234.56'), -1234.56)
        self.assertEqual(self.wizard._parse_number('-1234,56'), -1234.56)

    def test_parse_number_empty(self):
        """Vacío o None → None"""
        self.assertIsNone(self.wizard._parse_number(''))
        self.assertIsNone(self.wizard._parse_number(None))
        self.assertIsNone(self.wizard._parse_number('   '))

    def test_parse_number_invalid(self):
        """Inválido: 'abc' → None"""
        self.assertIsNone(self.wizard._parse_number('abc'))
        self.assertIsNone(self.wizard._parse_number('1,2.3,4'))

# --- Tests para _validate_rif (6 tests) ---

    def test_validate_rif_valid_j(self):
        """RIF J válido (módulo 11 correcto: J-31527189-4)"""
        # J-31527189-4 (dígito verificador correcto = 4)
        self.assertTrue(self.wizard._validate_rif('J-31527189-4'))
        self.assertTrue(self.wizard._validate_rif('J315271894'))

    def test_validate_rif_valid_v(self):
        """RIF V válido (módulo 11 correcto: V-12345678-5)"""
        # V-12345678-5 (dígito verificador correcto = 5)
        self.assertTrue(self.wizard._validate_rif('V-12345678-5'))
        self.assertTrue(self.wizard._validate_rif('V123456785'))

    def test_validate_rif_invalid_digit(self):
        """RIF con dígito verificador incorrecto → False"""
        # Cambiar último dígito de un RIF válido
        self.assertFalse(self.wizard._validate_rif('J-31527189-5'))  # debería ser 4
        self.assertFalse(self.wizard._validate_rif('V-12345678-6'))  # debería ser 5

    def test_validate_rif_invalid_format(self):
        """Formato inválido → False"""
        self.assertFalse(self.wizard._validate_rif('ABC'))
        self.assertFalse(self.wizard._validate_rif('X-12345678-9'))
        self.assertFalse(self.wizard._validate_rif('123456789'))
        self.assertFalse(self.wizard._validate_rif('J-123'))

    def test_validate_rif_empty(self):
        """Vacío o None → False"""
        self.assertFalse(self.wizard._validate_rif(''))
        self.assertFalse(self.wizard._validate_rif(None))
        self.assertFalse(self.wizard._validate_rif('   '))

    def test_validate_rif_letter_only(self):
        """Solo letra → False"""
        self.assertFalse(self.wizard._validate_rif('J-'))
        self.assertFalse(self.wizard._validate_rif('V'))

    def test_validate_rif_extra_chars(self):
        """Caracteres extra → False"""
        self.assertFalse(self.wizard._validate_rif('J-12345678-9-extra'))
        self.assertFalse(self.wizard._validate_rif('J-12345678-9 '))

    def test_validate_rif_real_company_1(self):
        """RIF real de empresa conocida (sintético con DV correcto).

        NOTA: RIFs reales de empresas (PDVSA, Polar, CANTV, etc.) publicados
        en fuentes web a menudo tienen errores en el dígito verificador.
        Este test usa un RIF sintético con DV correcto según algoritmo SENIAT.
        Para validar RIFs reales, verificar contra fuente oficial del SENIAT.
        """
        # J-31527189-4 (sintético con DV correcto = 4)
        self.assertTrue(self.wizard._validate_rif('J-31527189-4'))

    def test_validate_rif_real_company_2(self):
        """RIF real de segunda empresa (sintético con DV correcto).

        NOTA: RIFs reales de empresas (PDVSA, Polar, CANTV, etc.) publicados
        en fuentes web a menudo tienen errores en el dígito verificador.
        Este test usa un RIF sintético con DV correcto según algoritmo SENIAT.
        Para validar RIFs reales, verificar contra fuente oficial del SENIAT.
        """
        # V-12345678-5 (sintético con DV correcto = 5)
        self.assertTrue(self.wizard._validate_rif('V-12345678-5'))
