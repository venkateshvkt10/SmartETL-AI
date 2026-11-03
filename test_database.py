
from modules.database import test_database_connection

try:
    database = test_database_connection()

    print("SmartETL AI database connection successful!")
    print("Connected Database:", database)

except Exception as error:
    print("Database connection failed:")
    print(error)
