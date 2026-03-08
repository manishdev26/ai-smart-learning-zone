from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
import hashlib
from datetime import datetime
from functools import wraps

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'smartlearn_secret_key_2024'

# On Vercel, use /tmp (the only writable directory in serverless env).
# Locally it falls back to backend/database.db for development.
if os.environ.get('VERCEL'):
    DB_PATH = '/tmp/database.db'
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), 'backend', 'database.db')

# ─────────────────────────────────────────────
# Database Helpers
# ─────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        education TEXT DEFAULT 'Undergraduate',
        interests TEXT DEFAULT '',
        skill_level TEXT DEFAULT 'Beginner',
        is_admin INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT,
        difficulty TEXT DEFAULT 'Beginner',
        video_link TEXT,
        article_link TEXT,
        pdf_link TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS quiz_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL,
        question TEXT NOT NULL,
        option_a TEXT,
        option_b TEXT,
        option_c TEXT,
        option_d TEXT,
        correct_option TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS quiz_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        score INTEGER,
        total INTEGER,
        taken_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS user_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        course_id INTEGER,
        completed INTEGER DEFAULT 0,
        enrolled_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(course_id) REFERENCES courses(id)
    )''')

    # Seed Admin
    admin_pw = hash_password('admin123')
    c.execute("INSERT OR IGNORE INTO users (name, email, password, is_admin) VALUES (?, ?, ?, 1)",
              ('Admin', 'admin@smartlearn.com', admin_pw))

    # Seed Courses
    sample_courses = [
        ('Python for Beginners', 'Learn Python programming from scratch with hands-on examples.',
         'Python', 'Beginner',
         'https://www.youtube.com/watch?v=_uQrJ0TkZlc',
         'https://docs.python.org/3/tutorial/', ''),
        ('Programming Basics', 'Understand core programming concepts, algorithms and logic.',
         'Programming', 'Beginner',
         'https://www.youtube.com/watch?v=zOjov-2OZ0E',
         'https://www.geeksforgeeks.org/fundamentals-of-algorithms/', ''),
        ('Web Development Fundamentals', 'HTML, CSS and JavaScript essentials for web developers.',
         'Web', 'Beginner',
         'https://www.youtube.com/watch?v=mU6anWqZJcc',
         'https://www.w3schools.com/', ''),
        ('Machine Learning Basics', 'Introduction to ML concepts, supervised and unsupervised learning.',
         'AI', 'Intermediate',
         'https://www.youtube.com/watch?v=Gv9_4yMHFhI',
         'https://scikit-learn.org/stable/getting_started.html', ''),
        ('Data Science Introduction', 'Data analysis, visualization and statistics fundamentals.',
         'AI', 'Intermediate',
         'https://www.youtube.com/watch?v=ua-CiDNNj30',
         'https://www.kaggle.com/learn', ''),
        ('Advanced Python', 'OOP, decorators, generators and advanced Python patterns.',
         'Python', 'Advanced',
         'https://www.youtube.com/watch?v=Ej_02ICOIgs',
         'https://realpython.com/', ''),
        ('Deep Learning Fundamentals', 'Neural networks, backpropagation and deep learning basics.',
         'AI', 'Advanced',
         'https://www.youtube.com/watch?v=aircAruvnKk',
         'https://www.deeplearning.ai/', ''),
        ('SQL & Databases', 'Learn SQL queries, database design and normalization.',
         'Database', 'Beginner',
         'https://www.youtube.com/watch?v=HXV3zeQKqGY',
         'https://www.w3schools.com/sql/', ''),
        ('Data Structures & Algorithms', 'Arrays, linked lists, trees, graphs and sorting algorithms.',
         'Programming', 'Intermediate',
         'https://www.youtube.com/watch?v=8hly31xKli0',
         'https://www.geeksforgeeks.org/data-structures/', ''),
        ('JavaScript Modern', 'ES6+, async/await, fetch API and modern JS patterns.',
         'Web', 'Intermediate',
         'https://www.youtube.com/watch?v=W6NZfCO5SIk',
         'https://javascript.info/', ''),
        ('Mathematics for AI', 'Linear algebra, calculus and probability for machine learning.',
         'Math', 'Intermediate',
         'https://www.youtube.com/watch?v=1VSZtNYMntM',
         'https://www.khanacademy.org/math', ''),
        ('Flask Web Development', 'Build web applications using Python and Flask framework.',
         'Python', 'Intermediate',
         'https://www.youtube.com/watch?v=Z1RJmh_OqeA',
         'https://flask.palletsprojects.com/', ''),
    ]
    c.executemany('''INSERT OR IGNORE INTO courses (title, description, category, difficulty, video_link, article_link, pdf_link)
                    VALUES (?,?,?,?,?,?,?)''', sample_courses)

    # Seed Quiz Questions
    questions = [
        # Python
        ('Python', 'What is the correct way to create a variable in Python?', 'var x = 5', 'x = 5', 'int x = 5', 'create x = 5', 'B'),
        ('Python', 'Which keyword is used to define a function in Python?', 'function', 'def', 'fun', 'define', 'B'),
        ('Python', 'What does the len() function do?', 'Deletes items', 'Returns length of an object', 'Sorts a list', 'Counts numbers', 'B'),
        ('Python', 'Which of these is a valid Python list?', '{1, 2, 3}', '(1, 2, 3)', '[1, 2, 3]', '<1, 2, 3>', 'C'),
        ('Python', 'What symbol is used for comments in Python?', '//', '#', '/*', '--', 'B'),
        # Logic
        ('Logic', 'If A=2 and B=3, what is A+B*2?', '10', '8', '7', '12', 'B'),
        ('Logic', 'What is the output of: print(10 % 3)?', '3', '1', '0', '2', 'B'),
        ('Logic', 'Which of these is a loop statement?', 'if', 'for', 'def', 'return', 'B'),
        ('Logic', 'What does AND operator return?', 'True if any is True', 'True if all are True', 'Always True', 'Always False', 'B'),
        ('Logic', 'What is recursion?', 'A loop', 'A function calling itself', 'A variable type', 'A class method', 'B'),
        # Math
        ('Math', 'What is the square root of 144?', '11', '12', '13', '14', 'B'),
        ('Math', 'What is 2^8?', '128', '512', '256', '64', 'C'),
        ('Math', 'What is 15% of 200?', '25', '30', '35', '20', 'B'),
        ('Math', 'If x + 5 = 12, what is x?', '5', '6', '7', '8', 'C'),
        ('Math', 'What is the value of pi (approximately)?', '3.14', '2.71', '1.41', '1.73', 'A'),
    ]
    c.executemany('''INSERT OR IGNORE INTO quiz_questions
                    (topic, question, option_a, option_b, option_c, option_d, correct_option)
                    VALUES (?,?,?,?,?,?,?)''', questions)

    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
# Auth Decorators
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        conn = get_db()
        user = conn.execute('SELECT is_admin FROM users WHERE id=?', (session['user_id'],)).fetchone()
        conn.close()
        if not user or not user['is_admin']:
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

# ─────────────────────────────────────────────
# Recommendation Engine
# ─────────────────────────────────────────────

def get_recommendations(interests, skill_level, quiz_score=None, total=None):
    conn = get_db()
    interests_list = [i.strip().lower() for i in (interests or '').split(',') if i.strip()]

    # Determine effective skill level
    effective_skill = skill_level or 'Beginner'
    if quiz_score is not None and total and total > 0:
        pct = (quiz_score / total) * 100
        if pct >= 80:
            effective_skill = 'Advanced'
        elif pct >= 50:
            effective_skill = 'Intermediate'
        else:
            effective_skill = 'Beginner'

    # Map interests to categories
    category_map = {
        'python': 'Python',
        'ai': 'AI',
        'machine learning': 'AI',
        'ml': 'AI',
        'web': 'Web',
        'web development': 'Web',
        'data science': 'AI',
        'math': 'Math',
        'mathematics': 'Math',
        'programming': 'Programming',
        'database': 'Database',
        'sql': 'Database',
        'javascript': 'Web',
        'js': 'Web',
    }

    matched_categories = set()
    for interest in interests_list:
        for key, cat in category_map.items():
            if key in interest or interest in key:
                matched_categories.add(cat)

    if not matched_categories:
        matched_categories = {'Python', 'Programming'}

    # Skill level priority ordering
    skill_priority = {'Beginner': 0, 'Intermediate': 1, 'Advanced': 2}
    effective_num = skill_priority.get(effective_skill, 0)

    courses = conn.execute('SELECT * FROM courses').fetchall()
    conn.close()

    scored = []
    for c in courses:
        score = 0
        if c['category'] in matched_categories:
            score += 10
        diff_num = skill_priority.get(c['difficulty'], 0)
        score -= abs(diff_num - effective_num) * 3
        scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:6]]

# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.route('/')
def index():
    conn = get_db()
    courses = conn.execute('SELECT * FROM courses LIMIT 6').fetchall()
    conn.close()
    return render_template('index.html', courses=courses)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        education = request.form.get('education', 'Undergraduate')
        interests = request.form.get('interests', '')
        skill_level = request.form.get('skill_level', 'Beginner')

        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('signup'))

        conn = get_db()
        existing = conn.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone()
        if existing:
            conn.close()
            flash('Email already registered. Please login.', 'warning')
            return redirect(url_for('login'))

        conn.execute('''INSERT INTO users (name, email, password, education, interests, skill_level)
                        VALUES (?,?,?,?,?,?)''',
                     (name, email, hash_password(password), education, interests, skill_level))
        conn.commit()
        conn.close()
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email=? AND password=?',
                            (email, hash_password(password))).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['is_admin'] = bool(user['is_admin'])
            # Store full profile in session so dashboard works across Vercel serverless instances
            session['user_email'] = user['email']
            session['user_education'] = user['education']
            session['user_interests'] = user['interests']
            session['user_skill_level'] = user['skill_level']
            flash(f'Welcome back, {user["name"]}!', 'success')
            if user['is_admin']:
                return redirect(url_for('admin_panel'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()

    # Vercel serverless: if DB instance doesn't have this user (cross-instance),
    # fall back to session-stored profile data so dashboard never crashes.
    if user is None:
        user = {
            'id': session.get('user_id'),
            'name': session.get('user_name', 'User'),
            'email': session.get('user_email', ''),
            'education': session.get('user_education', 'Undergraduate'),
            'interests': session.get('user_interests', ''),
            'skill_level': session.get('user_skill_level', 'Beginner'),
            'is_admin': session.get('is_admin', False),
        }

    quiz_result = conn.execute('SELECT * FROM quiz_results WHERE user_id=? ORDER BY taken_at DESC LIMIT 1',
                               (session['user_id'],)).fetchone()
    progress = conn.execute('''SELECT up.*, c.title FROM user_progress up
                               JOIN courses c ON up.course_id=c.id
                               WHERE up.user_id=?''', (session['user_id'],)).fetchall()
    total_enrolled = len(progress)
    completed = sum(1 for p in progress if p['completed'])
    progress_pct = int((completed / total_enrolled * 100)) if total_enrolled > 0 else 0

    score = quiz_result['score'] if quiz_result else None
    total_q = quiz_result['total'] if quiz_result else None
    interests = user['interests'] if isinstance(user, dict) else user['interests']
    skill_level = user['skill_level'] if isinstance(user, dict) else user['skill_level']
    recommendations = get_recommendations(interests, skill_level, score, total_q)
    conn.close()
    return render_template('dashboard.html', user=user, quiz_result=quiz_result,
                           recommendations=recommendations, progress=progress,
                           total_enrolled=total_enrolled, completed=completed,
                           progress_pct=progress_pct)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = get_db()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        education = request.form.get('education', 'Undergraduate')
        interests = request.form.get('interests', '')
        skill_level = request.form.get('skill_level', 'Beginner')
        conn.execute('UPDATE users SET name=?, education=?, interests=?, skill_level=? WHERE id=?',
                     (name, education, interests, skill_level, session['user_id']))
        conn.commit()
        session['user_name'] = name
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    user = conn.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    # Vercel serverless fallback: use session data if DB user not found on this instance
    if user is None:
        user = {
            'id': session.get('user_id'),
            'name': session.get('user_name', 'User'),
            'email': session.get('user_email', ''),
            'education': session.get('user_education', 'Undergraduate'),
            'interests': session.get('user_interests', ''),
            'skill_level': session.get('user_skill_level', 'Beginner'),
            'is_admin': session.get('is_admin', False),
        }
    conn.close()
    return render_template('profile.html', user=user)

@app.route('/quiz', methods=['GET', 'POST'])
@login_required
def quiz():
    conn = get_db()
    if request.method == 'POST':
        questions = conn.execute('SELECT * FROM quiz_questions').fetchall()
        score = 0
        for q in questions:
            ans = request.form.get(f'q{q["id"]}', '')
            if ans.upper() == q['correct_option'].upper():
                score += 1
        total = len(questions)
        conn.execute('INSERT INTO quiz_results (user_id, score, total) VALUES (?,?,?)',
                     (session['user_id'], score, total))
        conn.commit()
        conn.close()
        flash(f'Quiz completed! You scored {score}/{total}.', 'success')
        return redirect(url_for('dashboard'))

    questions = conn.execute('SELECT * FROM quiz_questions').fetchall()
    conn.close()
    return render_template('quiz.html', questions=questions)

@app.route('/courses')
def courses():
    category = request.args.get('category', '')
    difficulty = request.args.get('difficulty', '')
    conn = get_db()
    query = 'SELECT * FROM courses WHERE 1=1'
    params = []
    if category:
        query += ' AND category=?'
        params.append(category)
    if difficulty:
        query += ' AND difficulty=?'
        params.append(difficulty)
    courses_list = conn.execute(query, params).fetchall()
    categories = conn.execute('SELECT DISTINCT category FROM courses').fetchall()
    conn.close()
    return render_template('courses.html', courses=courses_list, categories=categories,
                           selected_cat=category, selected_diff=difficulty)

@app.route('/courses/<int:course_id>')
def course_detail(course_id):
    conn = get_db()
    course = conn.execute('SELECT * FROM courses WHERE id=?', (course_id,)).fetchone()
    enrolled = False
    if 'user_id' in session:
        p = conn.execute('SELECT * FROM user_progress WHERE user_id=? AND course_id=?',
                         (session['user_id'], course_id)).fetchone()
        enrolled = p is not None
    conn.close()
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('courses'))
    return render_template('course_detail.html', course=course, enrolled=enrolled)

@app.route('/enroll/<int:course_id>')
@login_required
def enroll(course_id):
    conn = get_db()
    existing = conn.execute('SELECT * FROM user_progress WHERE user_id=? AND course_id=?',
                            (session['user_id'], course_id)).fetchone()
    if not existing:
        conn.execute('INSERT INTO user_progress (user_id, course_id) VALUES (?,?)',
                     (session['user_id'], course_id))
        conn.commit()
        flash('Enrolled successfully!', 'success')
    else:
        flash('Already enrolled in this course.', 'info')
    conn.close()
    return redirect(url_for('course_detail', course_id=course_id))

@app.route('/complete/<int:course_id>')
@login_required
def complete_course(course_id):
    conn = get_db()
    conn.execute('UPDATE user_progress SET completed=1 WHERE user_id=? AND course_id=?',
                 (session['user_id'], course_id))
    conn.commit()
    conn.close()
    flash('Course marked as completed! Great job!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/resources')
def resources():
    conn = get_db()
    courses_list = conn.execute('SELECT * FROM courses').fetchall()
    conn.close()
    return render_template('resources.html', courses=courses_list)

# ─────────────────────────────────────────────
# Admin Routes
# ─────────────────────────────────────────────

@app.route('/admin')
@admin_required
def admin_panel():
    conn = get_db()
    users = conn.execute('SELECT * FROM users WHERE is_admin=0').fetchall()
    courses = conn.execute('SELECT * FROM courses').fetchall()
    conn.close()
    return render_template('admin/panel.html', users=users, courses=courses)

@app.route('/admin/add_course', methods=['GET', 'POST'])
@admin_required
def admin_add_course():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        difficulty = request.form['difficulty']
        video_link = request.form.get('video_link', '')
        article_link = request.form.get('article_link', '')
        pdf_link = request.form.get('pdf_link', '')
        conn = get_db()
        conn.execute('''INSERT INTO courses (title, description, category, difficulty, video_link, article_link, pdf_link)
                        VALUES (?,?,?,?,?,?,?)''',
                     (title, description, category, difficulty, video_link, article_link, pdf_link))
        conn.commit()
        conn.close()
        flash('Course added successfully!', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('admin/add_course.html')

@app.route('/admin/edit_course/<int:course_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_course(course_id):
    conn = get_db()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        difficulty = request.form['difficulty']
        video_link = request.form.get('video_link', '')
        article_link = request.form.get('article_link', '')
        conn.execute('''UPDATE courses SET title=?, description=?, category=?, difficulty=?,
                        video_link=?, article_link=? WHERE id=?''',
                     (title, description, category, difficulty, video_link, article_link, course_id))
        conn.commit()
        conn.close()
        flash('Course updated!', 'success')
        return redirect(url_for('admin_panel'))
    course = conn.execute('SELECT * FROM courses WHERE id=?', (course_id,)).fetchone()
    conn.close()
    return render_template('admin/add_course.html', course=course)

@app.route('/admin/delete_course/<int:course_id>', methods=['POST'])
@admin_required
def admin_delete_course(course_id):
    conn = get_db()
    conn.execute('DELETE FROM courses WHERE id=?', (course_id,))
    conn.commit()
    conn.close()
    flash('Course deleted.', 'warning')
    return redirect(url_for('admin_panel'))

# Initialize DB at module level so Vercel serverless cold starts work correctly.
# init_db() is safe to call multiple times (uses CREATE TABLE IF NOT EXISTS).
init_db()

if __name__ == '__main__':
    app.run(debug=True)
