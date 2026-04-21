try:
    import cx_Oracle
except Exception:
    import oracledb as cx_Oracle

DB_USER = "teleferico"
DB_PASS = "Teleferico@2026"
DB_DSN = "localhost:1521/xe"

def get_connection():
    try:
        conexion = cx_Oracle.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)
        return conexion
    except Exception as e:
        raise RuntimeError(f"No se pudo conectar a Oracle ({DB_DSN}) con el usuario {DB_USER}: {e}")


def get_conection():
    return get_connection()