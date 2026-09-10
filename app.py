from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

materials = []
transactions = []

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

            <label>Unit</label>
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
                <option value="IN">IN / Entrada</option>
                <option value="OUT">OUT / Salida</option>
                <option value="ADJUST">ADJUST / Ajuste</option>
            </select>

            <label>Quantity / Cantidad</label>
            <input type="number" step="0.01" name="quantity" required>

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
                <td>{{"%.2f"|format(m['stock'])}}</td>
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
            </tr>

            {% for t in transactions %}
            <tr>
                <td>{{t['code']}}</td>
                <td>{{t['type']}}</td>
                <td>{{t['quantity']}}</td>
                <td>{{t['reference']}}</td>
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
    return render_template_string(
        HTML,
        materials=materials,
        transactions=transactions
    )


@app.route("/add-material", methods=["POST"])
def add_material():

    material = {
        "code": request.form["code"],
        "name": request.form["name"],
        "unit": request.form["unit"],
        "minimum": float(request.form["minimum"]),
        "stock": 0
    }

    materials.append(material)

    return redirect("/")


@app.route("/transaction", methods=["POST"])
def transaction():

    code = request.form["code"]
    transaction_type = request.form["type"]
    quantity = float(request.form["quantity"])
    reference = request.form["reference"]

    for material in materials:

        if material["code"] == code:

            if transaction_type == "IN":
                material["stock"] += quantity

            elif transaction_type == "OUT":
                material["stock"] -= quantity

            elif transaction_type == "ADJUST":
                material["stock"] = quantity

            break

    transactions.insert(0, {
        "code": code,
        "type": transaction_type,
        "quantity": quantity,
        "reference": reference
    })

    return redirect("/")


if __name__ == "__main__":
    app.run()
