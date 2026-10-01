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
    ]

    import_type = fields.Selection(
        IMPORT_TYPES, string='Tipo de Importación', required=True,
        default='obligation'
    )
    file = fields.Binary(string='Archivo Excel', required=True)
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

    def action_load_file(self):
        """Carga el archivo Excel, lee headers y crea mapeo automático."""
        self.ensure_one()
        if not self.file:
            raise UserError(_('Debe subir un archivo Excel.'))

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

    def _normalize(self, text):
        """Normaliza texto para comparación (minúsculas, sin espacios, sin acentos)."""
        import unicodedata
        if not text:
            return ''
        text = str(text).strip().lower()
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        return text.replace(' ', '_').replace('-', '_')

    def action_preview(self):
        """Genera preview de las primeras N filas."""
        self.ensure_one()
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
        """Ejecuta la importación real (upsert batch con savepoints)."""
        self.ensure_one()
        if self.mode == 'strict' and self.line_ids.filtered(lambda l: l.state == 'error'):
            raise UserError(_('Modo estricto: hay errores. Corríjalos antes de importar.'))

        lines_to_process = self.line_ids.filtered(
            lambda l: l.state in ('validated', 'draft')
        )
        success_count = 0
        error_count = 0
        skipped_count = 0
        records_created = []

        for line in lines_to_process:
            try:
                with self.env.cr.savepoint():
                    record = self._import_line(line)
                    if record:
                        line.write({
                            'state': 'imported',
                            'record_id': f'{record._name},{record.id}',
                            'record_name': record.display_name,
                            'model_name': record._name,
                            'error_msg': False,
                        })
                        records_created.append({
                            'model': record._name,
                            'id': record.id,
                            'name': record.display_name,
                        })
                        success_count += 1
                    else:
                        line.write({'state': 'skipped'})
                        skipped_count += 1
            except Exception as e:
                line.write({'state': 'error', 'error_msg': str(e)})
                error_count += 1
                if self.mode == 'strict':
                    raise

        # Crear log persistente
        self._create_import_log(success_count, error_count, skipped_count, records_created)

        self.state = 'done'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n.ve.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _import_line(self, line):
        """Importa una línea según el import_type. Retorna registro creado/actualizado."""
        # Placeholder: lógica específica por import_type se implementa en Fase 2
        return None

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