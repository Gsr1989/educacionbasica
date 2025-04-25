from flask import Flask, render_template
from supabase import create_client, Client

app = Flask(__name__)

# Conexión a Supabase
SUPABASE_URL = "https://axgqvhgtbzkraytzaomw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF4Z3F2aGd0YnprcmF5dHphb213Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU1NDAwNzUsImV4cCI6MjA2MTExNjA3NX0.fWWMBg84zjeaCDAg-DV1SOJwVjbWDzKVsIMUTuVUVsY"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
