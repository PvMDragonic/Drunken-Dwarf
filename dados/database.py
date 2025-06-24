import sqlite3
import os

class Database():
    def __init__(self):
        self.conn = None
        self.cursor = None

        db_exists = os.path.isfile('dados/dkdw.db')

        self.connect()

        if not db_exists:
            print("Banco de dados não encontrado. Criando novo banco de dados e tabelas...")
            self.setup_database()

    def connect(self):
        self.conn = sqlite3.connect('dados/dkdw.db')
        self.cursor = self.conn.cursor()

    def setup_database(self):
        try:
            with open('dados/dkdw.sql', 'r') as file:
                self.cursor.executescript(file.read())
                self.conn.commit()
        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo 'dkdw.sql' não foi encontrado.")
        
    def user_exists(self, name: str) -> tuple[int, str] | None:
        try:
            self.cursor.execute("SELECT * FROM users WHERE username = ?", (name,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f'Database error: {e}')
            return None

    def create_user(self, name: str) -> tuple[int, str] | None:
        try:
            self.cursor.execute("INSERT INTO users (username) VALUES (?)", (name,))
            self.conn.commit()
            return self.user_exists(name)
        except Exception as e:
            print(f'Database error: {e}')
            return None
        
    def get_all_users(self) -> list[tuple[int, str]] | None:
        try:
            self.cursor.execute("SELECT * FROM users")
            return self.cursor.fetchall()
        except Exception as e:
            print(f'Database error: {e}')
            return None

    def get_last_xp(self, id: int) -> tuple[int, int, str] | None:
        try:
            self.cursor.execute("SELECT xp, xp_date, rank FROM users_data WHERE id_user = ? ORDER BY xp_date DESC LIMIT 1", (id,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f'Database error: {e}')
            return None

    def add_xp(self, id_user: int, rank: str, xp: int, kc: int, today: str):
        try:
            self.cursor.execute(
                "INSERT INTO users_data (id_user, rank, xp, kc, xp_date) VALUES (?, ?, ?, ?, ?)",
                (id_user, rank, xp, kc, today)
            )
            self.conn.commit()
        except Exception as e:
            print(f'Database error: {e}')

    def close(self):
        if self.conn:
            self.conn.close()