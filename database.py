import sqlite3
from datetime import datetime

DB_NAME = 'financas.db'

def connect():
    return sqlite3.connect(DB_NAME)


def initialize_db():
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                date TEXT NOT NULL,
                category_id INTEGER,
                recurring INTEGER NOT NULL CHECK (recurring IN (0, 1)),
                FOREIGN KEY(category_id) REFERENCES categories(id)
            )
        ''')

        if _old_schema_exists(cursor) and _new_tables_empty(cursor):
            _migrate_old_schema(cursor)

        conn.commit()


def _old_schema_exists(cursor):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('categorias', 'gastos')")
    return bool(cursor.fetchall())


def _new_tables_empty(cursor):
    cursor.execute('SELECT COUNT(*) FROM categories')
    categories_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM expenses')
    expenses_count = cursor.fetchone()[0]
    return categories_count == 0 and expenses_count == 0


def _migrate_old_schema(cursor):
    cursor.execute('INSERT OR IGNORE INTO categories (id, user_id, name) SELECT id, user_id, nome FROM categorias')
    cursor.execute('INSERT OR IGNORE INTO expenses (id, user_id, amount, description, date, category_id, recurring) SELECT id, user_id, valor, descricao, data, categoria_id, recorrente FROM gastos')

    cursor.execute('DROP TABLE IF EXISTS gastos')
    cursor.execute('DROP TABLE IF EXISTS categorias')


def add_category(user_id, name):
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO categories (user_id, name) VALUES (?, ?)', (user_id, name))
        conn.commit()


def update_category(user_id, category_id, new_name):
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE categories SET name = ? WHERE user_id = ? AND id = ?',
            (new_name, user_id, category_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def list_categories(user_id):
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM categories WHERE user_id = ?', (user_id,))
        return cursor.fetchall()


def add_expense(user_id, amount, description, date, category_id, recurring):
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO expenses (user_id, amount, description, date, category_id, recurring)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, amount, description, date, category_id, recurring))
        conn.commit()


def get_monthly_total(user_id, year_month=None):
    if not year_month:
        year_month = datetime.now().strftime('%Y-%m')
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT SUM(amount) FROM expenses 
            WHERE user_id = ? AND date LIKE ?
        ''', (user_id, f"{year_month}%"))
        res = cursor.fetchone()[0]
        return res if res is not None else 0.0


def list_monthly_expenses(user_id, year_month=None):
    if not year_month:
        year_month = datetime.now().strftime('%Y-%m')
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT g.amount, g.description, g.date, c.name
            FROM expenses g
            LEFT JOIN categories c ON g.category_id = c.id
            WHERE g.user_id = ? AND g.date LIKE ?
            ORDER BY g.date ASC, g.id ASC
        ''', (user_id, f"{year_month}%"))
        return cursor.fetchall()


def get_total_by_category(user_id, year_month=None):
    if not year_month:
        year_month = datetime.now().strftime('%Y-%m')
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.name, SUM(g.amount) 
            FROM expenses g
            JOIN categories c ON g.category_id = c.id
            WHERE g.user_id = ? AND g.date LIKE ?
            GROUP BY c.name
        ''', (user_id, f"{year_month}%"))
        return cursor.fetchall()


def list_recurring_expenses(user_id):
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT g.id, g.amount, g.description, g.date, c.name 
            FROM expenses g
            LEFT JOIN categories c ON g.category_id = c.id
            WHERE g.user_id = ? AND g.recurring = 1
        ''', (user_id,))
        return cursor.fetchall()


def list_recent_expenses(user_id, limit=5):
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT g.id, g.amount, g.description, g.date 
            FROM expenses g
            WHERE g.user_id = ?
            ORDER BY g.id DESC LIMIT ?
        ''', (user_id, limit))
        return cursor.fetchall()


def delete_expense(user_id, expense_id):
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM expenses WHERE user_id = ? AND id = ?', (user_id, expense_id))
        conn.commit()
        return cursor.rowcount > 0


def reset_database():
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM expenses')
        cursor.execute('DELETE FROM categories')
        conn.commit()
