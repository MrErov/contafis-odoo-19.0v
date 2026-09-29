# Guía de contribución

Gracias por tu interés en contribuir a **l10n_ve_compliance_manager**.

## Cómo contribuir

1. Haz un *fork* del repositorio.
2. Crea una rama para tu feature:

   ```bash
   git checkout -b feature/nombre-descriptivo
   ```

3. Realiza tus cambios siguiendo las convenciones de Odoo 19.0.
4. Corre las pruebas:

   ```bash
   docker compose run --rm web odoo -d contea \
     -u l10n_ve_compliance_manager \
     --test-enable --stop-after-init --workers 0 \
     --test-tags /l10n_ve_compliance_manager:standard
   ```

5. Haz commit siguiendo **Conventional Commits**:

   ```
   feat: nueva funcionalidad
   fix: corrección de bug
   docs: cambios de documentación
   test: cambios en pruebas
   refactor: refactorización sin cambio funcional
   chore: tareas de mantenimiento
   ```

6. Abre un *Pull Request* describiendo claramente los cambios.

## Convenciones Odoo 19.0

- Usar `<list>` en lugar de `<tree>`.
- Usar `invisible="campo != 'valor'"` en lugar de `states=` o `attrs=`.
- Usar `view_mode="list,form"` en acciones.
- No usar `expand=` en vistas search.
- `@api.depends` explícito en campos computados.
- `inverse` en campos computados almacenados editables.

## Reportar bugs

Abre un *issue* con:

- Descripción del bug.
- Pasos para reproducirlo.
- Comportamiento esperado vs. observado.
- Versión de Odoo y del módulo.