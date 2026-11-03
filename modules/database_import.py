"""Read-only imports from supported relational databases."""

import pandas as pd
from sqlalchemy import MetaData, Table, create_engine, inspect, select, text
from sqlalchemy.engine import URL


def create_database_engine(
    database_type,
    host=None,
    port=None,
    database=None,
    username=None,
    password=None,
    windows_auth=False,
    driver="ODBC Driver 18 for SQL Server",
    sqlite_path=None,
):
    """Create a SQLAlchemy engine for the selected database."""
    db_type = database_type.lower()

    if db_type == "sqlite":
        if not sqlite_path:
            raise ValueError("Enter the path to your SQLite database file.")
        return create_engine(URL.create("sqlite", database=sqlite_path))

    if not host or not database:
        raise ValueError("Host and database name are required.")

    if db_type == "sql server":
        if windows_auth:
            connection_string = (
                f"DRIVER={{{driver}}};SERVER={host};DATABASE={database};"
                "Trusted_Connection=yes;TrustServerCertificate=yes;"
            )
            return create_engine(
                URL.create("mssql+pyodbc", query={"odbc_connect": connection_string}),
                pool_pre_ping=True,
            )
        if not username or password is None:
            raise ValueError("Enter SQL Server username and password.")
        return create_engine(
            URL.create(
                "mssql+pyodbc",
                username=username,
                password=password,
                host=host,
                port=int(port) if port else None,
                database=database,
                query={"driver": driver, "TrustServerCertificate": "yes"},
            ),
            pool_pre_ping=True,
        )

    if not username or password is None:
        raise ValueError("Username and password are required.")

    if db_type == "mysql":
        return create_engine(
            URL.create(
                "mysql+pymysql", username=username, password=password,
                host=host, port=int(port) if port else 3306, database=database
            ),
            pool_pre_ping=True,
        )

    if db_type == "postgresql":
        return create_engine(
            URL.create(
                "postgresql+psycopg", username=username, password=password,
                host=host, port=int(port) if port else 5432, database=database
            ),
            pool_pre_ping=True,
        )

    raise ValueError("Unsupported database type.")


def test_import_connection(engine):
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True


def get_database_schemas(engine):
    inspector = inspect(engine)
    schemas = inspector.get_schema_names()
    if engine.dialect.name == "sqlite":
        return ["main"]
    if engine.dialect.name == "mysql":
        return [None]
    return schemas or [None]


def get_database_tables(engine, schema=None):
    inspector = inspect(engine)
    return inspector.get_table_names(schema=schema)


def import_database_table(engine, table_name, schema=None, row_limit=100000):
    metadata = MetaData()
    table = Table(table_name, metadata, schema=schema, autoload_with=engine)
    statement = select(table).limit(int(row_limit) + 1)
    with engine.connect() as connection:
        result = connection.execute(statement)
        rows = result.fetchall()
        columns = list(result.keys())
    was_truncated = len(rows) > row_limit
    rows = rows[:row_limit]
    return pd.DataFrame(rows, columns=columns), was_truncated


def validate_read_only_query(query):
    """Allow a single SELECT/CTE statement; reject common write/DDL commands."""
    cleaned = query.strip()
    if not cleaned:
        raise ValueError("Enter a SQL SELECT query.")

    # Permit one optional trailing semicolon, but no multiple statements.
    if ";" in cleaned.rstrip(";"):
        raise ValueError("Only one SQL statement is allowed.")
    cleaned = cleaned.rstrip().rstrip(";").strip()

    first_word = cleaned.split(None, 1)[0].lower()
    if first_word not in {"select", "with"}:
        raise ValueError("Only SELECT queries and read-only CTE queries are allowed.")

    import re
    blocked = re.compile(
        r"\b(insert|update|delete|drop|alter|create|truncate|merge|execute|exec|grant|revoke|into)\b",
        re.IGNORECASE,
    )
    if blocked.search(cleaned):
        raise ValueError("The query contains a blocked write or DDL keyword.")
    return cleaned


def import_sql_query(engine, query, row_limit=100000):
    safe_query = validate_read_only_query(query)
    with engine.connect() as connection:
        result = connection.execute(text(safe_query))
        rows = result.fetchmany(int(row_limit) + 1)
        columns = list(result.keys())
    was_truncated = len(rows) > row_limit
    rows = rows[:row_limit]
    return pd.DataFrame(rows, columns=columns), was_truncated
