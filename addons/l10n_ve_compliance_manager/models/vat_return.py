from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class VatReturn(models.Model):
    _name = 'l10n.ve.vat.return'
    _description = 'Planilla IVA 99030 (Forma 99030 SENIAT)'
    _order = 'period_month desc, company_id'

    period_month = fields.Char(
        string='Período (YYYY-MM)',
        required=True,
        index=True,
        help='Formato: 2026-08',
    )

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('loaded', 'Cargado desde Libro'),
        ('calculated', 'Calculado'),
    ], string='Estado', default='draft', readonly=True)

    # DÉBITOS (ítems 40-49, 13 campos)
    item_40 = fields.Float(string='Item 40 - Ventas no sujetas', digits='Account', default=0.0)
    item_41 = fields.Float(string='Item 41 - Exportaciones', digits='Account', default=0.0)
    item_42 = fields.Float(string='Item 42 - Base gravada 16%', digits='Account', default=0.0)
    item_43 = fields.Float(string='Item 43 - IVA 16% ventas', digits='Account', default=0.0)
    item_442 = fields.Float(string='Item 442 - Base gravada + adicional', digits='Account', default=0.0)
    item_443 = fields.Float(string='Item 443 - Base alícuota reducida (8%)', digits='Account', default=0.0)
    item_452 = fields.Float(string='Item 452 - IVA adicional', digits='Account', default=0.0)
    item_453 = fields.Float(string='Item 453 - IVA reducido (8%)', digits='Account', default=0.0)
    item_46 = fields.Float(string='Item 46 - Total bases ventas', digits='Account', default=0.0, help='Computado: suma item_40 a item_443')
    item_47 = fields.Float(string='Item 47 - Total IVA ventas', digits='Account', default=0.0, help='Computado: item_43 + item_452 + item_453')
    item_48 = fields.Float(string='Item 48 - Ajuste a débitos', digits='Account', default=0.0)
    item_80 = fields.Float(string='Item 80 - Ajuste por prorrata', digits='Account', default=0.0)
    item_49 = fields.Float(string='Item 49 - Total débitos', digits='Account', default=0.0, help='Computado: item_47 + item_48 - item_80')

    # CRÉDITOS (ítems 30-39, 24 campos)
    item_30 = fields.Float(string='Item 30 - Compras sin crédito fiscal', digits='Account', default=0.0)
    item_31 = fields.Float(string='Item 31 - Importaciones', digits='Account', default=0.0)
    item_32 = fields.Float(string='Item 32 - Base gravada 16% importaciones', digits='Account', default=0.0)
    item_312 = fields.Float(string='Item 312 - Base gravada + adicional importaciones', digits='Account', default=0.0)
    item_313 = fields.Float(string='Item 313 - Base reducida importaciones', digits='Account', default=0.0)
    item_322 = fields.Float(string='Item 322 - IVA 16% importaciones', digits='Account', default=0.0)
    item_323 = fields.Float(string='Item 323 - IVA adicional importaciones', digits='Account', default=0.0)
    item_33 = fields.Float(string='Item 33 - Base gravada 16% compras', digits='Account', default=0.0)
    item_34 = fields.Float(string='Item 34 - IVA 16% compras', digits='Account', default=0.0)
    item_332 = fields.Float(string='Item 332 - Base gravada + adicional compras', digits='Account', default=0.0)
    item_333 = fields.Float(string='Item 333 - Base reducida (8%) compras', digits='Account', default=0.0)
    item_342 = fields.Float(string='Item 342 - IVA adicional compras', digits='Account', default=0.0)
    item_343 = fields.Float(string='Item 343 - IVA reducido (8%) compras', digits='Account', default=0.0)
    item_35 = fields.Float(string='Item 35 - Total bases compras', digits='Account', default=0.0, help='Computado: suma item_30 a item_343')
    item_36 = fields.Float(string='Item 36 - Total IVA compras', digits='Account', default=0.0, help='Computado: item_32+item_322+item_323+item_34+item_342+item_343')
    item_37 = fields.Float(string='Item 37 - Créditos por prorrata', digits='Account', default=0.0)
    item_70 = fields.Float(string='Item 70 - Otros créditos', digits='Account', default=0.0)
    item_38 = fields.Float(string='Item 38 - Ajuste a créditos', digits='Account', default=0.0)
    item_71 = fields.Float(string='Item 71 - Excedente período anterior', digits='Account', default=0.0)
    item_20 = fields.Float(string='Item 20 - Excedente arrastre (item_60 anterior)', digits='Account', default=0.0)
    item_21 = fields.Float(string='Item 21 - Ajuste excedente anterior', digits='Account', default=0.0)
    item_81 = fields.Float(string='Item 81 - Prorrata excedente anterior', digits='Account', default=0.0)
    item_82 = fields.Float(string='Item 82 - Ajuste prorrata', digits='Account', default=0.0)
    item_39 = fields.Float(string='Item 39 - Total créditos', digits='Account', default=0.0, help='Computado: item_71 + item_20 - item_21 - item_81 + item_38 - item_82')

    # AUTOLIQUIDACIÓN (ítems 53-90, 22 campos - filas 27-48 de la Forma 99030)
    item_53 = fields.Float(string='Item 53 - IVA a pagar', digits='Account', default=0.0)
    item_60 = fields.Float(string='Item 60 - Excedente crédito fiscal', digits='Account', default=0.0)
    item_22 = fields.Float(string='Item 22 - Excedente a favor', digits='Account', default=0.0)
    item_51 = fields.Float(string='Item 51 - Pago parcial', digits='Account', default=0.0)
    item_24 = fields.Float(string='Item 24 - Saldo a favor', digits='Account', default=0.0)
    item_78 = fields.Float(string='Item 78 - Intereses', digits='Account', default=0.0)
    item_54 = fields.Float(string='Item 54 - Multas', digits='Account', default=0.0)
    item_66 = fields.Float(string='Item 66 - Retenciones IVA período', digits='Account', default=0.0)
    item_72 = fields.Float(string='Item 72 - Total a pagar', digits='Account', default=0.0)
    item_73 = fields.Float(string='Item 73 - Total pagado', digits='Account', default=0.0)
    item_74 = fields.Float(string='Item 74 - Diferencia', digits='Account', default=0.0)
    item_55 = fields.Float(string='Item 55 - IVA retenido por tercero', digits='Account', default=0.0)
    item_67 = fields.Float(string='Item 67 - IVA percibido', digits='Account', default=0.0)
    item_56 = fields.Float(string='Item 56 - Base IVA percibido', digits='Account', default=0.0)
    item_57 = fields.Float(string='Item 57 - IVA sujeto a percepción', digits='Account', default=0.0)
    item_68 = fields.Float(string='Item 68 - Total percepciones', digits='Account', default=0.0)
    item_75 = fields.Float(string='Item 75 - Compensaciones', digits='Account', default=0.0)
    item_76 = fields.Float(string='Item 76 - Ajustes varios', digits='Account', default=0.0)
    item_77 = fields.Float(string='Item 77 - Créditos varios', digits='Account', default=0.0)
    item_58 = fields.Float(string='Item 58 - Total ajustes', digits='Account', default=0.0)
    item_69 = fields.Float(string='Item 69 - Saldo final', digits='Account', default=0.0)
    item_90 = fields.Float(string='Item 90 - Observaciones', digits='Account', default=0.0)

    _sql_constraints = [
        ('unique_return', 'UNIQUE(company_id, period_month)',
         'Ya existe una declaración IVA 99030 para esta compañía y período.'),
    ]

    def action_load_from_book(self):
        """Carga los ítems desde las líneas del libro de compras/ventas del período."""
        self.ensure_one()

        BookLine = self.env['l10n.ve.vat.book.line']
        domain = [
            ('period_month', '=', self.period_month),
            ('company_id', '=', self.company_id.id),
        ]
        lines = BookLine.search(domain)

        if not lines:
            self.state = 'loaded'
            return True

        # Resetear items a 0 antes de cargar
        item_fields = [f for f in self._fields if f.startswith('item_')]
        self.write({f: 0.0 for f in item_fields})

        # Agrupar por operation_code y book_type
        for line in lines:
            op_code = line.operation_code
            sign = 1  # todas las líneas del libro ya tienen signo según tipo factura

            if line.book_type == 'sale':
                if op_code == '40':
                    self.item_40 += sign * (line.base_not_subject + line.base_not_taxed)
                elif op_code == '41':
                    self.item_41 += sign * line.base_not_taxed
                elif op_code == '42':
                    self.item_42 += sign * line.base_general
                    self.item_43 += sign * line.vat_general
                elif op_code == '442':
                    self.item_442 += sign * line.base_general
                    self.item_452 += sign * line.vat_general
                elif op_code == '443':
                    self.item_443 += sign * line.base_reduced
                    self.item_453 += sign * line.vat_reduced

            elif line.book_type == 'purchase':
                if op_code == '30':
                    self.item_30 += sign * (line.base_no_credit + line.base_not_subject + line.base_not_taxed)
                elif op_code == '33':
                    self.item_33 += sign * line.base_general
                    self.item_34 += sign * line.vat_general
                elif op_code == '332':
                    self.item_332 += sign * line.base_general
                    self.item_342 += sign * line.vat_general
                elif op_code == '333':
                    self.item_333 += sign * line.base_reduced
                elif op_code == '343':
                    self.item_343 += sign * line.vat_reduced

        # Retenciones: item_66 = IVA retenido por comprador (direction = by_buyer)
        retenciones_venta = lines.filtered(lambda l: l.retention_direction == 'by_buyer')
        self.item_66 = sum(retenciones_venta.mapped('vat_retained'))

        # Computar agregados
        self._compute_aggregates()

        # Calcular arrastre de excedente
        self._compute_excedente_arrastre()

        self.state = 'loaded'
        return True

    def _compute_aggregates(self):
        """Calcula los campos agregados (item_46, 47, 49, 35, 36, 39)."""
        # Débitos
        self.item_46 = (self.item_40 + self.item_41 + self.item_42 +
                        self.item_442 + self.item_443)
        self.item_47 = self.item_43 + self.item_452 + self.item_453
        self.item_49 = self.item_47 + self.item_48 - self.item_80

        # Créditos
        self.item_35 = (self.item_30 + self.item_31 + self.item_32 +
                        self.item_312 + self.item_313 + self.item_322 +
                        self.item_323 + self.item_33 + self.item_332 +
                        self.item_333 + self.item_342 + self.item_343)
        self.item_36 = (self.item_32 + self.item_322 + self.item_323 +
                        self.item_34 + self.item_342 + self.item_343)

        # item_70 = Total créditos fiscales deducibles = IVA compras (item_36)
        self.item_70 = self.item_36
        # item_71 = Total créditos fiscales deducibles = item_70 + prorrata (item_37)
        self.item_71 = self.item_70 + self.item_37

        # item_39 = Total créditos = item_71 + item_20 - item_21 - item_81 + item_38 - item_82
        self.item_39 = (self.item_71 + self.item_20 - self.item_21 -
                        self.item_81 + self.item_38 - self.item_82)

    def _compute_excedente_arrastre(self):
        """
        Calcula excedente (item_60) y arrastra a item_20 del mes siguiente.
        item_60 = max(0, item_39 - item_49)
        Si item_60 > 0 → buscar return mes siguiente y setear su item_20
        Si item_60 < 0 → item_53 = abs(item_60) (pago)
        """
        self.ensure_one()
        excedente = self.item_39 - self.item_49
        self.item_60 = max(0.0, excedente)
        if excedente < 0:
            self.item_53 = abs(excedente)
        else:
            self.item_53 = 0.0

        # Buscar return del mes siguiente y actualizar item_20
        if self.item_60 > 0:
            try:
                year, month = map(int, self.period_month.split('-'))
                if month == 12:
                    next_period = f'{year + 1}-01'
                else:
                    next_period = f'{year}-{month + 1:02d}'

                next_return = self.search([
                    ('company_id', '=', self.company_id.id),
                    ('period_month', '=', next_period),
                ], limit=1)

                if next_return:
                    next_return.item_20 = self.item_60
                    next_return._compute_excedente_arrastre()  # Recalcular en cascada
            except Exception:
                pass

    def action_calculate(self):
        """Recalcula todos los agregados y autoliquidación."""
        self.ensure_one()
        self._compute_aggregates()
        self._compute_excedente_arrastre()
        self.state = 'calculated'
        return True

    def action_open_book_lines(self):
        """Abre las líneas del libro del período."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Líneas del Libro IVA',
            'res_model': 'l10n.ve.vat.book.line',
            'view_mode': 'list,form,pivot',
            'domain': [
                ('period_month', '=', self.period_month),
                ('company_id', '=', self.company_id.id),
            ],
        }