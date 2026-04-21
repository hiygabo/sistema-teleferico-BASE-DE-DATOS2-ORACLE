from flask import Flask, render_template, request, redirect, url_for, flash

try:
    import cx_Oracle
except Exception:
    import oracledb as cx_Oracle

import db


app = Flask(__name__)
app.secret_key = "clave_secreta_tel"


ORA_FRIENDLY_MESSAGES = {
    20001: "Validacion fallida de negocio (ORA-20001). Verifica los datos enviados.",
    20002: "Operacion no permitida por regla de negocio (ORA-20002).",
    20003: "Parametro invalido o restriccion operativa detectada (ORA-20003).",
    20004: "No se encontro el registro requerido (ORA-20004).",
    20005: "El valor ingresado no cumple la politica de validacion (ORA-20005).",
    20006: "No fue posible completar la operacion por una condicion de negocio (ORA-20006).",
}


def _build_error_payload(exc, contexto):
    code = None
    raw_message = str(exc)

    if isinstance(exc, cx_Oracle.DatabaseError):
        error_obj = exc.args[0]
        code = abs(getattr(error_obj, "code", 0))
        raw_message = getattr(error_obj, "message", str(exc))

    if code in ORA_FRIENDLY_MESSAGES:
        mensaje = f"{ORA_FRIENDLY_MESSAGES[code]} Detalle tecnico: {raw_message}"
    elif code == 942:
        mensaje = (
            "No tienes permisos para consultar una o mas vistas del diccionario de Oracle "
            "(por ejemplo DBA_USERS, DBA_ROLE_PRIVS o ROLE_SYS_PRIVS). "
            f"Detalle tecnico: {raw_message}"
        )
        return {
            "titulo": "Error de permisos Oracle (ORA-00942)",
            "mensaje": mensaje,
            "lista_resultados": [
                "Conectate con SYS o un usuario DBA y ejecuta:",
                "GRANT SELECT ON SYS.DBA_USERS TO TELEFERICO;",
                "GRANT SELECT ON SYS.DBA_ROLE_PRIVS TO TELEFERICO;",
                "GRANT SELECT ON SYS.ROLE_SYS_PRIVS TO TELEFERICO;",
                "Luego cierra y vuelve a abrir sesion del usuario TELEFERICO.",
            ],
        }
    elif "PLS-00905" in raw_message or "ORA-06550" in raw_message:
        mensaje = (
            "El objeto PL/SQL en Oracle esta INVALIDO y no puede ejecutarse. "
            "Debes recompilar el procedimiento/paquete y corregir errores de compilacion. "
            f"Detalle tecnico: {raw_message}"
        )
        return {
            "titulo": "Error de compilacion PL/SQL",
            "mensaje": mensaje,
            "lista_resultados": [
                "Ejecuta en Oracle: ALTER PROCEDURE SP_RECARGA_SALDO COMPILE;",
                "Luego consulta errores: SELECT line, position, text FROM user_errors WHERE name = 'SP_RECARGA_SALDO' ORDER BY sequence;",
                "Si no compila, corrige el codigo PL/SQL del procedimiento y vuelve a compilar.",
            ],
        }
    else:
        mensaje = f"{contexto}. Detalle tecnico: {raw_message}"

    return {
        "titulo": "Error en la operacion",
        "mensaje": mensaje,
        "lista_resultados": [],
    }


def _render_error(exc, contexto, template_name="resultado.html"):
    payload = _build_error_payload(exc, contexto)
    if template_name == "resultado.html":
        return render_template(
            "resultado.html",
            titulo=payload["titulo"],
            mensaje=payload["mensaje"],
            lista_resultados=payload["lista_resultados"],
        )

    return render_template(template_name, resultado=payload)


def _render_cu_result(template_name, titulo, mensaje, lista_resultados):
    return render_template(
        template_name,
        resultado={
            "titulo": titulo,
            "mensaje": mensaje,
            "lista_resultados": lista_resultados,
        },
    )


