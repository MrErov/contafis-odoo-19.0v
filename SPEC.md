# Proyecto: l10n_ve_compliance_manager
Módulo Odoo 19.0 para gestión de cumplimiento fiscal, parafiscal y documental
para contadores en Venezuela. Multi-cliente (el contador gestiona varias empresas).

## Stack
- Odoo 19.0 Community
- Python 3.10+, PostgreSQL 14+
- Dependencias: base, account, mail, l10n_ve

## Convenciones Odoo 19 (OBLIGATORIO)
- Usar `<list>` NO `<tree>`
- Usar `invisible="campo != 'valor'"` NO `states`
- `view_mode="list,form"`
- Sin `expand=` en search views
- Seguir API Odoo 19 (no usar `attrs=`)

## Índice de Especificaciones por Capacidad (SDD)
1. **[01-calendario-seniat.md](specs/01-calendario-seniat.md)** — Cálculo vencimientos SENIAT 2026 por dígito RIF + reglas genéricas
2. **[02-gestion-alertas.md](specs/02-gestion-alertas.md)** — Motor de alertas multi-canal (email + wa.me) + cron diario
3. **[03-cartelera-fiscal.md](specs/03-cartelera-fiscal.md)** — Documentos legales: vigencia, renovación, alertas expiración/faltantes
4. **[04-retenciones.md](specs/04-retenciones.md)** — Retenciones IVA/ISLR/IGTF en facturas proveedor + extensión account.move
5. **[05-dashboard-reportes.md](specs/05-dashboard-reportes.md)** — Dashboard contador (kanban semáforos, score, PDF)

## Modelos Principales (resumen)
- `l10n.ve.compliance.client` — Cliente multi-empresa, score, status, alertas
- `l10n.ve.institution` — SENIAT, IVSS, INCES, BANAVIH, municipales, SAREN
- `l10n.ve.obligation.type` — Configuración regla vencimiento, alertas, tasas
- `l10n.ve.obligation` — Instancia por período, due_date computed, estado, retención
- `l10n.ve.document.type` / `l10n.ve.document` — Cartelera fiscal
- `l10n.ve.alert` — Notificaciones multi-tipo, multi-canal
- `l10n.retention` — Comprobante retención (secuencia RET-YYYY-NNNN)

## Extensiones Core
- `account.move`: `retention_ids`, `retention_amount`, `action_generate_retention()` (solo `in_invoice`)
- `res.partner`: `compliance_client_ids`, `compliance_status`, `document_ids`

## Roadmap (Estado: Fase 7 completada)
1. ✅ Scaffold módulo + modelos + security
2. ✅ Vistas list/form/kanban de cada modelo
3. ✅ Cálculo de vencimientos + cron
4. ✅ Sistema de alertas (email + wa.me)
5. ✅ Dashboard contador + reportes PDF
6. ✅ Retenciones + account.move
7. ✅ Datos demo + tests (5/5 passing)

## Próximos Pasos (Portafolio / SDD)
- Refactor docs → specs/ (completado)
- README.md, CHANGELOG.md, LICENSE (LGPL-3), CONTRIBUTING.md
- Capturas pantalla en docs/screenshots/
- Topics GitHub + skills mart337i/odoo-skills + MCP Odoo