from flask import Flask, render_template, request, redirect, session, flash, url_for
import mysql.connector
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ✅ MySQL Connection (ENV BASED for Render)
if os.getenv("DB_HOST"):
    # 🔥 Production (Render / Railway)
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
else:
    # 💻 Localhost (XAMPP / MySQL)
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="praveen@2006",
        database="tamil_polyglot"
    )

cursor = db.cursor()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/language')
def language():
    return render_template('language.html')

@app.route('/playlist')
def playlist():
    cursor.execute("SELECT * FROM content")
    data = cursor.fetchall()

    videos = []

    for item in data:
        video = {
            "title": item[1],
            "description": item[2],
            "link": item[3],
            "thumbnail": "/static/uploads/" + item[4] if item[4] else "/static/image/default.jpg"
        }
        videos.append(video)

    return render_template('video.html', videos=videos)

def get_thumbnail(link):
    try:
        video_id = link.split("v=")[-1].split("&")[0]
        return f"https://img.youtube.com/vi/{video_id}/0.jpg"
    except:
        return "https://via.placeholder.com/300"

@app.route('/announcement')
def announcement():
    return render_template('announcement.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/profile')
def profile():
    if not session.get('user'):
        return redirect('/login')

    email = session.get('user')

    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    return render_template('profile.html', user=user)

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if not session.get('user'):
        return redirect('/login')

    email = session.get('user')

    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')

        if password:
            cursor.execute(
                "UPDATE users SET name=%s, password=%s WHERE email=%s",
                (name, password, email)
            )
        else:
            cursor.execute(
                "UPDATE users SET name=%s WHERE email=%s",
                (name, email)
            )

        db.commit()
        return redirect('/profile')

    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    return render_template('edit_profile.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        # USER LOGIN
        if 'email' in request.form and 'password' in request.form and 'name' not in request.form:
            email = request.form['email']
            password = request.form['password']

            cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
            user = cursor.fetchone()

            if user:
                session['user'] = email
                session['is_admin'] = False
                flash("User Login Successful!")
                return redirect('/profile')
            else:
                flash("Invalid Email or Password!")
                return redirect('/login')

        # ADMIN LOGIN
        elif request.form.get('username'):
            username = request.form.get('username')
            password = request.form.get('password')

            cursor.execute("SELECT * FROM admin WHERE username=%s AND password=%s",(username, password))
            admin = cursor.fetchone()

            if admin:
                session['is_admin'] = True
                session['admin'] = username
                flash("Admin Login Successful!")
                return redirect('/')
            else:
                flash("Invalid Admin Credentials!")
                return redirect('/login')

        # REGISTER
        elif 'name' in request.form:
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']

            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            existing = cursor.fetchone()

            if existing:
                flash("Email already exists!")
                return redirect('/login')

            try:
                cursor.execute(
                    "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                    (name, email, password)
                )
                db.commit()

                session['user'] = email
                session['is_admin'] = False

                flash("Account Created Successfully!")
                return redirect('/profile')

            except Exception as e:
                print(e)
                flash("Registration Failed!")
                return redirect('/login')

        flash("Something went wrong!")
        return redirect('/login')

    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect('/login')
    return render_template('dashboard.html')

@app.route('/users')
def user_data():
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return render_template('user_data.html', users=users)

@app.route('/delete_user/<int:id>')
def delete_user(id):
    try:
        cursor.execute("DELETE FROM users WHERE id=%s", (id,))
        db.commit()
    except Exception as e:
        print(e)
    
    return redirect('/users')

@app.route('/message', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        cursor.execute("INSERT INTO contact (name, email, message) VALUES (%s, %s, %s)",(name, email, message))
        db.commit()
        
    return redirect('/contact')

@app.route('/feedback')
def view_feedback():
    cursor.execute("SELECT * FROM contact")
    feedbacks = cursor.fetchall()
    return render_template('feedback.html', feedbacks=feedbacks)

@app.route('/delete_feedback/<int:id>')
def delete_feedback(id):
    try:
        cursor.execute("DELETE FROM contact WHERE id=%s", (id,))
        db.commit()
    except Exception as e:
        print(e)
    
    return redirect('/feedback')

@app.route('/content')
def content():
    return render_template('add_video.html')

@app.route('/add_content', methods=['POST'])
def add_content():
    title = request.form['title']
    description = request.form['description']
    link = request.form['link']

    file = request.files['image']

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        cursor.execute(
            "INSERT INTO content (title, description, link, image) VALUES (%s, %s, %s, %s)",
            (title, description, link, filename)
        )
        db.commit()

    return redirect('/content')

@app.route('/managevideos')
def manage_videos():
    cursor.execute("SELECT * FROM content")
    videos = cursor.fetchall()
    return render_template('manage_videos.html', videos=videos)

@app.route('/delete_video/<int:id>')
def delete_video(id):
    try:
        cursor.execute("DELETE FROM content WHERE id=%s", (id,))
        db.commit()
    except Exception as e:
        print(e)
    
    return redirect('/managevideos')

@app.route('/edit_content/<int:id>', methods=['GET', 'POST'])
def edit_content(id):
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        link = request.form['link']

        file = request.files['image']

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            cursor.execute(
                "UPDATE content SET title=%s, description=%s, link=%s, image=%s WHERE id=%s",
                (title, description, link, filename, id)
            )
        else:
            cursor.execute(
                "UPDATE content SET title=%s, description=%s, link=%s WHERE id=%s",
                (title, description, link, id)
            )

        db.commit()
        return redirect('/managevideos')

    cursor.execute("SELECT * FROM content WHERE id=%s", (id,))
    video = cursor.fetchone()
    return render_template('edit_content.html', video=video)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ✅ IMPORTANT FOR RENDER
if __name__ == '__main__':
    app.run()