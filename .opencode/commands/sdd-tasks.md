---
description: SDD — Divide el plan en tareas pequeñas y verificables
agent: plan
---

A partir de `specs/$1/spec.md` y `specs/$1/plan.md`, genera
`specs/$1/tasks.md` con:

- Tareas pequeñas (máx. 20-30 min cada una), en orden de dependencia.
- Cada una con los RF que cubre y una línea "Hecho cuando:"
  verificable (ej: "los 107 tests siguen pasando + demo visual").
- Checkboxes: `- [ ] **T1. <descripción>.** RF-1, RF-2`.
- Máximo 10 tareas. Si salen más, proponé dividir la spec en dos.

**Reglas:**
- ❌ NO crear archivos temporales
- ❌ NO tocar código
- ✅ "Hecho cuando:" debe ser comprobable sin ambigüedad

**Entrega:** ruta + lista de tareas (solo los títulos).
