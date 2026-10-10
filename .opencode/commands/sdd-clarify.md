---
description: SDD — Revisa la spec como QA (solo detecta)
agent: plan
---

Revisa `specs/$1/spec.md` como si fueras un QA muy profesional.
Lee también `docs/constitution.md`.

Lista, en orden:

1. **Ambigüedades restantes** — requisitos que no se pueden
   verificar tal como están escritos.
2. **Contradicciones** — entre dos o más RF, o con la constitución.
3. **Casos límite no cubiertos** — qué pasa con vacíos, duplicados,
   valores negativos, concurrencia, multi-company.
4. **Conflictos con docs/constitution.md** — qué RF viola qué
   principio.

**No propongas soluciones.** Solo detecta. Formato: lista numerada.

**Entrega:** la lista. Si está limpia, decí "Sin observaciones".
Esperá mi aprobación antes de pasar a `/sdd-plan`.
