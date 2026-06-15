from enum import StrEnum


class TipoVehiculoEnum(StrEnum):
    AUTO = "AUTO"
    SUV = "SUV"
    CAMIONETA = "CAMIONETA"
    CAMION = "CAMION"
    FURGON = "FURGON"
    MOTO = "MOTO"
    OTRO = "OTRO"


class EstadoOTEnum(StrEnum):
    ABIERTA = "ABIERTA"
    EN_PROCESO = "EN_PROCESO"
    LISTA = "LISTA"
    FACTURADA = "FACTURADA"
    CERRADA = "CERRADA"


class TipoItemOTEnum(StrEnum):
    REPUESTO = "REPUESTO"
    MATERIAL = "MATERIAL"
    OTRO = "OTRO"
