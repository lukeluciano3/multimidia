import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, get_flashed_messages
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User, db
import os

from models.video import Video

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:123@localhost:5432/meu_banco'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'media'

db.init_app(app)  # Inicializar o SQLAlchemy com o app Flask

# Configurar o Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Ajustar para criar tabelas apenas uma vez
@app.before_request
def create_tables_and_admin():
    db.create_all()

    # Verificar se o usuário admin já existe
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin')
        admin_user.set_password('admin')
        db.session.add(admin_user)
        db.session.commit()
        print("Usuário admin/admin criado com sucesso.")

@app.route('/')
@login_required
def index():
    videos = Video.query.all()
    return render_template('index.html', videos=videos)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'files[]' not in request.files:
            flash('Nenhum arquivo selecionado.')
            return redirect(url_for('upload'))

        files = request.files.getlist('files[]')
        video_extensions = {'.mp4', '.webm', '.ogg', '.mkv'}

        for file in files:
            if not any(file.filename.endswith(ext) for ext in video_extensions):
                flash('Formato de arquivo não suportado.')
                return redirect(url_for('upload'))

            # Gerar um nome aleatório para o arquivo
            unique_filename = f"{uuid.uuid4()}_{file.filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))

            # Registrar o vídeo no banco de dados
            new_video = Video(original_filename=file.filename, filename=unique_filename, user_id=current_user.id)
            db.session.add(new_video)

        db.session.commit()
        flash('Upload realizado com sucesso.')
        return redirect(url_for('index'))

    return render_template('upload.html')

@app.route('/media/<filename>')
def media(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/video/<filename>')
@login_required
def video(filename):
    video = Video.query.filter_by(filename=filename).first_or_404()
    return render_template('video.html', video=video)

@app.route('/logout')
@login_required
def logout():
    get_flashed_messages()
    logout_user()
    flash('Você saiu com sucesso.')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login realizado com sucesso.')
            return redirect(url_for('index'))
        else:
            flash('Nome de usuário ou senha inválidos.')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Verificar se o usuário já existe
        if User.query.filter_by(username=username).first():
            flash('Usuário já existe.')
            return redirect(url_for('register'))

        # Criar novo usuário com senha criptografada
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Usuário registrado com sucesso. Por favor, faça login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/delete_video/<int:video_id>', methods=['GET'])
@login_required
def delete_video(video_id):
    # Verificar se o usuário é admin
    if current_user.username != 'admin':
        flash('Apenas o administrador pode excluir vídeos.')
        return redirect(url_for('index'))

    # Obter o vídeo do banco de dados
    video = Video.query.get_or_404(video_id)

    # Remover o arquivo de vídeo do diretório
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
    if os.path.exists(video_path):
        os.remove(video_path)

    # Remover o vídeo do banco de dados
    db.session.delete(video)
    db.session.commit()

    flash(f'Vídeo "{video.original_filename}" excluído com sucesso.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)