def _fetch_dbms_output(cursor):
    salida = []
    line_var = cursor.var(str)
    status_var = cursor.var(int)
    while True:
        cursor.callproc("DBMS_OUTPUT.GET_LINE", [line_var, status_var])
        if status_var.getvalue() != 0:
            break
        value = line_var.getvalue()
        if value:
            salida.append(value)
    return salida


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/listaPasajeros")
def listaPasajeros():
    try:
        conexion = db.get_connection()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM pasajero")
            lista_pasajeros = cursor.fetchall()
        conexion.close()
        return render_template("pasajeros.html", pasajeros=lista_pasajeros)
    except Exception as exc:
        return _render_error(exc, "No se pudo consultar la lista de pasajeros")


@app.route("/agregarPasajero", methods=["POST"])
def agregarPasajero():
    ci = request.form["ci"]
    nombre = request.form["nombre"]
    paterno = request.form["paterno"]
    materno = request.form["materno"]
    fechanac = request.form["fechanac"]
    tipo_doc = request.form["tipo_doc"]

    try:
        conexion = db.get_connection()
        with conexion.cursor() as cursor:
            consulta = """
                INSERT INTO PASAJERO (ci, nombre, paterno, materno, fechanac, tipo_documento_validar)
                VALUES (:1, :2, :3, :4, TO_DATE(:5, 'YYYY-MM-DD'), :6)
            """
            cursor.execute(consulta, (ci, nombre, paterno, materno, fechanac, tipo_doc))
        conexion.commit()
        conexion.close()
        flash("Pasajero registrado con exito")
    except Exception as exc:
        flash(f"Error al registrar pasajero: {exc}")

    return redirect(url_for("listaPasajeros"))


@app.route("/eliminarPasajero/<ci>", methods=["GET"])
def eliminarPasajero(ci):
    try:
        conexion = db.get_connection()
        with conexion.cursor() as cursor:
            cursor.execute("DELETE FROM PASAJERO WHERE ci = :1", [ci])
        conexion.commit()
        conexion.close()
        flash(f"Pasajero con CI {ci} eliminado")
    except Exception as exc:
        flash(f"Error al eliminar pasajero: {exc}")

    return redirect(url_for("listaPasajeros"))


@app.route("/editarPasajero/<ci>", methods=["GET", "POST"])
def editarPasajero(ci):
    try:
        conexion = db.get_connection()
        with conexion.cursor() as cursor:
            if request.method == "GET":
                cursor.execute(
                    """
                    SELECT CI, NOMBRE, PATERNO, MATERNO,
                           TO_CHAR(FECHANAC, 'YYYY-MM-DD'), TIPO_DOCUMENTO_VALIDAR
                    FROM PASAJERO
                    WHERE CI = :1
                    """,
                    [ci],
                )
                pasajero_actual = cursor.fetchone()
                conexion.close()
                return render_template("editarPasajero.html", p=pasajero_actual)

            nombre = request.form["nombre"]
            paterno = request.form["paterno"]
            materno = request.form["materno"]
            fechanac = request.form["fechanac"]
            tipo_doc = request.form["tipo_doc"]

            cursor.execute(
                """
                UPDATE PASAJERO
                SET NOMBRE = :1,
                    PATERNO = :2,
                    MATERNO = :3,
                    FECHANAC = TO_DATE(:4, 'YYYY-MM-DD'),
                    TIPO_DOCUMENTO_VALIDAR = :5
                WHERE CI = :6
                """,
                (nombre, paterno, materno, fechanac, tipo_doc, ci),
            )
        conexion.commit()
        conexion.close()
        flash("Datos del pasajero actualizados")
        return redirect(url_for("listaPasajeros"))
    except Exception as exc:
        flash(f"Error al editar pasajero: {exc}")
        return redirect(url_for("listaPasajeros"))


@app.route("/cu01")
def cu01():
    return render_template("cu01.html")


@app.route("/cu02")
def cu02():
    return render_template("cu02.html")


@app.route("/cu03")
def cu03():
    return render_template("cu03.html")


@app.route("/cu04")
def cu04():
    return render_template("cu04.html")


@app.route("/cu05")
def cu05():
    return render_template("cu05.html")


@app.route("/cu06")
def cu06():
    return render_template("cu06.html")


