# Memory - Decisiones y Contexto del Proyecto

## Estado Actual
- **Fase**: Fase 1-7 + Fase 2A/2B + Fases A-E cartelera fiscal + **Fase E2 (UX visual cartelera) COMPLETADA** ✅ + **Fase G (Import Libro Compras/Ventas) COMPLETADA** ✅ + **Fase G.10 (Export bidireccional) COMPLETADA** ✅ + **DevOps.1c (Clean ruff: F601, E741, UP038, F841) COMPLETADA** ✅.
- **Repo**: https://github.com/MrErov/contafis-odoo-19.0v (público)
- **Tests**: 107/107 pasando en Odoo 19.0 + PostgreSQL 14 vía Docker
- **Módulo**: 10 modelos + 2 extensiones + wizard de importación (4 modelos) + cartelera status + evidence + evidence wizard + vat.book.line + vat.return + vat.book.export.wizard
- **Último commit**: e5464da refactor: remove unused variables (F841) + fix lint warnings
- **Próxima fase**: Trabajo Futuro (asientos contables, MCP Odoo, spec 11 conciliación ISLR, Playwright E2E)
- **MCP**: integración con mart337i/odoo-dev-mcp (pendiente)

## Decisiones Técnicas
  
| Fecha | Decisión | Razón |
|-------|----------|-------|
| 2026-09-26 | WhatsApp via wa.me (sin API Meta) | Costo cero, sin dependencia de Business API, suficiente para alertas puntuales |
| 2026-09-26 | Calendario SENIAT 2026 en código (`SENIAT_2026_CALENDAR` dict) | XML solo referencia; lógica de días 1-15 por dígito RIF requiere computación |
| 2026-09-26 | Nemotron 3 Ultra para docs (1M contexto) | Ventana de contexto amplia para SPEC.md + código + memory en una sola pasada |
| 2026-09-26 | No usar Odoo 20 aún | Odoo 19 LTS con soporte hasta 2028; Odoo 20 introduce cambios mayores (API JSON/2, OWL 3, IA agéntica) que requieren refactor |
| 2026-09-26 | Repo público en GitHub | Portafolio profesional; URL: https://github.com/MrErov/contafis-odoo |
| 2026-09-26 | Aplicar metodología SDD + AGENTS.md + memory.md + skills | Mejorar flujo de trabajo con IA, encapsular lógica, evitar repetir decisiones |
| 2026-10-01 | Importación Excel en MVP sin asientos contables | El contador venezolano trabaja en Excel; asientos requieren cuadre debe/haber, líneas múltiples, complejidad muy alta; fuera de MVP |
| 2026-10-01 | Modelos importación: wizard + mapping + line + log (4, no 5) | Fusionar preview + result en `l10n.ve.import.line` unificado; simplifica arquitectura y reduce modelos transientes |
| 2026-10-01 | Claves upsert: client+type+period, client+type+number, rif, invoice+partner | Los campos `name` son secuenciales automáticos; claves de negocio evitan duplicados reales |
| 2026-10-01 | Validación RIF con módulo 11 | Algoritmo oficial venezolano; evita RIFs inválidos en importación de clientes/obligaciones |
| 2026-10-01 | record_id como Reference + record_name + model_name | Reference polimórfico en line; log persistente guarda JSON con IDs para futuro "Deshacer" |
| 2026-10-03 | `file` del wizard SIN `required=True` a nivel de modelo | El cliente valida el required del modelo al pulsar "Descargar Plantilla" y bloquea con "Missing required fields". La vista conserva `required="true"` y `action_load_file`/`action_preview` ya lanzan UserError si falta |
| 2026-10-03 | Menú "Importar desde Excel" invisible: era entorno, no código | Un segundo Odoo fantasma (daemon snap docker en WSL) servía una BD vieja en localhost:8090 vía wslrelay. Ver "Diagnóstico real" en AGENTS.md |
| 2026-10-04 | Parser cartelera Excel: detección dinámica fila headers, col RIF, col nombre, rango docs | El archivo real tiene 12 hojas con variaciones posicionales (enero: RIF=C, feb-nov: RIF=A, dic: 39 docs). Mapeo posicional C01..C36 evita colisiones por nombres duplicados (C13/C18 "Planilla de Inscripción", C15/C23 "Último soporte de Pago"). Normalización elimina HTML tags (<br>). |
| 2026-10-05 | Commit 5e53e20 "fix: remove double base64 encoding" es engañoso | El código nunca tuvo doble encoding. `image_process` devuelve bytes, no base64. El commit solo movió imports al top, añadió newline final, deduplicó `_get_max_size_mb` y añadió test con PIL. No renombrar (repo público). |
| 2026-10-06 | vat_book_both: import_type único que procesa COMPRAS + VENTAS | El Excel real del cliente tiene ambas hojas en un archivo. El contador subía 2 veces el mismo archivo. UX mejorada: 1 solo upload. Cada import.line lleva `_book_type` para que el import cree vat.book.line con book_type correcto. Fallback seguro en _import_vat_book_line evita 'both' inválido. |
| 2026-10-07 | vat_book_both procesa ambas hojas en 1 upload | Cada import.line lleva data['_book_type'] con 'purchase' o 'sale' para que el import cree vat.book.line con el book_type correcto |
| 2026-10-07 | Helper _compute_expected_totals_from_fixture combina import en general | Refleja la decisión de Fase F de unificar base_import_16 en base_general en vat.book.line |
| 2026-10-07 | Mutation test en test_import_real_fixture_purchase_totals_matches_excel | Hardcodea valores esperados para detectar cambios en el fixture. Verificado: mutar base_general hace fallar el test |
| 2026-10-08 | G.10 completa - 3 exports | Export vat.book.line (XLSX), export vat.return (XLSX), fix conceptos PDF. 107 tests. Conceptos SENIAT literales del Excel real del contador, NO del PDF original. |

