from flask import Flask, render_template, request, redirect, url_for 
import psycopg2
import requests
import json

# drops the tables and creates the the tables for
# games, moneylines, spreads, overunders
def create_tables():

    conn = psycopg2.connect(database="flask_db",  
                        user="postgres", 
                        password="password",  
                        host="localhost", port="5432") 
    cur = conn.cursor() 

    # cur.execute( 
    #     ''' drop table MoneyLines;
    #         drop table Spreads;
    #         drop table OverUnders; 
    #         drop table Games;   
    #         ''') 
    
    cur.execute( 
        '''CREATE TABLE IF NOT EXISTS Games (
            GameID serial PRIMARY KEY,
            sport_title varchar(100),
            home_team varchar(100),
            away_team varchar(100),
            commence_time TIMESTAMP
            );''') 

    cur.execute( 
        '''CREATE TABLE IF NOT EXISTS Moneylines (
            MoneylineID serial PRIMARY KEY,
            GameID int,
            home_team_odds float,
            away_team_odds float,
            CONSTRAINT fk_moneyline FOREIGN KEY (GameID) REFERENCES Games(GameID)
            );''') 

    cur.execute( 
        '''CREATE TABLE IF NOT EXISTS Spreads (
            SpreadID serial PRIMARY KEY,
            GameID int,
            home_team_odds float,
            home_team_spread float,
            away_team_odds float,
            away_team_spread float,
            CONSTRAINT fk_spread FOREIGN KEY (GameID) REFERENCES Games(GameID)
            );''') 

    cur.execute( 
        '''CREATE TABLE IF NOT EXISTS OverUnders (
            OverUnderID serial PRIMARY KEY,
            GameID int,
            over_odds float,
            over_points float,
            under_odds float,
            under_points float,
            CONSTRAINT fk_OverUnder FOREIGN KEY (GameID) REFERENCES Games(GameID)
            );''') 

    conn.commit()
    cur.close() 
    conn.close() 

# pasres from the jason file and inserts the data into the database
def parse_game_info(game):

    conn = psycopg2.connect(database="flask_db",  
                        user="postgres", 
                        password="password",  
                        host="localhost", port="5432") 
    cur = conn.cursor() 

    away_team = game.get("away_team")
    home_team = game.get("home_team")
    commence_time = game.get("commence_time")
    sport_title = game.get("sport_title")

    h2h_market = None
    spreads_market = None
    totals_market = None

    home_team_price = None
    away_team_price = None

    home_team_spread_price = None
    away_team_spread_price = None
    home_team_spread_points = None
    away_team_spread_points = None

    over_price = None
    under_price = None
    over_points = None
    under_points = None
    
    bookmakers = game.get("bookmakers", [])
    if bookmakers:

        bookmaker = bookmakers[0]
        bookmaker_key = bookmaker.get("key")
        bookmaker_title = bookmaker.get("title")
        last_update = bookmaker.get("last_update")

        for market in bookmaker.get("markets", []):
            if market.get("key") == "h2h":
                h2h_market = market
                for outcome in h2h_market.get("outcomes", []):
                    if outcome.get("name") == home_team:
                        home_team_price = outcome.get("price")
                    elif outcome.get("name") == away_team:
                        away_team_price = outcome.get("price")           

            elif market.get("key") == "spreads":
                spreads_market = market
                for outcome in spreads_market.get("outcomes", []):
                    if outcome.get("name") == home_team:
                        home_team_spread_price = outcome.get("price")
                        home_team_spread_points = outcome.get("point")
                    elif outcome.get("name") == away_team:
                        away_team_spread_price = outcome.get("price")
                        away_team_spread_points = outcome.get("point")

            elif market.get("key") == "totals":
                totals_market = market
                for outcome in totals_market.get("outcomes", []):
                    if outcome.get("name") == "Over":
                        over_price = outcome.get("price")
                        over_points = outcome.get("point")
                    elif outcome.get("name") == "Under":
                        under_price = outcome.get("price")
                        under_points = outcome.get("point")

    else:
        bookmaker = None
        bookmaker_key = None
        bookmaker_title = None
        last_update = None

        
    cur.execute( '''INSERT INTO Games (sport_title, home_team, away_team, commence_time)  VALUES (%s, %s, %s, %s) RETURNING GameID;''', (sport_title, home_team, away_team, commence_time))
    conn.commit()  
    GameID = cur.fetchall()[0]
    # print("shit lmao", file=sys.stderr)
    # print(GameID, file=sys.stderr)
    
    if home_team_price:
        cur.execute( '''INSERT INTO Moneylines (GameID, home_team_odds, away_team_odds) VALUES (%s, %s, %s);''', (GameID, home_team_price, away_team_price)) 
    conn.commit() 

    if home_team_spread_price:
        cur.execute( '''INSERT INTO Spreads (GameID, home_team_odds, home_team_spread, away_team_odds, away_team_spread) VALUES (%s, %s, %s, %s, %s );''', (GameID, home_team_spread_price, home_team_spread_points, away_team_spread_price, away_team_spread_points)) 
    
    if over_price:
        cur.execute('''INSERT INTO OverUnders (GameID, over_odds, over_points, under_odds, under_points) VALUES (%s, %s, %s, %s, %s);''', (GameID, over_price, over_points, under_price, under_points)) 
    conn.commit()
    cur.close() 
    conn.close() 

    
    return {
        "away_team": away_team,
        "home_team": home_team,
        "commence_time": commence_time,
        "sport_title": sport_title,
        "bookmaker_key": bookmaker_key,
        "bookmaker_title": bookmaker_title,
        "last_update": last_update,
        "home_team_price": home_team_price,
        "away_team_price": away_team_price,
        "home_team_spread_price": home_team_spread_price,
        "away_team_spread_price": away_team_spread_price,
        "home_team_spread_points": home_team_spread_points,
        "away_team_spread_points": away_team_spread_points,
        "over_price": over_price,
        "under_price": under_price,
        "over_points": over_points,
        "under_points": under_points
    }
        

def create_db():

    odds_api_key = "b61bd7137ca2323be8051033c2798865"
    try:
        r = requests.get("https://api.the-odds-api.com/v4/sports/upcoming/odds/?regions=us&markets=h2h,spreads,totals&bookmakers=draftkings&apiKey=" + odds_api_key)
    except NameError:
        print("API Key didn't work get a new one?")
    create_tables()
    y = json.loads(r.content)
    for x in y:
        parse_game_info(x)

    