# Specs — Features (SDD)

Esta carpeta contiene specs de **features específicas** siguiendo
el flujo SDD: nace, se implementa, muere.

**Diferencia con `docs/specs/`:**

- `docs/specs/` → specs por **capacidad** del módulo (calendario,
  retenciones, cartelera). Viven para siempre, se actualizan.
- `specs/` (esta carpeta) → specs por **feature/iteración**
  (asientos contables, wizard factura física). Nacen, se
  implementan, quedan como registro histórico.

**Estructura de cada spec:**

    specs/NNN-nombre/
      spec.md    ← QUÉ y POR QUÉ (qué se construye, requisitos EARS)
      plan.md    ← CÓMO (archivos, funciones, tests, decisiones)
      tasks.md   ← tareas pequeñas con "Hecho cuando:" verificable

**Flujo (comandos en .opencode/commands/):**

1. `/sdd-spec NNN-nombre idea inicial`
2. `/sdd-clarify NNN-nombre`
3. `/sdd-plan NNN-nombre`
4. `/sdd-tasks NNN-nombre`
5. `/sdd-implement NNN-nombre T1`
6. `/sdd-status NNN-nombre`
