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
6. **[06-importacion-excel.md](specs/06-importacion-excel.md)** — Wizard de
   importación masiva desde Excel (obligaciones, documentos, clientes,
   retenciones) con validación en 3 niveles y upsert
7. **[07-cartelera-excel.md](specs/07-cartelera-excel.md)** — Importación de la cartelera fiscal desde
    Excel mensual (36 documentos, snapshot por cliente/mes)
8. **[08-evidencias.md](specs/08-evidencias.md)** — Evidencia
   fotográfica de documentos de cartelera + transición
   automática de estado
9. **[09-libro-compras-ventas.md](specs/09-libro-compras-ventas.md)**
   — Libro de Compras/Ventas + Planilla IVA 99030

## Modelos Principales (resumen)
- `l10n.ve.compliance.client` — Cliente multi-empresa, score, status, alertas
- `l10n.ve.institution` — SENIAT, IVSS, INCES, BANAVIH, municipales, SAREN
- `l10n.ve.obligation.type` — Configuración regla vencimiento, alertas, tasas
- `l10n.ve.obligation` — Instancia por período, due_date computed, estado, retención
- `l10n.ve.document.type` / `l10n.ve.document` — Cartelera fiscal
- `l10n.ve.alert` — Notificaciones multi-tipo, multi-canal
- `l10n.retention` — Comprobante retención (secuencia RET-YYYY-NNNN)
- `l10n.ve.import.wizard` / `l10n.ve.import.line` / `l10n.ve.import.mapping`
  / `l10n.ve.import.log` — Wizard de importación Excel (4 modelos)
- `l10n.ve.cartelera.status` — Snapshot mensual de cartelera fiscal
- `l10n.ve.cartelera.evidence` — Evidencia fotográfica con compresión automática
  y límite de tamaño configurable
- `l10n.ve.cartelera.evidence.wizard` — Captura/subida de evidencia al cliente

## Extensiones Core
- `account.move`: `retention_ids`, `retention_amount`, `action_generate_retention()` (solo `in_invoice`)
- `res.partner`: `compliance_client_ids`, `compliance_status`, `document_ids`

## Roadmap

### Fases 1-7: Módulo base (COMPLETADAS)
1. ✅ Scaffold módulo + modelos + security
2. ✅ Vistas list/form/kanban de cada modelo
3. ✅ Cálculo de vencimientos + cron
4. ✅ Sistema de alertas (email + wa.me)
5. ✅ Dashboard contador + reportes PDF
6. ✅ Retenciones + account.move
7. ✅ Datos demo + tests

### Fase 2A-2B: Wizard de importación Excel (COMPLETADA)
- ✅ 2A: Parser de números VE + validación RIF módulo 11
- ✅ 2B.1: `_validate_reference` (validación referencial)
- ✅ 2B.2: `_validate_business` (validación de negocio)
- ✅ 2B.3: `action_import` + `_upsert_record` + savepoints

### Fase A-E: Cartelera Fiscal Excel (COMPLETADA)
- ✅ A: 36 tipos de documento (C01-C36) + institución MINTRA
- ✅ B: Modelo `cartelera.status` + `document_score`
- ✅ C: Parser + import (rama `cartelera` del wizard)
- ✅ D: Vista de brechas + spec 07 + tests
- ✅ E: Parser dinámico (detección fila headers, col RIF, col nombre, rango docs; mapeo posicional C01..C36; manejo duplicados; normalización HTML; validación 30+ cols; warning headers no reconocidos)

### Fase E2: UX visual cartelera fiscal (COMPLETADA)
- ✅ Evidence con compresión automática + límite de tamaño configurable
- ✅ Logo cliente en kanban
- ✅ Mini-cartelera HTML agrupada por institución
- ✅ Kanban extendido con document_score
- ✅ Fix OWL: kanban_image y t-out reemplazados por patrones Odoo 19
- ✅ 63 tests pasando

### Trabajo Futuro
- ⬜ Spec 10: Conciliación ISLR
- ⬜ Fase F: Libro de Compras/Ventas + Planilla IVA 99030
  (spec 09 lista)
- ⬜ Importación de asientos contables (account.move)
- ⬜ Integración MCP Odoo (mart337i/odoo-dev-mcp)

## Estado del Portafolio

- ✅ README.md, CHANGELOG.md, LICENSE (LGPL-3), CONTRIBUTING.md
- ✅ Metodología SDD (AGENTS.md, docs/specs/, opencode.json)
- ✅ 63 tests pasando
- ✅ Comandos OpenCode en `.opencode/commands/`
- ⬜ Capturas de pantalla en docs/screenshots/
- ⬜ Topics GitHub
