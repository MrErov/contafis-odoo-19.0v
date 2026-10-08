from odoo import fields, models


class VeInstitution(models.Model):
    _name = 'l10n.ve.institution'
    _description = 'Institución'

    name = fields.Char(string='Nombre', required=True)
    type = fields.Selection([
        ('seniat', 'SENIAT'),
        ('ivss', 'IVSS'),
        ('inces', 'INCES'),
        ('banavih', 'BANAVIH'),
        ('municipal', 'Municipal'),
        ('mintra', 'MINTRA'),
        ('saren', 'SAREN'),
        ('otro', 'Otro'),
    ], string='Tipo')
    rif = fields.Char(string='RIF')
    contact_info = fields.Text(string='Información de contacto')
    portal_url = fields.Char(string='URL del portal')
