![][image1]

**PROMPT MODELO**

**App de Gestion de Taller Mecanico**

Stack: Python  ·  FastAPI  ·  HTMX  ·  PostgreSQL

| Este documento es la especificacion completa de la aplicacion. Usalo como prompt inicial en Google Antigravity o Claude Code. |
| :---: |

**SECCION 1 — OBJETIVO**

Quiero construir una aplicacion web para la administracion y manejo de los trabajos diarios de un taller mecanico.

La aplicacion debe permitir gestionar:

* Clientes y sus vehiculos

* Ordenes de Trabajo (OT) con todos sus detalles

* Mano de obra y materiales por OT

* Repuestos utilizados por OT

* Tecnicos del taller

* Usuarios y roles del sistema

Es para uso interno y la van a usar recepcionistas, tecnicos, supervisores y administradores del taller.

**SECCION 2 — TECNOLOGIA**

* **Backend:** Python con FastAPI

* **Frontend:** HTMX \+ HTML \+ Tailwind CSS (sin JavaScript adicional salvo lo que HTMX necesite)

* **Base de datos:** PostgreSQL

* **ORM:** SQLAlchemy con modelos declarativos

* **Templates:** Jinja2 (integrado con FastAPI)

* **Autenticacion:** JWT con sesiones en tabla PostgreSQL

* **Entorno:** Virtual environment Python (venv)

**SECCION 3 — LAYOUT Y DISENO**

* **Layout:** Dashboard responsivo con menu hamburguesa

* **Estilo:** Minimalista, sobrio, perfectamente legible y limpio

