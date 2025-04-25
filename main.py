from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_file
from supabase import create_client, SupabaseException
from datetime import datetime
import io
import base64
import qrcode

app = Flask(__name__)
app.secret_key = "cambiame_por_una_clave_segura"

# ——— Configuración de Supabase ———
SUPABASE_URL = "https://axgqvhgtbzkraytzaomw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF4Z3F2aGd0YnprcmF5dHphb213Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU1NDAwNzUsImV4cCI6MjA2MTExNjA3NX0.fWWMBg84zjeaCDAg-DV1SOJwVjbWDzKVsIMUTuVUVsY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        curp   = request.form["curp"].strip()
        nombre = request.form["nombre"].strip()

        if not curp or not nombre:
            flash("Debes proporcionar CURP y nombre.", "error")
            return redirect(url_for("registrar"))

        # — Verificar existencia para evitar error 23505 —
        existe = bool(supabase
            .table("alumnos")
            .select("id")
            .eq("curp", curp)
            .execute()
            .data
        )

        if not existe:
            try:
                supabase.table("alumnos") \
                         .insert({"curp": curp, "nombre": nombre}) \
                         .execute()
            except SupabaseException as e:
                # si llegase a fallar por duplicado, lo marcamos como existente
                if "duplicate key" in str(e).lower():
                    existe = True
                else:
                    flash("Error al guardar en la base.", "error")
                    return redirect(url_for("registrar"))

        # — Generar QR (siempre) —
        qr = qrcode.make(curp)
        buf = io.BytesIO()
        qr.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        return render_template(
            "registro_exitoso.html",
            curp=curp,
            nombre=nombre,
            qr_b64=qr_b64,
            ya_existe=existe
        )

    return render_template("registrar.html")


@app.route("/escanear", methods=["POST"])
def escanear():
    data = request.get_json(force=True, silent=True) or {}
    curp = (data.get("curp") or "").strip()
    if not curp:
        return jsonify(status="error", mensaje="QR inválido")

    # Buscar alumno
    r = supabase.table("alumnos") \
                .select("nombre") \
                .eq("curp", curp) \
                .execute()
    if not r.data:
        return jsonify(status="error", mensaje="QR inválido")

    nombre = r.data[0]["nombre"]
    # Registrar asistencia
    supabase.table("asistencias") \
             .insert({
                 "curp": curp,
                 "nombre": nombre,
                 "fecha_hora": datetime.utcnow().isoformat()
             }) \
             .execute()

    return jsonify(status="ok", mensaje="Asistencia registrada")


@app.route("/consultar", methods=["GET", "POST"])
def consultar():
    if request.method == "POST":
        curp = request.form["curp"].strip()
        r = supabase.table("asistencias") \
                    .select("*") \
                    .eq("curp", curp) \
                    .order("fecha_hora", desc=False) \
                    .execute()
        asistencias = r.data or []
        return render_template("calendario.html", asistencias=asistencias, curp=curp)
    return render_template("consultar.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(__import__("os").environ.get("PORT", 5000)), debug=True)
