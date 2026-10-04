from odoo import api, fields, models
from odoo.tools import image as image_tools


class CarteleraEvidence(models.Model):
    _name = 'l10n.ve.cartelera.evidence'
    _description = 'Evidencia de documento para cartelera fiscal'
    _order = 'uploaded_at desc'

    cartelera_status_id = fields.Many2one(
        'l10n.ve.cartelera.status',
        string='Snapshot Cartelera',
        required=True,
        ondelete='cascade',
    )
    image = fields.Binary(
        string='Imagen',
        attachment=True,
    )
    image_128 = fields.Binary(
        string='Imagen 128x128',
        compute='_compute_image_128',
        store=True,
    )
    uploaded_by = fields.Many2one(
        'res.users',
        string='Subido por',
        default=lambda self: self.env.user,
        readonly=True,
    )
    uploaded_at = fields.Datetime(
        string='Fecha de subida',
        default=fields.Datetime.now,
        readonly=True,
    )
    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptado'),
        ('rejected', 'Rechazado'),
    ], string='Estado', required=True, default='pending')
    notes = fields.Text(string='Notas')

    @api.depends('image')
    def _compute_image_128(self):
        for rec in self:
            rec.image_128 = image_tools.image_process(rec.image, size=(128, 128)) if rec.image else False

    def _notify_status_recompute(self):
        """Notifica al status asociado que debe recalcular su estado."""
        statuses = self.mapped('cartelera_status_id')
        if statuses:
            statuses._recompute_status_from_evidence()

    @api.model_create_multi
    def create(self, vals_list):
        evidences = super().create(vals_list)
        evidences._notify_status_recompute()
        return evidences

    def write(self, vals):
        # Si cambia el state, notificar recompute
        state_changed = 'state' in vals
        result = super().write(vals)
        if state_changed:
            self._notify_status_recompute()
        return result

    def unlink(self):
        # Mapear statuses antes de borrar
        statuses = self.mapped('cartelera_status_id')
        result = super().unlink()
        # Recomputar en statuses afectados
        if statuses:
            statuses._recompute_status_from_evidence()
        return result