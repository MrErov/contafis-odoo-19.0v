from odoo import fields, models


class VeDocument(models.Model):
    _name = 'l10n.ve.document'
    _description = 'Documento'

    client_id = fields.Many2one('l10n.ve.compliance.client', string='Cliente')
    obligation_id = fields.Many2one('l10n.ve.obligation', string='Obligación')
    partner_id = fields.Many2one('res.partner', string='Contacto')
    document_type_id = fields.Many2one('l10n.ve.document.type', string='Tipo de documento')
    number = fields.Char(string='Número')
    issue_date = fields.Date(string='Fecha de emisión')
    expiry_date = fields.Date(string='Fecha de vencimiento')
    attachment = fields.Binary(string='Archivo adjunto')
    state = fields.Selection([
        ('valid', 'Válido'),
        ('expired', 'Expirado'),
        ('pending', 'Pendiente'),
        ('rejected', 'Rechazado'),
    ], string='Estado')
    last_alert_date = fields.Datetime(string='Fecha de última alerta')
    notes = fields.Text(string='Notas')

    def _generate_document_alerts(self, now):
        today = fields.Date.today()
        for document in self:
            if document.expiry_date and document.expiry_date < today:
                document.state = 'expired'
                continue
            days = document.document_type_id.renewal_alert_days or 30
            if document.expiry_date and (document.expiry_date - today).days <= days:
                document._create_document_alert('document_expiring', now)

    def _create_document_alert(self, alert_type, now):
        client = self.client_id
        if not client:
            return
        alert_obj = self.env['l10n.ve.alert']
        recipients = client.partner_id
        channel = 'email'
        if self.document_type_id and self.document_type_id.alert_channel:
            channel = self.document_type_id.alert_channel
        for channel_name in self.env['l10n.ve.obligation']._get_alert_channels(channel):
            exists = alert_obj.search([
                ('client_id', '=', client.id),
                ('document_id', '=', self.id),
                ('alert_type', '=', alert_type),
                ('channel', '=', channel_name),
                ('state', 'in', ('pending', 'sent')),
            ])
            if exists:
                continue
            message = 'Documento: {} ({}). Vence: {}'.format(
                self.number or '',
                self.document_type_id.name if self.document_type_id else '',
                self.expiry_date,
            )
            alert = alert_obj.create({
                'name': '{} - {} - {}'.format(
                    client.name,
                    self.env['l10n.ve.obligation'].ALERT_TYPE_LABELS.get(
                        alert_type, alert_type
                    ),
                    self.number or self.expiry_date,
                ),
                'client_id': client.id,
                'document_id': self.id,
                'alert_type': alert_type,
                'date': now,
                'channel': channel_name,
                'recipient_ids': [(6, 0, recipients.ids)],
                'message': message,
            })
            self.env['l10n.ve.obligation']._send_alert(alert)