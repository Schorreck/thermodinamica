from flask import Flask, request, redirect, send_file, session, render_template_string
import pymysql

app = Flask(__name__)
app.secret_key = 'thermodinamica-secret-key'

# Configuração da conexão com o banco
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='Dragon1979#$',
        database='thermodinamica_db',
        cursorclass=pymysql.cursors.DictCursor
    )

# Rotas para servir as páginas HTML
@app.route('/')
def index():
    return send_file('index.html')

@app.route('/acesso.html')
def acesso():
    return send_file('acesso.html')

@app.route('/cadastro.html')
def cadastro():
    return send_file('cadastro.html')

# Rota que processa o formulário de cadastro
@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    nome = request.form.get('nome')
    documento = request.form.get('documento')
    telefone = request.form.get('telefone')
    endereco = request.form.get('endereco')

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO clientes (nome, documento, telefone, endereco) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (nome, documento, telefone, endereco))
            conn.commit()
        return redirect('/acesso.html')
    except pymysql.MySQLError as e:
        conn.rollback()
        return f"Erro ao cadastrar cliente: {e}", 400
    finally:
        conn.close()

# Rota para autenticar o cliente com os campos reais do banco
@app.route('/login', methods=['POST'])
def login():
    nome = request.form.get('nome')
    documento = request.form.get('documento')

    if not nome or not documento:
        return "Nome e documento são obrigatórios.", 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, nome, documento FROM clientes WHERE nome = %s AND documento = %s"
            cursor.execute(sql, (nome, documento))
            cliente = cursor.fetchone()

        if cliente:
            session['cliente_id'] = cliente['id']
            session['cliente_nome'] = cliente['nome']
            return redirect('/dashboard')

        return render_template_string('''
        <!doctype html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Cliente não Cadastrado</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-slate-100 min-h-screen flex items-center justify-center p-6">
            <div class="max-w-md w-full bg-white rounded-2xl shadow-lg p-8 text-center">
                <div class="text-5xl mb-4">⚠️</div>
                <h1 class="text-2xl font-bold text-slate-800 mb-3">Cliente não Cadastrado</h1>
                <p class="text-slate-600 mb-6">Não encontramos um cliente com os dados informados.</p>
                <a href="/cadastro.html" class="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold px-5 py-3 rounded-lg">Fazer cadastro</a>
                <div class="mt-4">
                    <a href="/acesso.html" class="text-blue-600 hover:underline">Voltar para o acesso</a>
                </div>
            </div>
        </body>
        </html>
        '''), 401
    finally:
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/acesso.html')

@app.route('/dashboard')
def dashboard():
    if 'cliente_id' not in session:
        return redirect('/acesso.html')

    cliente_id = session['cliente_id']
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM clientes WHERE id = %s", (cliente_id,))
            cliente = cursor.fetchone()

            cursor.execute("SELECT * FROM equipamentos WHERE cliente_id = %s ORDER BY id DESC", (cliente_id,))
            equipamentos = cursor.fetchall() or []

            cursor.execute("SELECT * FROM historico WHERE cliente_id = %s ORDER BY id DESC LIMIT 20", (cliente_id,))
            historico = cursor.fetchall() or []
    finally:
        conn.close()

    return render_template_string('''
    <!doctype html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Painel do Cliente</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-100 min-h-screen text-slate-800">
        <div class="max-w-6xl mx-auto px-4 py-8">
            <div class="flex justify-between items-center mb-8">
                <div>
                    <p class="text-sm uppercase tracking-wide text-blue-600 font-semibold">Painel do cliente</p>
                    <h1 class="text-3xl font-bold">Bem-vindo, {{ cliente['nome'] if cliente else 'Cliente' }}</h1>
                </div>
                <a href="/logout" class="bg-red-500 hover:bg-red-600 text-white font-semibold px-4 py-2 rounded-lg">Sair</a>
            </div>

            <div class="grid md:grid-cols-2 gap-6 mb-8">
                <div class="bg-white rounded-2xl shadow p-6">
                    <h2 class="text-xl font-bold mb-4">Dados do cliente</h2>
                    <ul class="space-y-2 text-sm">
                        {% if cliente %}
                            {% for key, value in cliente.items() %}
                                <li><strong>{{ key }}:</strong> {{ value }}</li>
                            {% endfor %}
                        {% else %}
                            <li>Cliente não encontrado.</li>
                        {% endif %}
                    </ul>
                </div>

                <div class="bg-white rounded-2xl shadow p-6">
                    <h2 class="text-xl font-bold mb-4">Resumo</h2>
                    <div class="grid grid-cols-2 gap-4 text-center">
                        <div class="bg-blue-50 rounded-xl p-4">
                            <div class="text-2xl font-bold text-blue-600">{{ equipamentos|length }}</div>
                            <div class="text-sm text-slate-600">Equipamentos</div>
                        </div>
                        <div class="bg-green-50 rounded-xl p-4">
                            <div class="text-2xl font-bold text-green-600">{{ historico|length }}</div>
                            <div class="text-sm text-slate-600">Histórico</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-2xl shadow p-6 mb-8">
                <h2 class="text-xl font-bold mb-4">Equipamentos</h2>
                {% if equipamentos %}
                    <div class="overflow-x-auto">
                        <table class="min-w-full text-left text-sm">
                            <thead>
                                <tr class="border-b">
                                    {% for key in equipamentos[0].keys() %}
                                        <th class="py-2 pr-4 font-semibold">{{ key }}</th>
                                    {% endfor %}
                                </tr>
                            </thead>
                            <tbody>
                                {% for equipamento in equipamentos %}
                                    <tr class="border-b">
                                        {% for value in equipamento.values() %}
                                            <td class="py-2 pr-4">{{ value }}</td>
                                        {% endfor %}
                                    </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                {% else %}
                    <p>Nenhum equipamento cadastrado para este cliente.</p>
                {% endif %}
            </div>

            <div class="bg-white rounded-2xl shadow p-6">
                <h2 class="text-xl font-bold mb-4">Histórico</h2>
                {% if historico %}
                    <div class="overflow-x-auto">
                        <table class="min-w-full text-left text-sm">
                            <thead>
                                <tr class="border-b">
                                    {% for key in historico[0].keys() %}
                                        <th class="py-2 pr-4 font-semibold">{{ key }}</th>
                                    {% endfor %}
                                </tr>
                            </thead>
                            <tbody>
                                {% for item in historico %}
                                    <tr class="border-b">
                                        {% for value in item.values() %}
                                            <td class="py-2 pr-4">{{ value }}</td>
                                        {% endfor %}
                                    </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                {% else %}
                    <p>Nenhum registro de histórico encontrado.</p>
                {% endif %}
            </div>
        </div>
    </body>
    </html>
    ''', cliente=cliente, equipamentos=equipamentos, historico=historico)


if __name__ == '__main__':
    app.run(debug=True)
