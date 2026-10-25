
from flask import Flask, request, redirect, url_for, render_template_string
from database import conectar, inicializar_db
from datetime import datetime

app = Flask(__name__)

ESTILOS = """
<style>
* { box-sizing: border-box; }
body { margin: 0; font-family: Arial, sans-serif; background: #f1f5f9; color: #1e293b; }
header { background: #12345a; color: white; padding: 22px; }
header h1 { margin: 0 0 8px; }
nav { display: flex; flex-wrap: wrap; gap: 18px; margin-top: 18px; }
nav a { color: white; text-decoration: none; font-weight: bold; }
main { max-width: 1050px; margin: 28px auto; padding: 0 18px; }
.panel { background: white; padding: 22px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 3px 12px #0000000d; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 16px; }
.numero { font-size: 30px; font-weight: bold; margin: 10px 0; }
label { display: block; font-weight: bold; margin-top: 14px; }
input, select, textarea { width: 100%; padding: 11px; margin-top: 6px; border: 1px solid #cbd5e1; border-radius: 6px; }
button, .boton { display: inline-block; margin-top: 16px; background: #176b45; color: white; padding: 11px 16px; border: 0; border-radius: 6px; cursor: pointer; text-decoration: none; }
table { width: 100%; border-collapse: collapse; background: white; }
th, td { text-align: left; padding: 12px 9px; border-bottom: 1px solid #e2e8f0; }
th { background: #eaf0f6; }
.tabla { overflow-x: auto; }
.libre { color: #15803d; font-weight: bold; }
.ocupada { color: #b91c1c; font-weight: bold; }
.mensaje { padding: 12px; background: #dcfce7; border-radius: 6px; }
.error { padding: 12px; background: #fee2e2; border-radius: 6px; }
small { color: #64748b; }
</style>
"""


