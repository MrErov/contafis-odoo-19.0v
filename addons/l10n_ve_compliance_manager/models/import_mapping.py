from odoo import fields, models


class ImportMapping(models.TransientModel):
    _name = 'l10n.ve.import.mapping'
    _description = 'Mapeo de Columnas Excel a Campos Odoo'
    _order = 'col_index'

    wizard_id = fields.Many2one(
        'l10n.ve.import.wizard', string='Wizard', required=True,
        ondelete='cascade'
    )
    col_index = fields.Integer(string='Índice Columna', required=True)
    column_letter = fields.Char(string='Letra Columna', required=True)
    col_name = fields.Char(string='Nombre en Excel', required=True)
    field_name = fields.Char(string='Campo Odoo')
    field_type = fields.Char(string='Tipo Campo')
    required = fields.Boolean(string='Obligatorio', default=False)
    relation_model = fields.Char(string='Modelo Relacionado')
    default_value = fields.Text(string='Valor por Defecto')

    _unique_col_per_wizard = models.Constraint(
        'UNIQUE(wizard_id, col_index)',
        'Cada columna solo puede mapearse una vez por wizard.',
    )
