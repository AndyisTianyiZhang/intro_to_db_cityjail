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
    host='localhost',
    user='root',
    password='',
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
        return self.role == 'admin'


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

# About page
@app.route('/about')
def about():
    return render_template('Zzz_about.html')

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        cur = mysql.cursor()
        cur.execute('SELECT * FROM users WHERE username=%s AND password=%s', (username, password))
        result = cur.fetchone()
        cur.close()

        if result:
            user = User(result[0], result[1], result[2], result[3])
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
        
        if result[0][0] == "No entries found":
            flash("No entries found")
            redirect(url_for('search'))
        else:
            return render_template('search_results.html', criminals=result)

    return render_template('search.html')

@app.route('/display/<string:data_type>', methods=['GET', 'POST'])
@login_required
def display(data_type):
    search_id = None
    data = {}

    with mysql.cursor() as cur:
        if request.method == 'POST' and request.form.get('action') == 'search':
            search_id = request.form.get('search_id')
            if data_type == 'criminal':
                cur.execute("SELECT * FROM Criminals WHERE criminal_ID = %s", (search_id,))
                data['criminals'] = cur.fetchall()
            elif data_type == 'officer':
                cur.execute("SELECT * FROM Officers WHERE officer_ID = %s", (search_id,))
                data['officers'] = cur.fetchall()
            elif data_type == 'prob_officer':
                cur.execute("SELECT * FROM Prob_officers WHERE prob_id = %s", (search_id,))
                data['prob_officers'] = cur.fetchall()
            elif data_type == 'crime_code':
                cur.execute("SELECT * FROM Crime_Codes WHERE crime_code = %s", (search_id,))
                data['crime_codes'] = cur.fetchall()
            elif data_type == 'crime_officer':
                search_officer_id = request.form.get('search_officer_id')
                cur.execute("SELECT * FROM Crime_Officers WHERE crime_id = %s AND officer_id = %s", (search_id, search_officer_id))
                data['crime_officers'] = cur.fetchall()
            elif data_type == 'crime':
                cur.execute("SELECT * FROM Crimes WHERE crime_id = %s", (search_id,))
                data['crime'] = cur.fetchall()
            elif data_type == 'appeal':
                cur.execute("SELECT * FROM Appeals WHERE appeal_id = %s", (search_id,))
                data['appeals'] = cur.fetchall()
        else:
            if data_type == 'criminal':
                cur.execute("SELECT * FROM Criminals")
                data['criminals'] = cur.fetchall()
            elif data_type == 'officer':
                cur.execute("SELECT * FROM Officers")
                data['officers'] = cur.fetchall()
            elif data_type == 'prob_officer':
                cur.execute("SELECT * FROM Prob_officers")
                data['prob_officers'] = cur.fetchall()
            elif data_type == 'crime_code':
                cur.execute("SELECT * FROM Crime_Codes")
                data['crime_codes'] = cur.fetchall()
            elif data_type == 'crime_officer':
                cur.execute("SELECT * FROM Crime_Officers")
                data['crime_officers'] = cur.fetchall()
            elif data_type == 'crime':
                cur.execute("SELECT * FROM Crimes")
                data['crimes'] = cur.fetchall()
            elif data_type == 'appeal':
                cur.execute("SELECT * FROM Appeals")
                data['appeals'] = cur.fetchall()

    return render_template('display.html', data=data, data_type=data_type, search_id=search_id)