def pagina(titulo, contenido):
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ titulo }} - Autos Colombia</title>
    """ + ESTILOS + """
    </head>
    <body>
        <header>
            <h1>Autos Colombia</h1>
            <div> Sistema de gestión de parqueadero</div>
            <nav>
                <a href="{{ url_for('inicio') }}">Inicio</a>
                <a href="{{ url_for('entrada') }}">Registrar entrada</a>
                <a href="{{ url_for('historial') }}">Historial</a>
                <a href="{{ url_for('celdas') }}">Celdas</a>
                <a href="{{ url_for('novedades') }}">Novedades</a>
            </nav>
        </header>
        <main>
            <h2>{{ titulo }}</h2>
            {{ contenido | safe }}
        </main>
    </body>
    </html>
    """, titulo=titulo, contenido=contenido)


@app.route("/")
def inicio():
    conexion = conectar()

    total = conexion.execute(
        "SELECT COUNT(*) FROM celdas"
    ).fetchone()[0]

    ocupadas = conexion.execute("""
        SELECT COUNT(DISTINCT celda_id)
        FROM movimientos
        WHERE salida IS NULL
    """).fetchone()[0]

    vehiculos = conexion.execute("""
        SELECT m.*, c.nombre AS celda
        FROM movimientos m
        JOIN celdas c ON c.id = m.celda_id
        WHERE m.salida IS NULL
        ORDER BY m.entrada DESC
    """).fetchall()

    conexion.close()

    filas = "".join(
        f"<tr><td>{v['placa']}</td>"
        f"<td>{v['propietario']}</td>"
        f"<td>{v['tipo_vehiculo']}</td>"
        f"<td>{v['celda']}</td>"
        f"<td>{v['entrada']}</td>"
        f"<td><form method='post' action='/salida/{v['id']}'>"
        f"<button type='submit'>Registrar salida</button></form></td></tr>"
        for v in vehiculos
    )

    if not filas:
        filas = "<tr><td colspan='6'>No hay vehículos dentro del parqueadero.</td></tr>"

    contenido = f"""
    <div class="grid">
        <section class="panel"><h3>Celdas totales</h3>
            <div class="numero">{total}</div></section>
        <section class="panel"><h3>Celdas ocupadas</h3>
            <div class="numero">{ocupadas}</div></section>
        <section class="panel"><h3>Celdas libres</h3>
            <div class="numero">{total - ocupadas}</div></section>
    </div>
    <section class="panel">
        <h3>Vehículos actualmente en el parqueadero</h3>
        <div class="tabla"><table>
        <tr><th>Placa</th><th>Propietario</th><th>Tipo</th>
        <th>Celda</th><th>Entrada</th><th>Acción</th></tr>
        {filas}
        </table></div>
        <a class="boton" href="/entrada">Registrar vehículo</a>
    </section>
    """
    return pagina("Panel principal", contenido)


@app.route("/entrada", methods=["GET", "POST"])
def entrada():
    error = ""

    if request.method == "POST":
        placa = request.form.get("placa", "").strip().upper()
        propietario = request.form.get("propietario", "").strip()
        tipo = request.form.get("tipo_vehiculo", "").strip()

        if not placa or not propietario or not tipo:
            error = "Todos los campos son obligatorios."
        else:
            conexion = conectar()

            existente = conexion.execute("""
                SELECT id FROM movimientos
                WHERE UPPER(placa) = ? AND salida IS NULL
            """, (placa,)).fetchone()

            celda = conexion.execute("""
                SELECT c.id, c.nombre
                FROM celdas c
                WHERE NOT EXISTS (
                    SELECT 1 FROM movimientos m
                    WHERE m.celda_id = c.id AND m.salida IS NULL
                )
                ORDER BY c.id LIMIT 1
            """).fetchone()

            if existente:
                error = "Este vehículo ya se encuentra dentro del parqueadero."
            elif not celda:
                error = "No hay celdas disponibles."
            else:
                ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conexion.execute("""
                    INSERT INTO movimientos
                    (placa, tipo_vehiculo, propietario, celda_id, entrada)
                    VALUES (?, ?, ?, ?, ?)
                """, (placa, tipo, propietario, celda["id"], ahora))
                conexion.commit()
                conexion.close()
                return redirect(url_for("inicio"))

            conexion.close()

    contenido = f"""
    <section class="panel">
        <p>Registra los datos del vehículo. El sistema asignará la primera celda disponible.</p>
        {"<p class='error'>" + error + "</p>" if error else ""}
        <form method="post">
            <label>Placa del vehículo</label>
            <input name="placa" maxlength="10" required placeholder="Ej. ABC123"
                value="{request.form.get('placa', '')}">
            <label>Nombre del propietario</label>
            <input name="propietario" required
                value="{request.form.get('propietario', '')}">
            <label>Tipo de vehículo</label>
            <select name="tipo_vehiculo" required>
                <option value="">Selecciona una opción</option>
                <option>Automóvil</option>
                <option>Motocicleta</option>
                <option>Camioneta</option>
            </select>
            <button type="submit">Registrar entrada</button>
        </form>
    </section>
    """
    return pagina("Entrada de vehículos", contenido)


@app.route("/salida/<int:movimiento_id>", methods=["POST"])
def salida(movimiento_id):
    conexion = conectar()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conexion.execute("""
        UPDATE movimientos
        SET salida = ?
        WHERE id = ? AND salida IS NULL
    """, (ahora, movimiento_id))

    conexion.commit()
    conexion.close()
    return redirect(url_for("inicio"))


@app.route("/historial")
def historial():
    conexion = conectar()
    movimientos = conexion.execute("""
        SELECT m.*, c.nombre AS celda
        FROM movimientos m
        JOIN celdas c ON c.id = m.celda_id
        ORDER BY m.id DESC
    """).fetchall()
    conexion.close()

    filas = "".join(
        f"<tr><td>{m['placa']}</td><td>{m['propietario']}</td>"
        f"<td>{m['tipo_vehiculo']}</td><td>{m['celda']}</td>"
        f"<td>{m['entrada']}</td><td>{m['salida'] or 'Dentro del parqueadero'}</td></tr>"
        for m in movimientos
    )

    if not filas:
        filas = "<tr><td colspan='6'>Aún no hay movimientos registrados.</td></tr>"

    contenido = f"""
    <section class="panel"><div class="tabla"><table>
    <tr><th>Placa</th><th>Propietario</th><th>Tipo</th>
    <th>Celda</th><th>Entrada</th><th>Salida</th></tr>
    {filas}
    </table></div></section>
    """
    return pagina("Historial de movimientos", contenido)


@app.route("/celdas")
def celdas():
    conexion = conectar()
    lista = conexion.execute("""
        SELECT c.id, c.nombre,
            m.placa, m.propietario
        FROM celdas c
        LEFT JOIN movimientos m
            ON m.celda_id = c.id AND m.salida IS NULL
        ORDER BY c.id
    """).fetchall()
    conexion.close()

    tarjetas = ""
    for celda in lista:
        if celda["placa"]:
            estado = "Ocupada"
            clase = "ocupada"
            detalle = f"Vehículo: {celda['placa']} — {celda['propietario']}"
        else:
            estado = "Libre"
            clase = "libre"
            detalle = "Disponible para asignación"
        tarjetas += f"""
        <section class="panel">
            <h3>{celda['nombre']}</h3>
            <p class="{clase}">{estado}</p>
            <p>{detalle}</p>
        </section>
        """

    return pagina("Estado de las celdas", f'<div class="grid">{tarjetas}</div>')


@app.route("/novedades/eliminar/<int:novedad_id>", methods=["POST"])
def eliminar_novedad(novedad_id):
    conexion = conectar()

    conexion.execute(
        "DELETE FROM novedades WHERE id = ?",
        (novedad_id,)
    )

    conexion.commit()
    conexion.close()

    return redirect(url_for("novedades"))


@app.route("/novedades", methods=["GET", "POST"])
def novedades():
    mensaje = ""

    if request.method == "POST":
        descripcion = request.form.get("descripcion", "").strip()

        if descripcion:
            conexion = conectar()
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            conexion.execute(
                "INSERT INTO novedades (descripcion, fecha) VALUES (?, ?)",
                (descripcion, ahora)
            )

            conexion.commit()
            conexion.close()

            return redirect(url_for("novedades"))

        mensaje = "<p class='error'>Escribe una descripción.</p>"

    conexion = conectar()
    lista = conexion.execute(
        "SELECT * FROM novedades ORDER BY id DESC"
    ).fetchall()
    conexion.close()

    filas = ""

    for n in lista:
        filas += f"""
        <tr>
            <td>{n['fecha']}</td>
            <td>{n['descripcion']}</td>
            <td>
                <form method="post"
                      action="/novedades/eliminar/{n['id']}"
                      onsubmit="return confirm('¿Eliminar esta novedad?');">
                    <button type="submit">Eliminar</button>
                </form>
            </td>
        </tr>
        """

    if not filas:
        filas = "<tr><td colspan='3'>No hay novedades registradas.</td></tr>"

    contenido = f"""
    <section class="panel">
        <h3>Registrar novedad o incidente</h3>
        {mensaje}
        <form method="post" action="/novedades">
            <label>Descripción</label>
            <textarea name="descripcion" required rows="4"></textarea>
            <button type="submit">Guardar novedad</button>
        </form>
    </section>

    <section class="panel">
        <h3>Novedades registradas</h3>
        <div class="tabla">
            <table>
                <tr>
                    <th>Fecha</th>
                    <th>Descripción</th>
                    <th>Acciones</th>
                </tr>
                {filas}
            </table>
        </div>
    </section>
    """

    return pagina("Novedades", contenido)



if __name__ == "__main__":
    inicializar_db()
    app.run(debug=True)
