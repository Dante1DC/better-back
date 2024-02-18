import psycopg2

def update_user_puid(user_id, puid):
    # Create a connection to the database
    try:
        conn = psycopg2.connect(database="flask_db",  
                        user="postgres", 
                        password="password",  
                        host="localhost", port="5432") 

        # Create a cursor object
        cur = conn.cursor()

        # SQL update statement
        sql = """
        UPDATE Users
        SET puid = %s
        WHERE id = %s;
        """

        # Execute the update statement
        cur.execute(sql, (puid, user_id))

        # Commit the changes to the database
        conn.commit()

        # Close communication with the database
        cur.close()
        print("puid updated successfully")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
    finally:
        if conn is not None:
            conn.close()
