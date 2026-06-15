from __future__ import annotations

import unittest
from decimal import Decimal

from app.services.costos_service import calcular_totales_mano_obra


class ManoObraTotalsTests(unittest.TestCase):
    def test_sin_descuento_ni_bonificacion(self) -> None:
        neto, con_iva = calcular_totales_mano_obra(Decimal("2"), Decimal("10"))
        self.assertEqual(neto, Decimal("20"))
        self.assertEqual(con_iva, Decimal("23.80"))

    def test_descuento_porcentual(self) -> None:
        # base 20, -10% => 18
        neto, con_iva = calcular_totales_mano_obra(Decimal("2"), Decimal("10"), Decimal("10"))
        self.assertEqual(neto, Decimal("18"))
        self.assertEqual(con_iva, Decimal("21.42"))

    def test_bonificacion_fija(self) -> None:
        # base 20, -5 => 15
        neto, con_iva = calcular_totales_mano_obra(Decimal("2"), Decimal("10"), Decimal("0"), Decimal("5"))
        self.assertEqual(neto, Decimal("15"))
        self.assertEqual(con_iva, Decimal("17.85"))

    def test_descuento_y_bonificacion_combinados(self) -> None:
        # base 20, -50% => 10, -5 => 5
        neto, con_iva = calcular_totales_mano_obra(Decimal("2"), Decimal("10"), Decimal("50"), Decimal("5"))
        self.assertEqual(neto, Decimal("5"))
        self.assertEqual(con_iva, Decimal("5.95"))

    def test_neto_negativo_se_clampea_a_cero(self) -> None:
        # base 10, bonificacion 50 => -40 => 0
        neto, con_iva = calcular_totales_mano_obra(Decimal("1"), Decimal("10"), Decimal("0"), Decimal("50"))
        self.assertEqual(neto, Decimal("0"))
        self.assertEqual(con_iva, Decimal("0"))

    def test_horas_fraccionarias(self) -> None:
        neto, con_iva = calcular_totales_mano_obra(Decimal("1.5"), Decimal("25"))
        self.assertEqual(neto, Decimal("37.5"))
        self.assertEqual(con_iva, Decimal("44.625"))


if __name__ == "__main__":
    unittest.main()
