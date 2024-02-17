from flask import Flask, render_template, request, redirect, url_for 
import psycopg2

app = Flask(__name__)

conn = psycopg2.connect(database="flask_db",  
                        user="postgres", 
                        password="password",  
                        host="localhost", port="5432") 
  
cur = conn.cursor() 
  
cur.execute( 
    '''CREATE TABLE IF NOT EXISTS Users (
        id serial PRIMARY KEY,
        name varchar(100),
        usd_balance float,
        point_balance float
        );''') 

cur.execute(
    '''CREATE TABLE IF NOT EXISTS UserFriends (
        uid INT,
        fid INT,
        CONSTRAINT fk_user FOREIGN KEY (uid) REFERENCES Users(id),
        CONSTRAINT fk_friend FOREIGN KEY (fid) REFERENCES Users(id),
        PRIMARY KEY (uid, fid)
        );
    '''
)

conn.commit() 
  
cur.close() 
conn.close() 

@app.route('/') 
def index(): 
    # Connect to the database 
    conn = psycopg2.connect(database="flask_db", 
                            user="postgres", 
                            password="password", 
                            host="localhost", port="5432") 
  
    # create a cursor 
    cur = conn.cursor() 
  
    # Select all products from the table 
    cur.execute('''SELECT * FROM Users''') 
    
    # Fetch the data 
    data = cur.fetchall() 

    # Fetch user friends
    cur.execute('''SELECT u.id, f.fid, uf.name FROM UserFriends f JOIN Users u ON f.uid = u.id JOIN Users uf ON f.fid = uf.id''')
    
    # Fetcg the user friends data
    user_friends = cur.fetchall()
  
    # close the cursor and connection 
    cur.close() 
    conn.close() 
  
    return render_template('index.html', data=data, user_friends=user_friends) 
  
  
@app.route('/create', methods=['POST']) 
def create(): 
    conn = psycopg2.connect(database="flask_db", 
                            user="postgres", 
                            password="password", 
                            host="localhost", port="5432") 
  
    cur = conn.cursor() 
  
    # Get the data from the form 
    name = request.form['name'] 
    usd_balance = request.form['usd_balance'] 
    point_balance = request.form['point_balance']
  
    # Insert the data into the table 
    cur.execute( 
        '''INSERT INTO Users 
        (name, usd_balance, point_balance) VALUES (%s, %s, %s)''', 
        (name, usd_balance, point_balance)) 
  
    # commit the changes 
    conn.commit() 
  
    # close the cursor and connection 
    cur.close() 
    conn.close() 
  
    return redirect(url_for('index')) 

@app.route('/update', methods=['POST']) 
def update(): 
    conn = psycopg2.connect(database="flask_db", 
                            user="postgres", 
                            password="password", 
                            host="localhost", port="5432") 
  
    cur = conn.cursor() 
  
    # Get the data from the form 
    name = request.form['name'] 
    usd_balance = request.form['usd_balance'] 
    point_balance = request.form['point_balance']
    id = request.form['id'] 
  
    # Update the data in the table 
    cur.execute( 
        '''UPDATE Users SET name=%s, 
        usd_balance=%s, point_balance=%s WHERE id=%s''', (name, usd_balance, point_balance, id)) 
  
    # commit the changes 
    conn.commit() 
    return redirect(url_for('index')) 

@app.route('/add_friend', methods=['POST']) 
def add_friend(): 
    conn = psycopg2.connect(database="flask_db", user="postgres", password="password", host="localhost", port="5432") 
    cur = conn.cursor()

    uid = request.form['uid']
    fid = request.form['fid']

    # Insert the friendship data into the table
    cur.execute('''INSERT INTO UserFriends (uid, fid) VALUES (%s, %s)''', (uid, fid))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('index'))

if __name__ == '__main__': 
    app.run(debug=True) 