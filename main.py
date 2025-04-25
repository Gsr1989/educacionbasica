from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from supabase import create_client
from datetime import datetime
import qrcode
import io
import base64

app = Flask(__name__)
app.secret_key = "clave_super_secreta"

# Supabase
SUPABASE_URL = "https://axgqvhgtbzkraytzaomw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF4Z3F2aGd0YnprcmF5dHphb213Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU1NDAwNzUsImV4cCI6MjA2MTExNjA3NX0.fWWMBg84zjeaCDAg-DV1SOJwVjbWDzKVsIMUTuVUVsY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Contraseña
CONTRASENA = "Nivelbasico2025"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        clave = request.form.get("clave")
        if clave != CONTRASENA:
            return render_template("error.html", mensaje="Contraseña incorrecta")
        return render_template("registro_form.html")
    return render_template("registro_clave.html")

@app.route("/registrar_alumno", methods=["POST"])
def registrar_alumno():
    curp = request.form["curp"]
    nombre = request.form["nombre"]
    fecha = datetime.now().isoformat()

    supabase.table("alumnos").insert({"curp": curp, "nombre": nombre}).execute()

    qr = qrcode.make(curp)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return render_template("registro_exitoso.html", curp=curp, nombre=nombre, qr_base64=qr_base64)

@app.route("/escanear", methods=["GET", "POST"])
def escanear():
    if request.method == "POST":
        clave = request.form.get("clave")
        if clave != CONTRASENA:
            return render_template("error.html", mensaje="Contraseña incorrecta")
        return render_template("escanear_qr.html")
    return render_template("escanear_clave.html")

@app.route("/registrar_asistencia", methods=["POST"])
def registrar_asistencia():
    curp = request.json.get("curp")
    fecha = datetime.now().isoformat()

    alumno = supabase.table("alumnos").select("*").eq("curp", curp).execute().data
    if not alumno:
        return jsonify({"status": "error", "mensaje": "CURP no encontrado"})

    supabase.table("asistencias").insert({
        "curp": curp,
        "nombre": alumno[0]["nombre"],
        "fecha": fecha
    }).execute()

    return jsonify({"status": "ok", "mensaje": "Asistencia registrada correctamente"})

@app.route("/consultar", methods=["GET", "POST"])
def consultar():
    if request.method == "POST":
        curp = request.form["curp"]
        asistencias = supabase.table("asistencias").select("*").eq("curp", curp).execute().data
        return render_template("calendario.html", curp=curp, asistencias=asistencias)
    return render_template("consultar.html")

if __name__ == "__main__":
    app.run(debug=True)
