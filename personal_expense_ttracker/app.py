# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from flask import Flask, render_template, request, redirect, session 
from flask_mysqldb import MySQL
import MySQLdb.cursors
import mysql.connector
import re
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from datetime import date


app = Flask(__name__)


app.secret_key = 'a'

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Sonu@2005",
    database="expense_db"
)


#HOME--PAGE
@app.route("/home")
def home():
    return render_template("homepage.html")

@app.route("/")
def add():
    return render_template("home.html")



#SIGN--UP--OR--REGISTER


@app.route("/signup")
def signup():
    return render_template("signup.html")



@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        cursor = db.cursor()
        cursor.execute('SELECT * FROM register WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account:
            msg = 'Account already exists !'

        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'

        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Name must contain only characters and numbers !'

        else:
            cursor.execute("INSERT INTO register (username, password) VALUES (%s, %s)",(username, password))
            db.commit()

            msg = 'You have successfully registered !'
            return render_template('signup.html', msg=msg)

    # ✅ VERY IMPORTANT (handles GET + failed POST)
    return render_template('signup.html', msg=msg)
        
 
        
 #LOGIN--PAGE
    
@app.route("/signin")
def signin():
    return render_template("login.html")
        
@app.route('/login',methods =['GET', 'POST'])
def login():
    global userid
    msg = ''
   
  
    if request.method == 'POST' :
        username = request.form['username']
        password = request.form['password']
        cursor = db.cursor()
        cursor.execute("SELECT * FROM register WHERE username=%s AND password=%s",(username, password))
        account = cursor.fetchone()
        print (account)
        
        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            userid=  account[0]
            session['username'] = account[1]
           
            return redirect('/home')
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)



       

#ADDING----DATA


@app.route("/add")
def adding():
    return render_template('add.html')


@app.route('/addexpense',methods=['GET', 'POST'])
def addexpense():
    
    date = request.form['date']
    expensename = request.form['expensename']
    amount = request.form['amount']
    paymode = request.form['paymode']
    category = request.form['category']
    
    cursor = db.cursor()
    cursor.execute("""INSERT INTO expenses (user_id, date, expensename, amount, paymode, category)VALUES (%s, %s, %s, %s, %s, %s)""", (session['id'], date, expensename, amount, paymode, category))
    db.commit()
    print(date + " " + expensename + " " + amount + " " + paymode + " " + category)
    
    return redirect("/display")



#DISPLAY---graph 

@app.route("/display")
def display():

    cursor = db.cursor()

    # GET MONTH AND YEAR FROM URL

    selected_month = request.args.get('month')
    selected_year = request.args.get('year')

    # IF NOTHING SELECTED -> CURRENT MONTH

    if not selected_month:
        selected_month = datetime.now().month

    if not selected_year:
        selected_year = datetime.now().year

    selected_month = int(selected_month)
    selected_year = int(selected_year)



    # GET EXPENSES OF SELECTED MONTH

    cursor.execute('''
    SELECT * FROM expenses
    WHERE user_id=%s
    AND MONTH(date)=%s
    AND YEAR(date)=%s
    ORDER BY date DESC
    ''', (session['id'], selected_month, selected_year))

    expense = cursor.fetchall()



    # TOTALS

    total = 0

    t_food = 0
    t_entertainment = 0
    t_business = 0
    t_rent = 0
    t_EMI = 0
    t_other = 0


    for x in expense:

        amount = float(x[2])
        category = x[3].lower()

        total += amount

        if category == "food":
            t_food += amount

        elif category == "entertainment":
            t_entertainment += amount

        elif category == "business":
            t_business += amount

        elif category == "rent":
            t_rent += amount

        elif category == "emi":
            t_EMI += amount

        elif category == "other":
            t_other += amount



    # GET LIMIT

    cursor.execute('''
    SELECT limit_amount
    FROM limits
    WHERE user_id=%s
    AND month=%s
    AND year=%s
    ORDER BY id DESC LIMIT 1
    ''', (session['id'], selected_month, selected_year))

    data = cursor.fetchone()

    if data:
        limit_amount = float(data[0])
    else:
        limit_amount = 0



    # WARNING

    if total > limit_amount:
        warning = "⚠️ You exceeded your budget!"
    else:
        warning = "✅ Budget is under control"



    return render_template(

        "display.html",

        expense=expense,

        total=total,

        t_food=t_food,
        t_entertainment=t_entertainment,
        t_business=t_business,
        t_rent=t_rent,
        t_EMI=t_EMI,
        t_other=t_other,

        limit_amount=limit_amount,
        warning=warning,

        selected_month=selected_month,
        selected_year=selected_year
    )




#delete---the--data