@app.route("/cu01/emitir-tarjeta", methods=["POST"])
def cu01_emitir_tarjeta():
    ci = request.form["ci"]
    idcategoria = request.form["idcategoria"]
    saldo = request.form["saldo"]

    try:
        conexion = db.get_connection()
        with conexion.cursor() as cursor:
            cursor.callproc("sp_emitir_tarjeta", [ci, idcategoria, saldo])
        conexion.commit()
        conexion.close()

        return _render_cu_result(
            "cu01.html",
            "Resultado CU01 - Tarjeta emitida",
            "Se invoco sp_emitir_tarjeta correctamente. Los triggers de auditoria y bloqueo se ejecutan automaticamente en Oracle.",
            [f"CI: {ci}", f"Categoria: {idcategoria}", f"Saldo inicial: {saldo}"],
        )
    except Exception as exc:
        return _render_error(exc, "No se pudo emitir la tarjeta", template_name="cu01.html")


@app.route("/cu01/emitir-ticket", methods=["POST"])
def cu01_emitir_ticket():
    idtipo = request.form["idtipo"]
    idestacion = request.form["idestacion"]
    idviaje = request.form.get("idviaje") or None

    try:
        conexion = db.get_connection()
        with conexion.cursor() as cursor:
            cursor.execute(
                "BEGIN sp_emitir_ticket(:idtipo, :idestacion, :idviaje); END;",
                {"idtipo": idtipo, "idestacion": idestacion, "idviaje": idviaje},
            )
        conexion.commit()
        conexion.close()

        return _render_cu_result(
            "cu01.html",
            "Resultado CU01 - Ticket emitido",
            "Se invoco sp_emitir_ticket correctamente.",
            [
                f"Tipo ticket: {idtipo}",
                f"Estacion: {idestacion}",
                f"Id viaje (si aplica): {idviaje}",
            ],
        )
    except Exception as exc:
        return _render_error(exc, "No se pudo emitir el ticket", template_name="cu01.html")


