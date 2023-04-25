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
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']

        with mysql.cursor() as cur:
            cur.callproc('GetCriminalDetails', (first_name, last_name))
            result = cur.fetchall()
        
        print("Stored procedure result:", result)  # Debugging line

        return render_template('search_results.html', criminals=result)

    return render_template('search.html')

@app.route('/get_all_criminals')
@login_required
def get_all_criminals():
    with mysql.cursor() as cur:
        cur.execute("SELECT * FROM Criminals;")
        result = cur.fetchall()

    return render_template('get_all_criminals.html', criminals=result)


@app.route('/add_criminal', methods=['GET', 'POST'])
@login_required
def add_criminal():
    if request.method == 'POST':
        # Retrieve form data
        criminal_id = request.form['criminal_id']
        l_name = request.form['l_name']
        f_name = request.form['f_name']
        street = request.form['street']
        city = request.form['city']
        state = request.form['state']
        zip = request.form['zip']
        phone_num = request.form['phone_num']
        v_status = request.form['v_status']
        p_status = request.form['p_status']

        # Insert new criminal into database
            # Insert new criminal into database
        with mysql.cursor() as cur:
            cur.execute('INSERT INTO Criminals (criminal_ID, l_name, f_name, street, city, state, zip, phone_num, V_status, P_status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (criminal_id, l_name, f_name, street, city, state, zip, phone_num, v_status, p_status))
            mysql.commit()

        flash('New criminal added successfully!', 'success')

    return render_template('add_criminal.html')



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