@app.route('/delete/<string:id>', methods = ['POST', 'GET' ])
def delete(id):
     cursor = db.cursor()
     cursor.execute('DELETE FROM expenses WHERE  id = {0}'.format(id))
     db.commit()
     print('deleted successfully')    
     return redirect("/display")
 
    
#EDIT---DATA

@app.route('/edit/<id>', methods = ['POST', 'GET' ])
def edit(id):
    cursor = db.cursor()
    cursor.execute('SELECT * FROM expenses WHERE  id = %s', (id,))
    row = cursor.fetchall()
   
    print(row[0])
    return render_template('edit.html', expenses = row[0])


#UPDATE---DATA

@app.route("/update/<int:id>", methods=['GET', 'POST'])
def update(id):
    if request.method == "POST":

        date = request.form.get('date')
        expensename = request.form.get('expensename')
        amount = request.form.get('amount')
        paymode = request.form.get('paymode')
        category = request.form.get('category')

        print("VALUES:", date, expensename, amount, paymode, category, id)

        if not date:
            return "Date missing!"

        amount = request.form.get('amount')

        if not amount or amount.strip() == "":
            return "Amount cannot be empty!"

        try:
            amount = float(amount)
        except:
            return "Amount must be a number!"

        print("Amount value:", amount)
        cursor = db.cursor()

        cursor.execute(
            "UPDATE expenses SET date=%s, expensename=%s, amount=%s, paymode=%s, category=%s WHERE id=%s",
            (date, expensename, amount, paymode, category, id)
        )

        db.commit()
        cursor.close()

        return redirect('/display')  # or your page
     

#HISTORY--DATA

@app.route("/history")
def history():

    cursor = db.cursor()

    cursor.execute('''
    SELECT * FROM expenses
    WHERE user_id=%s
    ORDER BY date DESC
    ''', (session['id'],))

    expense = cursor.fetchall()

    return render_template("history.html", expense=expense)




#LIMIT---DATA

@app.route("/limit", methods=['GET', 'POST'])
def limit():

    cursor = db.cursor()

    current_month = date.today().month
    current_year = date.today().year

    # =========================
    # SAVE LIMIT
    # =========================

    if request.method == "POST":

        limit_amount = request.form['limit']

        # CHECK IF LIMIT EXISTS

        cursor.execute('''
        SELECT * FROM limits
        WHERE user_id=%s
        AND month=%s
        AND year=%s
        ''', (
            session['id'],
            current_month,
            current_year
        ))

        existing = cursor.fetchone()

        # UPDATE LIMIT

        if existing:

            cursor.execute('''
            UPDATE limits
            SET limit_amount=%s
            WHERE user_id=%s
            AND month=%s
            AND year=%s
            ''', (
                limit_amount,
                session['id'],
                current_month,
                current_year
            ))

        # INSERT NEW LIMIT

        else:

            cursor.execute('''
            INSERT INTO limits(user_id, limit_amount, month, year)
            VALUES(%s,%s,%s,%s)
            ''', (
                session['id'],
                limit_amount,
                current_month,
                current_year
            ))

        db.commit()

    # =========================
    # GET CURRENT LIMIT
    # =========================

    cursor.execute('''
    SELECT limit_amount
    FROM limits
    WHERE user_id=%s
    AND month=%s
    AND year=%s
    ORDER BY id DESC
    LIMIT 1
    ''', (
        session['id'],
        current_month,
        current_year
    ))

    data = cursor.fetchone()

    if data:
        limit_amount = float(data[0])
    else:
        limit_amount = 0

    # =========================
    # GET CURRENT MONTH EXPENSES
    # =========================

    cursor.execute('''
    SELECT amount
    FROM expenses
    WHERE user_id=%s
    AND MONTH(date)=%s
    AND YEAR(date)=%s
    ''', (
        session['id'],
        current_month,
        current_year
    ))

    expenses = cursor.fetchall()

    total_expense = 0

    for x in expenses:
        total_expense += float(x[0])

    # =========================
    # REMAINING
    # =========================

    remaining = limit_amount - total_expense

    # =========================
    # STATUS
    # =========================

    if remaining < 0:
        status = "Exceeded Budget"
    else:
        status = "Within Budget"

    # =========================
    # SEND TO HTML
    # =========================

    return render_template(
        "limit.html",
        limit_amount=limit_amount,
        total_expense=total_expense,
        remaining=remaining,
        status=status
    )



#REPORT

