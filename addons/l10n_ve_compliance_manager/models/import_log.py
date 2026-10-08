from odoo import fields, models


class ImportLog(models.Model):
    _name = 'l10n.ve.import.log'
    _description = 'Log de Auditoría de Importaciones'
    _order = 'date desc'

    wizard_id = fields.Char(
        string='Wizard ID', help='ID del wizard origen (TransientModel)'
    )
    user_id = fields.Many2one(
        'res.users', string='Usuario', default=lambda self: self.env.user,
        required=True, readonly=True
    )
    date = fields.Datetime(
        string='Fecha', default=fields.Datetime.now, readonly=True
    )
    import_type = fields.Char(string='Tipo de Importación', readonly=True)
    file_name = fields.Char(string='Archivo', readonly=True)
    total_rows = fields.Integer(string='Total Filas', readonly=True)
    success_count = fields.Integer(string='Éxitos', readonly=True)
    error_count = fields.Integer(string='Errores', readonly=True)
    skipped_count = fields.Integer(string='Omitidos', readonly=True)
    record_ids = fields.Text(
        string='IDs de Registros',
        help='JSON con [{model, id, name}, ...] para futuro "Deshacer"'
    )
    attachment_id = fields.Many2one(
        'ir.attachment', string='Adjunto', readonly=True,
        help='Archivo original + log de resultados'
    )
