# portal_central.py
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
db = SQLAlchemy(app)

# === MODELO ===
class Estacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ubicacion = db.Column(db.String(100), nullable=False)
    url_ngrok = db.Column(db.String(200), nullable=False)

# === RUTAS ===
@app.route('/')
def home():
    estaciones = Estacion.query.all()
    return render_template('portal_publico.html', estaciones=estaciones)

@app.route('/agregar_estacion', methods=['GET', 'POST'])
def agregar_estacion():
    CLAVE = "admin2024"
    if request.method == "POST":
        clave_ingresada = request.form.get("clave")
        if clave_ingresada != CLAVE:
            return "🔒 Clave incorrecta"
        nombre = request.form['nombre']
        ubicacion = request.form['ubicacion']
        url_ngrok = request.form['url_ngrok']
        nueva = Estacion(nombre=nombre, ubicacion=ubicacion, url_ngrok=url_ngrok)
        db.session.add(nueva)
        db.session.commit()
        return redirect('/')
    return render_template("agregar_estacion.html")

@app.route('/api/actualizar_url', methods=['POST'])
def actualizar_url():
    data = request.get_json()
    estacion = Estacion.query.get(data['id_estacion'])
    if estacion:
        estacion.url_ngrok = data['url_ngrok']
        db.session.commit()
        print(f"✔️ Estación {data['id_estacion']} actualizó URL a {data['url_ngrok']}")
        return {'status': 'ok'}
    return {'status': 'error', 'message': 'Estación no encontrada'}, 404

# === INICIO ===
if __name__ == '__main__':
    if not os.path.exists('estaciones.db'):
        with app.app_context():
            db.create_all()
    app.run(host='0.0.0.0', port=5000)
