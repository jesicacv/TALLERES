"""Modelos SQLAlchemy del proyecto."""

from app.models.auditoria import Auditoria
from app.models.cliente import Cliente
from app.models.orden_trabajo import OrdenTrabajo
from app.models.ot_checklist import OTChecklist
from app.models.ot_mano_obra import OTManoObra
from app.models.ot_repuestos import OTRepuesto
from app.models.repuesto import Repuesto
from app.models.tecnico import Tecnico
from app.models.usuario import IntentoLogin, Permiso, Rol, RolPermiso, Sesion, Usuario, UsuarioRol
from app.models.vehiculo import Vehiculo

__all__ = [
	"Auditoria",
	"Cliente",
	"IntentoLogin",
	"OrdenTrabajo",
	"OTChecklist",
	"OTManoObra",
	"OTRepuesto",
	"Permiso",
	"Repuesto",
	"Rol",
	"RolPermiso",
	"Sesion",
	"Tecnico",
	"Usuario",
	"UsuarioRol",
	"Vehiculo",
]
