from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import datetime, timedelta

app = Flask(__name__)

# configure MySQL
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = 'sagnikroy'
# app.config['MYSQL_DB'] = 'myflaskapp2'
# app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

app.config['MYSQL_HOST'] = 'skillup-team-09.cxgok3weok8n.ap-south-1.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'admin'
app.config['MYSQL_PASSWORD'] = 'coscskillup'
app.config['MYSQL_DB'] = 'team9'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# initialize MySQL
mysql = MySQL(app)
# mysql=pymysql.connect( host='skillup-team-09.cxgok3weok8n.ap-south-1.rds.amazonaws.com',
#                             user='admin',
#                             password='coscskillup',
#                             db='team9',
#                             cursorclass=pymysql.cursors.DictCursor )
posts = [
    {
        'author': 'Corey Schafer',
        'title': 'Blog Post 1',
        'content': 'First post content',
        'date_posted': 'April 20, 2018'
    },
    {
        'author': 'Jane Doe',
        'title': 'Blog Post 2',
        'content': 'Second post content',
        'date_posted': 'April 21, 2018'
    }
]

# Home page


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


# Disable dashboard if user is logged in:
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Please login to view dashboard', 'danger')
            return redirect(url_for('login'))
    return wrap


@app.route('/articles')
@is_logged_in
def articles():
    # create cursor
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = "No Articles Found"
        return render_template('articles.html', msg=msg)

    cur.close()


@app.route('/article/<string:id>/')
@is_logged_in
def article(id):
    # create cursor
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    cur.close()

    return render_template('article.html', article=article)


# User registration class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50) ,validators.Email()] )
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='passwords do not match')
    ])
    confirm = PasswordField('confirm password')


# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        actualpass = form.password.data

    # create a cursor to mysqldb
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users(name, email, username, password,actualpass) VALUES (%s, %s, %s, %s, %s)",
                    (name, email, username, password, actualpass))

        # commit changes to db
        mysql.connection.commit()

        # close connection to db
        cur.close()
        flash('Registration completed successfully', 'success')

        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET' and 'logged_in' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # get form data
        username = request.form['username']
        passwordEntered = request.form['password']

        # create mysql cursor
        cur = mysql.connection.cursor()

        # get user by username
        result = cur.execute(
            "SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # get stored hash
            data = cur.fetchone()
            correctPassword = data['password']

            # compare hash with entered hash
            if sha256_crypt.verify(passwordEntered, correctPassword):
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/search', methods=['GET', 'POST'])
@is_logged_in
def search():
    if request.method == 'GET' and 'logged_in' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        searchvalue = "%" + request.form['search'] + "%"

        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM articles WHERE title like %s ", [searchvalue])

        articles = cur.fetchall()

        if result > 0:
            return render_template('viewarticlecopy.html', articles=articles)
        else:
            msg = "No Articles Found"
            return render_template('dashboard.html', msg=msg)





# log out
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('Successfully logged out', 'success')
    return redirect(url_for('login'))


@app.route('/dashboard')
@is_logged_in
def dashboard():
    # create cursor
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = "No Articles Found"
        return render_template('dashboard.html', msg=msg)

    cur.close()


@app.route('/mydashboard')
@is_logged_in
def mydashboard():
    # create cursor
    cur = mysql.connection.cursor()

    result = cur.execute(
        "SELECT * FROM articles where author=%s", [session['username']])
    # result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    articles = cur.fetchall()

    if result > 0:
        return render_template('mydashboard.html', articles=articles)
    else:
        msg = "No Articles Found"
        return render_template('mydashboard.html', msg=msg)

    cur.close()


# Article form class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body')


@app.route("/viewarticle")
def viewarticle():
    return render_template('viewarticle.html', posts=posts)


# @app.route('/viewarticlecopy/<string:id>', methods=['GET','POST'])
# @is_logged_in
# def viewarticlecopy(id):
#
#     cur = mysql.connection.cursor()
# 	result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
# 	articles = cur.fetchone()

@app.route('/viewarticlecopy/<string:id>', methods=['GET', 'POST'])
def viewarticlecopy(id):
    # create cursor
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    articles = cur.fetchall()

    if result > 0:
        return render_template('viewarticlecopy.html', articles=articles)


# Add article


@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # create cursor to mysql
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO articles(title, body,create_date,author) VALUES(%s, %s,%s,%s)", (title, body,
                                                                                                  datetime.now().replace(microsecond=0, second=0, minute=0) - timedelta(hours=1), session['username']))

        # commit to DB
        mysql.connection.commit()
        cur.close()
        flash('Article Created!', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


# Edit article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # create cursor
    cur = mysql.connection.cursor()

    # search article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    # get form
    form = ArticleForm(request.form)

    # populate form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # create cursor to mysql
        cur = mysql.connection.cursor()

        cur.execute(
            "UPDATE articles SET title=%s, body=%s WHERE id=%s", (title, body, id))

        # commit to DB
        mysql.connection.commit()
        cur.close()
        flash('Article Updated!', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM articles WHERE id=%s", [id])

    # commit to DB
    mysql.connection.commit()
    cur.close()
    flash('Article Deleted!', 'success')

    return redirect(url_for('dashboard'))

@app.route('/block_article', methods=['POST'])
@is_logged_in
def block_article():
    flash('User Blocked', 'success')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)
