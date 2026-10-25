
import sqlite3

DB_NAME = "autos_colombia.db"


def conectar():
    conexion = sqlite3.connect(DB_NAME)
    conexion.row_factory = sqlite3.Row
    return conexion


def inicializar_db():
    conexion = conectar()

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS celdas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT NOT NULL,
            tipo_vehiculo TEXT NOT NULL,
            propietario TEXT NOT NULL,
            celda_id INTEGER NOT NULL,
            entrada TEXT NOT NULL,
            salida TEXT,
            FOREIGN KEY (celda_id) REFERENCES celdas(id)
        )
    """)

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS novedades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            fecha TEXT NOT NULL
        )
    """)

    for numero in range(1, 11):
        conexion.execute(
            "INSERT OR IGNORE INTO celdas (nombre) VALUES (?)",
            (f"C-{numero:02d}",)
        )

    conexion.commit()
    conexion.close()


if __name__ == "__main__":
    inicializar_db()
    print("Base de datos creada correctamente.")
    print("Se han preparado 10 celdas de parqueo.")
