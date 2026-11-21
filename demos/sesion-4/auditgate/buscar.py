from flask import Flask, request
import sqlite3

app = Flask(__name__)


@app.get("/buscar")
def buscar():
    q = request.args.get("q", "")
    con = sqlite3.connect("tienda.db")
    # ✅ Consulta parametrizada: `?` es un marcador y `q` viaja aparte como dato.
    #    La base de datos nunca interpreta la entrada del usuario como SQL.
    filas = con.execute(
        "SELECT nombre, precio FROM productos WHERE nombre = ?", (q,)
    ).fetchall()
    return {"resultados": [{"nombre": n, "precio": p} for n, p in filas]}


if __name__ == "__main__":
    app.run()
