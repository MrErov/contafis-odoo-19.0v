# Constitución — contafis-odoo-19.0v

Principios innegociables. Toda spec, plan y tarea debe cumplirlos.

1. **Odoo como única fuente de verdad**: se extiende con `_inherit`,
   no se reimplementa lo que `account`, `l10n_ve` o `mail` ya hacen.
2. **Datos del contador, no del sistema**: cualquier dato ingresado
   debe poder editarse. Se registra trazabilidad (`modified_by`,
   `modified_at`), no se bloquea.
3. **Multi-cliente primero**: toda query filtra por `company_id`.
   Ningún feature asume una sola empresa ni un solo cliente.
4. **Tests como puerta**: ningún commit con menos de 107 tests
   pasando. Nada avanza con tests en rojo.
5. **Ruff + pre-commit como puerta**: ningún commit pasa si ruff,
   check-xml, trailing-whitespace o mixed-line-ending fallan.
6. **Idioma**: código en inglés (`field_name`, `def method`); UI,
   help= y docs en español. Commits con Conventional Commits en inglés.
