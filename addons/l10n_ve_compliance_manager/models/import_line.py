from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class ImportLine(models.TransientModel):
    _name = 'l10n.ve.import.line'
    _description = 'Línea de Importación (Preview + Resultado)'
    _order = 'row_index'

    wizard_id = fields.Many2one(
        'l10n.ve.import.wizard', string='Wizard', required=True,
        ondelete='cascade'
    )
    row_index = fields.Integer(string='Nº Fila', required=True)
    data = fields.Json(string='Datos Parseados')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('validated', 'Validado'),
        ('imported', 'Creado'),
        ('updated', 'Actualizado'),
        ('error', 'Error'),
        ('skipped', 'Omitido'),
    ], string='Estado', default='draft', required=True)
    record_id = fields.Reference(
        selection='_get_reference_models',
        string='Registro Creado/Actualizado'
    )
    record_name = fields.Char(string='Nombre Registro')
    model_name = fields.Char(string='Modelo Destino')
    error_msg = fields.Text(string='Errores')

    def _get_reference_models(self):
        """Modelos que pueden ser referenciados por record_id."""
        return [
            ('l10n.ve.obligation', 'Obligación'),
            ('l10n.ve.document', 'Documento'),
            ('l10n.ve.compliance.client', 'Cliente Cumplimiento'),
            ('l10n.retention', 'Retención'),
        ]

    def _validate_syntax(self):
        """
        Valida tipos de datos según el mapping del wizard.
        Actualiza self.error_msg si falla.
        Retorna True si válido, False si no.
        """
        self.ensure_one()
        wizard = self.wizard_id
        if not wizard or not self.data:
            self.write({'state': 'error', 'error_msg': 'Sin wizard o datos'})
            return False

        errors = []
        data = self.data or {}

        # Obtener mapeos del wizard
        mappings = wizard.mapping_ids.filtered(lambda m: m.field_name)
        for m in mappings:
            value = self.data.get(m.field_name) if self.data else None
            required = m.required
            field_type = m.field_type

            # Validar required
            if required and (value is None or value == ''):
                errors.append(f"Campo '{m.col_name}' ({m.field_name}) es obligatorio")
                continue

            if value is None or value == '':
                continue  # No validar tipo si vacío y no required

            # Validar según tipo
            try:
                if field_type == 'date':
                    fields.Date.to_date(value)
                elif field_type in ('float', 'monetary'):
                    wizard._parse_number(value)
                elif field_type == 'integer':
                    int(value)
                elif field_type == 'many2one':
                    # Validar RIF para res.partner
                    if m.relation_model == 'res.partner' and m.field_name in ('rif', 'client_id'):
                        if not wizard._validate_rif(value):
                            errors.append(f"RIF inválido: '{value}'")
                # char, selection, boolean, text: no validación extra de formato
            except Exception as e:
                errors.append(f"Campo '{m.col_name}' ({m.field_name}): {e}")

        if errors:
            self.write({
                'state': 'error',
                'error_msg': '; '.join(errors)
            })
            return False
        else:
            self.write({'state': 'validated', 'error_msg': False})
            return True