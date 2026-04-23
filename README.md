# Sistema Transaccional para el Control de Recaudaciones y Flujo de Pasajeros en la Red Mi Teleférico
 
> Proyecto académico — Materia: Base de Datos 2  
> Universidad Mayor de San Andrés (UMSA) — Carrera de Informática  
> Gestión 2026
 
---
 
## Integrantes

| Nombre completo |
|---|
| Gabriel Omar Andia Alave |
| Marcos Daniel Fernandez Cazas |
 
---
 
## Descripción del proyecto
 
Sistema web transaccional desarrollado con **Python Flask** conectado a **Oracle Database**, que implementa la gestión completa de la Red de Transporte por Cable Mi Teleférico de La Paz y El Alto, Bolivia.
 
El sistema cubre el control de recaudaciones, flujo de pasajeros, emisión de credenciales de viaje, recargas de saldo y generación de reportes operativos, aplicando la lógica tarifaria real del sistema (3 Bs tarifa base, 2 Bs transbordo, descuentos preferenciales por categoría).
 
---
**3. Ejecutar los scripts Oracle en DBeaver**
 
Conectarse a Oracle como `SYS` o `SYSTEM` en SQLDeveloper y ejecutar en este orden, cada script por separado seleccionando el contenido y presionando `F5`:
 
```
01_tablas.sql       → Crea las 10 tablas
02_inserts.sql      → Inserta datos de prueba (30 registros por tabla)
03_objetos.sql      → Crea procedimientos, funciones, triggers, vistas y paquete
04_usuarios.sql     → Crea usuarios de negocio, roles y perfiles
```
 
> **Importante en SQLDeveloper:** Los bloques PL/SQL deben ejecutarse uno por uno, no todos juntos. Seleccionar cada bloque desde `CREATE OR REPLACE` hasta su `END;` y ejecutar con `F5`.
 
**4. Crear el usuario Oracle principal del sistema**
 
Abrir SQLDeveloper conectado como `SYS` o `SYSTEM` y ejecutar:
 
```sql
-- Habilitar modo script (necesario en Oracle 19c+)
ALTER SESSION SET "_ORACLE_SCRIPT" = TRUE;
 
-- Crear el usuario principal del sistema
CREATE USER teleferico IDENTIFIED BY "Teleferico@2026"
DEFAULT TABLESPACE USERS
TEMPORARY TABLESPACE TEMP;
 
ALTER USER teleferico QUOTA UNLIMITED ON USERS;
 
-- Otorgar todos los privilegios necesarios
GRANT ALL PRIVILEGES TO teleferico;
 
-- Otorgar acceso al diccionario de datos (necesario para CU06)
GRANT SELECT ON SYS.DBA_USERS TO teleferico;
GRANT SELECT ON SYS.DBA_ROLE_PRIVS TO teleferico;
GRANT SELECT ON SYS.ROLE_SYS_PRIVS TO teleferico;
GRANT SELECT_CATALOG_ROLE TO teleferico;
```
 
> **Nota:** Si Oracle muestra el error `ORA-65096: invalid common user or role name`, asegurarse de ejecutar primero el `ALTER SESSION SET "_ORACLE_SCRIPT" = TRUE` en la misma sesión.
 
---
 
**5. Identificar el DSN correcto de la instalación Oracle**
 
Crear la conexion en SQLDeveloper o DBeaver con el usuario `teleferico` y verificar el service name o SID correcto para tu instalación. EL SIS es `xe`.
 
Para verificar el service name exacto de tu Oracle, ejecutar en DBeaver como SYS:
 

 
**6. Configurar la conexión en `db.py`**
 
Abrir el archivo `db.py` y modificar los valores según tu instalación:
 
```python
try:
    import cx_Oracle
except Exception:
    import oracledb as cx_Oracle
 
def get_connection():
    # ── MODIFICAR ESTOS VALORES SEGÚN TU INSTALACIÓN ──
    HOST         = "localhost"       # IP o nombre del servidor Oracle
    PORT         = 1521              # Puerto (casi siempre 1521)
    SERVICE_NAME = "xe"        
    USER         = "teleferico"      # Usuario creado en el paso 4
    PASSWORD     = "Teleferico@2026" # Contraseña del usuario
    # ──────────────────────────────────────────────────
 
    dsn = cx_Oracle.makedsn(HOST, PORT, service_name=SERVICE_NAME)
    return cx_Oracle.connect(user=USER, password=PASSWORD, dsn=dsn)
```
 
**Ejemplos de configuración según versión de Oracle:**
 
```python

dsn = cx_Oracle.makedsn("localhost", 1521, sid="XE")
```
 
**Verificar que la conexión funciona** antes de correr Flask:
 

 
**7. Ejecutar la aplicación Flask**
```bash
python app.py
```
 
