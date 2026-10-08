---
description: "Ejecuta los tests del módulo y muestra el resumen oficial"
---
Ejecuta el siguiente comando y muéstrame la **línea literal** de Odoo que indica el resultado de los tests.

!docker compose run --rm web odoo -d contea -u l10n_ve_compliance_manager --test-enable --stop-after-init --workers 0 --test-tags /l10n_ve_compliance_manager 2>&1 | grep -E "failed|tests when"

**Regla obligatoria (AGENTS.md):** El número oficial de tests es el que reporta Odoo. NO uses `grep -c "def test_"`. NO inventes cifras.
