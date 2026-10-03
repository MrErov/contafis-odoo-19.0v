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
- `docs/specs/06-importacion-excel.md` → importación desde Excel
- `docs/memory.md` → decisiones y contexto

## Anti-patterns (PROHIBIDO)

Estas prácticas están terminantemente prohibidas en este repositorio.
Cualquier agente que las ejecute debe revertir su cambio inmediatamente.

### 1. Scripts temporales

- ❌ NO crear archivos `fix_*.py`, `patch_*.py`, `temp_*.py`, `test_*.py` en la raíz.
- ❌ NO crear scripts que modifiquen otros archivos vía `open().write()`.
- ❌ NO crear archivos fuera de `addons/l10n_ve_compliance_manager/` sin autorización.

Si un archivo tiene un error de sintaxis o lógica, edítalo DIRECTAMENTE
con la herramienta `edit`. No crees un script intermedio.

### 2. Loops de "arreglar → fallar → arreglar"

Si intentas arreglar algo y sigue fallando después de 2 intentos:
-  DETENTE inmediatamente.
-  Reporta al usuario: qué intentaste, qué falló, qué archivos tocaste.
-  Espera instrucciones. NO sigas intentando.

Continuar en un loop genera:
- Scripts temporales basura.
- Cambios que rompen el working tree.
- Pérdida de tiempo.

### 3. Declarar errores como "pre-existentes" sin verificar

Antes de decir "este error ya existía", verifica con:
- `git stash` + correr tests + `git stash pop` (aislar el cambio).
- `git log` para confirmar el estado del último commit.
- `git diff` para ver exactamente qué tocaste.

Si el número de tests verdes BAJA, es regresión tuya. NO lo disfraces.

### 4. Dejar cambios sin commitear

- ❌ NO terminar una tarea con `git status` mostrando cambios sin commitear.
- ❌ NO dejar fixes aplicados sin commitear "para después".
- ✅ Cada sub-tarea termina con COMMIT INMEDIATO si los tests pasan.

Razón: un `git checkout -- <path>` durante un revert borra cambios sin
commitear. Se perdió trabajo real por esta razón en Fase 2B.

### 5. Archivos de output y rutas externas

- ❌ NO escribir archivos de output a disco (`test_output*.txt`, `result*.log`).
- ❌ NO intentar acceder a rutas fuera del proyecto (`C:\tmp\`, `/tmp/`).
- ❌ NO modificar `models/` si la tarea es solo de tests.
- 🛑 Si un comando falla, DETENERSE. NO crear variantes (`test_output2.txt`, etc.).

### 6. Diagnóstico sin archivos temporales

Cuando necesites diagnosticar un problema en Odoo:
- ✅ USA `docker compose run --rm web odoo shell -d <db> --no-http << 'EOF' ... EOF`
  (stdin, sin archivos)
- ✅ USA `docker compose exec db psql -U odoo -d <db> -c "..."`
- ❌ NO crees archivos `.py` de diagnóstico (`check_*.py`, `diag_*.py`, `deep_*.py`)
- ❌ NO crees archivos `fix_*.py` ni `install_*.py`
- Si te encuentras creando un archivo de diagnóstico, DETENTE. Usa shell inline.

Motivo: en una sesión se crearon 14 archivos temporales contaminando el repo.

## Workflow de sub-tareas

Para tareas grandes (>100 líneas), dividir en sub-tareas de máximo 1-2 horas.
Cada sub-tarea:

1. **Alcance:** UNA sola cosa a implementar.
2. **Prompt corto:** menos de 50 líneas de especificación.
3. **Verificación:** correr tests al finalizar.
4. **Commit:** SIEMPRE commitear si los tests pasan.
5. **Esperar confirmación** antes de la siguiente sub-tarea.

Ejemplos bien divididos:
- "Implementar _validate_reference() en import_line.py"
- "Añadir botón Validar al wizard"

Ejemplo mal dividido:
- "Implementar motor completo con 4 importadores, validación 3 niveles
  y tests de integración" (demasiado grande)

Si una sub-tarea genera más de 200 líneas de código nuevo, está mal dividida.

## Verificación obligatoria antes de declarar éxito

Antes de decir "tarea completada":

1. `git status` → solo los archivos esperados están modificados.
2. `git diff --stat` → cantidad de cambios coherente.
3. Correr tests:
docker compose run --rm web odoo -d contea
-u l10n_ve_compliance_manager
--test-enable --stop-after-init --workers 0
--test-tags /l10n_ve_compliance_manager 2>&1 | grep -E "failed|tests when"

4. Confirmar: `0 failed, 0 error(s) of N tests` donde N >= último valor conocido.
5. Si N < valor anterior → REGRESIÓN. Revertir con `git checkout` y avisar.

### Conteo de tests — fuente oficial
El ÚNICO conteo válido es el que reporta Odoo:
`odoo.tests.result: 0 failed, 0 error(s) of N tests`
NO usar `grep -c "def test_"`. NO inventar cifras. Si el agente reporta
un número distinto al de Odoo, es error del agente.

Reportar al usuario:
- Lista de archivos modificados
- Conteo de tests (antes / después)
- Diff stat
- Cualquier warning nuevo en los logs

## Reglas estrictas

- Añadir al FINAL del archivo, no en medio.
- Asegurar nueva línea final (`\n` al terminar).
- NO modificar la sección Anti-patterns existente.