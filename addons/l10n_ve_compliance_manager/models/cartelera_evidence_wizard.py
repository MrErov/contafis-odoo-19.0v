from odoo import api, fields, models


class CarteleraEvidenceWizard(models.TransientModel):
    _name = 'l10n.ve.cartelera.evidence.wizard'
    _description = 'Wizard para subir evidencia de cartelera'

    cartelera_status_id = fields.Many2one(
        'l10n.ve.cartelera.status',
        string='Snapshot Cartelera',
        required=True,
        default=lambda self: self.env.context.get('default_cartelera_status_id'),
    )
    image = fields.Binary(
        string='Imagen',
        required=True,
        attachment=True,
    )
    notes = fields.Text(string='Notas')

    def action_upload(self):
        """Crea la evidencia y cierra el wizard."""
        self.ensure_one()
        self.env['l10n.ve.cartelera.evidence'].create({
            'cartelera_status_id': self.cartelera_status_id.id,
            'image': self.image,
            'notes': self.notes,
        })
        return {'type': 'ir.actions.act_window_close'}