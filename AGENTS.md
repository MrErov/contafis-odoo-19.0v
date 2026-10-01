# AGENTS.md

## Project Overview
Módulo Odoo 19.0 para gestión de cumplimiento fiscal, parafiscal y documental en Venezuela.
Multi-cliente: un contador gestiona varias empresas desde una sola instancia.
Ver SPEC.md para especificaciones técnicas completas.

## Repo Map
- `addons/l10n_ve_compliance_manager/` → Código del módulo Odoo
- `docs/` → Documentación interna (memory.md, specs/)
- `docker-compose.yml`, `odoo.conf.example` → Setup de desarrollo
- `tests/` → Pruebas unitarias

## Build & Test Commands
```bash
# Levantar Odoo
docker compose up -d

# Instalar módulo
docker compose run --rm web odoo -d contea -i l10n_ve_compliance_manager --stop-after-init --workers 0

# Actualizar módulo
docker compose run --rm web odoo -d contea -u l10n_ve_compliance_manager --stop-after-init --workers 0

# Correr tests
docker compose run --rm web odoo -d contea \
  -u l10n_ve_compliance_manager \
  --test-enable --stop-after-init --workers 0 \
  --test-tags /l10n_ve_compliance_manager

# Ver logs
docker compose logs -f web
```

## Odoo 19.0 Conventions (OBLIGATORIO)
- Usar `<list>` NO `<tree>`
- Usar `invisible="campo != 'valor'"` NO `states` ni `attrs`
- `view_mode="list,form"`
- Sin `expand=` en search views
- `@api.depends` explícito en computed fields
- `inverse` en computed stored editables
- No usar `attrs=` ni `states=` (deprecados en Odoo 17+)

## Workflow Rules
- Antes de tocar código, leer `docs/specs/[capacidad].md` correspondiente.
- Consultar `docs/memory.md` para decisiones ya tomadas. NO preguntar lo ya resuelto.
- NO tocar archivos fuera de `addons/l10n_ve_compliance_manager/` sin autorización.
- NO commitear secrets (`odoo.conf`, `.env`, `filestore/`).
- Commits en inglés con Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`.

## Skills Disponibles
- `odoo-code-review`: revisar código contra guías Odoo
- `odoo-grill-me`: stress-test de planes Odoo
- `calcular-retencion-venezuela`: lógica ISLR/IVA/IGTF (creado)

## Memory
Consultar `docs/memory.md` para:
- Estado actual del proyecto
- Decisiones técnicas tomadas
- Convenciones específicas
- Pendientes

## Reference Files
- `SPEC.md` → índice de capacidades
- `docs/specs/01-calendario-seniat.md` → vencimientos
- `docs/specs/02-gestion-alertas.md` → alertas
- `docs/specs/03-cartelera-fiscal.md` → documentos
- `docs/specs/04-retenciones.md` → retenciones
- `docs/specs/05-dashboard-reportes.md` → dashboard y reportes
- `docs/memory.md` → decisiones y contexto