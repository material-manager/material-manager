import os
from decimal import Decimal, InvalidOperation

import psycopg
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)


def get_connection():
    return psycopg.connect(os.environ["DATABASE_URL"])


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Material Manager</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            background: #f4f6f8;
        }

        header {
            background: #1f2937;
            color: white;
            padding: 20px;
            text-align: center;
        }

        .container {
            max-width: 1100px;
            margin: 20px auto;
            padding: 15px;
        }

        .card {
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,.08);
        }

        input, select, button {
            width: 100%;
            padding: 12px;
            margin: 6px 0 12px;
            box-sizing: border-box;
        }

        button {
            background: #2563eb;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
            text-align: left;
        }

        th {
            background: #f1f5f9;
        }
    </style>
</head>

<body>

<header>
    <h1>Material Manager</h1>
    <div>Gestor de Materiales</div>
</header>

<div class="container">

    <div class="card">
        <h2>Add Material / Agregar Material</h2>

        <form method="POST" action="/add-material">

            <label>Material Code / Código</label>
            <input name="code" required>

            <label>Material Name / Nombre</label>
            <input name="name" required>

            <label>Unit / Unidad</label>
            <select name="unit">
                <option value="kg">kg</option>
                <option value="pcs">pcs</option>
                <option value="bag">bag</option>
            </select>

            <label>Minimum Stock / Stock Mínimo</label>
            <input type="number" step="0.01" name="minimum" value="0">

            <button type="submit">
                Add Material / Agregar
            </button>

        </form>
    </div>


    <div class="card">
        <h2>Material IN / OUT / Entrada / Salida</h2>

        <form method="POST" action="/transaction">

            <label>Material</label>
            <select name="code" required>

                {% for m in materials %}

                    <option value="{{m['code']}}">
                        {{m['code']}} - {{m['name']}}
                    </option>

                {% endfor %}

            </select>

            <label>Type / Tipo</label>

            <select name="type">

                <option value="IN">
                    IN / Entrada
                </option>

                <option value="OUT">
                    OUT / Salida
                </option>

                <option value="ADJUST">
                    ADJUST / Ajuste
                </option>

            </select>

            <label>Quantity / Cantidad</label>
            <input
                type="number"
                step="0.01"
                name="quantity"
                min="0"
                required
            >

            <label>Reference / Referencia</label>
            <input name="reference">

            <button type="submit">
                Save / Guardar
            </button>

        </form>
    </div>


    <div class="card">
        <h2>Current Stock / Stock Actual</h2>

        <table>

            <tr>
                <th>Code</th>
                <th>Material</th>
                <th>Unit</th>
                <th>Stock</th>
                <th>Min</th>
                <th>Status</th>
            </tr>

            {% for m in materials %}

            <tr>

                <td>{{m['code']}}</td>

                <td>{{m['name']}}</td>

                <td>{{m['unit']}}</td>

                <td>{{m['stock']}}</td>

                <td>{{m['minimum']}}</td>

                <td>

                    {% if m['stock'] <= m['minimum'] %}
                        LOW / BAJO
                    {% else %}
                        OK
                    {% endif %}

                </td>

            </tr>

            {% endfor %}

        </table>
    </div>


    <div class="card">

        <h2>Recent Transactions / Movimientos Recientes</h2>

        <table>

            <tr>
                <th>Material</th>
                <th>Type</th>
                <th>Quantity</th>
                <th>Reference</th>
                <th>Date</th>
            </tr>

            {% for t in transactions %}

            <tr>

                <td>{{t['code']}}</td>

                <td>{{t['type']}}</td>

                <td>{{t['quantity']}}</td>

                <td>{{t['reference'] or ''}}</td>

                <td>{{t['created_at']}}</td>

            </tr>

            {% endfor %}

        </table>

    </div>

</div>

</body>
</html>
"""


@app.route("/")
def home():

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    code,
                    name,
                    unit,
                    minimum_stock,
                    current_stock
                FROM materials
                WHERE active = TRUE
                ORDER BY code
            """)

            material_rows = cur.fetchall()

            cur.execute("""
                SELECT
                    t.id,
                    m.code,
                    t.type,
                    t.quantity,
                    t.reference,
                    t.created_at
                FROM transactions t
                JOIN materials m
                    ON m.id = t.material_id
                ORDER BY t.created_at DESC
                LIMIT 100
            """)

            transaction_rows = cur.fetchall()

    materials = []

    for row in material_rows:

        materials.append({
            "id": row[0],
            "code": row[1],
            "name": row[2],
            "unit": row[3],
            "minimum": float(row[4]),
            "stock": float(row[5])
        })


    transactions = []

    for row in transaction_rows:

        transactions.append({
            "id": row[0],
            "code": row[1],
            "type": row[2],
            "quantity": float(row[3]),
            "reference": row[4],
            "created_at": row[5].strftime("%Y-%m-%d %H:%M")
        })


    return render_template_string(
        HTML,
        materials=materials,
        transactions=transactions
    )


@app.route("/add-material", methods=["POST"])
def add_material():

    code = request.form["code"].strip()
    name = request.form["name"].strip()
    unit = request.form["unit"]

    try:
        minimum = Decimal(request.form["minimum"])
    except InvalidOperation:
        return "Invalid minimum stock", 400


    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO materials
                    (code, name, unit, minimum_stock, current_stock)
                VALUES
                    (%s, %s, %s, %s, 0)
            """, (
                code,
                name,
                unit,
                minimum
            ))

        conn.commit()


    return redirect("/")


@app.route("/transaction", methods=["POST"])
def transaction():

    code = request.form["code"]
    transaction_type = request.form["type"]
    reference = request.form["reference"].strip()

    try:
        quantity = Decimal(request.form["quantity"])
    except InvalidOperation:
        return "Invalid quantity", 400


    if quantity < 0:
        return "Quantity cannot be negative", 400


    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT id, current_stock
                FROM materials
                WHERE code = %s
                AND active = TRUE
                FOR UPDATE
            """, (code,))

            material = cur.fetchone()


            if material is None:
                return "Material not found", 404


            material_id = material[0]
            current_stock = material[1]


            if transaction_type == "IN":

                new_stock = current_stock + quantity


            elif transaction_type == "OUT":

                new_stock = current_stock - quantity

                if new_stock < 0:
                    return "Insufficient stock", 400


            elif transaction_type == "ADJUST":

                new_stock = quantity


            else:
                return "Invalid transaction type", 400


            cur.execute("""
                UPDATE materials
                SET
                    current_stock = %s,
                    updated_at = now()
                WHERE id = %s
            """, (
                new_stock,
                material_id
            ))


            cur.execute("""
                INSERT INTO transactions
                    (material_id, type, quantity, reference)
                VALUES
                    (%s, %s, %s, %s)
            """, (
                material_id,
                transaction_type,
                quantity,
                reference
            ))


        conn.commit()


    return redirect("/")


if __name__ == "__main__":
    app.run()
    
