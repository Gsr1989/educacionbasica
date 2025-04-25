# main.py
from flask import Flask, render_template, request, jsonify
from supabase import create_client
from datetime import datetime
import io, qrcode, base64, os

app = Flask(__name__)

# --- CONFIG SUPABASE ---
SUPABASE_URL = "https://axgqvhgtbzkraytzaomw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF4Z3F2aGd0YnprcmF5dHphb213Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU1NDAwNzUsImV4cCI6MjA2MTExNjA3NX0.fWWMBg84zjeaCDAg-DV1SOJwVjbWDzKVsIMUTuVUVsY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- CONTRASEÑA GLOBAL ---
PASSWORD = "Nivelbasico2025"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    error = None
    if request.method == "POST":
        pwd = request.form.get("password","")
        if pwd != PASSWORD:
            error = "Contraseña incorrecta"
        else:
            curp   = request.form["curp"]
            nombre = request.form["nombre"]
            # Insertar en alumnos
            supabase.table("alumnos").insert({
                "curp": curp, "nombre": nombre
            }).execute()
            # Generar QR (solo CURP)
            qr = qrcode.make(curp)
            buf = io.BytesIO()
            qr.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode()
            return render_template("registro_exitoso.html",
                                   curp=curp, nombre=nombre, qr_b64=img_b64)
    return render_template("registrar.html", error=error)

@app.route("/escanear")
def escanear_get():
    # muestra la página con form de contraseña + escáner
    return render_template("escanear.html", error=None)

@app.route("/escanear", methods=["POST"])
def escanear_post():
    data = request.json or {}
    if data.get("password") != PASSWORD:
        return jsonify(status="error", mensaje="Contraseña inválida")
    curp = data.get("curp","")
    # valida alumno
    resp = supabase.table("alumnos").select("*").eq("curp", curp).execute()
    if not resp.data:
        return jsonify(status="error", mensaje="QR inválido")
    nombre = resp.data[0]["nombre"]
    # inserta asistencia
    supabase.table("asistencias").insert({
        "curp": curp, "nombre": nombre
    }).execute()
    return jsonify(status="ok", mensaje="Asistencia registrada")

@app.route("/consultar", methods=["GET", "POST"])
def consultar():
    if request.method=="POST":
        pwd = request.form.get("password","")
        if pwd != PASSWORD:
            return render_template("consultar.html", error="Contraseña inválida")
        curp = request.form["curp"]
        resp = supabase.table("asistencias").select("*").eq("curp", curp).execute()
        # convertir a lista de eventos para FullCalendar
        eventos = [{
            "title":  f"Asistencia: {x['nombre']}",
            "start":  x["fecha_hora"]  # iso string
        } for x in resp.data]
        return render_template("calendario.html",
                               eventos=eventos, curp=curp)
    return render_template("consultar.html", error=None)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",5000)), debug=True)
