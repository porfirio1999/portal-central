# portal_central.py actualizado con login, registro unico y recuperacion
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave_predeterminada")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")

# Inicializaciones
db = SQLAlchemy(app)
mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# === MODELOS ===
class Estacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ubicacion = db.Column(db.String(100), nullable=False)
    url_ngrok = db.Column(db.String(200), nullable=False)

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    nombre_real = db.Column(db.String(100), nullable=False)
    contrasena_hash = db.Column(db.String(128), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)

    def set_password(self, password):
        self.contrasena_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.contrasena_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# === CREAR TABLAS ===
with app.app_context():
    db.create_all()

# === RUTAS ===
@app.route('/')
@login_required
def home():
    estaciones = Estacion.query.all()
    return render_template('portal_publico.html', estaciones=estaciones)

@app.route('/agregar_estacion', methods=['GET', 'POST'])
@login_required
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
@login_required
def actualizar_url():
    data = request.get_json()
    estacion = Estacion.query.get(data['id_estacion'])
    if estacion:
        estacion.url_ngrok = data['url_ngrok']
        db.session.commit()
        print(f"✔️ Estación {data['id_estacion']} actualizó URL a {data['url_ngrok']}")
        return {'status': 'ok'}
    return {'status': 'error', 'message': 'Estación no encontrada'}, 404

@app.route('/registrarse', methods=['GET', 'POST'])
def registrarse():
    if Usuario.query.first():
        return "❌ Ya existe un usuario registrado."
    if request.method == 'POST':
        nombre_real = request.form['nombre_real']
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        correo = request.form['correo']
        nuevo = Usuario(nombre_real=nombre_real, usuario=usuario, correo=correo)
        nuevo.set_password(contrasena)
        db.session.add(nuevo)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        user = Usuario.query.filter_by(usuario=usuario).first()
        if user and user.check_password(contrasena):
            login_user(user)
            return redirect('/')
        return "❌ Credenciales incorrectas"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/reset', methods=['GET', 'POST'])
def reset_request():
    if request.method == 'POST':
        correo = request.form['correo']
        user = Usuario.query.filter_by(correo=correo).first()
        if user:
            token = s.dumps(correo, salt='recuperar-clave')
            link = url_for('reset_token', token=token, _external=True)
            msg = Message("Recuperar contraseña", sender="noreply@demo.com", recipients=[correo])
            msg.body = f"Usa este enlace para restablecer tu contraseña: {link}"
            mail.send(msg)
        return "📧 Revisa tu correo"
    return render_template('reset_request.html')

@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_token(token):
    try:
        correo = s.loads(token, salt='recuperar-clave', max_age=600)
    except:
        return "❌ Token inválido o expirado"
    user = Usuario.query.filter_by(correo=correo).first()
    if request.method == 'POST':
        nueva = request.form['nueva']
        user.set_password(nueva)
        db.session.commit()
        return redirect('/login')
    return render_template('reset_token.html')

# === INICIO LOCAL ===
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
