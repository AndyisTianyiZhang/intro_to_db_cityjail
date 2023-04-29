from functools import wraps
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
    def __init__(self, id, username, password, role):
        self.id = id
        self.username = username
        self.password = password
        self.role = role

    @staticmethod
    def get(user_id):
        cur = mysql.cursor()
        cur.execute('SELECT * FROM users WHERE id=%s', (user_id,))
        result = cur.fetchone()
        cur.close()

        if result:
            return User(result[0], result[1], result[2], result[3])
        else:
            return None
        
    def is_admin(self):
        return self.username == 'admin'


# Flask-Login user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Admin dashboard
@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        cur = mysql.cursor()
        cur.execute('SELECT * FROM users WHERE username=%s AND password=%s', (username, password))
        result = cur.fetchone()
        cur.close()

        if result:
            user = User(result[0], result[1], result[2], result[3])  # Include the role in the User constructor
            login_user(user)
            next_page = request.args.get('next', url_for('dashboard'))
            return redirect(next_page)

        flash('Invalid username or password', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')


# Route for rendering the sign-up page
@app.route('/signup_page')
def signup_page():
    return render_template('signup.html')


# Route for processing the sign-up form data
@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if password != confirm_password:
        flash('Passwords do not match', 'error')
        return redirect(url_for('signup_page'))

    cur = mysql.cursor()
    cur.execute('SELECT * FROM users WHERE username=%s', (username,))
    result = cur.fetchone()

    if result:
        flash('Username already exists', 'error')
        return redirect(url_for('signup_page'))

    cur.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password))
    mysql.commit()
    cur.close()

    flash('Account created successfully! Please log in.', 'success')
    return redirect(url_for('login'))

# Login error page
@app.route('/login_error')
def login_error():
    flash('Invalid username or password', 'error')
    return redirect(url_for('login'))

# Logout page
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

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
@admin_required
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

@app.route('/delete_criminal', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_criminal():
    if request.method == 'POST':
        criminal_id = request.form['criminal_id']

        with mysql.cursor() as cur:
            cur.execute('DELETE FROM Aliases WHERE criminal_ID = %s', (criminal_id,))
            cur.execute('DELETE FROM Sentences WHERE criminal_ID = %s', (criminal_id,))
            
            cur.execute('SELECT crime_id FROM Crimes WHERE criminal_ID = %s', (criminal_id,))
            crime_ids = [row[0] for row in cur.fetchall()]
            
            if crime_ids:
                cur.execute('DELETE FROM Appeals WHERE crime_id IN %s', (tuple(crime_ids),))
                cur.execute('DELETE FROM CriminalCharges WHERE crime_id IN %s', (tuple(crime_ids),))
                cur.execute('DELETE FROM Crime_Officers WHERE crime_id IN %s', (tuple(crime_ids),))
                cur.execute('DELETE FROM Crimes WHERE criminal_ID = %s', (criminal_id,))
            
            cur.execute('DELETE FROM Criminals WHERE criminal_ID = %s', (criminal_id,))
            mysql.commit()

        flash('Criminal deleted successfully!', 'success')

    with mysql.cursor() as cur:
        cur.execute("SELECT * FROM Criminals;")
        result = cur.fetchall()

    return render_template('delete_criminal.html', criminals=result)


@app.route('/update_criminal/<int:criminal_ID>', methods=['GET', 'POST'])
@login_required
@admin_required
def update_criminal(criminal_ID):
    if request.method == 'POST':
        l_name = request.form['l_name']
        f_name = request.form['f_name']
        street = request.form['street']
        city = request.form['city']
        state = request.form['state']
        zip = request.form['zip']
        phone_num = request.form['phone_num']
        v_status = request.form['v_status']
        p_status = request.form['p_status']

        with mysql.cursor() as cur:
            cur.execute("""
                UPDATE Criminals
                SET l_name = %s, f_name = %s, street = %s, city = %s, state = %s, zip = %s, phone_num = %s, V_status = %s, P_status = %s
                WHERE criminal_ID = %s
            """, (l_name, f_name, street, city, state, zip, phone_num, v_status, p_status, criminal_ID))
            mysql.commit()

        flash('Criminal information updated successfully!', 'success')
        return redirect(url_for('get_all_criminals'))

    with mysql.cursor() as cur:
        cur.execute("SELECT * FROM Criminals WHERE criminal_ID = %s", (criminal_ID,))
        criminal = cur.fetchone()

    if criminal is None:
        flash('Criminal not found', 'error')
        return redirect(url_for('get_all_criminals'))

    return render_template('update_criminal.html', criminal=criminal)



# About page
@app.route('/about')
def about():
    return render_template('Zzz_about.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port = 8000)