## Convenciones del Proyecto
- **Odoo 19**: `<list>` no `<tree>`, `invisible=` no `states`, `view_mode="list,form"`, sin `expand=`, sin `attrs=`, `@api.depends` explícito, inverse en computed stored editables
- **Git**: commits en inglés (Conventional Commits: feat:, fix:, docs:)
- **Docker**: `docker compose run --rm` (no `exec`) para evitar conflicto de puerto 8090
- **Tests**: `--workers 0 --stop-after-init` en contenedor efímero

## Pendientes
1. Crear AGENTS.md en la raíz (para el agente IA)
2. Crear README.md, CHANGELOG.md, LICENSE (LGPL-3), CONTRIBUTING.md en la raíz
3. Añadir capturas de pantalla en docs/screenshots/
4. Configurar Topics en GitHub: odoo, odoo19, venezuela, compliance, fiscal, accounting, seniat, docker, python
5. Refactorizar SPEC.md en docs/specs/01-calendario-seniat.md, 02-gestion-alertas.md, etc.
6. Instalar skills de mart337i/odoo-skills y crear skills propios (calcular-retencion-venezuela)
7. Configurar subagente "Desarrollador Odoo 19" con Nemotron 3.5 Lightning
8. Integrar MCP de Odoo (mart337i/odoo-dev-mcp)
9. Añadir tests extendidos (document_missing, alertas, calendario SENIAT otros años)
10. Integración futura con WhatsApp Business API (opcional)
11. ~~Importación Excel Fase 1: infraestructura wizard + plantillas + parser~~ ✅
12. ~~Importación Excel Fase 2: motor validación + upsert + importadores core~~ ✅
13. ~~Importación Excel Fase 3: tests + pulido + documentación~~ ✅
14. ~~Cartelera Fiscal Fase A: 36 tipos + MINTRA~~ ✅
15. ~~Cartelera Fiscal Fase B: cartelera.status + document_score~~ ✅
16. ~~Cartelera Fiscal Fase C: Parser + import wizard~~ ✅
17. ~~Cartelera Fiscal Fase D: Vista de brechas + spec 07 + tests~~ ✅
18. ~~Cartelera Fiscal Fase E: Parser dinámico~~ ✅
19. ~~Fase E2.1: Modelo `cartelera.evidence` + transición automática de status~~ ✅
20. ~~Fase E2.2: Límite de tamaño + compresión automática de imágenes~~ ✅
21. ~~Fase E2.3: Logo cliente en kanban~~ ✅
22. ~~Fase E2.4: Mini-cartelera HTML agrupada por institución~~ ✅
23. ~~Fase E2.5: Kanban extendido con `document_score`~~ ✅
24. ~~Fase E2.6: Fix OWL `kanban_image` + `t-out` (patrones Odoo 19)~~ ✅
25. ~~Fase E2.7: Tests kanban/logo/cartelera HTML (63/63)~~ ✅
26. ⬜ Spec de evidencia fotográfica (`docs/specs/08-evidencia.md`) — pendiente

## Conteo de tests y contexto del agente

### Fuente oficial de conteo
El número oficial de tests es el que reporta Odoo al finalizar:
    odoo.tests.result: 0 failed, 0 error(s) of N tests
Cualquier otro conteo (grep, suma manual, estimación) es inválido.

### Conteo actual
- **107 tests** (Odoo report: 0 failed, 0 error(s) of 107 tests)
- Desglose: 96 base + 8 vat_book_export + 2 vat_return_export + 1 pdf_conceptos

