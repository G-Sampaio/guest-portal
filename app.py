from flask import Flask, request, render_template
import sqlite3
import smtplib
import ssl
import random
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

# Carregar variáveis do .env
load_dotenv()

app = Flask(__name__)

# Configurações do e-mail
EMAIL_REMETENTE = os.getenv('EMAIL_REMETENTE')
SENHA_REMETENTE = os.getenv('SENHA_REMETENTE')
SMTP_SERVIDOR = os.getenv('SMTP_SERVIDOR')
SMTP_PORTA = int(os.getenv('SMTP_PORTA'))  # porta SSL direta


# Inicializar banco
def init_db():
    conn = sqlite3.connect('guest_wifi.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            sobrenome TEXT NOT NULL,
            email TEXT NOT NULL,
            codigo_verificacao TEXT NOT NULL,
            verificado BOOLEAN DEFAULT 0,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def salvar_usuario(nome, sobrenome, email, codigo):
    conn = sqlite3.connect('guest_wifi.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO usuarios (nome, sobrenome, email, codigo_verificacao) VALUES (?, ?, ?, ?)', (nome, sobrenome, email, codigo))
    conn.commit()
    conn.close()

def validar_codigo(email, codigo):
    conn = sqlite3.connect('guest_wifi.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM usuarios WHERE email=? AND codigo_verificacao=? AND verificado=0', (email, codigo))
    result = cursor.fetchone()
    if result:
        cursor.execute('UPDATE usuarios SET verificado=1 WHERE id=?', (result[0],))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nome = request.form['nome']
        sobrenome = request.form['sobrenome']
        email = request.form['email']
        codigo = str(random.randint(100000, 999999))

        salvar_usuario(nome, sobrenome, email, codigo)

        # Construir e-mail MIME com acentos
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = email
        msg['Subject'] = Header("Seu código de acesso à rede Guest", 'utf-8')

        corpo = f"Olá {nome},\n\nSeu código de acesso é: {codigo}\n\nDigite-o no portal para liberar seu acesso."
        msg.attach(MIMEText(corpo, 'plain', 'utf-8'))

        # Enviar e-mail
        context = ssl._create_unverified_context()
        with smtplib.SMTP_SSL(SMTP_SERVIDOR, SMTP_PORTA, context=context) as server:
            server.login(EMAIL_REMETENTE, SENHA_REMETENTE)
            server.sendmail(EMAIL_REMETENTE, email, msg.as_string())

        return render_template('verificar.html', email=email)
    return render_template('index.html')

@app.route('/validar', methods=['POST'])
def validar():
    email = request.form['email']
    codigo = request.form['codigo']
    if validar_codigo(email, codigo):
        return render_template('sucesso.html')
    else:
        return "❌ Código inválido ou já utilizado. <a href='/'>Tente novamente</a>"

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=5000)
