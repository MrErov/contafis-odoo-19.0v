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
        today = fields.Date.today()
        for move in self:
            if move.move_type != 'in_invoice':
                continue
            islr_rate = self._get_retention_rate('islr')
            iva_rate = self._get_retention_rate('iva')
            vals_list = []
            if islr_rate:
                vals_list.append({
                    'partner_id': move.partner_id.id,
                    'amount': move.amount_untaxed * islr_rate / 100.0,
                    'currency_id': move.currency_id.id,
                    'date': move.invoice_date or today,
                    'invoice_id': move.id,
                })
            if iva_rate and move.amount_tax:
                vals_list.append({
                    'partner_id': move.partner_id.id,
                    'amount': move.amount_tax * iva_rate / 100.0,
                    'currency_id': move.currency_id.id,
                    'date': move.invoice_date or today,
                    'invoice_id': move.id,
                })
            if vals_list:
                self.env['l10n.retention'].create(vals_list)

    def _get_retention_rate(self, tax_type):
        obligation_type = self.env['l10n.ve.obligation.type'].search([
            ('tax_type', '=', tax_type),
            ('base_calculation', '=', 'purchase'),
            ('rate', '>', 0),
        ], limit=1)
        if obligation_type:
            return obligation_type.rate
        return {'iva': 75.0, 'islr': 3.0}.get(tax_type, 0.0)