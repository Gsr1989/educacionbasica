from flask import Flask, render_template, request, redirect, url_for, jsonify
from supabase import create_client
from datetime import datetime, timedelta
import io
import qrcode
import base64

app = Flask(__name__)

# Configuración Supabase
SUPABASE_URL = "https://axgqvhgtbzkraytzaomw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF4Z3F2aGd0YnprcmF5dHphb213Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU1NDAwNzUsImV4cCI6MjA2MTExNjA3NX0.fWWMBg84zjeaCDAg-DV1SOJwVjbWDzKVsIMUTuVUVsY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Contraseña requerida
PASSWORD = "Nivelbasico2025"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        curp = request.form["curp"]
        nombre = request.form["nombre"]
        password = request.form["password"]

        if password != PASSWORD:
            return render_template("registrar.html", error="Contraseña incorrecta")

        existe = supabase.table("alumnos").select("curp").eq("curp", curp).execute().data
        if existe:
            return render_template("registrar.html", error="Este CURP ya fue registrado")

        supabase.table("alumnos").insert({"curp": curp, "nombre": nombre}).execute()

        # Crear QR
        qr = qrcode.make(curp)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return render_template("registro_exitoso.html", curp=curp, nombre=nombre, qr_base64=qr_base64)

    return render_template("registrar.html")

@app.route("/escanear", methods=["GET", "POST"])
def escanear():
    if request.method == "POST":
        curp = request.form["curp"]
        password = request.form["password"]

        if password != PASSWORD:
            return render_template("escanear.html", error="Contraseña incorrecta")

        alumno = supabase.table("alumnos").select("*").eq("curp", curp).execute().data
        if not alumno:
            return render_template("escanear.html", error="CURP no válido")

        hoy = datetime.now().date().isoformat()
        supabase.table("asistencias").insert({"curp": curp, "nombre": alumno[0]["nombre"], "fecha": hoy}).execute()

        return render_template("exito_asistencia.html", curp=curp)
    return render_template("escanear.html")

@app.route("/consultar", methods=["GET", "POST"])
def consultar():
    if request.method == "POST":
        curp = request.form["curp"]
        asistencias = supabase.table("asistencias").select("fecha").eq("curp", curp).execute().data
        fechas = [a["fecha"] for a in asistencias]
        return render_template("calendario.html", fechas=fechas, curp=curp)
    return render_template("consultar.html")

if __name__ == "__main__":
    app.run(debug=True)
