from flask import g, session, redirect, url_for, flash
from functools import wraps
from models import User  # Zorg ervoor dat User correct wordt geïmporteerd

# Before request: Laad ingelogde gebruiker
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id:
        g.user = User.query.get(user_id)
    else:
        g.user = None

# Decorator voor login-toegang
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Je moet ingelogd zijn om deze pagina te bekijken.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator voor admin-toegang
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session['username'] != 'admin':
            flash('Alleen de admin heeft toegang tot deze pagina.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function