* **Paleta de colores:** Verde oscuro (\#1B6B5A) y Azul oscuro (\#1B3F7A), fondos claros, textos oscuros

* **Responsive:** Adaptado para telefono movil, tablet y notebook

* **En desktop:** Sidebar fijo con menu desplegado

* **En mobile/tablet:** Menu hamburguesa colapsable en la parte superior

* **Tipografia:** Inter o Arial, tamanio base 15px, alto contraste

* **Modo oscuro:** No (fase 1\)

**SECCION 4 — COMPONENTES**

* Navbar/Header con logo, nombre de la app y menu hamburguesa en mobile

* Sidebar con menu agrupado (visible en desktop, colapsable en mobile)

* Dashboard con Cards de KPIs: OT abiertas, En proceso, Listas hoy, Vehiculos en taller

* Tablas con busqueda, filtros y paginacion, botones de accion por fila

* Formularios de alta y edicion en Modal via HTMX (sin recargar pagina)

* Badges de estado para OT: Abierta / En Proceso / Lista / Facturada / Cerrada

* Alerts/Toasts para confirmar acciones (guardado, error, eliminado)

* Confirmacion antes de eliminar registros

**SECCION 5 — MENU Y MODULOS**

**Nota:** El menu lateral se organiza en tres grupos: Inicio, Maestros/Mantenedores y Movimientos/Operaciones.

**INICIO**

* Dashboard (KPIs y resumen del dia)

**MAESTROS / MANTENEDORES**

Datos base que se cargan una vez y se reutilizan:

* Clientes

* Vehiculos

* Tipos de Vehiculo

* Tecnicos

* Repuestos / Catalogo

* Usuarios del Sistema

* Roles y Permisos

**MOVIMIENTOS / OPERACIONES**

Las transacciones diarias del taller:

* Ordenes de Trabajo (listado general \+ nueva OT)

* Mano de Obra por OT

* Repuestos por OT

* Checklist de Vehiculo por OT

**REPORTES (fase 2\)**

* OT por periodo

* OT por tecnico

* OT por cliente / vehiculo

| Opción de Menú | Módulo/Entidad | Descripción breve |
| :---- | :---- | :---- |
| Dashboard | Inicio | KPIs del dia: OT abiertas, en proceso, listas, vehiculos en taller |
| Clientes | Maestros | ABM de clientes con RUT como clave primaria |
| Vehiculos | Maestros | ABM de vehiculos con patente como clave primaria |
| Tipos de Vehiculo | Maestros | Catalogo de tipos: AUTO, SUV, CAMIONETA, etc. |
| Tecnicos | Maestros | ABM de tecnicos del taller |
| Repuestos / Catalogo | Maestros | Catalogo de repuestos con stock y precios |
| Usuarios del Sistema | Maestros | ABM de usuarios con roles y permisos |
| Roles y Permisos | Maestros | Gestion de roles y permisos por modulo |
| Ordenes de Trabajo | Movimientos | Listado y nueva OT. Centro de operaciones del taller |
| Mano de Obra por OT | Movimientos | Registro de trabajos y horas por tecnico en cada OT |
| Repuestos por OT | Movimientos | Registro de repuestos utilizados en cada OT |
| Checklist por OT | Movimientos | Items de verificacion del vehiculo al ingreso |

**SECCION 6 — ENTIDADES Y CAMPOS CLAVE**

**Info:** Cada entidad corresponde a una tabla en PostgreSQL. Las PK marcadas son claves naturales.

**clientes**

rut (PK), nombre, direccion, ciudad, comuna, fono\_particular, fono\_oficina, celular, email, forma\_pago\_default

**vehiculos**

patente (PK), cliente\_rut (FK), marca, modelo, sub\_modelo, tipo (enum), anio, color, chasis\_vin

**tecnicos**

id (PK), codigo, nombre, activo

**repuestos**

codigo (PK), nombre, precio\_costo, precio\_venta, stock\_actual

**ordenes\_trabajo**

id (PK), numero\_ot, patente (FK), cliente\_rut (FK), recepcionista\_id (FK), fecha\_ingreso, fecha\_prometida, fecha\_termino, kms\_ingreso, glosa\_general, forma\_pago, estado (enum)

**ot\_mano\_obra**

id (PK), ot\_id (FK), tecnico\_id (FK), descripcion\_trabajo, horas, precio\_unitario, descuento\_pct, bonificacion, total\_neto, total\_con\_impuesto

**ot\_repuestos**

id (PK), ot\_id (FK), repuesto\_codigo (FK nullable), descripcion, cantidad, precio\_costo\_unitario, precio\_venta\_unitario, descuento\_pct, es\_siniestro, tipo (enum)

**usuarios**

id (PK), username, email, password\_hash, nombre\_completo, activo, debe\_cambiar\_password, ultimo\_acceso

**roles**

id (PK), nombre, descripcion

**permisos**

id (PK), codigo, modulo, descripcion

**usuarios\_roles**

usuario\_id (FK), rol\_id (FK) — PK compuesta

**roles\_permisos**

rol\_id (FK), permiso\_id (FK) — PK compuesta

**auditoria**

id (PK), usuario\_id (FK), accion, modulo, entidad\_id, datos\_anteriores (JSONB), datos\_nuevos (JSONB), ip\_origen, fecha

**sesiones**

id UUID (PK), usuario\_id (FK), token\_hash, ip\_origen, expira\_en, activa

**intentos\_login**

id (PK), username\_intento, ip\_origen, exitoso, fecha

**SECCION 7 — ESTILO VISUAL**

Color primario:    \#1B6B5A  (verde oscuro — del logo)  
Color secundario:  \#1B3F7A  (azul oscuro — del logo)  
Fondo general:     \#F8F9FA  (gris muy claro)  
Fondo sidebar:     \#1B3F7A  con texto blanco  
Fondo cards KPI:   \#FFFFFF  con borde suave  
Tablas:            filas alternadas gris claro, sin bordes pesados  
Botones:           primario azul, peligro rojo, secundario gris  
   
Badges estado OT:  
  ABIERTA    → gris  
  EN\_PROCESO → amarillo  
  LISTA      → verde  
  FACTURADA  → azul  
  CERRADA    → rojo

**SECCION 8 — COMPORTAMIENTO HTMX**

* Click en 'Nueva OT'         → hx-get carga formulario vacio en modal

* Envio de formulario          → hx-post, actualiza tabla sin recargar pagina

* Click en 'Editar'            → hx-get carga formulario prellenado en modal

* Click en 'Eliminar'          → hx-delete con confirmacion, elimina fila

* Cambio de estado OT          → hx-patch actualiza solo el badge de estado

* Busqueda y filtros           → hx-get recarga solo el bloque de tabla

* Paginacion                   → hx-get recarga solo el contenido principal

* Target de respuestas HTMX    → hx-target='\#contenido-principal' o id especifico

**SECCION 9 — ESTRUCTURA DEL PROYECTO**

taller\_app/  
├── main.py                  \# App FastAPI, rutas principales  
├── database.py              \# Conexion PostgreSQL con SQLAlchemy  
├── models.py                \# Modelos ORM (tablas)  
├── schemas.py               \# Schemas Pydantic (validacion)  
├── auth.py                  \# Login, sesiones, JWT  
├── routers/  
│   ├── clientes.py  
│   ├── vehiculos.py  
│   ├── tecnicos.py  
│   ├── repuestos.py  
│   ├── ordenes\_trabajo.py  
│   ├── ot\_mano\_obra.py  
│   ├── ot\_repuestos.py  
│   └── usuarios.py  
├── templates/  
│   ├── base.html            \# Layout base con sidebar y hamburguesa  
│   ├── dashboard.html  
│   ├── clientes/  
│   ├── vehiculos/  
│   ├── tecnicos/  
│   ├── repuestos/  
│   ├── ordenes\_trabajo/  
│   └── usuarios/  
├── static/  
│   ├── css/                 \# Tailwind output  
│   ├── js/htmx.min.js  
│   └── img/logo.png  
└── requirements.txt

**Slogan Flex:** Donde el ERP no llega, Flex resuelve.

[image1]: <data:image/png;base64,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>