@app.route("/today")
def today():
      cursor = db.cursor()
      cursor.execute('''SELECT DATE_FORMAT(date, '%h:%i %p'), amount FROM expenses WHERE user_id = %s AND DATE(date) = CURDATE()''',(session['id'],))      
      texpense = cursor.fetchall()
      print(texpense)
      
      cursor = db.cursor()
      cursor.execute('''SELECT * FROM expenses WHERE user_id = %s AND DATE(date) = CURDATE() ORDER BY date DESC''',(session['id'],))
      expense = cursor.fetchall()
  
      total=0
      t_food=0
      t_entertainment=0
      t_business=0
      t_rent=0
      t_EMI=0
      t_other=0
 
     
      for x in expense:
        amount = x[2]         
        category = x[3].lower() 

        total += amount

        if category == "food":
            t_food += amount

        elif category == "entertainment":
            t_entertainment += amount

        elif category == "business":
            t_business += amount

        elif category == "rent":
            t_rent += amount

        elif category == "emi":
            t_EMI += amount

        elif category == "other":
            t_other += amount
            
      print(total)
        
      print(t_food)
      print(t_entertainment)
      print(t_business)
      print(t_rent)
      print(t_EMI)
      print(t_other)


     
      return render_template("today.html", texpense = texpense, expense = expense,  total = total ,
                           t_food = t_food,t_entertainment =  t_entertainment,
                           t_business = t_business,  t_rent =  t_rent, 
                           t_EMI =  t_EMI,  t_other =  t_other )
     

#MONTH--

@app.route("/month")
def month():
      cursor = db.cursor()
      cursor.execute('''SELECT DATE(date), SUM(amount) FROM expenses WHERE user_id = %s AND MONTH(date) = MONTH(CURDATE()) AND YEAR(date) = YEAR(CURDATE()) GROUP BY DATE(date) ORDER BY DATE(date)''',(session['id'],))
      texpense = cursor.fetchall()
      print(texpense)
      
      cursor = db.cursor()
      cursor.execute('''SELECT * FROM expenses WHERE user_id = %s AND MONTH(date) = MONTH(CURDATE()) AND YEAR(date) = YEAR(CURDATE()) ORDER BY date DESC''',(session['id'],))
      expense = cursor.fetchall()
      
      if expense:
        print("Sample expense row:", expense[0])
      else:
        print("No expense data found")
  
      total=0
      t_food=0
      t_entertainment=0
      t_business=0
      t_rent=0
      t_EMI=0
      t_other=0
 
      for row in expense:
        amount = row[2]
        category = row[3].lower()

        total += amount

        if category == "food":
            t_food += amount

        elif category == "entertainment":
            t_entertainment += amount

        elif category == "business":
            t_business += amount

        elif category == "rent":
            t_rent += amount

        elif category == "emi":
            t_EMI += amount

        elif category == "other":
            t_other += amount
            
      print(total)
        
      print(t_food)
      print(t_entertainment)
      print(t_business)
      print(t_rent)
      print(t_EMI)
      print(t_other)

      for row in texpense:
        date = row[0]
        amount = row[1]
        print(date, amount)


     
      return render_template("month.html", texpense = texpense, expense = expense,  total = total ,
                           t_food = t_food,t_entertainment =  t_entertainment,
                           t_business = t_business,  t_rent =  t_rent, 
                           t_EMI =  t_EMI,  t_other =  t_other )


 #YEAR--        
@app.route("/year")
def year():
      cursor = db.cursor()
      cursor.execute('''SELECT MONTH(date), SUM(amount) FROM expenses WHERE user_id = %s AND YEAR(date) = YEAR(CURDATE()) GROUP BY MONTH(date) ORDER BY MONTH(date)''',(session['id'],))
      texpense = cursor.fetchall()
      print(texpense)
      
      cursor = db.cursor()
      cursor.execute('''SELECT * FROM expenses  WHERE user_id = %s AND YEAR(date) = YEAR(CURDATE()) ORDER BY date DESC''',(session['id'],))
      expense = cursor.fetchall()
  
      total=0
      t_food=0
      t_entertainment=0
      t_business=0
      t_rent=0
      t_EMI=0
      t_other=0
 
     
      for row in expense:
        amount = row[2]
        category = row[3].lower()

        total += amount

        if category == "food":
            t_food += amount

        elif category == "entertainment":
            t_entertainment += amount

        elif category == "business":
            t_business += amount

        elif category == "rent":
            t_rent += amount

        elif category == "emi":
            t_EMI += amount

        elif category == "other":
            t_other += amount
            
      print(total)
        
      print(t_food)
      print(t_entertainment)
      print(t_business)
      print(t_rent)
      print(t_EMI)
      print(t_other)


     
      return render_template("today.html", texpense = texpense, expense = expense,  total = total ,
                           t_food = t_food,t_entertainment =  t_entertainment,
                           t_business = t_business,  t_rent =  t_rent, 
                           t_EMI =  t_EMI,  t_other =  t_other )

#log-out

@app.route('/logout')

def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   return render_template('home.html')

             

if __name__ == "__main__":
    app.run(debug=True)