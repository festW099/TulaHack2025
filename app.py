from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import os
import json
from werkzeug.utils import secure_filename
import base64

app = Flask(__name__)
secret_key = os.urandom(24).hex()
app.secret_key = f'{secret_key}'

UPLOAD_FOLDER = 'static/photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

USER_BASE = 'Data/users.db'
HEROES_BASE = 'Data/heroes.db'

def connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        conn = connection(USER_BASE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

        conn = connection(HEROES_BASE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS heroes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                awards TEXT NOT NULL,
                letter TEXT,
                battles TEXT NOT NULL,
                photos TEXT NOT NULL,
                born TEXT NOT NULL,
                year_start TEXT NOT NULL,
                year_end TEXT NOT NULL,
                locations TEXT NOT NULL,
                born_latitude REAL NOT NULL,
                born_longitude REAL NOT NULL,
                battle_locations TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_login(email, password):
    conn = connection(USER_BASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
    user = cursor.fetchone()
    conn.close()
    return user

@app.route('/')
def home():
    return render_template("home.html", user=session.get('user'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        try:
            conn = connection(USER_BASE)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', 
                         (username, email, password))
            conn.commit()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            conn.close()
            session['user'] = dict(user)
            return redirect(url_for('home')) 
        except sqlite3.IntegrityError:
            return "Email уже существует"
        except Exception as e:
            print(f"Error: {e}")
            return "Произошла ошибка при регистрации"
    else:
        return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = check_login(email, password)
        if user:
            session['user'] = dict(user)
            return redirect(url_for('home'))
        else:
            return render_template("login.html", error="Invalid email or password")
    else:
        return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/create', methods=['GET', 'POST'])
def create_hero():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            awards = request.form.get('awards', '[]')
            full_name = request.form.get('full_name', '')
            battles = request.form.get('battles', '')
            born = request.form.get('born', '')
            year_start = request.form.get('year_start', '')
            year_end = request.form.get('year_end', '')
            born_latitude = request.form.get('born_latitude', '0.0')
            born_longitude = request.form.get('born_longitude', '0.0')
            battle_locations = request.form.get('battle_locations', '[]')
            locations = request.form.get('locations', '') 
            
            letter_photo_path = None
            if 'letter_photo' in request.files:
                letter_file = request.files['letter_photo']
                if letter_file and allowed_file(letter_file.filename):
                    filename = secure_filename(letter_file.filename)
                    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_' + filename)
                    letter_file.save(temp_path)
                    letter_photo_path = temp_path
            
            conn = connection(HEROES_BASE)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO heroes (
                    full_name, awards, battles, born,
                    year_start, year_end, born_latitude, born_longitude,
                    battle_locations, photos, letter, locations
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                full_name,
                awards,
                battles,
                born,
                year_start,
                year_end,
                born_latitude,
                born_longitude,
                battle_locations,
                '',
                letter_photo_path,
                locations 
            ))
            
            hero_id = cursor.lastrowid
            
            photos = []
            if 'photos' in request.files:
                os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], str(hero_id)), exist_ok=True)
                
                for file in request.files.getlist('photos'):
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(str(hero_id), filename)
                        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filepath)
                        file.save(save_path)
                        photos.append(filepath)
            
            if letter_photo_path and os.path.exists(letter_photo_path):
                letter_filename = os.path.basename(letter_photo_path).replace('temp_', '')
                new_letter_path = os.path.join(str(hero_id), letter_filename)
                os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], str(hero_id)), exist_ok=True)
                os.rename(
                    letter_photo_path,
                    os.path.join(app.config['UPLOAD_FOLDER'], new_letter_path))
                
                cursor.execute('UPDATE heroes SET letter = ? WHERE id = ?', 
                             (new_letter_path, hero_id))
            
            if photos:
                cursor.execute('UPDATE heroes SET photos = ? WHERE id = ?', 
                             (json.dumps(photos), hero_id))
            
            conn.commit()
            conn.close()
            
            return redirect(url_for('home'))
            
        except Exception as e:
            print(f"Error: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return f"Произошла ошибка при создании: {str(e)}", 400
    
    return render_template("create.html", user=session.get('user'))

def get_remember_data(id):
    conn = sqlite3.connect('Data/heroes.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, full_name, awards, letter, battles, photos, born,
               year_start, year_end, born_latitude, born_longitude,
               battle_locations
        FROM heroes WHERE id=?
    """, (id,))
    
    columns = [column[0] for column in cursor.description]
    data = cursor.fetchone()
    conn.close()
    
    if not data:
        return None
    
    data_dict = dict(zip(columns, data))
    
    def parse_json_field(value, default):
        try:
            return json.loads(value) if value else default
        except (json.JSONDecodeError, TypeError):
            return default
    
    data_dict['awards'] = parse_json_field(data_dict.get('awards'), [])
    data_dict['photos'] = parse_json_field(data_dict.get('photos'), [])
    data_dict['battle_locations'] = parse_json_field(data_dict.get('battle_locations'), [])
    
    try:
        data_dict['born_latitude'] = float(data_dict.get('born_latitude', 0))
    except (ValueError, TypeError):
        data_dict['born_latitude'] = 0.0
    
    try:
        data_dict['born_longitude'] = float(data_dict.get('born_longitude', 0))
    except (ValueError, TypeError):
        data_dict['born_longitude'] = 0.0
    
    return data_dict

@app.route('/remember/<int:id>')
def remember(id):
    data = get_remember_data(id)
    if not data:
        return "Record not found", 404
    
    map_data = {
        'birth': {
            'lat': data['born_latitude'],
            'lng': data['born_longitude'],
            'locations': data.get('locations', 'Не указано')
        },
        'battles': data['battle_locations']
    }
    
    return render_template(
        'hero.html',
        data=data,
        map_data=json.dumps(map_data, ensure_ascii=False), user=session.get('user')
    )

def get_all_heroes():
    conn = sqlite3.connect('Data/heroes.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, full_name, awards, letter, battles, photos, born,
               year_start, year_end, born_latitude, born_longitude,
               battle_locations
        FROM heroes
    """)
    
    columns = [column[0] for column in cursor.description]
    all_data = cursor.fetchall()
    conn.close()
    
    heroes_list = []
    
    def parse_json_field(value, default):
        try:
            return json.loads(value) if value else default
        except (json.JSONDecodeError, TypeError):
            return default
    
    for data in all_data:
        data_dict = dict(zip(columns, data))
        
        data_dict['awards'] = parse_json_field(data_dict.get('awards'), [])
        data_dict['photos'] = parse_json_field(data_dict.get('photos'), [])
        data_dict['battle_locations'] = parse_json_field(data_dict.get('battle_locations'), [])
        
        try:
            data_dict['born_latitude'] = float(data_dict.get('born_latitude', 0))
        except (ValueError, TypeError):
            data_dict['born_latitude'] = 0.0
        
        try:
            data_dict['born_longitude'] = float(data_dict.get('born_longitude', 0))
        except (ValueError, TypeError):
            data_dict['born_longitude'] = 0.0
        
        heroes_list.append(data_dict)
    
    return heroes_list

@app.route('/remember')
def remember_search():
    all_heroes = get_all_heroes()
    
    transformed_heroes = []
    for hero in all_heroes:
        transformed_hero = {
            'id': hero['id'],
            'name': hero['full_name'],
            'warYears': f"{hero['year_start']}-{hero['year_end']}",
            'birthPlace': hero['born'],
            'warPlaces': hero.get('battle_locations', []),
            'battles': hero.get('battles', ""),
            'awards': hero.get('awards', []),
            'photos': hero.get('photos', []),
            'coords': [hero.get('born_latitude', 0), hero.get('born_longitude', 0)],
            'warCoords': hero.get('battle_coordinates', [])
        }
        transformed_heroes.append(transformed_hero)
    
    return render_template("remember.html", mockHeroes=transformed_heroes, user=session.get('user'))

if __name__ == '__main__':
    init_db()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)