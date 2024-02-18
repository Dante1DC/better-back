import sys

from flask import Flask, render_template, request, redirect, url_for , jsonify, g
import psycopg2
from flask_cors import CORS, cross_origin

from plaid_app import get_link 

from plaid_app import config

import plaid

from bets import *

from plaid.api import plaid_api

from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode

from plaid.configuration import Configuration
from plaid.api_client import ApiClient

from help import update_user_puid

from odds_db_poplute import *

from flask import jsonify

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(database="flask_db", 
                                user="postgres", 
                                password="password", 
                                host="localhost", port="5432")
    return g.db


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
        point_balance float,
        puid varchar(200)
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
# cur.execute(
#     '''DROP TABLE UserBets;
#     '''
# )
# cur.execute(
#     '''CREATE TABLE IF NOT EXISTS UserBets (
#         uid INT,
#         bid INT,
#         type varchar(100),
#         home_team_odds float,
#         away_team_odds float,
#         CONSTRAINT fk_user FOREIGN KEY (uid) REFERENCES Users(id),
#         CONSTRAINT fk_bet FOREIGN KEY (bid) REFERENCES Users(id),
#         PRIMARY KEY (uid, bid)
#         );
#     '''
# )

conn.commit() 
  
cur.close() 
conn.close() 

create_db()

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
    cur.execute('''INSERT INTO UserFriends (uid, fid) VALUES (%s, %s)''', (fid, uid))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('index'))

api_client = plaid.ApiClient(config)
client = plaid_api.PlaidApi(api_client)

@app.route('/create_link_token', methods=['POST'])
@cross_origin()
def create_link_token():
    # Assume a user ID is sent with the request
    user_id = request.get_json()["user_id"]
    link_token = get_link(user_id)
    return jsonify({'link_token': link_token})


access_token = None
item_id = None

@app.route('/exchange_public_token', methods=['POST'])
def exchange_public_token():
    global access_token
    public_token = request.get_json()['public_token']
    prequest = ItemPublicTokenExchangeRequest(
      public_token=public_token
    )
    response = client.item_public_token_exchange(prequest)

    # These values should be saved to a persistent database and
    # associated with the currently signed-in user
    access_token = response['access_token']


    if response["access_token"]: 
        update_user_puid(request.get_json()["user_id"], access_token)

    return jsonify({'public_token_exchange': 'complete'})

@app.route("/get_balance", methods=["POST"])
@cross_origin()
def get_balance():
    user_id = request.get_json()["user_id"]
    conn = psycopg2.connect(database="flask_db", 
                            user="postgres", 
                            password="password", 
                            host="localhost", port="5432") 
    cur = conn.cursor() 
    try:
        cur.execute('''SELECT * FROM Users WHERE id=%s
                    ''', ([user_id])
                    )
        access_token = cur.fetchall()[0][4]
    except Exception:
        print("shit lmao")

    cur.close()
    conn.close()
    
    
    prequest = AccountsBalanceGetRequest(access_token=access_token)
    response = client.accounts_balance_get(prequest)
    # be weary, oh lone traveler
    # for ye who parse here will not come out the same
    return {"balance" : response['accounts'][0]["balances"]["current"]}
    
@app.route("/get_point_balance", methods=["POST"])
@cross_origin()
def get_point_balance():
    user_id = request.get_json()["user_id"]
    conn = psycopg2.connect(database="flask_db", 
                            user="postgres", 
                            password="password", 
                            host="localhost", port="5432") 
    cur = conn.cursor()
    try: 
        cur.execute('''SELECT * FROM Users WHERE id=%s
                    ''', ([user_id])
                    )
        point_balance = cur.fetchall()[0][3]
    except Exception:
        print("shit lmao")
    
    cur.close()
    conn.close()
    return str(point_balance)




