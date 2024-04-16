from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta

import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)


# Database connection
DATABASE = '378 Final Project/library.db'

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
        session['student_name'] = name
        return redirect(url_for('student_page'))
    elif role == 'faculty':
        print("Redirecting to faculty page.")
        session['faculty_name'] = name
        return redirect(url_for('faculty_page'))
    elif role == 'librarian':
        print("Redirecting to librarian page.")
        session['librarian_name'] = name
        return redirect(url_for('librarian_page'))
    else:
        print("User not found!")
        return render_template('main_page.html', error="User not found!")
    
# View functions for each role
@app.route('/student')
def student_page():
    student_name = session.get('student_name', 'Default Name')
    return render_template('student_page.html', name=student_name)

@app.route('/faculty')
def faculty_page():
    faculty_name = session.get('faculty_name', 'Default Name')
    return render_template('faculty_page.html', name=faculty_name)

@app.route('/librarian')
def librarian_page():
    librarian_name = session.get('librarian_name', 'Default Name')
    return render_template('librarian_page.html', name=librarian_name)

@app.route('/add_book', methods=['POST'])
def add_book():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    title = request.form['title']
    author = request.form['author']
    category = request.form['category']
    isbn = request.form['isbn']
    year = request.form['year']

    # Adding a book
    cur.execute('INSERT INTO Books (Title, Authors, ISBN, PublicationYear, Category, Availability) VALUES  (?, ?, ?, ?, ?, ?)', (title, author, isbn, year, category, 'Yes'))
    conn.commit()
    return redirect(url_for('librarian_page'))


@app.route('/search_books', methods = ['GET'])
def search():
    query = request.args.get("query")
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('SELECT * FROM Books WHERE Title LIKE ? OR Authors LIKE ? OR Category LIKE ? ', (f"%{query}%", f"%{query}%", f"%{query}%"))
    results = cur.fetchall()
    conn.close
    return render_template('search_results.html', results=results)


#Routes to the different pages
@app.route('/update_book')
def redirect_update():
    return render_template('update.html')

@app.route('/book_availability')
def redirect_availability():
    return render_template('availability.html')

@app.route('/overdue_books')
def redirect_overdue():
    return render_template('overdue.html')

@app.route('/borrowing_trends')
def redirect_borrowTrends():
    return render_template('borrowTrends.html')

@app.route('/sign_out')
def sign_out():
    return render_template('main_page.html')

@app.route('/borrowing_history')
def redirect_borrowHistory():
    return render_template('borrowhistory.html')

@app.route('/borrow_book')
def redirect_borrow_book():
    return render_template('borrow.html')

@app.route('/return_book')
def redirect_return_book():
    return render_template('return.html')


@app.route('/availabilityType', methods=['GET'])
def report_book_availability():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    choice = request.args.get('output')
    if choice == 'Yes' or choice == 'No':
     cur.execute('SELECT * FROM Books WHERE Availability = ?', (choice,))
    else:
     cur.execute('SELECT * FROM Books')
    results = cur.fetchall()
    conn.close
    return render_template('availability.html', results=results)

@app.route('/borrowTrends', methods = ['GET'])
def report_book_trend():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('SELECT Book_ID,Title, COUNT(Book_ID) AS Count FROM Transactions INNER JOIN Books ON Books.BookID = Transactions.Book_ID  GROUP BY Book_ID  ORDER BY Count DESC LIMIT 10')
    results = cur.fetchall()
    return render_template('borrowTrends.html', results = results)

@app.route('/overdue', methods = ['GET'])
def report_overdue():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    today = datetime.now()
    cur.execute('SELECT * FROM Transactions WHERE Returned_Date IS NULL AND Borrowed_Date < ?', (today - timedelta(days=30),)) 
    results = cur.fetchall()
    return render_template('overdue.html', results=results)

@app.route('/update_book', methods = ['POST'])
def update_book():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    bookid = request.form.get('BookID')
    fields = {}
    for field in ('Title', 'Authors', 'Category', 'ISBN', 'PublicationYear', 'Availability'):
        value = request.form.get(field)
        if value != "":
            fields[field] = value

    command = 'UPDATE Books SET '
    update_fields = []
    update_values = []
    for field, value in fields.items():
        update_fields.append(f'{field} = ?')
        update_values.append(value)
    command += ', '.join(update_fields) + ' WHERE BookID = ?'
    update_values.append(bookid)

    cur.execute(command, update_values)
    conn.commit()
    conn.close()
    return render_template('update.html')

@app.route('/borrowHistory', methods = ['GET'])
def borrow_History():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    id = request.args.get('ID')
    cur.execute('SELECT * FROM Transactions WHERE Student_Faculty_ID = ?', id)
    results = cur.fetchall()
    conn.close()
    return render_template('borrowhistory.html', results=results)

@app.route('/borrow', methods=['POST'])
def borrow():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    bookID = request.form.get('BookID')
    id = request.form.get("ID")
    librarian_id = request.form.get("Librarian_ID")
    cur.execute('INSERT INTO Transactions (Book_ID, Student_Faculty_ID, Librarian_ID, Borrowed_Date, Returned_Date) VALUES (?,?,?,?,?)', (bookID,id,librarian_id, datetime.now(), ""))
    cur.execute('UPDATE Books SET Availability = "No" WHERE BookID = ?', (bookID))
    conn.commit()
    conn.close()
    return render_template('borrow.html')

@app.route('/return', methods = ['POST'])
def return_books():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    try:
        transaction_id = request.form.get('Transaction_ID')
        cur.execute('UPDATE Transactions SET Returned_Date = ? WHERE Transaction_ID = ?', (datetime.now(), transaction_id))
        cur.execute('SELECT Book_ID From Transactions WHERE Transaction_ID = ?', (transaction_id))
        if book_id:
            book_id = cur.fetchone()[0]
            cur.execute('UPDATE Books SET Availability = "Yes" WHERE BookID = ?', (book_id))
            conn.commit()
            return render_template('return.html')
        else:
            return "Transaction not found"
    except Exception as e:
        return str(e)
    finally:
        conn.close()
        
    






if __name__ == '__main__':
    app.run(debug=True)
