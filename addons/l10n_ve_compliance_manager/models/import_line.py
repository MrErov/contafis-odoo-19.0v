from odoo import fields, models


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