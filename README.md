# Better Bets Backend Implementation
The following is an explanation of the technical architecture of the backend of the Better Bets application. For a comprehensive explanation of the whole project, see # Project Manifest in the Frontend's GitHub.

## Architecture
### Flask
Flask is a Python framework package for building web applications. This framework supports and builds our backend, allowing rapid development with it's feature-filled debug mode.

## Dependencies
### sys
sys was a testing package used to write console error messages and assist future developers building upon this application.
### flask
We used render_template, request, redirect, url_for, and jsonify for in order to relate to various frontend endpoints and relay reported information in .json format. 
### psycopg2
This is a PostgreSQL database adapter designed for Python. Because we built this application off PostgreSQL, we needed a useable and agile package that maintains thread safety and complex applications. This particular package is super applicable for our use case because of client-side and server-side cursor capabilities and easy PostgreSQL data type matching in Python.
### cross_origin
This is a library used for allowing cross-origin connections. We used this to connect between ports, which was necessary in testing as PostgreSQL was on :5432, the frontend was on :3000, and the backend was on :5000. This layered approach was integral for development and security concerns, but required a specific library for cross-communication.
### Plaid
We used a large amount of utilities from the Plaid API, which is a financial and banking API for tracking different balances and transactions. This was integral for our use case.

# Paradigm
The primary design principles that guided our backend's development was security, useability, and access. We took a highly-layered approach with our web application stack for this reason: to try and divide our principles as much as possible. We built our database for scaleability, so future developers already have existing table and database structures pre-defined for them to use on our application. 
## Database
We used a relational database with the following tables: Users, UserFriends, UserBets, Games, and three types of bet tables. Building it this way allowed for easy access to the relationships between the User, their current bets, and the games that those bets pertain to, all in one. 