@app.route("/cu01/ver-auditoria", methods=["POST"])
def cu01_ver_auditoria():
    try:
        conexion = db.get_connection()
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT idauditoria, accion, usuario, TO_CHAR(fecha_hora, 'YYYY-MM-DD HH24:MI:SS'),
                       NVL(dato_antes, 'N/A'), NVL(dato_despues, 'N/A')
                FROM auditoria
                ORDER BY idauditoria DESC
                FETCH FIRST 20 ROWS ONLY
                """
            )
            filas = cursor.fetchall()
        conexion.close()

        lista = [
            f"ID {f[0]} | {f[1]} | Usuario: {f[2]} | Fecha: {f[3]} | Antes: {f[4]} | Despues: {f[5]}"
            for f in filas
        ]
        return _render_cu_result(
            "cu01.html",
            "Resultado CU01 - Trigger trg_auditoria_cambios",
            "Ultimos registros de auditoria generados por operaciones sobre TARJETA.",
            lista,
        )
    except Exception as exc:
        return _render_error(exc, "No se pudo consultar AUDITORIA", template_name="cu01.html")


@app.route("/cu02/recargar", methods=["POST"])
def cu02_recargar():
    idtarjeta = request.form["idtarjeta"]
    monto = request.form["monto"]

    try:
        conexion = db.get_connection()
        with conexion.cursor() as cursor:
            cursor.callproc("sp_recarga_saldo", [idtarjeta, monto])
        conexion.commit()
        conexion.close()

        return _render_cu_result(
            "cu02.html",
            "Resultado CU02 - Recarga de saldo",
            "Se invoco sp_recarga_saldo correctamente. El trigger de validacion de recargas se ejecuta en Oracle.",
            [f"Tarjeta: {idtarjeta}", f"Monto abonado: {monto} Bs"],
        )
    except Exception as exc:
        return _render_error(exc, "No se pudo recargar saldo", template_name="cu02.html")


@app.route("/cu03/registrar-acceso", methods=["POST"])
def cu03_registrar_acceso():
    idtarjeta = request.form["idtarjeta"]
    idmolinete = request.form["idmolinete"]

    try:
        conexion = db.get_connection()
        with conexion.cursor() as cursor:
            cursor.callproc("sp_registrar_acceso", [idtarjeta, idmolinete])
        conexion.commit()
        conexion.close()

        return _render_cu_result(
            "cu03.html",
            "Resultado CU03 - Acceso registrado",
            "Se invoco sp_registrar_acceso correctamente. La funcion de tarifa/transbordo y el trigger de descuento automatico se ejecutan en Oracle.",
            [f"Tarjeta: {idtarjeta}", f"Molinete: {idmolinete}"],
        )
    except Exception as exc:
        return _render_error(exc, "No se pudo registrar el acceso", template_name="cu03.html")


@app.route("/cu04/mostrar-viaje", methods=["POST"])
def cu04_mostrar_viaje():
    ci = request.form["ci"]

    try:
        conexion = db.get_connection()
        with conexion.cursor() as cursor:
            cursor.callproc("pkg_operaciones_teleferico.sp_mostrar_viaje", [ci])
            cursor.execute(
                """
                SELECT dato_importante, usuario_consulta, TO_CHAR(fecha_consulta, 'YYYY-MM-DD HH24:MI:SS')
                FROM tabla_auxiliar
                ORDER BY fecha_consulta DESC
                FETCH FIRST 30 ROWS ONLY
                """
            )
            filas = cursor.fetchall()
        conexion.commit()
        conexion.close()

        lista = [f"Dato: {f[0]} | Usuario: {f[1]} | Fecha: {f[2]}" for f in filas]
        return _render_cu_result(
            "cu04.html",
            "Resultado CU04 - Historial de viaje respaldado",
            "Se invoco pkg_operaciones_teleferico.sp_mostrar_viaje y luego se consulto TABLA_AUXILIAR.",
            lista,
        )
    except Exception as exc:
        return _render_error(exc, "No se pudo ejecutar sp_mostrar_viaje", template_name="cu04.html")


@app.route("/cu04/historial", methods=["POST"])
def cu04_historial():
    ci = request.form["ci_historial"]

    try:
        conexion = db.get_connection()
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT pasajero, categoria, idtarjeta, saldo, idviaje, monto_cobrado, estransbordo,
                       TO_CHAR(fecha_hora_ingreso, 'YYYY-MM-DD HH24:MI:SS'), estacion, linea
                FROM vw_historial_pasajero
                WHERE ci = :1
                ORDER BY fecha_hora_ingreso DESC
                """,
                [ci],
            )
            filas = cursor.fetchall()
        conexion.close()

        lista = [
            f"Pasajero: {f[0]} | Categoria: {f[1]} | Tarjeta: {f[2]} | Saldo: {f[3]} | Viaje: {f[4]} | Cobro: {f[5]} | Transbordo: {f[6]} | Fecha: {f[7]} | Estacion: {f[8]} | Linea: {f[9]}"
            for f in filas
        ]
        return _render_cu_result(
            "cu04.html",
            "Resultado CU04 - Vista VW_HISTORIAL_PASAJERO",
            f"Se consulto la vista VW_HISTORIAL_PASAJERO para el CI {ci}.",
            lista,
        )
    except Exception as exc:
        return _render_error(exc, "No se pudo consultar el historial de pasajero", template_name="cu04.html")


@app.route("/cu04/edad", methods=["POST"])
def cu04_edad():
    ci = request.form["ci_edad"]

    try:
        conexion = db.get_connection()
        with conexion.cursor() as cursor:
            edad = cursor.callfunc("pkg_operaciones_teleferico.fn_edad_pasajero_anios", int, [ci])
        conexion.close()

        return _render_cu_result(
            "cu04.html",
            "Resultado CU04 - Funcion fn_edad_pasajero_anios",
            "Se invoco la funcion de edad del paquete pkg_operaciones_teleferico.",
            [f"CI: {ci}", f"Edad: {edad} anios"],
        )
    except Exception as exc:
        return _render_error(exc, "No se pudo calcular la edad del pasajero", template_name="cu04.html")