Abrir el navegador en: `http://localhost:5000`
 
## Tecnologías utilizadas
 
| Tecnología | Versión | Uso |
|---|---|---|
| Oracle Database | 19c / 21c | Motor de base de datos principal |
| Python | 3.10+ | Lenguaje backend |
| Flask | 3.x | Framework web |
| cx_Oracle / oracledb | 8.x | Conector Python-Oracle |
| HTML + CSS | — | Frontend / templates Jinja2 |
| DBeaver | 24.x | Administración de la BD |
 
---
 
## Estructura del proyecto
 
```
sistema-teleferico/
│
├── app.py                  # Rutas Flask y lógica de invocación a Oracle
├── db.py                   # Configuración de conexión a Oracle
│
├── templates/
│   ├── base.html           # Template base con header y footer
│   ├── index.html          # Página principal con introducción del proyecto
│   ├── cu01.html           # CU01 — Emitir credenciales
│   ├── cu02.html           # CU02 — Recargar saldo
│   ├── cu03.html           # CU03 — Controlar acceso y cobro
│   ├── cu04.html           # CU04 — Consultar saldo e historial
│   ├── cu05.html           # CU05 — Reportes y métricas
│   ├── cu06.html           # CU06 — Administrar usuarios y roles
│   ├── pasajeros.html      # CRUD completo de pasajeros
│   ├── editarPasajero.html # Formulario de edición de pasajero
│   ├── resultado.html      # Template de resultados standalone
│   └── _resultado_embebido.html  # Partial de resultados inline
│
├── static/
│   └── style.css           # Estilos del sistema
│
└── scripts_oracle/
    ├── 01_tablas.sql       # Creación de las 10 tablas
    ├── 02_inserts.sql      # Datos de prueba (30 registros por tabla)
    ├── 03_objetos.sql      # Procedimientos, funciones, triggers, vistas, paquete
    └── 04_usuarios.sql     # Usuarios, roles y perfiles Oracle
```
 
---
 
## Modelo de base de datos
 
El sistema cuenta con **10 tablas** relacionales en Oracle:
 
| Tabla | Tipo | Descripción |
|---|---|---|
| `LINEA` | Entidad principal | Las 10 líneas de la red (Rojo, Amarillo, Verde...) |
| `ESTACION` | Entidad principal | 30 estaciones distribuidas por línea |
| `MOLINETE` | Entidad principal | Hardware de control de acceso por estación |
| `PASAJERO` | Entidad principal | Registro de usuarios del sistema |
| `CATEGORIA_TARJETA` | Entidad principal | Normal, Adulto Mayor, Discapacidad, Estudiante |
| `TARJETA` | **Tabla intermedia** | Une PASAJERO con CATEGORIA_TARJETA, almacena saldo |
| `RECARGA` | **Tabla intermedia** | Historial de recargas por tarjeta |
| `VIAJE` | **Tabla central** | Registro transaccional de cada acceso al molinete |
| `TIPOTICKET` | Entidad principal | Normal, Turismo, Escolar, Express |
| `TICKET` | **Tabla intermedia** | Tickets físicos de un solo uso |
 
---
 
## Objetos del servidor Oracle implementados
 
### Procedimientos almacenados
| Procedimiento | Caso de uso | Descripción |
|---|---|---|
| `sp_emitir_tarjeta` | CU01 | Emite tarjeta validando pasajero y categoría |
| `sp_emitir_ticket` | CU01 | Emite ticket validando tipo y estación |
| `sp_recarga_saldo` | CU02 | Recarga saldo con transacción ACID |
| `sp_registrar_acceso` | CU03 | Registra acceso aplicando lógica tarifaria |
| `sp_mostrar_viaje` | CU04 | Cursor con historial de viajes por CI |
| `sp_mostrar_lineas_molinetes` | CU05 | Cursor anidado líneas-estaciones-molinetes |
 
### Funciones
| Función | Caso de uso | Descripción |
|---|---|---|
| `fn_calcular_tarifa` | CU03 | Calcula monto según categoría y transbordo |
| `fn_es_transbordo` | CU03 | Detecta si el viaje es transbordo (< 60 min) |
| `fn_edad_pasajero_anios` | CU04 | Edad del pasajero en años |
| `fn_antiguedad_tarjeta_meses` | CU04 | Meses desde emisión de la tarjeta |
| `fn_dias_emision_ticket` | CU04 | Días desde emisión del ticket |
 
### Paquete PL/SQL
| Paquete | Descripción |
|---|---|
| `pkg_operaciones_teleferico` | Agrupa las 3 funciones y 2 procedimientos del CU04 |
 