@app.route("/get_sports_db", methods=["GET"])
@cross_origin()
def get_sports_db():

    conn = psycopg2.connect(database="flask_db", 
                            user="postgres", 
                            password="password", 
                            host="localhost", port="5432") 
    cur = conn.cursor()
    try: 
        cur.execute('''SELECT json_agg(Games) FROM Games
                    '''
                    )
        returnable = cur.fetchall()
    except Exception:
        print("shit lmao")
    
    cur.close()
    conn.close()


    return returnable

@app.route("/get_moneylines", methods=["POST"])
@cross_origin()
def get_moneylines():
    return table_to_json("Moneylines")

@app.route("/get_spreads", methods=["POST"])
@cross_origin()
def get_spreads():
    return table_to_json("Spreads")

@app.route("/get_overunders", methods=["POST"])
@cross_origin()
def get_overunders():
    return table_to_json("OverUnders")

# MUST BE POST
@app.route("/get_odds_ml", methods=["POST"])
@cross_origin()
def get_odds_ml():
    GameID = request.get_json()["GameID"]
    conn = get_db() 
    cur = conn.cursor()
    try: 
        cur.execute('''SELECT home_team_odds FROM Moneylines WHERE GameID=%s
                    ''', ([GameID])
                    )
        home_team_odds = cur.fetchall()
    except Exception:
        return [0,0]
    
    try: 
        cur.execute('''SELECT away_team_odds FROM Moneylines WHERE GameID=%s
                    ''', ([GameID])
                    )
        away_team_odds = cur.fetchall()
    except Exception:
        return [0,0]
    
    cur.close()
    return [home_team_odds, away_team_odds]

# MUST BE POST
@app.route("/get_odds_sp", methods=["POST"])
@cross_origin()
def get_odds_sp():
    GameID = request.get_json()["GameID"]
    conn = psycopg2.connect(database="flask_db", 
                            user="postgres", 
                            password="password", 
                            host="localhost", port="5432") 
    cur = conn.cursor()
    try: 
        cur.execute('''SELECT home_team_odds FROM Spreads WHERE GameID=%s
                    ''', ([GameID])
                    )
        home_team_odds = cur.fetchall()
    except Exception:
        return [0,0]
    
    try: 
        cur.execute('''SELECT away_team_odds FROM Spreads WHERE GameID=%s
                    ''', ([GameID])
                    )
        away_team_odds = cur.fetchall()
    except Exception:
        return [0,0]
    
    cur.close()
    conn.close()
    return [home_team_odds, away_team_odds]

# MUST BE POST
@app.route("/get_odds_ou", methods=["POST"])
@cross_origin()
def get_odds_ou():
    GameID = request.get_json()["GameID"]
    conn = psycopg2.connect(database="flask_db", 
                            user="postgres", 
                            password="password", 
                            host="localhost", port="5432") 
    cur = conn.cursor()
    try: 
        cur.execute('''SELECT home_team_odds FROM OverUnders WHERE GameID=%s
                    ''', ([GameID])
                    )
        home_team_odds = cur.fetchall()
    except Exception:
        return [0,0]
    
    try: 
        cur.execute('''SELECT away_team_odds FROM OverUnders WHERE GameID=%s
                    ''', ([GameID])
                    )
        away_team_odds = cur.fetchall()
    except Exception:
        return [0,0]
    
    cur.close()
    conn.close()
    return [home_team_odds, away_team_odds]

# @app.route("/recieve_bet", methods=["POST"])
# @cross_origin()
# def recieve_bet():
#     bet_info = request.get_json()
#     conn = psycopg2.connect(database="flask_db", 
#                             user="postgres", 
#                             password="password", 
#                             host="localhost", port="5432") 
#     cur = conn.cursor()
#     if bet_info["type"] == "Moneyline":
        
#             cur.execute('''INSERT INTO UserBets (uid, bid, home_team_odds, away_team_odds)
#                             VALUES (%s, %s, %s, %s)''',
#                             (bet_info["uid"], bet_info["bid"], bet_info["home_team_odds"], bet_info["away_team_odds"])
#                         )
    
        
#     if bet_info["type"] == "Spread":
#         try: 
#             cur.execute('''INSERT INTO UserBets (uid, bid, home_team_odds, away_team_odds)
#                             VALUES (%s, %s, %s, %s)''',
#                             (bet_info["uid"], bet_info["bid"], bet_info["home_team_odds"], bet_info["away_team_odds"])
#                         )
#         except Exception:
#             return {"confirmed" : "False"}
    
