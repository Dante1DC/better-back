from flask import Flask, render_template, request, redirect, url_for 
import psycopg2

app = Flask(__name__)

conn = psycopg2.connect(database="flask_db",  
                        user="postgres", 
                        password="root",  
                        host="localhost", port="5432") 
  
cur = conn.cursor() 
  


conn.commit() 
  
cur.close() 
conn.close() 