### Triggers
| Trigger | Caso de uso | Descripción |
|---|---|---|
| `trg_auditoria_cambios` | CU01 | Audita INSERT/UPDATE/DELETE en TARJETA |
| `trg_bloqueo_domingo` | CU01 | Bloquea emisión de tarjetas los domingos |
| `trg_validacion_recargas` | CU02 | Valida monto mínimo de 10 Bs en recargas |
| `trg_auto_cobro_viaje` | CU03 | Descuenta saldo automáticamente al registrar viaje |
| `trg_restriccion_molinetes` | CU05 | Impide eliminar molinetes en estado ACTIVO |
 
### Vistas
| Vista | Caso de uso | Descripción |
|---|---|---|
| `VW_HISTORIAL_PASAJERO` | CU04 | Historial completo de viajes por pasajero |
| `VW_RECAUDACION_POR_LINEA` | CU05 | Recaudación total agrupada por línea |
| `VW_PASAJEROS_POR_FRANJA` | CU05 | Volumen de pasajeros por franja horaria |
 
### Usuarios y roles Oracle
| Usuario | Rol asignado | Perfil |
|---|---|---|
| `admin_gabriel` | `rol_admin_teleferico` | `perfil_admin` |
| `auditor_marcos` | `rol_auditor_teleferico` | `perfil_operativo` |
| `cajero_lucia` | `rol_cajero_teleferico` | `perfil_operativo` |
| `cajero_pedro` | `rol_cajero_teleferico` | `perfil_operativo` |
 
---
 
## Instalación y configuración
 
### Requisitos previos
 
- Oracle Database 19c o 21c instalado y corriendo
- Python 3.10 o superior
- pip (gestor de paquetes Python)
### Pasos de instalación
 
**1. Clonar el repositorio**
```bash
git clone https://github.com/hiygabo/sistema-teleferico-BASE-DE-DATOS2-ORACLE
cd sistema-teleferico-BASE-DE-DATOS2-ORACLE
```
 
**2. Crear entorno virtual e instalar dependencias**
```bash
python -m venv venv
 
# Windows
venv\Scripts\activate
 
# Linux / Mac
source venv/bin/activate
 
pip install flask cx_Oracle oracledb
```
 
**3. Ejecutar los scripts Oracle en DBeaver**
 
Ejecutar en este orden, cada script por separado:
```
01_tablas.sql       → Crea las 10 tablas
02_inserts.sql      → Inserta datos de prueba
03_objetos.sql      → Crea procedimientos, funciones, triggers, vistas y paquete
04_usuarios.sql     → Crea usuarios, roles y perfiles
```
 
**4. Configurar la conexión en `db.py`**
```python
import cx_Oracle
 
def get_connection():
    dsn = cx_Oracle.makedsn("localhost", 1521, service_name="XEPDB1")
    return cx_Oracle.connect(
        user="teleferico",
        password="Teleferico@2026",
        dsn=dsn
    )
```
 
**5. Ejecutar la aplicación Flask**
```bash
python app.py
```
 
Abrir el navegador en: `http://localhost:5000`
 
---
 
## Casos de uso implementados
 
| CU | Nombre | Objetos Oracle invocados |
|---|---|---|
| CU01 | Emitir credenciales | `sp_emitir_tarjeta`, `sp_emitir_ticket`, `trg_auditoria_cambios`, `trg_bloqueo_domingo` |
| CU02 | Recargar saldo | `sp_recarga_saldo`, `trg_validacion_recargas` |
| CU03 | Controlar acceso y cobro | `sp_registrar_acceso`, `fn_es_transbordo`, `fn_calcular_tarifa`, `trg_auto_cobro_viaje` |
| CU04 | Consultar saldo e historial | `pkg_operaciones_teleferico`, `VW_HISTORIAL_PASAJERO` |
| CU05 | Reportes y métricas | `sp_mostrar_lineas_molinetes`, `VW_RECAUDACION_POR_LINEA`, `VW_PASAJEROS_POR_FRANJA`, `trg_restriccion_molinetes` |
| CU06 | Administrar usuarios y roles | `DBA_USERS`, `DBA_ROLE_PRIVS`, `ROLE_SYS_PRIVS` |
 
### CRUD implementado
| Tabla | Operaciones |
|---|---|
| `PASAJERO` | CREATE, READ, UPDATE, DELETE |
| `TARJETA` | CREATE (vía `sp_emitir_tarjeta`) |
| `RECARGA` | CREATE (vía `sp_recarga_saldo`) |
 
---
 
## Lógica tarifaria
 
```
Tarifa base (1ra línea):     3.00 Bs
Transbordo (< 60 min):       2.00 Bs
Adulto Mayor (50% desc):     1.50 Bs
Discapacidad (50% desc):     1.50 Bs
Estudiante (25% desc):       2.25 Bs
Mínimo de recarga:          10.00 Bs
Máximo de recarga:         500.00 Bs
```
 
---

 
*Base de Datos 2 — UMSA Informática — 2026*