### Señales de contexto saturado
Cuando el agente empieza a:
- Reportar números de tests distintos al de Odoo
- Reciclar roadmap viejo como "próximas áreas"
- Declarar tareas completas sin verificar
- Repetir los mismos errores después de corregirlos

Significa que el contexto está saturado. ACCIÓN:
1. Cerrar la sesión de OpenCode
2. Abrir sesión nueva
3. La sesión nueva debe leer AGENTS.md + memory.md + spec relevante
   ANTES de responder

### Verificación obligatoria
Antes de declarar éxito en cualquier sub-tarea:
1. Correr tests y copiar la línea LITERAL de Odoo
2. Comparar con el número esperado (ver memory.md)
3. Si el número es distinto → regresión, no commitear
4. Si el agente reporta otro número distinto al de Odoo → cerrar sesión

## Historial de sesiones recientes

| Fecha | Sesión | Resultado |
|---|---|---|
| 2026-10-08 | DevOps.1c completa | Clean ruff (F601, E741, UP038, F841), 11 files, 107 tests |
| 2026-10-08 | G.10 completa | Export vat.book.line + vat.return (XLSX), fix PDF conceptos SENIAT, 107 tests |
| 2026-10-07 | Fase G completa | Wizard import libro compras/ventas con 3 modes, parser dinámico, 6 tests integración, mutation test verificado, 96 tests |
| 2026-10-05 | Fase E2 completa | Evidence con compresión + límite, logo cliente, mini-cartelera HTML, kanban extendido. 63 tests pasan. Fix de 2 OWL errors en kanban (`kanban_image` + `t-out`). |
| 2026-10-04 | Fase E: Parser dinámico cartelera (completa) | `_detect_cartelera_structure()` + validación 30+ docs + warning headers no reconocidos + mapeo posicional C01..C36 (duplicados) + tests 53/53 |
| 2026-10-04 | Fase D Cartelera: vista brechas + spec 07 | Spec 07 creado, decoraciones list/search, smart button cliente, percentage computed, tests nuevos |
| 2026-10-03 | Diagnóstico menú invisible | Causa: Odoo fantasma en WSL (snap docker) + service worker; `snap.docker.dockerd` detenido |
| 2026-10-03 | Fix plantilla Excel | `file` sin `required` en modelo; "Descargar Plantilla" ya no lanza "Missing required fields" |
| 2026-10-02 | Import Excel 2B.3 | `action_import` + `_upsert_record` implementados |
| 2026-10-02 | Fixes AGENTS.md | Anti-patterns + workflow + verificación |
| 2026-10-02 | Fixes tests | `country_id` en account.tax |
| 2026-10-01 | Import Excel 2B.2 | `_validate_business` |
| 2026-10-01 | Import Excel 2B.1 | `_validate_reference` |
| 2026-09-30 | Import Excel 2A | `_parse_number` + `_validate_rif` |

## Bug conocido: menú no aparece tras cambios en ir.ui.menu

Síntoma: tras añadir/modificar un `<menuitem>` y actualizar el módulo con `-u`, el menú aparece en `load_menus()` (shell) pero NO en la UI.

Causa raíz (confirmada 2026-10-03 — CORREGIDA):
1. [CORRECCIÓN] NO era la caché `ormcache` de los workers. 60/60 peticiones
   internas devolvían el menú correcto.
2. La causa real: un SEGUNDO servidor Odoo (contenedor del daemon snap docker
   dentro de WSL) escuchaba en `localhost:8090` vía `wslrelay` y servía una BD
   `contea` vieja (164 menús, sin el 212). El navegador hablaba con él.
3. Agravante: el service worker de Odoo (`/web/service-worker.js`, caché
   `odoo-sw-cache`) cacheaba `/web/webclient/load_menus` y el `localStorage`
   (`webclient_menus`) renderizaba menús viejos.

Fix real:
1. `netstat -ano | findstr :8090` → si aparece `wslrelay`, hay Odoo fantasma en WSL.
2. Detenerlo: `wsl.exe -u root -e bash -lc "systemctl stop snap.docker.dockerd"`.
3. Confirmar con UA única que el tráfico del host llega al contenedor:
   `curl -A DSH-PROBE-X http://localhost:8090/web/login` + `docker compose logs web`.
4. En el navegador: desregistrar service worker, borrar `caches`, `localStorage`
   y `sessionStorage`, recargar.
5. Verificar: `GET localhost:8090/web/webclient/load_menus` debe contener `"212"`.

NO intentar: quitar `groups=`, tocar XML, reinstall, limpiar assets, o cualquier
otra teoría. El backend siempre estuvo correcto.