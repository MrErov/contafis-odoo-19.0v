from odoo import fields, models


class VeObligationType(models.Model):
    _name = 'l10n.ve.obligation.type'
    _description = 'Tipo de obligación'

    name = fields.Char(string='Nombre', required=True)
    institution_id = fields.Many2one('l10n.ve.institution', string='Institución')
    category = fields.Selection([
        ('fiscal_nacional', 'Fiscal Nacional'),
        ('parafiscal', 'Parafiscal'),
        ('municipal', 'Municipal'),
        ('documental', 'Documental'),
    ], string='Categoría')
    tax_type = fields.Selection([
        ('iva', 'IVA'),
        ('islr', 'ISLR'),
        ('igtf', 'IGTF'),
        ('municipal', 'Municipal'),
        ('ivss', 'IVSS'),
        ('inces', 'INCES'),
        ('banavih', 'BANAVIH'),
        ('otro', 'Otro'),
    ], string='Tipo de impuesto')
    periodicity = fields.Selection([
        ('monthly', 'Mensual'),
        ('bimonthly', 'Bimestral'),
        ('trimestral', 'Trimestral'),
        ('anual', 'Anual'),
        ('event', 'Evento'),
    ], string='Periodicidad')
    due_day_rule = fields.Selection([
        ('1-15', 'Días 01-15'),
        ('primeros_5_dias_habiles', 'Primeros 5 días hábiles'),
        ('ultimo_digito_rif', 'Último dígito RIF'),
        ('dia_fijo', 'Día fijo'),
    ], string='Regla de vencimiento')
    due_day_value = fields.Integer(string='Valor de día de vencimiento')
    base_calculation = fields.Selection([
        ('invoice', 'Sobre facturación'),
        ('payroll', 'Sobre nómina'),
        ('purchase', 'Sobre compras'),
        ('gross_income', 'Sobre ingresos brutos'),
        ('fixed', 'Monto fijo'),
    ], string='Base de cálculo')
    rate = fields.Float(string='Tasa (%)')
    currency_id = fields.Many2one('res.currency', string='Moneda')
    alert_days_before = fields.Integer(string='Días de alerta previa')
    alert_channel = fields.Selection([
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('both', 'Ambos'),
    ], string='Canal de alerta')
    alert_enabled = fields.Boolean(string='Alertas activadas')
    alert_on_overdue = fields.Boolean(string='Alertar al vencer')
    alert_on_missing_payment = fields.Boolean(string='Alertar por falta de pago')