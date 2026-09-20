from odoo import fields, models


class VeDocumentType(models.Model):
    _name = 'l10n.ve.document.type'
    _description = 'Tipo de documento'

    name = fields.Char(string='Nombre', required=True)
    institution_id = fields.Many2one('l10n.ve.institution', string='Institución')
    validity_days = fields.Integer(string='Días de validez')
    renewal_alert_days = fields.Integer(string='Días de alerta de renovación')
    required_for = fields.Selection([
        ('company', 'Compañía'),
        ('partner', 'Contacto'),
        ('employee', 'Empleado'),
    ], string='Requerido para')
    alert_channel = fields.Selection([
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('both', 'Ambos'),
    ], string='Canal de alerta')