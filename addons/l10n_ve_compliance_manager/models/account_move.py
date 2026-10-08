from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    retention_ids = fields.One2many('l10n.retention', 'invoice_id', string='Retenciones')
    retention_amount = fields.Monetary(
        string='Monto retenido',
        compute='_compute_retention_amount',
        currency_field='currency_id',
    )
    obligation_ids = fields.One2many('l10n.ve.obligation', 'move_id', string='Obligaciones')

    @api.depends('retention_ids.amount')
    def _compute_retention_amount(self):
        for move in self:
            move.retention_amount = sum(move.retention_ids.mapped('amount'))

    def action_generate_retention(self):
        service = self.env['l10n.ve.retention.service']
        for move in self:
            service.generate_retentions(move)
