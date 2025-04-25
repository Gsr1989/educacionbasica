from flask import Flask, render_template, request, jsonify, redirect, url_for
from supabase import create_client
from datetime import datetime
import qrcode
import io
import base64

app = Flask(__name__)
app.secret_key = "clave_super_secreta"

# Supabase
SUPABASE_URL = "https://axgqvhgtbzkraytzaomw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Contraseña para acceder a registro y escaneo
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

    try:
        supabase.table("alumnos").insert({"curp": curp, "nombre": nombre}).execute()
    except Exception:
        return render_template("error.html", mensaje="Este CURP ya fue registrado")

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
    data = request.get_json()
    curp = data.get("curp")
    fecha = datetime.now().isoformat()

    alumno = supabase.table("alumnos").select("*").eq("curp", curp).execute().data
    if not alumno:
        return jsonify({"status": "error", "mensaje": "CURP no encontrado"})

    nombre = alumno[0]["nombre"]

    supabase.table("asistencias").insert({
        "curp": curp,
        "nombre": nombre,
        "fecha_hora": fecha
    }).execute()

    return jsonify({"status": "ok", "mensaje": "Asistencia registrada correctamente"})

@app.route("/consultar", methods=["GET", "POST"])
def consultar():
    if request.method == "POST":
        curp = request.form["curp"]
        asistencias_raw = supabase.table("asistencias").select("*").eq("curp", curp).execute().data

        dias = []
        for a in asistencias_raw:
            try:
                fecha_str = a["fecha_hora"]
                fecha_obj = datetime.fromisoformat(fecha_str)
                dias.append(fecha_obj.strftime("%Y-%m-%d"))
            except:
                continue

        return render_template("calendario.html", curp=curp, dias=dias)

    return render_template("consultar.html")

if __name__ == "__main__":
    app.run(debug=True)
