# calcular-retencion-venezuela

## Cuándo usar este skill
Cuando el agente necesite:
- Calcular retenciones de IVA, ISLR o IGTF sobre una factura
- Validar tasas de retención según normativa venezolana
- Generar comprobantes de retención vinculados a account.move

## Reglas de cálculo
- **IVA (75%)**: sobre el monto del impuesto (amount_tax)
  - Ejemplo: factura con IVA 16% sobre base 1000 → amount_tax = 160 → retención = 120
- **ISLR (3%)**: sobre el subtotal (amount_untaxed)
  - Ejemplo: base 1000 → retención = 30
- **IGTF (3%)**: sobre pagos en divisas (si aplica)

## Modelos involucrados
- `l10n.retention`: registra el comprobante
- `account.move`: factura origen (solo move_type = 'in_invoice')
- `l10n.ve.obligation.type`: catálogo con tasas configurables

## Método clave
`account.move.action_generate_retention()`:
1. Verifica move_type == 'in_invoice'
2. Busca tasa ISLR en l10n.ve.obligation.type (fallback 3%)
3. Busca tasa IVA en l10n.ve.obligation.type (fallback 75%)
4. Calcula montos
5. Crea registros en l10n.retention

## Tests asociados
- tests/test_obligation.py::test_generate_retention
- Ver docs/specs/04-retenciones.md para criterios de aceptación

## Referencias
- Providencia SNAT/2025/000091 (calendario SENIAT)
- docs/specs/04-retenciones.md