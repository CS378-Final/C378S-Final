from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Database connection
DATABASE = 'library.db'

# Function to check user role
def get_user_role(name, user_id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    # Check if user is a student
    cur.execute('SELECT * FROM Students WHERE Name = ? AND Student_ID = ?', (name, user_id))
    if cur.fetchone():
        return 'student'
    # Check if user is faculty
    cur.execute('SELECT * FROM Faculty WHERE Name = ? AND Faculty_ID = ?', (name, user_id))
    if cur.fetchone():
        return 'faculty'
    # Check if user is a librarian
    cur.execute('SELECT * FROM Librarians WHERE Name = ? AND Librarian_ID = ?', (name, user_id))
    if cur.fetchone():
        return 'librarian'
    conn.close()
    return 'unknown'

@app.route('/')
def main_page():
    return render_template('main_page.html')  # You need to create this template

@app.route('/login', methods=['POST'])
def login():
    name = request.form['name']
    user_id = request.form['id']
    print("Login Attempt:", name, user_id)  # Check the terminal for this output after login attempt

    role = get_user_role(name,user_id)
    print("Determined Role:", role)  # This should show what role has been determined

    if role == 'student':
        print("Redirecting to student page.")
        return redirect(url_for('student_page'))
    elif role == 'faculty':
        print("Redirecting to faculty page.")
        return redirect(url_for('faculty_page'))
    elif role == 'librarian':
        print("Redirecting to librarian page.")
        return redirect(url_for('librarian_page'))
    else:
        print("User not found!")
        return render_template('main_page.html', error="User not found!")
    
# View functions for each role
@app.route('/student')
def student_page():
    return render_template('student_page.html')

@app.route('/faculty')
def faculty_page():
    return render_template('faculty_page.html')

@app.route('/librarian')
def librarian_page():
    return render_template('librarian_page.html')

if __name__ == '__main__':
    app.run(debug=True)
