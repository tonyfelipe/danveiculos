from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'sua-chave-secreta-aqui-mude-em-producao'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Criar pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db():
    """Conecta ao banco de dados SQLite"""
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Tabela de usuários admin
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de veículos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            ano INTEGER NOT NULL,
            valor REAL NOT NULL,
            descricao TEXT,
            quilometragem INTEGER,
            cor TEXT,
            combustivel TEXT,
            cambio TEXT,
            status TEXT DEFAULT 'disponivel',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de fotos dos veículos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicle_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            ordem INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE
        )
    ''')
    
    # Criar usuário admin padrão se não existir
    cursor.execute("SELECT * FROM users WHERE username = ?", ('admin',))
    if not cursor.fetchone():
        hashed_password = generate_password_hash('admin123')
        cursor.execute(
            "INSERT INTO users (username, password, name) VALUES (?, ?, ?)",
            ('admin', hashed_password, 'Daniel Lopes')
        )
    
    conn.commit()
    conn.close()

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    """Decorator para proteger rotas que requerem login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== ROTAS PÚBLICAS ====================

@app.route('/')
def index():
    """Página inicial - vitrine de veículos"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Buscar todos os veículos
    cursor.execute('''
        SELECT v.*, 
               (SELECT filename FROM vehicle_photos WHERE vehicle_id = v.id ORDER BY ordem LIMIT 1) as foto_principal
        FROM vehicles v
        ORDER BY v.created_at DESC
    ''')
    vehicles = cursor.fetchall()
    conn.close()
    
    return render_template('index.html', vehicles=vehicles)

@app.route('/veiculo/<int:id>')
def vehicle_details(id):
    """Página de detalhes do veículo"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Buscar veículo
    cursor.execute('SELECT * FROM vehicles WHERE id = ?', (id,))
    vehicle = cursor.fetchone()
    
    if not vehicle:
        flash('Veículo não encontrado.', 'error')
        return redirect(url_for('index'))
    
    # Buscar fotos do veículo
    cursor.execute('SELECT * FROM vehicle_photos WHERE vehicle_id = ? ORDER BY ordem', (id,))
    photos = cursor.fetchall()
    conn.close()
    
    return render_template('vehicle_details.html', vehicle=vehicle, photos=photos)

# ==================== ROTAS DE AUTENTICAÇÃO ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login do administrador"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['name'] = user['name']
            flash(f'Bem-vindo, {user["name"]}!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Usuário ou senha incorretos.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout do administrador"""
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('index'))

# ==================== ROTAS ADMINISTRATIVAS ====================

@app.route('/admin')
@login_required
def admin_dashboard():
    """Painel administrativo"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Buscar todos os veículos com foto principal
    cursor.execute('''
        SELECT v.*, 
               (SELECT filename FROM vehicle_photos WHERE vehicle_id = v.id ORDER BY ordem LIMIT 1) as foto_principal
        FROM vehicles v
        ORDER BY v.created_at DESC
    ''')
    vehicles = cursor.fetchall()
    conn.close()
    
    return render_template('admin_dashboard.html', vehicles=vehicles)

@app.route('/admin/veiculo/novo', methods=['GET', 'POST'])
@login_required
def admin_new_vehicle():
    """Adicionar novo veículo"""
    if request.method == 'POST':
        marca = request.form.get('marca')
        modelo = request.form.get('modelo')
        ano = request.form.get('ano')
        valor = request.form.get('valor')
        descricao = request.form.get('descricao')
        quilometragem = request.form.get('quilometragem')
        cor = request.form.get('cor')
        combustivel = request.form.get('combustivel')
        cambio = request.form.get('cambio')
        status = request.form.get('status', 'disponivel')
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Inserir veículo
        cursor.execute('''
            INSERT INTO vehicles (marca, modelo, ano, valor, descricao, quilometragem, cor, combustivel, cambio, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (marca, modelo, ano, valor, descricao, quilometragem, cor, combustivel, cambio, status))
        
        vehicle_id = cursor.lastrowid
        
        # Upload de fotos
        files = request.files.getlist('photos')
        for i, file in enumerate(files):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"{vehicle_id}_{timestamp}_{i}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                cursor.execute(
                    'INSERT INTO vehicle_photos (vehicle_id, filename, ordem) VALUES (?, ?, ?)',
                    (vehicle_id, filename, i)
                )
        
        conn.commit()
        conn.close()
        
        flash('Veículo adicionado com sucesso!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_vehicle_form.html', vehicle=None)

