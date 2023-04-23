from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import pymysql

# Initializing Flask application and login manager
app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.static_folder = 'static'

login_manager = LoginManager()
login_manager.init_app(app)

# Creating a MySQL database connection
mysql = pymysql.connect(
    host='localhost',      # Replace with your MySQL server host
    user='root',  # Replace with your MySQL username
    password='',  # Replace with your MySQL password
    database='city_jail'
)

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    @staticmethod
    def get(user_id):
        cur = mysql.cursor()
        cur.execute('SELECT * FROM users WHERE id=%s', (user_id,))
        result = cur.fetchone()
        cur.close()

        if result:
            return User(result[0], result[1], result[2])
        else:
            return None

# Flask-Login user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Criminals page
@app.route('/criminals')
def get_criminals():
    cur = mysql.cursor()
    cur.execute('SELECT * FROM Criminals')
    result = cur.fetchall()
    cur.close()
    return render_template('criminals.html', criminals=result)

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        cur = mysql.cursor()
        cur.execute('SELECT * FROM users WHERE username=%s AND password=%s', (username, password))
        result = cur.fetchone()
        cur.close()

        if result:
            user = User(result[0], result[1], result[2])
            login_user(user)
            next_page = request.args.get('next', url_for('dashboard'))
            return redirect(next_page)

        flash('Invalid username or password', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')

# Login error page
@app.route('/login_error')
def login_error():
    flash('Invalid username or password', 'error')
    return redirect(url_for('login'))




# Dashboard
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']

        with mysql.cursor() as cur:
            cur.callproc('GetCriminalDetails', (first_name, last_name))
            criminals = cur.fetchall()

            cur.execute('SELECT * FROM Officers')
            officers = cur.fetchall()

            cur.execute('SELECT * FROM Crimes')
            crimes = cur.fetchall()

            cur.execute('SELECT * FROM Crime_Codes')
            crime_codes = cur.fetchall()

            cur.execute('SELECT * FROM Crime_Officers')
            crime_officers = cur.fetchall()

            cur.execute('SELECT * FROM Appeals')
            appeals = cur.fetchall()

            cur.execute('SELECT * FROM CriminalCharges')
            criminal_charges = cur.fetchall()

            cur.execute('SELECT * FROM Aliases')
            aliases = cur.fetchall()

            cur.execute('SELECT * FROM Prob_officers')
            prob_officers = cur.fetchall()

            cur.execute('SELECT * FROM Sentences')
            sentences = cur.fetchall()

        return render_template('dashboard.html', 
                                criminals=criminals,
                                officers=officers,
                                crimes=crimes,
                                crime_codes=crime_codes,
                                crime_officers=crime_officers,
                                appeals=appeals,
                                criminal_charges=criminal_charges,
                                aliases=aliases,
                                prob_officers=prob_officers,
                                sentences=sentences)

    return render_template('dashboard.html')


# About page
@app.route('/about')
def about():
    return render_template('Zzz_about.html')

# Logout page
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
