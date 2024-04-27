from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta

import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)


# Database connection
DATABASE = 'library.db'

# Function to check user role
def get_user_role(name, user_id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    # Check if user is a student
    cur.execute('SELECT * FROM Users WHERE Name = ? AND User_ID = ?', (name, user_id))
    check = cur.fetchone()
    if check:
        return ['user', check[2]]
    # Check if user is a librarian
    cur.execute('SELECT * FROM Librarians WHERE Name = ? AND Librarian_ID = ?', (name, user_id))
    if cur.fetchone():
        return ['librarian']
    # Check if user is a manager
    cur.execute('SELECT * FROM Managers WHERE Name = ? AND Manager_ID = ?', (name, user_id))
    check = cur.fetchone()
    if check:
        return ['manager']
    conn.close()
    return ['unknown']

@app.route('/')
def main_page():
    return render_template('main_page.html')  # You need to create this template

@app.route('/login', methods=['POST'])
def login():
    name = request.form['name']
    id = request.form['id']
    print("Login Attempt:", name, id)  # Check the terminal for this output after login attempt

    ret = get_user_role(name,id)
    role = ret[0]
    print("Determined Role:", role)  # This should show what role has been determined

    if role == 'user':
        print("Redirecting to user page.")
        session['user_name'] = name
        session['user_id'] = id
        if ret[1] == "Faculty":
            session['user_name'] = "Prof. " + name
        return redirect(url_for('user_page'))
    elif role == 'librarian':
        print("Redirecting to librarian page.")
        session['librarian_name'] = name
        session['librarian_id'] = id
        return redirect(url_for('librarian_page'))
    elif role == 'manager':
        print("Redirecting to manager page.")
        session['manager_name'] = name
        session['manager_id'] = id
        return redirect(url_for('manager_page'))
    else:
        print("User not found!")
        return render_template('main_page.html', error="User not found!")
    
# View functions for each role

@app.route('/user')
def user_page():
    user_name = session.get('user_name', 'Default Name')
    user_id = session.get('user_id', 'Default ID')
    return render_template('user_page.html', name=user_name, id=user_id)

@app.route('/librarian')
def librarian_page():
    librarian_name = session.get('librarian_name', 'Default Name')
    librarian_id = session.get('librarian_id', 'Default ID')
    return render_template('librarian_page.html', name=librarian_name, id=librarian_id)

@app.route('/manager')
def manager_page():
    manager_name = session.get('manager_name', 'Default Name')
    manager_id = session.get('manager_id', 'Default ID')
    return render_template('manager_page.html', name=manager_name, id=manager_id)
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

@app.route('/requests')
def redirect_requests():
    return render_template('requests.html')

@app.route("/user_rep")
def redirect_request():
    return render_template('users_report.html')


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


@app.route('/transactionType', methods=['GET'])
def report_requests():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    choice = request.args.get('output')
    if choice == 'Return' or choice == 'Borrow':
     cur.execute('SELECT * FROM Requests WHERE Transaction_Kind = ?', (choice,))
    else:
     cur.execute('SELECT * FROM Requests')
    results = cur.fetchall()
    conn.close
    return render_template('requests.html', results=results)

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
    user_id = session.get('user_id')
    cur.execute('SELECT * FROM Transactions WHERE User_ID = ?', (user_id,))
    results = cur.fetchall()
    conn.close()
    return render_template('borrowhistory.html', results=results)

@app.route('/borrow', methods=['POST'])
def borrow():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    bookID = request.form.get('BookID')
    user_id = session.get('user_id')
    cur.execute('INSERT INTO Requests (Book_ID, Transaction_Kind, User_ID) VALUES (?,?,?)', (bookID,"Borrow",user_id))
    conn.commit()
    conn.close()
    return render_template('user_page.html')

@app.route('/return', methods=['POST'])
def return_books():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    transaction_id = request.form['transaction_id']
    session_user_id = session.get('user_id') 

    cur.execute('SELECT User_ID FROM Transactions WHERE Transaction_ID = ?', (transaction_id,))
    transaction_user_id = cur.fetchone()[0]

    if session_user_id == transaction_user_id:
        cur.execute('UPDATE Transactions SET Returned_Date = ? WHERE Transaction_ID = ?', (datetime.now(), transaction_id))
        cur.execute('SELECT Book_ID FROM Transactions WHERE Transaction_ID = ?', (transaction_id,))
        book_id = cur.fetchone()[0]
        cur.execute('UPDATE Books SET Availability = "Yes" WHERE BookID = ?', (book_id,))
        conn.commit()

    conn.close()
    return render_template('user_page.html')



@app.route('/register', methods = ['POST'])
def register_users():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    name = request.form.get("name")
    email = request.form.get("email")
    department = request.form.get("department")
    role = request.form.get("role")
    if role == "Student":
        cur.execute("INSERT INTO Users (Name, Role)  VALUES(?,?)", (name, role))
        cur.execute("INSERT INTO Students (Name, Email, Department) VALUES(?,?, ?)", (name, email, department))
    elif role == "Faculty":
        cur.execute("INSERT INTO Users (Name, Role) VALUES(?,?)", (name, role))
        cur.execute("INSERT INTO Faculty (Name, Email, Department) VALUES(?,?, ?)", (name, email, department))
    elif role == "Librarian":
        cur.execute("INSERT INTO Librarians (Name, Email) VALUES(?,?)", (name, email))
    elif role == "Manager":
        cur.execute("INSERT INTO Managers (Name, Email) VALUES(?,?)", (name, email))
    else:
        print("Not a valid role!")
    conn.commit()
    conn.close()
    return render_template('manager_page.html',  error="Invalid Role! Must be Faculty, Librarian, Manager or Student ")



@app.route('/decision', methods = ['POST'])
def approve_requests():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    selected_values = request.form.get('result')
    for row_index, choice in enumerate(selected_values.split(',')):
        if choice == 'deny':
            request_id = request.form.get(f'request_{row_index}')
            user_id = request.form.get(f'user_{row_index}')
            book_id = request .form.get(f'book_{row_index}')
            cur.execute('DELETE FROM Requests WHERE Request_ID = ? AND User_ID = ? AND Book_ID = ?', (request_id, user_id, book_id))


    conn.commit()
    conn.close()
    return render_template('requests.html')
        
    
#To check if register is working 
@app.route('/user_report', methods=['GET'])
def report_users():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    choice = request.args.get('output')
    if choice == 'Faculty':
     cur.execute('SELECT * FROM Users WHERE Role = ?', ('Faculty',))
    elif choice == 'Student':
        cur.execute('SELECT * FROM Users WHERE Role = ?', ('Student',))
    else:
        cur.execute('SELECT * FROM Users' )
    results = cur.fetchall()
    conn.close
    return render_template('users_report.html', results=results)

@app.route('/redirect_previous', methods=['GET'])
def redirect_to_previous():
    user_id = session.get('user_id')
    user_name = session.get('user_name')
    ret = get_user_role(user_name,user_id)
    if ret[0] == 'user':
        return user_page()
    elif ret[0] == 'librarian':
        return librarian_page()
    elif ret[0] == 'manager':
        return manager_page()




if __name__ == '__main__':
    app.run(debug=True)
