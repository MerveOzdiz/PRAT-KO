import sqlite3
from pathlib import Path


def apply_sqlite_migrations(engine):
    if engine.dialect.name != 'sqlite':
        return

    with engine.begin() as connection:
        connection.exec_driver_sql('BEGIN IMMEDIATE')
        connection.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS schema_migration (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        applied = set(connection.exec_driver_sql('SELECT version FROM schema_migration').scalars())
        for path in sorted(Path(__file__).parent.glob('[0-9]*.sql')):
            if path.stem in applied:
                continue
            statement = ''
            for line in path.read_text(encoding='utf-8').splitlines(keepends=True):
                statement += line
                if sqlite3.complete_statement(statement):
                    connection.exec_driver_sql(statement)
                    statement = ''
            if statement.strip():
                raise ValueError(f'Incomplete SQL migration: {path.name}')
            connection.exec_driver_sql('INSERT INTO schema_migration (version) VALUES (?)', (path.stem,))