@app.route('/add_entry/<string:data_type>', methods=['GET', 'POST'])
@login_required
@admin_required
def add_entry(data_type):
    if request.method == 'POST':
        # Retrieve form data
        if data_type == 'criminal':
            id = request.form['id']
            l_name = request.form['l_name']
            f_name = request.form['f_name']
            street = request.form['street']
            city = request.form['city']
            state = request.form['state']
            zip = request.form['zip']
            phone_num = request.form['phone_num']
            v_status = request.form['v_status']
            p_status = request.form['p_status']
        elif data_type == 'officer':
            id = request.form['id']
            l_name = request.form['l_name']
            f_name = request.form['f_name']
            precinct = request.form['precinct']
            badge = request.form['badge']
            phone_num = request.form['phone_num']
            status = request.form['status']
        elif data_type == 'prob_officer':
            id = request.form['id']
            l_name = request.form['l_name']
            f_name = request.form['f_name']
            street = request.form['street']
            city = request.form['city']
            state = request.form['state']
            zip = request.form['zip']
            phone_num = request.form['phone_num']
            email = request.form['email']
            status = request.form['status']
        elif data_type == 'crime_code':
            crime_code = request.form['crime_code']
            code_description = request.form['code_description']
        elif data_type == 'crime_officer':
            crime_id = request.form['crime_id']
            officer_id = request.form['officer_id']
        elif data_type == 'crime':
            crime_id = request.form['crime_id']
            criminal_id = request.form['criminal_id']
            classification = request.form['classification']
            date_charged = request.form['date_charged']
            status = request.form['status']
            hearing_date = request.form['hearing_date']
            appeal_cutoff_date = request.form['appeal_cutoff_date']
        elif data_type == 'appeal':
            appeal_id = request.form['appeal_id']
            crime_id = request.form['crime_id']
            filing_date = request.form['filing_date']
            hearing_date = request.form['hearing_date']
            status = request.form['status']

        # Insert new entry into database
        with mysql.cursor() as cur:
            if data_type == 'criminal':
                cur.execute('INSERT INTO Criminals (criminal_ID, l_name, f_name, street, city, state, zip, phone_num, V_status, P_status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (id, l_name, f_name, street, city, state, zip, phone_num, v_status, p_status))
            elif data_type == 'officer':
                cur.execute('INSERT INTO Officers (officer_id, last, first, precinct, badge, phone, status) VALUES  (%s, %s, %s, %s, %s, %s, %s)', (id, l_name, f_name, precinct, badge, phone_num, status))
            elif data_type == 'prob_officer':
                cur.execute('INSERT INTO Prob_officers (prob_id, last_name, first_name, street, city, state, zip, phone, email, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (id, l_name, f_name, street, city, state, zip, phone_num, email, status))
            elif data_type == 'crime_code':
                cur.execute('INSERT INTO Crime_Codes (crime_code, code_description) VALUES (%s, %s)', (crime_code, code_description))
            elif data_type == 'crime_officer':
                cur.execute('INSERT INTO Crime_Officers (crime_id, officer_id) VALUES (%s, %s)', (crime_id, officer_id))
            elif data_type == 'crime':
                cur.execute('INSERT INTO Crimes (crime_id, criminal_id, classification, date_charged, status, hearing_date, appeal_cutoff_date) VALUES (%s, %s, %s, %s, %s, %s, %s)', (crime_id, criminal_id, classification, date_charged, status, hearing_date, appeal_cutoff_date))
            elif data_type == 'appeal':
                cur.execute('INSERT INTO Appeals (appeal_id, crime_id, filing_date, hearing_date, status) VALUES (%s, %s, %s, %s, %s)', (appeal_id, crime_id, filing_date, hearing_date, status))
            else:
                flash('Invalid data type specified.', 'error')
                return redirect(url_for('index'))
            
            mysql.commit()

        flash(f'New {data_type[:-1]} added successfully!', 'success')
        return redirect(url_for('display', data_type=data_type))

    return render_template('add_entry.html', data_type =data_type)

@app.route('/delete_entry/<string:data_type>/<string:id>', methods=['GET', 'POST'])
@app.route('/delete_entry/<string:data_type>/<string:id>/<string:id2>', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_entry(data_type, id, id2=None):
    if data_type == "criminal":
        with mysql.cursor() as cur:
            cur.execute('DELETE FROM Aliases WHERE criminal_ID = %s', (id,))
            cur.execute('DELETE FROM Sentences WHERE criminal_ID = %s', (id,))
            
            cur.execute('SELECT crime_id FROM Crimes WHERE criminal_ID = %s', (id,))
            crime_ids = [row[0] for row in cur.fetchall()]
            
            if crime_ids:
                cur.execute('DELETE FROM Appeals WHERE crime_id IN %s', (tuple(crime_ids),))
                cur.execute('DELETE FROM CriminalCharges WHERE crime_id IN %s', (tuple(crime_ids),))
                cur.execute('DELETE FROM Crime_Officers WHERE crime_id IN %s', (tuple(crime_ids),))
                cur.execute('DELETE FROM Crimes WHERE criminal_ID = %s', (id,))
        
            cur.execute('DELETE FROM Criminals WHERE criminal_ID = %s', (id,))
    elif data_type == "officer":
        with mysql.cursor() as cur:
            cur.execute('DELETE FROM Crime_Officers WHERE officer_id = %s', (id,))
            cur.execute('DELETE FROM Officers WHERE officer_id = %s', (id,))
    elif data_type == "prob_officer":
        with mysql.cursor() as cur:
            cur.execute('DELETE FROM Sentences WHERE prob_id = %s', (id,))
            cur.execute('DELETE FROM Prob_officers WHERE prob_id = %s', (id,))
    elif data_type == "crime_code":
        with mysql.cursor() as cur:
            cur.execute('DELETE FROM CriminalCharges WHERE crime_code = %s', (id,))
            cur.execute('DELETE FROM Crime_Codes WHERE crime_code = %s', (id,))
    elif data_type == 'crime_officer':
        with mysql.cursor() as cur:
            cur.execute("""
                DELETE FROM Crime_Officers
                WHERE crime_id = %s AND officer_id = %s
            """, (id, id2))
    elif data_type == "crime":
        with mysql.cursor() as cur:
            cur.execute('DELETE FROM Appeals WHERE crime_id = %s', (id,))
            cur.execute('DELETE FROM CriminalCharges WHERE crime_id = %s', (id,))
            cur.execute('DELETE FROM Crime_Officers WHERE crime_id = %s', (id,))
            cur.execute('DELETE FROM Crimes WHERE crime_id = %s', (id,))
    elif data_type == "appeal":
        with mysql.cursor() as cur:
            cur.execute('DELETE FROM Appeals WHERE appeal_id = %s', (id,))
            mysql.commit()
            flash(f'{data_type} deleted successfully!', 'success')
            return redirect(url_for('display', data_type=data_type))

    mysql.commit()

    flash(f'{data_type} deleted successfully!', 'success')
    return redirect(url_for('display', data_type=data_type))


@app.route('/update_entry/<string:data_type>/<string:id>', methods=['GET', 'POST'])
@app.route('/update_entry/<string:data_type>/<string:id>/<string:id2>', methods=['GET', 'POST'])
@login_required
@admin_required
def update_entry(data_type, id, id2=None):
    if request.method == 'POST':
        if data_type == 'criminal':
            l_name = request.form['l_name']
            f_name = request.form['f_name']
            phone_num = request.form['phone_num']
            street = request.form['street']
            city = request.form['city']
            state = request.form['state']
            zip = request.form['zip']
            v_status = request.form['v_status']
            p_status = request.form['p_status']
            with mysql.cursor() as cur:
                cur.execute("""
                    UPDATE Criminals
                    SET l_name = %s, f_name = %s, street = %s, city = %s, state = %s, zip = %s, phone_num = %s, V_status = %s, P_status = %s
                    WHERE criminal_ID = %s
                """, (l_name, f_name, street, city, state, zip, phone_num, v_status, p_status, id))
        elif data_type == 'officer':
            l_name = request.form['l_name']
            f_name = request.form['f_name']
            phone_num = request.form['phone_num']
            precinct = request.form['precinct']
            badge = request.form['badge']
            status = request.form['status']
            with mysql.cursor() as cur:
                cur.execute("""
                    UPDATE Officers
                    SET last = %s, first = %s, precinct = %s, badge = %s, phone = %s, status = %s
                    WHERE officer_ID = %s
                """, (l_name, f_name, precinct, badge, phone_num, status, id))
        elif data_type == 'prob_officer':
            street = request.form['street']
            city = request.form['city']
            state = request.form['state']
            zip = request.form['zip']
            email = request.form['email']
            status = request.form['status']
            with mysql.cursor() as cur:
                cur.execute("""
                    UPDATE Prob_officers
                    SET last_name = %s, first_name = %s, street = %s, city = %s, state = %s, zip = %s, phone = %s, email = %s, status = %s
                    WHERE prob_id = %s
                """, (l_name, f_name, street, city, state, zip, phone_num, email, status, id))
        elif data_type == 'crime_code':
            crime_code = request.form['crime_code']
            code_description = request.form['code_description']
            with mysql.cursor() as cur:
                cur.execute("""
                    UPDATE Crime_Codes
                    SET crime_code = %s, code_description = %s
                    WHERE crime_code = %s
                """, (crime_code, code_description, id))
        elif data_type == 'crime_officer':
            crime_id = request.form['crime_id']
            officer_id = request.form['officer_id']
            with mysql.cursor() as cur:
                cur.execute("""
                    UPDATE Crime_Officers
                    SET crime_id = %s, officer_id = %s
                    WHERE crime_id = %s AND officer_id = %s
                """, (crime_id, officer_id, id, id2))
                print(id2)
        elif data_type == 'crime':
            criminal_id = request.form['criminal_id']
            classification = request.form['classification']
            date_charged = request.form['date_charged']
            status = request.form['status']
            hearing_date = request.form['hearing_date']
            appeal_cutoff_date = request.form['appeal_cutoff_date']
            with mysql.cursor() as cur:
                cur.execute("""
                    UPDATE Crimes
                    SET criminal_id = %s, classification = %s, date_charged = %s, status = %s, hearing_date = %s, appeal_cutoff_date = %s
                    WHERE crime_id = %s
                """, (criminal_id, classification, date_charged, status, hearing_date, appeal_cutoff_date, id))
        elif data_type == "appeal":
            crime_id = request.form['crime_id']
            filing_date = request.form['filing_date']
            hearing_date = request.form['hearing_date']
            status = request.form['status']
            with mysql.cursor() as cur:
                cur.execute("""
                    UPDATE Appeals
                    SET crime_id = %s, filing_date = %s, hearing_date = %s, status = %s
                    WHERE appeal_id = %s
                """, (crime_id, filing_date, hearing_date, status, id))
        else:
            flash(f'Invalid data type: {data_type}', 'danger')
            return redirect(url_for('index'))

        mysql.commit()

        flash(f'{data_type[:-1].capitalize()} information updated successfully!', 'success')
        return redirect(url_for('display', data_type=data_type))

    with mysql.cursor() as cur:
        if data_type == 'criminal':
            cur.execute("SELECT * FROM Criminals WHERE criminal_ID = %s", (id,))
        elif data_type == 'officer':
            cur.execute("SELECT * FROM Officers WHERE officer_ID = %s", (id,))
        elif data_type == 'prob_officer':
            cur.execute("SELECT * FROM Prob_officers WHERE prob_id = %s", (id,))
        elif data_type == 'crime_code':
            cur.execute("SELECT * FROM Crime_Codes WHERE crime_code = %s", (id,))
        elif data_type == 'crime_officer':
            cur.execute("SELECT * FROM Crime_Officers WHERE crime_id = %s AND officer_id = %s", (id, id2))
        elif data_type == 'crime':
            cur.execute("SELECT * FROM Crimes WHERE crime_id = %s", (id,))
        elif data_type == 'appeal':
            cur.execute("SELECT * FROM Appeals WHERE appeal_id = %s", (id,))
        else:
            flash(f'Invalid data type: {data_type}', 'danger')
            return redirect(url_for('index'))
        

        entry = cur.fetchone()

    return render_template('update_entry.html', data_type=data_type, id=id, id2=id2, entry=entry)


@app.route('/all_user')
@login_required
def all_user():
    with mysql.cursor() as cur:
        cur.execute("SELECT * FROM users;")
        result = cur.fetchall()

    return render_template('all_users.html', users=result)


@app.route('/add_user', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    if request.method == 'POST':
        # Retrieve form data
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # Insert new user into the database
        with mysql.cursor() as cur:
            cur.execute('INSERT INTO users (username, password, role) VALUES (%s, %s, %s)', (username, password, role))
            mysql.commit()

        flash('New user added successfully!', 'success')
        return redirect(url_for('all_user'))

    return render_template('add_user.html')

@app.route('/delete_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_user(user_id):
    with mysql.cursor() as cur:
        cur.execute('DELETE FROM users WHERE id = %s', (user_id,))
        mysql.commit()

    flash('User deleted successfully!', 'success')
    return redirect(url_for('all_user'))

@app.route('/update_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def update_user(user_id):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        with mysql.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET username = %s, password = %s, role = %s
                WHERE id = %s
            """, (username, password, role, user_id))
            mysql.commit()

        flash('User information updated successfully!', 'success')
        return redirect(url_for('all_user'))

    with mysql.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()

    if user is None:
        flash('User not found', 'error')
        return redirect(url_for('all_user'))

    return render_template('update_user.html', user=user)





if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port = 8000)

