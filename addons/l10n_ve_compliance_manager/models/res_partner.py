from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    compliance_client_ids = fields.One2many('l10n.ve.compliance.client', 'partner_id', string='Clientes de cumplimiento')
    compliance_status = fields.Selection([
        ('al_dia', 'Al día'),
        ('pendiente', 'Pendiente'),
        ('vencido', 'Vencido'),
    ], string='Estado de cumplimiento')
    document_ids = fields.One2many('l10n.ve.document', 'partner_id', string='Documentos')