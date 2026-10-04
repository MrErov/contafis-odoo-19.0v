---
description: "Inicia una nueva fase de desarrollo siguiendo el plan aprobado"
---
**Contexto del proyecto:** `@AGENTS.md` (reglas) y `@docs/memory.md` (estado actual).

**Tarea:** Vas a iniciar la fase de trabajo indicada en: **$ARGUMENTS**

Sigue este protocolo:

1.  **Lectura de contexto**: Lee `@AGENTS.md` y `@docs/memory.md` para entender las reglas y el estado actual.
2.  **Análisis del plan**: Busca en `docs/specs/` la especificación relevante para la fase. Si no existe, propón crearla.
3.  **Propuesta de plan**: Antes de escribir código, dame un plan detallado de los archivos a modificar, los cambios exactos y los tests a añadir.
4.  **Implementación**: Una vez apruebe el plan, implementa los cambios siguiendo las convenciones de Odoo 19 y las reglas de `AGENTS.md`.
5.  **Verificación y commit**: Al terminar, ejecuta el flujo del comando `/commit` con la descripción de la fase.