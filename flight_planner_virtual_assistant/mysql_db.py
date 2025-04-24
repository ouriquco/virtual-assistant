from mysql.connector import connect, Error
import os
class Database:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        try:
            self.connection = connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print("Connection successful")
        except Error as e:
            print(f"Error: {e}")
            return None

    def close(self):
        if self.connection:
            self.connection.close()
            print("Connection closed")
    
    def execute_query(self, query, params=None):
        if self.connection is None:
            print("No connection to the database.")
            return None

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall()
            self.connection.commit()
            return result
        except Error as e:
            print(f"Error: {e}")
            return None
        finally:
            cursor.close()

    def show_table_names_and_variables(self):
        table_directory = "tables"
        if not os.path.exists(table_directory):
            os.makedirs(table_directory)

        if self.connection is None:
            print("No connection to the database.")
            return None

        try:
            cursor = self.connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            for table in tables:
                with open('./tables/tables.txt', 'a') as file:
                    file.write(f"Table: {table[0]}\n")
                    print(f"Table: {table[0]}")
                    cursor.execute(f"DESCRIBE `{table[0]}`")
                    columns = cursor.fetchall()
                    print(columns)

                    for column in columns:
                        file.write(f"  Column: {column[0]}, Type: {column[1]}\n")
                        print(f"  Column: {column[0]}, Type: {column[1]}")
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()




