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
            self.cursor.execute("SELECT id_user, username FROM users_names WHERE username = ? ORDER BY name_date", (name,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f'Database error: {e}')
            return None

    def create_user(self, name: str, today: str) -> tuple[int, str] | None:
        try:
            self.cursor.execute("INSERT INTO users DEFAULT VALUES")
            self.cursor.execute("SELECT * FROM users ORDER BY id DESC LIMIT 1")
            id = self.cursor.fetchone()[0]
            self.cursor.execute(
                "INSERT INTO users_names (id_user, username, name_date) VALUES (?, ?, ?)", 
                (id, name, today, )
            )
            self.conn.commit()
            return self.user_exists(name)
        except Exception as e:
            print(f'Database error: {e}')
            return None
        
    def get_all_users(self) -> list[tuple[int, str]] | None:
        try:
            self.cursor.execute("""
                SELECT id_user, username
                    FROM users_names un
                    WHERE name_date = (
                        SELECT MAX(name_date)
                        FROM users_names
                        WHERE id_user = un.id_user
                    )
            """)
            return self.cursor.fetchall()
        except Exception as e:
            print(f'Database error: {e}')
            return None
        
    def get_all_users_with_data(self, excluding_id: int) -> list[tuple[int, str]] | None:
        try:
            self.cursor.execute("""
                SELECT un.id_user, un.username
                FROM users_names un
                WHERE un.id_user != ? 
                    AND EXISTS (
                        SELECT 1 
                        FROM users_stats d 
                        WHERE d.id_user = un.id_user
                    )
                ORDER BY un.id_user;
            """, (excluding_id, ))
            return self.cursor.fetchall()
        except Exception as e:
            print(f'Database error: {e}')
            return None

    def get_last_xp(self, id: int) -> tuple[int, str] | None:
        try:
            self.cursor.execute("SELECT xp, xp_date FROM users_data WHERE id_user = ? ORDER BY xp_date DESC LIMIT 1", (id,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f'Database error: {e}')
            return None
        
    def get_user_stats(self, id: int) -> tuple[int] | None:
        try:
            self.cursor.execute("SELECT * FROM users_stats WHERE id_user = ?", (id,))
            return self.cursor.fetchone()[2:]
        except Exception as e:
            print(f'Database error: {e}')
            return None
        
    def get_all_user_stats(self, excluding_id: int) -> tuple[tuple[int]] | None:
        try:
            columns = ', '.join([f"stat{i+1}" for i in range(150)])
            self.cursor.execute(f"SELECT {columns} FROM users_stats WHERE id_user != ? ORDER BY id_user", (excluding_id, ))
            return self.cursor.fetchall()
        except Exception as e:
            print(f'Database error: {e}')
            return None
        
    def get_user_name_history(self, name: str) -> tuple[str, str] | None:
        try:
            id, _ = self.user_exists(name)
            self.cursor.execute(
                "SELECT username, name_date FROM users_names WHERE id_user = ?", 
                (id, )
            )
            return self.cursor.fetchall()
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

    def add_stats(self, id_user: int, stats: list[int]):
        try:
            columns = [f"stat{i+1}" for i in range(len(stats))]
    
            self.cursor.execute("SELECT id FROM users_stats WHERE id_user = ?", (id_user,))
            row = self.cursor.fetchone()

            if row is None:
                size = len(columns)
                columns = ["id_user"] + [f"stat{i+1}" for i in range(size)]
                placeholders = ", ".join(["?"] * (size + 1)) # 150 stats + id_user
                sql = f"INSERT INTO users_stats ({', '.join(columns)}) VALUES ({placeholders});"
                params = [id_user] + stats
            else:
                set_clause = ", ".join([f"{col} = ?" for col in columns])
                sql = f"UPDATE users_stats SET {set_clause} WHERE id_user = ?;"
                params = stats + [id_user]

            self.cursor.execute(sql, params)
            self.conn.commit()
        except Exception as e:
            print(f'Database error: {e}')

    def merge_users(self, id_old: int, id_new: int):
        try:
            self.cursor.execute(
                'UPDATE users_stats SET id_user = ? WHERE id_user = ?', 
                (id_old, id_new, )
            )
            self.cursor.execute(
                'UPDATE users_data SET id_user = ? WHERE id_user = ?', 
                (id_old, id_new, )
            )
            self.cursor.execute(
                'UPDATE users_names SET id_user = ? WHERE id_user = ?',
                (id_old, id_new, )
            )
            self.cursor.execute(
                'DELETE FROM users WHERE id = ?', 
                (id_new, )
            )
            self.conn.commit()
        except Exception as e:
            print(f'Database MOGGED: {e}')

    def delete_user(self, id: str):
        try:
            self.cursor.execute('DELETE FROM users WHERE id = ?', (id, ))
            self.conn.commit()
        except Exception as e:
            print(f'Database error: {e}')

    def close(self):
        if self.conn:
            self.conn.close()