@app.route("/cu04/antiguedad", methods=["POST"])
def cu04_antiguedad():
    idtarjeta = request.form["idtarjeta_antiguedad"]

    try:
        conexion = db.get_connection()
        with conexion.cursor() as cursor:
            meses = cursor.callfunc("pkg_operaciones_teleferico.fn_antiguedad_tarjeta_meses", int, [idtarjeta])
        conexion.close()

        return _render_cu_result(
            "cu04.html",
            "Resultado CU04 - Funcion fn_antiguedad_tarjeta_meses",
            "Se invoco la funcion de antiguedad de tarjeta.",
            [f"Tarjeta: {idtarjeta}", f"Antiguedad: {meses} meses"],
        )
    except Exception as exc:
        return _render_error(exc, "No se pudo calcular la antiguedad de la tarjeta", template_name="cu04.html")


@app.route("/cu04/dias-ticket", methods=["POST"])
def cu04_dias_ticket():
    idticket = request.form["idticket_dias"]

    try:
        conexion = db.get_connection()
        with conexion.cursor() as cursor:
            dias = cursor.callfunc("pkg_operaciones_teleferico.fn_dias_emision_ticket", int, [idticket])
        conexion.close()

        return _render_cu_result(
            "cu04.html",
            "Resultado CU04 - Funcion fn_dias_emision_ticket",
            "Se invoco la funcion de dias desde la emision del ticket.",
            [f"Ticket: {idticket}", f"Dias transcurridos: {dias}"],
        )
    except Exception as exc:
        return _render_error(exc, "No se pudo calcular los dias del ticket", template_name="cu04.html")


@app.route("/cu05/recaudacion", methods=["POST"])
def cu05_recaudacion():
    try:
        conexion = db.get_connection()
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT linea, cantidad_viajes, recaudacion_total_bs
                FROM vw_recaudacion_por_linea
                ORDER BY linea
                """
            )
            filas = cursor.fetchall()
        conexion.close()

        lista = [f"Linea: {f[0]} | Viajes: {f[1]} | Recaudacion total: {f[2]} Bs" for f in filas]
        return _render_cu_result(
            "cu05.html",
            "Resultado CU05 - Vista VW_RECAUDACION_POR_LINEA",
            "Reporte de recaudacion por linea generado desde la vista.",
            lista,
        )
    except Exception as exc:
        return _render_error(exc, "No se pudo consultar VW_RECAUDACION_POR_LINEA", template_name="cu05.html")


@app.route("/cu05/franja", methods=["POST"])
def cu05_franja():
    try:
        conexion = db.get_connection()
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT franja_horaria, total_pasajeros
                FROM vw_pasajeros_por_franja
                ORDER BY franja_horaria
                """
            )
            filas = cursor.fetchall()
        conexion.close()

        lista = [f"Franja: {f[0]} | Total pasajeros: {f[1]}" for f in filas]
        return _render_cu_result(
            "cu05.html",
            "Resultado CU05 - Vista VW_PASAJEROS_POR_FRANJA",
            "Reporte de pasajeros por franja horaria generado desde la vista.",
            lista,
        )
    except Exception as exc:
        return _render_error(exc, "No se pudo consultar VW_PASAJEROS_POR_FRANJA", template_name="cu05.html")


@app.route("/cu05/lineas-molinetes", methods=["POST"])
def cu05_lineas_molinetes():
    try:
        conexion = db.get_connection()
        with conexion.cursor() as cursor:
            cursor.callproc("DBMS_OUTPUT.ENABLE", [None])
            cursor.callproc("sp_mostrar_lineas_molinetes")
            salida = _fetch_dbms_output(cursor)
        conexion.close()

        return _render_cu_result(
            "cu05.html",
            "Resultado CU05 - Procedimiento sp_mostrar_lineas_molinetes",
            "Se invoco el procedimiento y se recupero su salida de DBMS_OUTPUT.",
            salida,
        )
    except Exception as exc:
        return _render_error(exc, "No se pudo ejecutar sp_mostrar_lineas_molinetes", template_name="cu05.html")


