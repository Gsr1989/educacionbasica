from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from supabase import create_client
from datetime import datetime
import io
import qrcode
import base64

app = Flask(__name__)

# Configuración de Supabase
SUPABASE_URL = "https://axgqvhgtbzkraytzaomw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        curp = request.form["curp"]
        nombre = request.form["nombre"]

        # Insertar en tabla alumnos
        supabase.table("alumnos").insert({"curp": curp, "nombre": nombre}).execute()

        # Crear QR con solo la CURP
        qr_data = curp
        qr = qrcode.make(qr_data)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return render_template("registro_exitoso.html", curp=curp, nombre=nombre, qr_base64=qr_base64)
    return render_template("registrar.html")

@app.route("/escanear", methods=["POST"])
def escanear():
    data = request.json
    curp = data.get("curp")

    alumno = supabase.table("alumnos").select("*").eq("curp", curp).execute().data
    if not alumno:
        return jsonify({"status": "error", "mensaje": "QR inválido"})

    supabase.table("asistencias").insert({
        "curp": curp,
        "nombre": alumno[0]["nombre"]
    }).execute()

    return jsonify({"status": "ok", "mensaje": "Asistencia registrada"})

@app.route("/consultar", methods=["GET", "POST"])
def consultar():
    if request.method == "POST":
        curp = request.form["curp"]
        asistencias = supabase.table("asistencias").select("*").eq("curp", curp).execute().data
        return render_template("calendario.html", asistencias=asistencias, curp=curp)
    return render_template("consultar.html")

if __name__ == "__main__":
    app.run(debug=True)
