from flask import Flask, render_template, request, redirect, url_for 
import psycopg2
import requests

def make_bets_t():

    conn = psycopg2.connect(database="flask_db",  
                            user="postgres", 
                            password="password",  
                            host="localhost", port="5432") 
    cur = conn.cursor() 

    cur.execute( 
        '''CREATE TABLE IF NOT EXISTS Bets (
            BetID serial PRIMARY KEY,
            tokens int,
            comptetors varchar(100),
            done BOOLEAN    
            );''') 
    conn.commit()  
    
    cur.close()
    conn.close()
    
def update_bets(took, comp , done):
    conn = psycopg2.connect(database="flask_db",  
                            user="postgres", 
                            password="password",  
                            host="localhost", port="5432") 
    cur = conn.cursor() 

    cur.execute( '''INSERT INTO Bets (tokens, comptetors, done)  VALUES (%s, %s, %s)''', (took, comp, done))
    conn.commit()  

    cur.close()
    conn.close()