@app.route('/admin/veiculo/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def admin_edit_vehicle(id):
    """Editar veículo existente"""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        marca = request.form.get('marca')
        modelo = request.form.get('modelo')
        ano = request.form.get('ano')
        valor = request.form.get('valor')
        descricao = request.form.get('descricao')
        quilometragem = request.form.get('quilometragem')
        cor = request.form.get('cor')
        combustivel = request.form.get('combustivel')
        cambio = request.form.get('cambio')
        status = request.form.get('status', 'disponivel')
        
        # Atualizar veículo
        cursor.execute('''
            UPDATE vehicles 
            SET marca=?, modelo=?, ano=?, valor=?, descricao=?, quilometragem=?, 
                cor=?, combustivel=?, cambio=?, status=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (marca, modelo, ano, valor, descricao, quilometragem, cor, combustivel, cambio, status, id))
        
        # Upload de novas fotos
        files = request.files.getlist('photos')
        if files and files[0].filename:
            # Contar fotos existentes para ordenação
            cursor.execute('SELECT COUNT(*) as count FROM vehicle_photos WHERE vehicle_id = ?', (id,))
            count = cursor.fetchone()['count']
            
            for i, file in enumerate(files):
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    filename = f"{id}_{timestamp}_{count + i}_{filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    
                    cursor.execute(
                        'INSERT INTO vehicle_photos (vehicle_id, filename, ordem) VALUES (?, ?, ?)',
                        (id, filename, count + i)
                    )
        
        conn.commit()
        conn.close()
        
        flash('Veículo atualizado com sucesso!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    # GET - buscar veículo e fotos
    cursor.execute('SELECT * FROM vehicles WHERE id = ?', (id,))
    vehicle = cursor.fetchone()
    
    cursor.execute('SELECT * FROM vehicle_photos WHERE vehicle_id = ? ORDER BY ordem', (id,))
    photos = cursor.fetchall()
    
    conn.close()
    
    if not vehicle:
        flash('Veículo não encontrado.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_vehicle_form.html', vehicle=vehicle, photos=photos)

@app.route('/admin/veiculo/<int:id>/excluir', methods=['POST'])
@login_required
def admin_delete_vehicle(id):
    """Excluir veículo"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Buscar fotos para deletar arquivos
    cursor.execute('SELECT filename FROM vehicle_photos WHERE vehicle_id = ?', (id,))
    photos = cursor.fetchall()
    
    # Deletar arquivos de fotos
    for photo in photos:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], photo['filename'])
        if os.path.exists(filepath):
            os.remove(filepath)
    
    # Deletar fotos do banco
    cursor.execute('DELETE FROM vehicle_photos WHERE vehicle_id = ?', (id,))
    
    # Deletar veículo
    cursor.execute('DELETE FROM vehicles WHERE id = ?', (id,))
    
    conn.commit()
    conn.close()
    
    flash('Veículo excluído com sucesso!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/foto/<int:id>/excluir', methods=['POST'])
@login_required
def admin_delete_photo(id):
    """Excluir foto de veículo"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Buscar foto
    cursor.execute('SELECT * FROM vehicle_photos WHERE id = ?', (id,))
    photo = cursor.fetchone()
    
    if photo:
        # Deletar arquivo
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], photo['filename'])
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Deletar do banco
        cursor.execute('DELETE FROM vehicle_photos WHERE id = ?', (id,))
        conn.commit()
    
    conn.close()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
