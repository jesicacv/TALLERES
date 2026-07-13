from enum import StrEnum


class TipoVehiculoEnum(StrEnum):
    """Catalogo interno de tipos de vehiculo. No es administrable desde la UI.

    Para agregar un tipo hacen falta DOS pasos, no alcanza con la base:
    1. Base:   ALTER TYPE tipo_vehiculo_enum ADD VALUE 'NUEVO';  (via migracion Alembic)
    2. Codigo: agregar el miembro aca y redesplegar.
    Si solo se agrega en la base, al leer un vehiculo con ese tipo SQLAlchemy falla
    con LookupError porque el valor no existe en este enum.
    """

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