#     if bet_info["type"] == "OverUnder":
#         try: 
#             cur.execute('''INSERT INTO UserBets (uid, bid, home_team_odds, away_team_odds)
#                             VALUES (%s, %s, %s, %s)''',
#                             (bet_info["uid"], bet_info["bid"], bet_info["home_team_odds"], bet_info["away_team_odds"])
#                         )
#         except Exception:
#             return {"confirmed" : "False"}

#     cur.close()
#     conn.close()
#     return {"confirmed" : "True"}

@app.route("/get_friends", methods=["POST"])
@cross_origin()
def get_friends():
    user_id = request.get_json()["user_id"]
    conn = psycopg2.connect(database="flask_db", 
                            user="postgres", 
                            password="password", 
                            host="localhost", port="5432") 
    cur = conn.cursor()
    try: 
        cur.execute('''SELECT * FROM UserFriends WHERE uid=%s
                    ''', ([user_id])
                    )
        friends = cur.fetchall()
    except Exception:
        print("shit lmao")
    
    cur.close()
    conn.close()
    return friends

@app.route("/add_bet", methods=["POST"])
@cross_origin()
def add_bet():
    
    token_amount = request.get_json()['token_amount']
    cleared = False
    competitors = request.get_json()['competitors']

    update_bets(token_amount, competitors, cleared)
    
    
    return {}


@app.route("/get_bets", methods=["GET"])
@cross_origin()
def get_bets():
    conn = psycopg2.connect(database="flask_db", 
                            user="postgres", 
                            password="password", 
                            host="localhost", port="5432") 
    cur = conn.cursor()
    try: 
        cur.execute('''SELECT * FROM bets''')
        rows = cur.fetchall()
        
        # Filter bets where done is false
        undone_bets = []
        for row in rows:
            bet_dict = {
                'betid': row[0],         # betid is at index 0
                'tokens': row[1],        # tokens is at index 1
                'competitors': row[2],   # competitors is at index 2
                'done': row[3]           # done is at index 3
            }
           
            undone_bets.append(bet_dict)
        
    except Exception as e:
        print("Error fetching bets:", e)
        return jsonify({"error": "Failed to fetch bets"}), 500
    
    finally:
        cur.close()
        conn.close()
    return jsonify(undone_bets)


@app.route("/end_bet", methods=["GET"])
@cross_origin()
def end_bet():
    bet_id = 1
    conn = psycopg2.connect(database="flask_db", 
                            user="postgres", 
                            password="password", 
                            host="localhost", port="5432") 
    cur = conn.cursor()
    try: 
        cur.execute('''UPDATE bets SET done = true WHERE betid = %s''', ([bet_id]))
        conn.commit()
    except Exception as e:
        print("Error ending bet:", e)
        return jsonify({"error": "Failed to end bet"}), 500
    
    finally:
        cur.close()
        conn.close()
    
    return jsonify({"success": "Bet ended"})


@app.route("/update_tokens", methods=["POST"])
@cross_origin()
def update_tokens():
    user_id = 1
    new_token_balance = request.get_json()["new_token_balance"]
    conn = psycopg2.connect(database="flask_db", 
                            user="postgres", 
                            password="password", 
                            host="localhost", port="5432") 
    cur = conn.cursor()
    try: 
        cur.execute('''UPDATE Users SET point_balance = %s WHERE id = %s''', (new_token_balance, user_id))
        conn.commit()
    except Exception as e:
        print("Error updating tokens:", e)
        return jsonify({"error": "Failed to update tokens"}), 500
    
    finally:
        cur.close()
        conn.close()
    
    return jsonify({"success": "Tokens updated"})





if __name__ == '__main__': 
    app.run(debug=True) 
