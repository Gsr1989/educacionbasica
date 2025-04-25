import io
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from supabase import create_client
import qrcode

app = Flask(__name__, static_folder="static", template_folder="templates")

# *** Configuración de Supabase (hardcodeada) ***
SUPABASE_URL = "https://axgqvhgtbzkraytzaomw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF4Z3F2aGd0YnprcmF5dHphb213Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU1NDAwNzUsImV4cCI6MjA2MTExNjA3NX0.fWWMBg84zjeaCDAg-DV1SOJwVjbWDzKVsIMUTuVUVsY"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        curp = request.form.get("curp", "").strip()
        nombre = request.form.get("nombre", "").strip()
        if not curp or not nombre:
            return render_template("registrar.html", error="Todos los campos son obligatorios")
        # Insertar alumno en la tabla 'alumnos'
        supabase.table("alumnos").insert({"curp": curp, "nombre": nombre}).execute()

        # Generar QR con la CURP
        img = qrcode.make(curp)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        return render_template(
            "registro_exitoso.html",
            curp=curp,
            nombre=nombre,
            qr_b64=qr_b64
        )
    return render_template("registrar.html")

@app.route("/escanear", methods=["POST"])
def escanear():
    data = request.get_json(force=True)
    curp = data.get("curp", "").strip()
    # Verificar que el alumno exista
    resp = supabase.table("alumnos").select("*").eq("curp", curp).execute()
    alumnos = resp.data or []
    if not alumnos:
        return jsonify({"status": "error", "mensaje": "QR inválido"})
    nombre = alumnos[0]["nombre"]
    # Registrar asistencia en la tabla 'asistencias'
    supabase.table("asistencias").insert({
        "curp": curp,
        "nombre": nombre,
        "fecha_hora": datetime.utcnow().isoformat()
    }).execute()
    return jsonify({"status": "ok", "mensaje": "Asistencia registrada"})

@app.route("/consultar", methods=["GET", "POST"])
def consultar():
    if request.method == "POST":
        curp = request.form.get("curp", "").strip()
        resp = supabase.table("asistencias") \
                        .select("*") \
                        .eq("curp", curp) \
                        .order("fecha_hora", desc=True) \
                        .execute()
        asistencias = resp.data or []
        return render_template("calendario.html", asistencias=asistencias, curp=curp)
    return render_template("consultar.html")

if __name__ == "__main__":
    # Para correr local: python main.py
    app.run(host="0.0.0.0", port=5000, debug=True)