@app.route("/cu05/restriccion-molinete", methods=["POST"])
def cu05_restriccion_molinete():
    idmolinete = request.form["idmolinete"]
    try:
        conexion = db.get_connection()
        with conexion.cursor() as cursor:
            cursor.execute("DELETE FROM molinete WHERE idmolinete = :1", [idmolinete])
        conexion.commit()
        conexion.close()

        return _render_cu_result(
            "cu05.html",
            "Resultado CU05 - Prueba Trigger trg_restriccion_molinetes",
            "Se intento eliminar el molinete. Si estaba ACTIVO, Oracle debio bloquear por trigger.",
            [f"Molinete procesado: {idmolinete}"],
        )
    except Exception as exc:
        return _render_error(exc, "No se pudo ejecutar la prueba de restriccion de molinete", template_name="cu05.html")


@app.route("/cu06/usuarios-roles", methods=["POST"])
def cu06_usuarios_roles():
    try:
        conexion = db.get_connection()
        with conexion.cursor() as cursor:
            usuarios_objetivo = ["ADMIN_GABRIEL", "AUDITOR_MARCOS", "CAJERO_LUCIA", "CAJERO_PEDRO"]

            cursor.execute(
                """
                SELECT username, profile, account_status
                FROM dba_users
                WHERE username IN (:1, :2, :3, :4)
                ORDER BY username
                """,
                usuarios_objetivo,
            )
            filas_usuarios = cursor.fetchall()

            cursor.execute(
                """
                SELECT grantee, granted_role
                FROM dba_role_privs
                WHERE grantee IN (:1, :2, :3, :4)
                ORDER BY grantee, granted_role
                """,
                usuarios_objetivo,
            )
            filas_roles = cursor.fetchall()

            cursor.execute(
                """
                SELECT privilege
                FROM role_sys_privs
                WHERE role = 'ROL_ADMIN_TELEFERICO'
                ORDER BY privilege
                """
            )
            filas_privilegios = cursor.fetchall()
        conexion.close()

        lista = []
        lista.append("=== DBA_USERS ===")
        if filas_usuarios:
            for f in filas_usuarios:
                lista.append(f"Usuario: {f[0]} | Perfil: {f[1]} | Estado: {f[2]}")
        else:
            lista.append("Sin registros en DBA_USERS para los usuarios solicitados")

        lista.append("=== DBA_ROLE_PRIVS ===")
        if filas_roles:
            for f in filas_roles:
                lista.append(f"Grantee: {f[0]} | Rol: {f[1]}")
        else:
            lista.append("Sin registros en DBA_ROLE_PRIVS para los usuarios solicitados")

        lista.append("=== ROLE_SYS_PRIVS (ROL_ADMIN_TELEFERICO) ===")
        if filas_privilegios:
            for f in filas_privilegios:
                lista.append(f"Privilegio: {f[0]}")
        else:
            lista.append("Sin privilegios encontrados para ROL_ADMIN_TELEFERICO")

        return _render_cu_result(
            "cu06.html",
            "Resultado CU06 - Usuarios y Roles",
            "Consulta de solo lectura a DBA_USERS, DBA_ROLE_PRIVS y ROLE_SYS_PRIVS.",
            lista,
        )
    except cx_Oracle.DatabaseError as exc:
        error_obj = exc.args[0]
        if abs(getattr(error_obj, "code", 0)) == 942:
            return _render_cu_result(
                "cu06.html",
                "Error de permisos Oracle (ORA-00942)",
                "El usuario TELEFERICO no tiene acceso a vistas del diccionario requeridas por CU06.",
                [
                    "Ejecuta con SYS/DBA:",
                    "GRANT SELECT ON SYS.DBA_USERS TO TELEFERICO;",
                    "GRANT SELECT ON SYS.DBA_ROLE_PRIVS TO TELEFERICO;",
                    "GRANT SELECT ON SYS.ROLE_SYS_PRIVS TO TELEFERICO;",
                    "Reinicia la sesion y vuelve a probar CU06.",
                ],
            )
        return _render_error(exc, "No se pudo consultar usuarios y roles", template_name="cu06.html")
    except Exception as exc:
        return _render_error(exc, "No se pudo consultar usuarios y roles", template_name="cu06.html")


if __name__ == "__main__":
    app.run(debug=True)

