from odoo import api, fields, models


class ComplianceClient(models.Model):
    _name = 'l10n.ve.compliance.client'
    _description = 'Compliance Client'

    name = fields.Char(string='Nombre', required=True)
    partner_id = fields.Many2one('res.partner', string='Contacto', required=True)
    company_id = fields.Many2one('res.company', string='Compañía', required=True)
    accountant_id = fields.Many2one('res.users', string='Contador')
    rif = fields.Char(string='RIF')
    rif_last_digit = fields.Integer(string='Último dígito RIF', compute='_compute_rif_last_digit')
    activity_type = fields.Selection([
        ('comercio', 'Comercio'),
        ('servicios', 'Servicios'),
        ('industria', 'Industria'),
        ('mixto', 'Mixto'),
    ], string='Tipo de actividad')
    municipality = fields.Char(string='Municipio')
    obligation_ids = fields.One2many('l10n.ve.obligation', 'client_id', string='Obligaciones')
    document_ids = fields.One2many('l10n.ve.document', 'client_id', string='Documentos')
    alert_ids = fields.One2many('l10n.ve.alert', 'client_id', string='Alertas')
    compliance_status = fields.Selection([
        ('al_dia', 'Al día'),
        ('pendiente', 'Pendiente'),
        ('vencido', 'Vencido'),
    ], string='Estado de cumplimiento', compute='_compute_compliance_status')
    compliance_score = fields.Float(string='Puntuación de cumplimiento', compute='_compute_compliance_score')
    document_score = fields.Float(
        string='Puntuación documental',
        compute='_compute_document_score',
        help='% de documentos requeridos con estado válido',
    )
    last_alert_date = fields.Datetime(string='Fecha de última alerta')
    pending_alert_count = fields.Integer(string='Alertas pendientes', compute='_compute_pending_alert_count')

    @api.depends('rif')
    def _compute_rif_last_digit(self):
        for client in self:
            digits = [c for c in (client.rif or '') if c.isdigit()]
            client.rif_last_digit = int(digits[-1]) if digits else 0

    @api.depends('obligation_ids.state', 'obligation_ids.due_date')
    def _compute_compliance_status(self):
        today = fields.Date.today()
        for client in self:
            active = client.obligation_ids.filtered(
                lambda obligation: obligation.state != 'cancelled'
            )
            overdue = active.filtered(
                lambda obligation: obligation.state == 'overdue'
                or (
                    obligation.state == 'pending'
                    and obligation.due_date
                    and obligation.due_date < today
                )
            )
            pending = active.filtered(
                lambda obligation: obligation.state == 'pending'
            )
            if overdue:
                client.compliance_status = 'vencido'
            elif pending:
                client.compliance_status = 'pendiente'
            else:
                client.compliance_status = 'al_dia'

    @api.depends('obligation_ids.state', 'obligation_ids.due_date')
    def _compute_compliance_score(self):
        today = fields.Date.today()
        for client in self:
            active = client.obligation_ids.filtered(
                lambda obligation: obligation.state != 'cancelled'
            )
            total = len(active)
            if not total:
                client.compliance_score = 100.0
                continue
            subject = active.filtered(
                lambda obligation: obligation.state == 'overdue'
                or (
                    obligation.state == 'pending'
                    and obligation.due_date
                    and obligation.due_date < today
                )
            )
            client.compliance_score = round((total - len(subject)) * 100.0 / total, 2)

    @api.depends('document_ids.state', 'document_ids.document_type_id')
    def _compute_document_score(self):
        for client in self:
            required_types = self.env['l10n.ve.document.type'].search([
                ('required_for', '=', 'company'),
            ])
            if not required_types:
                client.document_score = 100.0
                continue
            valid_count = 0
            for doc_type in required_types:
                docs = client.document_ids.filtered(
                    lambda d: d.document_type_id == doc_type
                )
                if docs.filtered(lambda d: d.state == 'valid'):
                    valid_count += 1
            client.document_score = round(valid_count * 100.0 / len(required_types), 2)

    @api.depends('alert_ids.state')
    def _compute_pending_alert_count(self):
        for client in self:
            client.pending_alert_count = len(
                client.alert_ids.filtered(
                    lambda alert: alert.state == 'pending'
                )
            )