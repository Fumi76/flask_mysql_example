from flask import Flask 
import mysql.connector as mysqldb
import os

app = Flask(__name__) 
 
@app.route('/') 
def hello_world(): 

    conn = mysqldb.connect(user=os.environ['DB_USER']
                        , password=os.environ['DB_PASSWORD'],
                              host=os.environ['DB_HOST'],
                              database=os.environ['DB_DATABASE'])

    cur = conn.cursor(dictionary=True)

    query = ("SELECT * FROM test")

    cur.execute(query)
    rows = cur.fetchall()

    for row in cur:
        print("row={}".format(row))
        
    cur.close()
    conn.close()
    
    return rows, 200

