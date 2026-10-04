from io import BytesIO
import base64
import json

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class ImportWizard(models.TransientModel):
    _name = 'l10n.ve.import.wizard'
    _description = 'Wizard de Importación desde Excel'

    IMPORT_TYPES = [
        ('obligation', 'Obligaciones'),
        ('document', 'Documentos'),
        ('client', 'Clientes'),
        ('retention', 'Retenciones'),
        ('cartelera', 'Cartelera Fiscal'),
    ]

    import_type = fields.Selection(
        IMPORT_TYPES, string='Tipo de Importación', required=True,
        default='obligation'
    )
    # No `required=True`: el wizard debe poder crearse para descargar la
    # plantilla sin archivo. `action_load_file`/`action_preview` lo validan.
    file = fields.Binary(string='Archivo Excel')
    filename = fields.Char(string='Nombre de Archivo')
    template_file = fields.Binary(string='Plantilla')
    mapping_ids = fields.One2many(
        'l10n.ve.import.mapping', 'wizard_id', string='Mapeo de Columnas'
    )
    line_ids = fields.One2many(
        'l10n.ve.import.line', 'wizard_id', string='Líneas de Importación'
    )
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('mapping', 'Mapeo'),
        ('preview', 'Vista Previa'),
        ('validating', 'Validando'),
        ('done', 'Completado'),
    ], string='Estado', default='draft')
    preview_limit = fields.Integer(
        string='Límite de Vista Previa', default=50,
        help='Máximo de filas a mostrar en la vista previa'
    )
    preview_exceeded = fields.Boolean(
        string='Preview Excedido', default=False,
        help='Indica si el archivo tiene más filas que el límite de preview'
    )
    company_id = fields.Many2one(
        'res.company', string='Compañía',
        default=lambda self: self.env.company, required=True
    )
    mode = fields.Selection([
        ('strict', 'Estricto (rollback total en error)'),
        ('lax', 'Flexible (continúa en error, default)'),
    ], string='Modo', default='lax')
    cartelera_year = fields.Integer(
        string='Año cartelera',
        default=lambda self: fields.Date.today().year,
        help='Año del período a importar',
    )
    cartelera_month = fields.Selection([
        ('1', 'Enero'), ('2', 'Febrero'), ('3', 'Marzo'),
        ('4', 'Abril'), ('5', 'Mayo'), ('6', 'Junio'),
        ('7', 'Julio'), ('8', 'Agosto'), ('9', 'Septiembre'),
        ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre'),
    ], string='Mes cartelera',
       default=lambda self: str(fields.Date.today().month))
    attachment_id = fields.Many2one(
        'ir.attachment', string='Log de Importación', readonly=True
    )

    # Datos para plantillas por tipo de importación
    @api.model
    def _get_import_templates(self):
        """Devuelve la definición de campos por tipo de importación."""
        return {
            'obligation': {
                'model': 'l10n.ve.obligation',
                'fields': [
                    ('name', 'char', 'Nombre / Referencia', True),
                    ('client_id', 'many2one', 'Cliente (RIF o nombre)', True,
                     'l10n.ve.compliance.client'),
                    ('obligation_type_id', 'many2one', 'Tipo Obligación', True,
                     'l10n.ve.obligation.type'),
                    ('period', 'char', 'Período (MM/YYYY)', True),
                    ('due_date', 'date', 'Fecha Vencimiento', False),
                    ('amount', 'float', 'Monto', False),
                    ('currency_id', 'many2one', 'Moneda', False,
                     'res.currency'),
                    ('state', 'selection', 'Estado', False,
                     [('pending', 'Pendiente'), ('paid', 'Pagada'),
                      ('overdue', 'Vencida'), ('cancelled', 'Cancelada')]),
                    ('payment_date', 'date', 'Fecha Pago', False),
                    ('payment_reference', 'char', 'Ref. Pago', False),
                    ('notes', 'text', 'Notas', False),
                ]
            },
            'document': {
                'model': 'l10n.ve.document',
                'fields': [
                    ('client_id', 'many2one', 'Cliente (RIF o nombre)', True,
                     'l10n.ve.compliance.client'),
                    ('document_type_id', 'many2one', 'Tipo Documento', True,
                     'l10n.ve.document.type'),
                    ('number', 'char', 'Número Documento', True),
                    ('issue_date', 'date', 'Fecha Emisión', True),
                    ('expiry_date', 'date', 'Fecha Vencimiento', True),
                    ('state', 'selection', 'Estado', False,
                     [('valid', 'Válido'), ('expired', 'Expirado'),
                      ('pending', 'Pendiente'), ('rejected', 'Rechazado')]),
                    ('notes', 'text', 'Notas', False),
                ]
            },
            'client': {
                'model': 'l10n.ve.compliance.client',
                'fields': [
                    ('name', 'char', 'Nombre', True),
                    ('partner_id', 'many2one', 'Contacto (crea si no existe)', True,
                     'res.partner'),
                    ('rif', 'char', 'RIF', True),
                    ('activity_type', 'selection', 'Actividad', False,
                     [('comercio', 'Comercio'), ('servicios', 'Servicios'),
                      ('industria', 'Industria'), ('mixto', 'Mixto')]),
                    ('municipality', 'char', 'Municipio', False),
                ]
            },
            'retention': {
                'model': 'l10n.retention',
                'fields': [
                    ('partner_id', 'many2one', 'Proveedor', True,
                     'res.partner'),
                    ('amount', 'float', 'Monto', True),
                    ('currency_id', 'many2one', 'Moneda', True,
                     'res.currency'),
                    ('date', 'date', 'Fecha', True),
                    ('invoice_id', 'many2one', 'Factura (in_invoice)', True,
                     'account.move'),
                    ('state', 'selection', 'Estado', False,
                     [('draft', 'Borrador'), ('posted', 'Publicada'),
                      ('cancel', 'Cancelada')]),
                ]
            },
        }

    def action_download_template(self):
        """Genera y descarga la plantilla Excel para el tipo seleccionado."""
        self.ensure_one()
        template_data = self._get_import_templates().get(self.import_type)
        if not template_data:
            return
        xlsx_content = self._generate_template_xlsx(template_data)
        filename = f'plantilla_{self.import_type}.xlsx'
        self.write({
            'template_file': base64.b64encode(xlsx_content),
            'filename': filename,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model=l10n.ve.import.wizard&id={self.id}'
                   f'&field=template_file&download=true&filename={filename}',
            'target': 'self',
        }

    def _generate_template_xlsx(self, template_data):
        """Genera archivo xlsx con headers de la plantilla."""
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Plantilla'

        headers = []
        for field in template_data['fields']:
            headers.append(field[2])  # label

        # Estilo header
        header_font = Font(bold=True, color='FFFFFF')
        header_fill = PatternFill(
            start_color='2C3E50', end_color='2C3E50', fill_type='solid'
        )
        header_align = Alignment(horizontal='center', wrap_text=True)

        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align
            ws.column_dimensions[get_column_letter(col_idx)].width = 25

        # Fila de ejemplo (vacía)
        for col_idx in range(1, len(headers) + 1):
            ws.cell(row=2, column=col_idx, value='')

        # Guardar en bytes
        from io import BytesIO
        output = BytesIO()
        wb.save(output)
        return output.getvalue()

    def _parse_cartelera_excel(self):
        """
        Parsea el Excel de cartelera fiscal para el mes/año seleccionados.
        
        Estructura esperada:
        - Hoja según mes: enero, febrero, ..., diciembre (minúsculas)
        - Fila 3: 36 headers columnas E..AN (índices 4..39 0-based)
        - Filas 4+: una por empresa
          - Col B (índice 1): RIF
          - Col C (índice 2): Nombre empresa
          - Cols E..AN (índices 4..39): 36 valores True/False para C01..C36
        
        Crea líneas l10n.ve.import.line con data = {
            'rif': rif, 'name': name, 'year': year, 'month': month, 'statuses': statuses
        }
        """
        self.ensure_one()
        if not self.file:
            raise UserError(_('Debe subir un archivo Excel.'))
        
        import base64
        import openpyxl
        from io import BytesIO
        
        file_data = base64.b64decode(self.file)
        wb = openpyxl.load_workbook(BytesIO(file_data), read_only=True, data_only=True)
        
        # Mapear mes a nombre de hoja
        month_names = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        month_int = int(self.cartelera_month)
        sheet_name = month_names.get(month_int)
        
        if sheet_name not in wb.sheetnames:
            raise UserError(_(
                "La hoja '%s' no existe en el archivo. "
                "Verifique que el archivo tiene 12 hojas: enero, febrero, ..., diciembre."
            ) % sheet_name)
        
        ws = wb[sheet_name]
        
        # Leer fila 3 para headers (índices 4..39 = columnas E..AN)
        # En read_only, iter_rows min_row=3, max_row=3, min_col=5, max_col=40
        # values_only=True devuelve tuplas de valores, no objetos cell
        headers = []
        for row in ws.iter_rows(min_row=3, max_row=3, min_col=5, max_col=40, values_only=True):
            for val in row:
                headers.append(str(val) if val else '')
        
        if len(headers) != 36:
            raise UserError(_(
                "Se esperaban 36 columnas de documentos (E..AN) en la fila 3, "
                "se encontraron %d. Verifique la estructura del archivo."
            ) % len(headers))
        
        # Códigos C01..C36 en orden posicional
        codes = [f'C{i:02d}' for i in range(1, 37)]
        
        # Leer filas 4+ (empresas)
        row_count = 0
        for row in ws.iter_rows(min_row=4, values_only=True):
            if not row or len(row) < 3:
                continue
            
            rif = row[1] if len(row) > 1 else None  # Columna B (índice 1)
            name = row[2] if len(row) > 2 else None  # Columna C (índice 2)
            
            # Parar si RIF y nombre están vacíos
            if not rif and not name:
                break
            
            if not rif:
                continue  # Saltar filas sin RIF
            
            # Normalizar RIF: si viene sin guiones (J000000001), formatear
            rif_str = str(rif).strip().upper().replace('.', '').replace(' ', '')
            if '-' not in rif_str and len(rif_str) >= 9:
                # Formato J000000001 -> J-00000001-? (no podemos calcular DV sin el original)
                # Dejamos como viene si no tiene guiones
                pass
            
            # Leer 36 valores de estado (columnas E..AN = índices 4..39)
            statuses = {}
            for i, code in enumerate(codes):
                col_idx = 4 + i  # 0-based: E=4, F=5, ..., AN=39
                cell_value = row[col_idx] if col_idx < len(row) else None
                # True si valor es True, '1', 'true', 'sí', 'si', 'yes', 'verdadero'
                # False si vacío, False, '0', 'false', 'no', 'falso'
                if cell_value is None:
                    statuses[code] = False
                elif isinstance(cell_value, bool):
                    statuses[code] = cell_value
                else:
                    val_str = str(cell_value).strip().lower()
                    statuses[code] = val_str in ('1', 'true', 'verdadero', 'si', 'sí', 'yes', 'x')
            
            # Crear línea de importación
            self.env['l10n.ve.import.line'].create({
                'wizard_id': self.id,
                'row_index': row_count + 1,
                'data': {
                    'rif': rif_str,
                    'name': str(name).strip() if name else '',
                    'year': self.cartelera_year,
                    'month': self.cartelera_month,
                    'statuses': statuses,
                },
                'state': 'draft',
            })
            row_count += 1
        
        if row_count == 0:
            raise UserError(_(
                "No se encontraron empresas válidas en la hoja '%s'. "
                "Verifique que la columna B (RIF) y C (Nombre) tengan datos."
            ) % sheet_name)
        
        return row_count

    def action_load_file(self):
        """Carga el archivo Excel, lee headers y crea mapeo automático.
        
        Para import_type='cartelera', usa parser específico y salta a preview directamente.
        """
        self.ensure_one()
        if not self.file:
            raise UserError(_('Debe subir un archivo Excel.'))

        if self.import_type == 'cartelera':
            return self._load_cartelera_file()

        import base64
        import openpyxl
        from openpyxl.utils import get_column_letter

        file_data = base64.b64decode(self.file)
        wb = openpyxl.load_workbook(BytesIO(file_data), read_only=True)
        ws = wb.active

        # Leer primera fila (headers)
        headers = []
        for col_idx, cell in enumerate(ws[1], 1):
            headers.append({
                'col_index': col_idx - 1,
                'column_letter': get_column_letter(col_idx),
                'col_name': str(cell.value) if cell.value else f'Columna_{col_idx}',
            })

        # Crear mapeo automático
        template_data = self._get_import_templates().get(self.import_type)
        if not template_data:
            return

        odoo_fields = template_data['fields']
        for h in headers:
            # Auto-match por nombre normalizado
            match_field = None
            for of in odoo_fields:
                if self._normalize(h['col_name']) == self._normalize(of[2]):
                    match_field = of
                    break

            vals = {
                'wizard_id': self.id,
                'col_index': h['col_index'],
                'column_letter': h['column_letter'],
                'col_name': h['col_name'],
                'field_name': match_field[0] if match_field else '',
                'field_type': match_field[1] if match_field else 'char',
                'required': match_field[3] if match_field else False,
                'relation_model': match_field[4] if match_field and len(of) > 4 else '',
            }
            self.env['l10n.ve.import.mapping'].create(vals)

        # Cambiar estado a mapping
        self.state = 'mapping'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n.ve.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _load_cartelera_file(self):
        """Carga archivo cartelera: parsea directo y va a preview (sin paso mapping)."""
        self.ensure_one()
        row_count = self._parse_cartelera_excel()
        self.state = 'preview'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n.ve.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _normalize(self, text):
        """Normaliza texto para comparación (minúsculas, sin espacios, sin acentos)."""
        import unicodedata
        if not text:
            return ''
        text = str(text).strip().lower()
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        return text.replace(' ', '_').replace('-', '_')

    @api.model
    def _parse_number(self, value):
        """
        Convierte strings numéricos con formato venezolano/latino a float.
        Maneja:
          '1.234,56'  → 1234.56
          '1,234.56'  → 1234.56
          '1234,56'   → 1234.56
          '1234.56'   → 1234.56
          '1.234'     → 1234.0
          '-1.234,56' → -1234.56
          ''          → None
        Retorna float o None si falla.
        """
        if value is None or value == '':
            return None
        if isinstance(value, (int, float)):
            return float(value)
        s = str(value).strip()
        if not s:
            return None
        # Manejar signo negativo
        negative = s.startswith('-')
        if negative:
            s = s[1:]
        # Detectar separadores
        has_dot = '.' in s
        has_comma = ',' in s
        if has_dot and has_comma:
            # Ambos presentes: el último es decimal
            last_dot = s.rfind('.')
            last_comma = s.rfind(',')
            if last_dot > last_comma:
                # Punto es decimal
                s = s.replace(',', '')
            else:
                # Coma es decimal
                s = s.replace('.', '').replace(',', '.')
        elif has_comma:
            # Solo coma: puede ser decimal o miles
            parts = s.split(',')
            if len(parts[-1]) <= 2:
                # Última parte 1-2 dígitos → decimal
                s = s.replace(',', '.')
            else:
                # 3 dígitos → separador de miles
                s = s.replace(',', '')
        elif has_dot:
            # Solo punto: puede ser decimal o miles
            parts = s.split('.')
            if len(parts[-1]) <= 2:
                # Última parte 1-2 dígitos → decimal (ya es .)
                pass
            else:
                # 3 dígitos → separador de miles
                s = s.replace('.', '')
        try:
            result = float(s)
            return -result if negative else result
        except ValueError:
            return None

    @api.model
    def _validate_rif(self, rif):
        """
        Valida RIF venezolano con algoritmo oficial módulo 11 (SENIAT).
        Formato: [JVEGP]-XXXXXXXX-X (9 dígitos + dígito verificador)
        
        Algoritmo oficial SENIAT:
        1. Extraer letra (J/V/E/G/P) y 9 dígitos (8 dígitos + 1 dígito verificador)
        2. Usar pesos fijos para los 8 dígitos principales: [3, 2, 7, 6, 5, 4, 3, 2]
        3. Sumar: suma = Σ(digito_i * peso_i) para i=1..8
        4. Calcular DV = 11 - (suma % 11)
           - Si DV = 10 → DV = 0
           - Si DV = 11 → DV = 1
        5. Comparar DV calculado con el 9no dígito (dígito verificador)
        
        La letra (J/V/E/G/P) solo valida el formato, NO afecta el cálculo del DV.
        La letra SÍ está en el RIF pero el algoritmo SENIAT usa solo los 8 dígitos
        para calcular el dígito verificador (la letra es solo clasificatoria).
        
        Ejemplo V-12345678:
        Dígitos: 1,2,3,4,5,6,7,8 | Pesos: 3,2,7,6,5,4,3,2
        Suma = 1*3+2*2+3*7+4*6+5*5+6*4+7*3+8*2 = 138
        138 % 11 = 6 → DV = 11-6 = 5 → V-12345678-5 (válido)
        
        Ejemplo J-31527189:
        Dígitos: 3,1,5,2,7,1,8,9 | Pesos: 3,2,7,6,5,4,3,2
        Suma = 3*3+1*2+5*7+2*6+7*5+1*4+8*3+9*2 = 139
        139 % 11 = 7 → DV = 11-7 = 4 → J-31527189-4 (válido)
        """
        if not rif:
            return False
        import re
        # Limpiar y extraer letra y dígitos
        rif_clean = str(rif).strip().upper().replace('-', '').replace('.', '').replace(' ', '')
        match = re.match(r'^([JVEGP])(\d{9})$', rif_clean)
        if not match:
            return False
        letter, digits = match.groups()
        if len(digits) != 9:
            return False
        # Pesos fijos para los 8 dígitos principales (algoritmo SENIAT)
        weights = [3, 2, 7, 6, 5, 4, 3, 2]
        # Calcular suma de primeros 8 dígitos * pesos
        total = sum(int(digits[i]) * weights[i] for i in range(8))
        # Calcular dígito verificador
        resto = total % 11
        dv = 11 - resto
        if dv == 10:
            dv = 0
        elif dv == 11:
            dv = 1
        # Comparar con 9no dígito (dígito verificador)
        return dv == int(digits[8])

    def action_validate_syntax(self):
        """
        Valida la sintaxis de todas las líneas del preview.
        Muestra notificación con resumen.
        """
        self.ensure_one()
        for line in self.line_ids:
            line._validate_syntax()
        total = len(self.line_ids)
        errors = len(self.line_ids.filtered(lambda l: l.state == 'error'))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Validación completada',
                'message': f'{total - errors} válidas, {errors} con errores',
                'type': 'success' if errors == 0 else 'warning',
            }
        }

    def action_preview(self):
        """Genera preview de las primeras N filas.
        
        Para import_type='cartelera', el preview ya se generó en _load_cartelera_file.
        """
        self.ensure_one()
        if self.import_type == 'cartelera':
            # Preview ya generado, solo verificar que hay líneas
            if not self.line_ids:
                raise UserError(_('No hay datos de preview. Cargue el archivo primero.'))
            if len(self.line_ids) > self.preview_limit:
                self.preview_exceeded = True
            self.state = 'preview'
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'l10n.ve.import.wizard',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }

        if not self.file:
            raise UserError(_('Debe subir un archivo Excel.'))

        import base64
        import openpyxl
        from io import BytesIO

        file_data = base64.b64decode(self.file)
        wb = openpyxl.load_workbook(BytesIO(file_data), read_only=True)
        ws = wb.active

        # Obtener mapeos válidos
        mappings = self.mapping_ids.filtered(lambda m: m.field_name)
        if not mappings:
            raise UserError(_('Debe mapear al menos una columna.'))

        limit = self.preview_limit or 50
        row_count = 0

        # Limpiar líneas previas
        self.line_ids.unlink()

        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 1):
            if row_count >= limit:
                break
            if all(v is None for v in row):
                continue

            data = {}
            for m in mappings:
                col_idx = m.col_index
                value = row[col_idx] if col_idx < len(row) else None
                data[m.field_name] = value

            # Crear línea de preview
            self.env['l10n.ve.import.line'].create({
                'wizard_id': self.id,
                'row_index': row_count + 1,
                'data': data,
                'state': 'draft',
            })
            row_count += 1

        if row_count == 0:
            raise UserError(_('El archivo no contiene datos válidos.'))

        if ws.max_row - 1 > limit:
            self.preview_exceeded = True

        self.state = 'preview'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n.ve.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_validate(self):
        """Ejecuta validación 3 niveles en todas las líneas del preview."""
        self.ensure_one()
        lines = self.line_ids.filtered(lambda l: l.state in ('draft', 'validated'))
        for line in lines:
            errors = self._validate_line(line)
            if errors:
                line.write({'state': 'error', 'error_msg': '\n'.join(errors)})
            else:
                line.write({'state': 'validated', 'error_msg': False})
        self.state = 'validating'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n.ve.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _validate_line(self, line):
        """Valida una línea según 3 niveles. Retorna lista de errores."""
        errors = []
        data = line.data or {}

        # Nivel 1: Sintaxis
        # TODO: implementar validaciones sintácticas

        # Nivel 2: Referencial
        # TODO: implementar validaciones referenciales

        # Nivel 3: Negocio
        # TODO: implementar validaciones de negocio

        return errors

    def action_import(self):
        """
        Ejecuta la importación real (upsert batch con savepoints).
        Modo strict: primer error → rollback total y excepción.
        Modo lax: continúa procesando, reporta errores por fila.
        """
        self.ensure_one()
        if self.mode == 'strict':
            lines_with_errors = self.line_ids.filtered(
                lambda l: l.state == 'error'
            )
            if lines_with_errors:
                raise UserError(
                    f"Modo estricto: hay {len(lines_with_errors)} fila(s) con error. "
                    "Corríjalos antes de importar o cambie a modo lax."
                )

        lines = self.line_ids.filtered(
            lambda l: l.state in ('validated', 'draft')
        )
        error_fatal = False
        for line in lines:
            if self.import_type == 'cartelera':
                action = self._import_cartelera_line(line)
            else:
                action = self._import_line(line)
            if action == 'error' and self.mode == 'strict':
                error_fatal = True
                break

        if error_fatal:
            raise UserError(
                "Importación abortada en modo estricto por error en una fila."
            )

        # Crear log persistente (solo si no hubo error fatal)
        # Re-contar stats desde los states de las líneas
        success_count = len(self.line_ids.filtered(
            lambda l: l.state in ('imported', 'updated')
        ))
        error_count = len(self.line_ids.filtered(lambda l: l.state == 'error'))
        skipped_count = len(self.line_ids.filtered(lambda l: l.state == 'skipped'))

        # Obtener records del log desde record_id (Reference field)
        import json
        records_created = []
        for line in self.line_ids.filtered(lambda l: l.state in ('imported', 'updated')):
            if line.record_id:
                try:
                    # record_id es Reference: "model,id"
                    model_name, record_id_str = line.record_id.split(',')
                    records_created.append({
                        'model': model_name,
                        'id': int(record_id_str),
                        'name': line.record_name or '',
                    })
                except Exception:
                    pass

        self._create_import_log(
            success_count, error_count, skipped_count, records_created
        )

        self.state = 'done'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n.ve.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _upsert_record(self, model_name, values, unique_domain):
        """
        Busca por unique_domain. Si existe → write. Si no → create.
        Retorna (record, 'created' | 'updated').
        """
        Model = self.env[model_name]
        existing = Model.search(unique_domain, limit=1)
        if existing:
            existing.write(values)
            return existing, 'updated'
        else:
            record = Model.create(values)
            return record, 'created'

    def _get_import_target(self, line, values):
        """
        Devuelve (model_name, unique_domain) según wizard.import_type.
        """
        wizard = self
        import_type = wizard.import_type

        if import_type == 'obligation':
            client_id = values.get('client_id')
            obligation_type_id = values.get('obligation_type_id')
            period = values.get('period')
            model_name = 'l10n.ve.obligation'
            unique_domain = [
                ('client_id', '=', client_id),
                ('obligation_type_id', '=', obligation_type_id),
                ('period', '=', period),
            ]
            return model_name, unique_domain

        elif import_type == 'document':
            client_id = values.get('client_id')
            document_type_id = values.get('document_type_id')
            number = values.get('number')
            model_name = 'l10n.ve.document'
            unique_domain = [
                ('client_id', '=', client_id),
                ('document_type_id', '=', document_type_id),
                ('number', '=', number),
            ]
            return model_name, unique_domain

        elif import_type == 'client':
            rif = values.get('rif')
            model_name = 'l10n.ve.compliance.client'
            unique_domain = [('rif', '=', rif)]
            return model_name, unique_domain

        elif import_type == 'retention':
            invoice_id = values.get('invoice_id')
            partner_id = values.get('partner_id')
            model_name = 'l10n.ve.retention'
            unique_domain = [
                ('invoice_id', '=', invoice_id),
                ('partner_id', '=', partner_id),
            ]
            return model_name, unique_domain

        return 'l10n.ve.import.wizard', []

    def _resolve_values(self, line):
        """
        Resuelve los Many2one campos y construye un dict de valores
        plano para upsert a partir de los datos de la línea y el mapping.
        """
        wizard = self
        data = line.data or {}
        mappings = wizard.mapping_ids.filtered(lambda m: m.field_name)

        values = {}
        for m in mappings:
            field_name = m.field_name
            if field_name not in data:
                continue
            value = data[field_name]

            # Resolver Many2one: buscar ID por dominio si viene valor de texto
            if m.field_type == 'many2one' and value:
                relation_model = m.relation_model
                if relation_model == 'res.partner' and field_name in ('vat', 'rif'):
                    # Buscar partner por RIF o VAT
                    partner = self.env['res.partner'].search([
                        '|', ('vat', '=', value), ('rif', '=', value)
                    ], limit=1)
                    values[field_name] = partner.id if partner else False
                elif relation_model and field_name in ('client_id', 'obligation_type_id',
                                                       'document_type_id', 'partner_id'):
                    # Buscar por name o código dependiendo del modelo
                    record = self.env[relation_model].search([
                        ('name', '=', value)
                    ], limit=1)
                    values[field_name] = record.id if record else False
                else:
                    values[field_name] = value
            else:
                values[field_name] = value

        return values

    def _import_line(self, line):
        """
        Importa UNA línea usando savepoint para rollback granular.
        Retorna 'created' | 'updated' | 'error'.
        """
        if self.import_type == 'cartelera':
            return self._import_cartelera_line(line)
        
        try:
            with self.env.cr.savepoint():
                # Resolver Many2one según mapping
                values = self._resolve_values(line)
                # Determinar modelo y clave única según import_type
                model_name, unique_domain = self._get_import_target(line, values)
                # Upsert
                record, action = self._upsert_record(model_name, values, unique_domain)
                # Actualizar la línea
                line.write({
                    'state': 'imported' if action == 'created' else 'updated',
                    'record_id': f"{model_name},{record.id}",
                    'record_name': record.display_name,
                    'model_name': model_name,
                })
                return action
        except Exception as e:
            line.write({'state': 'error', 'error_msg': str(e)[:500]})
            return 'error'

    def _import_cartelera_line(self, line):
        """
        Importa una línea de cartelera fiscal.
        
        Crea/actualiza cliente (res.partner + l10n.ve.compliance.client) por RIF
        y genera snapshot de cartelera via generate_snapshot().
        
        Modo strict: si cliente no existe → error.
        Modo lax: crea cliente si no existe.
        """
        try:
            with self.env.cr.savepoint():
                data = line.data or {}
                rif = data.get('rif')
                name = data.get('name')
                year = data.get('year')
                month = data.get('month')
                statuses = data.get('statuses', {})
                
                if not rif:
                    raise UserError(_('RIF vacío en la fila %d') % line.row_index)
                if not name:
                    raise UserError(_('Nombre de empresa vacío en la fila %d') % line.row_index)
                
                # Buscar cliente por RIF
                client = self.env['l10n.ve.compliance.client'].search([
                    ('rif', '=', rif)
                ], limit=1)
                
                if not client:
                    # Buscar partner por VAT (res.partner no tiene campo rif, solo vat)
                    partner = self.env['res.partner'].search([
                        ('vat', '=', rif)
                    ], limit=1)
                    
                    if not partner:
                        if self.mode == 'strict':
                            raise UserError(_(
                                "Cliente con RIF '%s' no existe. En modo estricto no se crean clientes."
                            ) % rif)
                        # Modo lax: crear partner y cliente
                        partner = self.env['res.partner'].create({
                            'name': name,
                            'vat': rif,
                        })
                    
                    # Asegurar company_id (required en compliance.client)
                    company_id = self.company_id.id or self.env.company.id
                    
                    client = self.env['l10n.ve.compliance.client'].create({
                        'name': name,
                        'partner_id': partner.id,
                        'rif': rif,
                        'company_id': company_id,
                    })
                
                # Generar snapshot de cartelera
                cartelera_statuses = self.env['l10n.ve.cartelera.status'].generate_snapshot(
                    client_id=client.id,
                    year=year,
                    month=month,
                    statuses=statuses,
                )
                
                # Actualizar la línea
                line.write({
                    'state': 'imported',
                    'record_id': f"l10n.ve.compliance.client,{client.id}",
                    'record_name': client.display_name,
                    'model_name': 'l10n.ve.compliance.client',
                })
                return 'created'
        except Exception as e:
            line.write({'state': 'error', 'error_msg': str(e)[:500]})
            return 'error'

    def _create_import_log(self, success_count, error_count, skipped_count, records_created):
        """Crea log persistente de importación."""
        import json
        import base64
        from io import BytesIO

        # Generar log Excel de resultados
        import openpyxl
        from openpyxl.styles import Font, PatternFill

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Resultados'

        headers = ['Fila', 'Estado', 'Registro', 'Modelo', 'Error']
        for col_idx, h in enumerate(headers, 1):
            ws.cell(row=1, column=col_idx, value=h).font = Font(bold=True)

        for idx, line in enumerate(self.line_ids, 2):
            ws.cell(row=idx, column=1, value=line.row_index)
            ws.cell(row=idx, column=2, value=line.state)
            ws.cell(row=idx, column=3, value=line.record_name or '')
            ws.cell(row=idx, column=4, value=line.model_name or '')
            ws.cell(row=idx, column=5, value=line.error_msg or '')

        output = BytesIO()
        wb.save(output)

        attachment = self.env['ir.attachment'].create({
            'name': f'log_import_{self.import_type}_{fields.Datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            'datas': base64.b64encode(output.getvalue()),
            'res_model': 'l10n.ve.import.log',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        self.env['l10n.ve.import.log'].create({
            'wizard_id': self.id,
            'import_type': self.import_type,
            'file_name': self.filename,
            'total_rows': len(self.line_ids),
            'success_count': success_count,
            'error_count': error_count,
            'skipped_count': skipped_count,
            'record_ids': json.dumps(records_created),
            'attachment_id': attachment.id,
        })

    def action_reset(self):
        """Reinicia el wizard al estado inicial."""
        self.ensure_one()
        self.line_ids.unlink()
        self.mapping_ids.unlink()
        self.write({
            'file': False,
            'filename': False,
            'template_file': False,
            'filename': False,
            'state': 'draft',
            'preview_exceeded': False,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n.ve.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }