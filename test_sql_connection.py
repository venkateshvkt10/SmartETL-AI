
import pyodbc

server = "localhost"

connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={server};"
    "DATABASE=master;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

try:
    connection = pyodbc.connect(connection_string)
    cursor = connection.cursor()

    cursor.execute("SELECT @@SERVERNAME, @@VERSION")

    result = cursor.fetchone()

    print("SQL Server connection successful!")
    print("Server Name:", result[0])
    print("Version:", result[1].split("\n")[0])

    cursor.close()
    connection.close()

except Exception as error:
    print("Connection failed:")
    print(error)
