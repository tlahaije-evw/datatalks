from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash, g
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from utils import *
from seeddata import seed_data
from models import db, User, Chat, Message, Dataset, Permission
from biutilsauth import load_logged_in_user, login_required, admin_required

# Basis configuratie
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

app.before_request(load_logged_in_user)

# Routes
@app.route('/')
@login_required
def home():
    user = User.query.get(session['user_id'])
    permissions = Permission.query.filter_by(user_id=user.id, granted=True).all()
    datasets = [p.dataset for p in permissions]
    chats = Chat.query.filter_by(user_id=user.id).all()
    return render_template('home.html', chats=chats, datasets=datasets, user=user)

@app.route('/start_chat', methods=['POST'])
@login_required
def start_chat():
    user = User.query.get(session['user_id'])  
    dataset_info = request.form['dataset_path']
    dataset_name, dataset_path = dataset_info.split(';')
    title = f"Start gesprek over {dataset_name}"
    new_chat = Chat(user_id=user.id, title=title, dataset_path=dataset_path)
    db.session.add(new_chat)
    db.session.commit()

    # Redirect naar de chatpagina
    return redirect(url_for('chat', chat_id=new_chat.id))

@app.route('/chat/<int:chat_id>')
@login_required
def chat(chat_id):
    user = User.query.get(session['user_id'])
    permissions = Permission.query.filter_by(user_id=user.id, granted=True).all()
    chat = Chat.query.get_or_404(chat_id)
    messages = Message.query.filter_by(chat_id=chat.id).order_by(Message.timestamp).all()
    datasets = [p.dataset for p in permissions]
    chats = Chat.query.filter_by(user_id=user.id).all()

    # Token Calculatie
    tokens = calculate_tokens_with_preview(chat.dataset_path)
    print(tokens)

    # Haal de dataset-preview op
    dataset_preview = get_dataset_preview(chat.dataset_path)

    return render_template(
        'chat.html',
        chat=chat,
        messages=messages,
        datasets=datasets,
        chats=chats,
        dataset_preview=dataset_preview
    )

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    chat_id = request.form['chat_id']
    sender = request.form['sender']
    content = request.form['content']

    # Voeg het gebruikersbericht toe aan de database
    new_message = Message(chat_id=chat_id, sender=sender, content=content)
    db.session.add(new_message)
    db.session.commit()

    # Roep een functie aan om de AI-reactie te genereren
    ai_response = generate_ai_response(chat_id, content)

    # Voeg de AI-reactie toe aan de database
    ai_message = Message(chat_id=chat_id, sender='bot', content=ai_response)
    db.session.add(ai_message)
    db.session.commit()

    # Retourneer zowel het gebruikersbericht als de AI-reactie
    return jsonify({
        "success": True,
        "user_message": {
            "content": content,
            "sender": sender,
            "timestamp": new_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        },
        "ai_message": {
            "content": ai_response,
            "sender": "bot",
            "timestamp": ai_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
    })

# Dummy functie om een AI-reactie te genereren
def generate_ai_response(chat_id, user_message):
    # Voor nu een dummy reactie
    return "Reactie succesvol"

@app.route('/admin/datasets', methods=['GET', 'POST'])
@login_required
def manage_datasets():
    if 'username' in session and session['username'] != 'admin':
        flash('Alleen de admin heeft toegang tot deze pagina.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        dataset_name = request.form['name']
        dataset_path = request.form['path']

        # Validatie
        if not dataset_name or not dataset_path:
            flash('Naam en pad zijn verplicht.', 'danger')
            return redirect(url_for('manage_datasets'))
        if not dataset_path.lower().endswith(('.xls', '.xlsx')):
            flash('Alleen Excel-bestanden zijn toegestaan.', 'danger')
            return redirect(url_for('manage_datasets'))
        if not os.path.isfile(dataset_path):
            flash(f'Het opgegeven bestand bestaat niet of is niet toegankelijk. Pad: {dataset_path}' , 'danger')
            return redirect(url_for('manage_datasets'))

        # Dataset toevoegen
        new_dataset = Dataset(
            name=dataset_name,
            path=dataset_path
        )
        db.session.add(new_dataset)
        db.session.commit()

        flash('Dataset succesvol toegevoegd.', 'success')
        return redirect(url_for('manage_datasets'))

    datasets = Dataset.query.all()
    return render_template('admin_datasets.html', datasets=datasets)


@app.route('/admin/datasets/delete/<int:dataset_id>', methods=['POST'])
@admin_required
def delete_dataset(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)

    # Verwijder gekoppelde permissies
    Permission.query.filter_by(dataset_id=dataset.id).delete()

    db.session.delete(dataset)
    db.session.commit()

    flash('Dataset succesvol verwijderd.', 'success')
    return redirect(url_for('manage_datasets'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Je bent succesvol ingelogd.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash('Ongeldige gebruikersnaam of wachtwoord.', 'danger')

    return render_template('login.html')

@app.route('/admin/permissions', methods=['GET', 'POST'])
@login_required
def manage_permissions():
    # Controleer of de ingelogde gebruiker een admin is
    if 'username' in session and session['username'] != 'admin':
        flash('Alleen de admin heeft toegang tot deze pagina.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        # Verwerk de toegangsrechten
        Permission.query.delete()  # Verwijder bestaande permissies
        for user_id in request.form:
            if user_id.isdigit():  # Controleer of het een gebruikers-ID is
                dataset_ids = request.form.getlist(user_id)
                for dataset_id in dataset_ids:
                    permission = Permission(
                        user_id=int(user_id),
                        dataset_id=int(dataset_id),
                        granted=True
                    )
                    db.session.add(permission)
        db.session.commit()
        flash('Permissies succesvol bijgewerkt.', 'success')
        return redirect(url_for('manage_permissions'))

    # Haal gebruikers en datasets op
    users = User.query.all()
    datasets = Dataset.query.all()

    # Maak een permissiemap om huidige permissies te controleren
    permissions = Permission.query.all()
    permission_map = {(p.user_id, p.dataset_id): p.granted for p in permissions}

    return render_template(
        'permissions.html',
        users=users,
        datasets=datasets,
        permission_map=permission_map
    )

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Je bent succesvol uitgelogd.', 'success')
    return redirect(url_for('login'))

# Initialiseer de database bij app-start
if __name__ == '__main__':
    with app.app_context():
        seed_data(db, User, Dataset)
        app.run(debug=True)
