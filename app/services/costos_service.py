from __future__ import annotations

from decimal import Decimal

# IVA Chile (19%). Factor multiplicativo sobre el neto.
IVA_FACTOR = Decimal("1.19")


def calcular_totales_mano_obra(
    horas: Decimal,
    precio_unitario: Decimal,
    descuento_pct: Decimal = Decimal("0"),
    bonificacion: Decimal = Decimal("0"),
) -> tuple[Decimal, Decimal]:
    """Calcula (total_neto, total_con_impuesto) de una linea de mano de obra.

    - base = horas * precio_unitario
    - total_neto = base - descuento% sobre la base - bonificacion, con piso en 0
    - total_con_impuesto = total_neto * IVA (19%)
    """
    base = horas * precio_unitario
    total_neto = base - (base * descuento_pct / Decimal("100")) - bonificacion
    if total_neto < 0:
        total_neto = Decimal("0")
    total_con_impuesto = total_neto * IVA_FACTOR
    return total_neto, total_con_impuesto
