from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import image as image_tools


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
    filename = fields.Char(string='Nombre del archivo')
    file_size_mb = fields.Float(
        string='Tamaño (MB)',
        compute='_compute_file_size_mb',
        store=False,
    )
    notes = fields.Text(string='Notas')

    @api.depends('image')
    def _compute_file_size_mb(self):
        for rec in self:
            if rec.image:
                import base64
                rec.file_size_mb = len(base64.b64decode(rec.image)) / (1024 * 1024)
            else:
                rec.file_size_mb = 0.0

    @api.model
    def _get_max_size_mb(self):
        """Obtiene el tamaño máximo permitido en MB desde ir.config_parameter."""
        ICP = self.env['ir.config_parameter'].sudo()
        return float(ICP.get_param('l10n_ve_compliance.evidence_max_size_mb', '5.0'))

    def _get_extension(self):
        """Extrae la extensión del filename (sin punto, lowercase)."""
        if not self.filename:
            return ''
        return self.filename.rsplit('.', 1)[-1].lower() if '.' in self.filename else ''

    def _compress_image(self, image_data):
        """Comprime una imagen a 1024x1024 manteniendo aspect ratio.
        
        Args:
            image_data: base64-encoded image data
        Returns:
            base64-encoded compressed image data
        """
        if not image_data:
            return image_data
        import base64
        # Decode base64 to bytes for image_process
        image_bytes = base64.b64decode(image_data)
        compressed_bytes = image_tools.image_process(image_bytes, size=(1024, 1024))
        # Re-encode to base64 for storage
        return base64.b64encode(compressed_bytes).decode()

    def _get_size_mb(self, image_data):
        """Calcula el tamaño en MB de un binario base64."""
        if not image_data:
            return 0.0
        import base64
        return len(base64.b64decode(image_data)) / (1024 * 1024)

    def action_upload(self):
        """Crea la evidencia y cierra el wizard con validación y compresión."""
        self.ensure_one()

        ext = self._get_extension()
        image_data = self.image
        max_mb = self._get_max_size_mb()

        # 1. Si es imagen soportada, comprimir
        if ext in ('jpg', 'jpeg', 'png', 'webp'):
            image_data = self._compress_image(self.image)
        # 2. Si es PDF, no comprimir
        elif ext == 'pdf':
            pass  # usar image tal cual
        # 3. Si extensión no reconocible o sin filename, no comprimir
        else:
            pass  # usar image tal cual

        # 4. Validar tamaño del archivo final (post-compresión si aplica)
        size_mb = self._get_size_mb(image_data)
        if size_mb > max_mb:
            raise UserError(
                f"El archivo '{self.filename or 'sin nombre'}' pesa "
                f"{size_mb:.1f} MB y supera el límite de "
                f"{max_mb:.1f} MB. Reduce su tamaño antes de subir."
            )

        # 5. Rechazar formatos no soportados (solo después de validar tamaño)
        if ext not in ('jpg', 'jpeg', 'png', 'webp', 'pdf'):
            raise UserError(
                "Formato no soportado. Sube una imagen "
                "(JPG/PNG/WEBP) o un PDF."
            )

        # 6. Crear la evidence
        self.env['l10n.ve.cartelera.evidence'].create({
            'cartelera_status_id': self.cartelera_status_id.id,
            'filename': self.filename,
            'image': image_data,
            'notes': self.notes,
        })
        return {'type': 'ir.actions.act_window_close'}