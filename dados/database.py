from collections import defaultdict
from datetime import datetime, timedelta
import sqlite3
import os

class Database():
    """Classe responsável por conectar e acessar o banco de dados sqlite."""

    def __init__(self):
        self.conn = None
        self.cursor = None

        db_exists = os.path.isfile('dados/dkdw.db')

        self.conectar()

        if not db_exists:
            print("Banco de dados não encontrado. Criando novo banco de dados e tabelas...")
            self.criar_banco()

    def conectar(self):
        self.conn = sqlite3.connect('dados/dkdw.db')
        self.cursor = self.conn.cursor()

    def criar_banco(self):
        """Executa o script para criação das tabelas no banco de dados."""

        try:
            with open('dados/dkdw.sql', 'r') as file:
                self.cursor.executescript(file.read())
                self.conn.commit()
        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo 'dkdw.sql' não foi encontrado.")
        
    def jogador_registrado(self, nome: str, incluir_arqv: bool = False) -> tuple[int, str, bool] | None:
        """Retorna (id, nome, no_clan) se o nome estiver registrado e (opcionalmente) no clã."""

        try:
            query = """
                SELECT un.id_user, un.username, u.in_clan
                FROM users_names un
                JOIN users u ON un.id_user = u.id
                WHERE un.username = ?
            """
            
            if not incluir_arqv:
                query += " AND u.in_clan = 1"

            self.cursor.execute(query, (nome,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f'Erro no banco ao verificar se jogador está registrado: {e}')
            return None

    def registrar_jogador(self, nome: str, hoje: str) -> tuple[int, str] | None:
        """Registra um novo jogador ao banco de dados (ou re-ativa um inativo) e retorna seu (id, nome)."""

        try:
            self.cursor.execute("SELECT id_user FROM users_names WHERE username = ?", (nome, ))
            id = self.cursor.fetchone()

            # Pessoa saiu e voltou depois, com o mesmo nome (não é tijolinho).
            if id:
                self.cursor.execute("UPDATE users SET in_clan = 1 WHERE id = ?", (id[0], ))
            # Randola (ou trocou de nome antes de voltar).
            else: 
                self.cursor.execute("INSERT INTO users DEFAULT VALUES")
                self.cursor.execute("SELECT * FROM users ORDER BY id DESC LIMIT 1")
                id = self.cursor.fetchone()[0]
                self.cursor.execute(
                    "INSERT INTO users_names (id_user, username, name_date) VALUES (?, ?, ?)", 
                    (id, nome, hoje, )
                )
            self.cursor.execute(
                'INSERT INTO users_join (id_user, join_date) VALUES (?, ?)',
                (id, hoje, )
            )

            self.conn.commit()
            return self.jogador_registrado(nome)
        except Exception as e:
            print(f'Erro no banco ao registrar jogador: {e}')
            return None
        
    def todos_jogadores(self, incluir_inativos: bool = False) -> list[tuple[int, str]] | None:
        """Retorna todos os jogadores registrados como [(id, nome), ...]."""

        try:
            if incluir_inativos:
                self.cursor.execute("""
                    SELECT id_user, username
                    FROM users_names un
                    WHERE name_date = (
                        SELECT MAX(name_date)
                        FROM users_names
                        WHERE id_user = un.id_user
                    )
                """)
            else:
                self.cursor.execute("""
                    SELECT un.id_user, un.username
                    FROM users_names un
                    JOIN users u ON un.id_user = u.id
                    WHERE u.in_clan = 1
                    AND un.name_date = (
                        SELECT MAX(name_date)
                        FROM users_names
                        WHERE id_user = un.id_user
                    );
                """)
            return self.cursor.fetchall()
        except Exception as e:
            print(f'Erro no banco ao buscar todos os jogadores: {e}')
            return None
        
    def todos_jogadores_com_stats(self, excluding_id: int) -> list[tuple[int, str]] | None:
        """Retorna (id_user, username) para todo aquele que tiver um registro em 'users_stats'."""
        
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
                AND un.id = (
                    SELECT MAX(un2.id)
                    FROM users_names un2
                    WHERE un2.id_user = un.id_user
                )
                ORDER BY un.id_user;
            """, (excluding_id, ))
            return self.cursor.fetchall()
        except Exception as e:
            print(f'Database error: {e}')
            return None

    def buscar_ultimo_xp(self, id: int) -> tuple[int, str, str] | None:
        """Retorna o último (xp, xp_date, rank) de um usuário por seu id."""
        
        try:
            self.cursor.execute("""
                SELECT ud.xp, ud.xp_date, ur.rank
                FROM users_data ud
                JOIN ranks ur ON ud.id_rank = ur.id
                WHERE ud.id_user = ?
                ORDER BY ud.xp_date DESC
                LIMIT 1;
            """, (id,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f'Erro no banco ao buscar último XP: {e}')
            return None
        
    def buscar_estatisticas(self, id: int) -> tuple[int] | None:
        """Retorna as 150 estatísticas dos hi-scores de dado id."""

        try:
            self.cursor.execute("SELECT * FROM users_stats WHERE id_user = ?", (id,))
            return self.cursor.fetchone()[2:]
        except Exception as e:
            print(f'Erro no banco ao buscar estatística de jogador: {e}')
            return None
        
    def buscar_todas_estatísticas(self, excluding_id: int) -> tuple[tuple[int]] | None:
        """Retorna as 150 estatísticas dos hi-scores de todos, menos de dado id."""
        
        try:
            columns = ', '.join([f"stat{i+1}" for i in range(150)])
            self.cursor.execute(f"SELECT {columns} FROM users_stats WHERE id_user != ? ORDER BY id_user", (excluding_id, ))
            return self.cursor.fetchall()
        except Exception as e:
            print(f'Erro no banco ao buscar todas as estatísticas: {e}')
            return None
        
    def buscar_historico_nomes(self, name: str) -> tuple[str, str] | None:
        """Retorna o todos os nomes registrados de dado jogador."""

        try:
            id = (self.jogador_registrado(name, True))[0]
            self.cursor.execute("SELECT username, name_date FROM users_names WHERE id_user = ?", (id, ))
            return self.cursor.fetchall()
        except Exception as e:
            print(f'Erro no banco ao buscar histórico de nomes: {e}')
            return None

    def historico_geral_mes(self, dias: int) -> dict | None:
        """Retorna o histórico de membros do último mês (30 dias)."""

        try:
            data_limite = (datetime.now() - timedelta(days = int(dias))).date()

            self.cursor.execute("""
                -- JOIN EVENTS
                SELECT
                    uj.id_user,
                    (
                        SELECT un.username
                        FROM users_names un
                        WHERE un.id_user = uj.id_user
                        AND un.name_date <= uj.join_date
                        ORDER BY un.name_date DESC
                        LIMIT 1
                    ) AS username,
                    NULL AS previous_username,
                    'entrou' AS change_type,
                    uj.join_date AS change_date
                FROM users_join uj
                WHERE uj.join_date >= ?

                UNION ALL

                -- LEAVE EVENTS
                SELECT
                    ul.id_user,
                    (
                        SELECT un.username
                        FROM users_names un
                        WHERE un.id_user = ul.id_user
                        AND un.name_date <= ul.leave_date
                        ORDER BY un.name_date DESC
                        LIMIT 1
                    ) AS username,
                    NULL AS previous_username,
                    'saiu' AS change_type,
                    ul.leave_date AS change_date
                FROM users_leave ul
                WHERE ul.leave_date >= ?

                UNION ALL

                -- NAME CHANGE EVENTS
                SELECT
                    un.id_user,
                    un.username AS username,
                    (
                        SELECT un_prev.username
                        FROM users_names un_prev
                        WHERE un_prev.id_user = un.id_user
                        AND un_prev.id < un.id
                        ORDER BY un_prev.id DESC
                        LIMIT 1
                    ) AS previous_username,
                    'nome' AS change_type,
                    un.name_date AS change_date
                FROM users_names un
                WHERE un.name_date >= ?

                ORDER BY id_user, change_date;
            """, (data_limite, data_limite, data_limite, ))
            
            query_mostro = self.cursor.fetchall()

            historico = defaultdict(list)

            for linha in query_mostro:
                id_user, username, previous_username, change_type, change_date = linha
                historico[id_user].append({
                    "tipo": change_type,
                    "data": change_date,
                    "nome": username,
                    "nome_antigo": previous_username
                })

            for changes in historico.values():
                # Ordena o que cada um fez pela data, vide 
                # a prioridade abaixo para datas iguais.
                changes.sort(key = lambda c: (
                    datetime.strptime(c["data"], "%Y-%m-%d"),
                    { "entrou": 0, "nome": 1, "saiu": 2 }.get(c["tipo"], 99)
                ))

            return dict(
                # Ordena o dicionário como um todo pela data 
                # do primeiro evento de cada pessoa.
                sorted(
                    historico.items(),
                    key = lambda item: datetime.strptime(item[1][0]["data"], "%Y-%m-%d")
                )
            )
        except Exception as e:
            print(f'Erro no banco ao buscar histórico do último mês: {e}')
            return None

    def adicionar_xp(self, id_user: int, id_rank: int, xp: int, kc: int, today: str):
        """Adiciona um novo registro de XP feito no clã para dado jogador por id."""
        
        try:
            self.cursor.execute(
                "INSERT INTO users_data (id_user, id_rank, xp, kc, xp_date) VALUES (?, ?, ?, ?, ?)",
                (id_user, id_rank, xp, kc, today)
            )
            self.conn.commit()
        except Exception as e:
            print(f'Erro no banco ao adicionar XP: {e}')

    def adicionar_estatisticas(self, id_user: int, stats: list[int]):
        """Adiciona (ou atualiza) as 150 estatísticas de dado jogador por id."""

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
            print(f'Erro no banco ao adicionar estatísticas: {e}')

    def unir_registros(self, id_old: int, id_new: int, jogador_ativo: bool):
        """Muda o 'id_user' do jogador com 'id_new' para 'id_old', unificando seus registros."""

        try:
            # Estava inativo, daí voltou tempos depois com outro nome.
            if not jogador_ativo:
                self.cursor.execute(
                    'UPDATE users_join SET id_user = ? WHERE id_user = ?',
                    (id_old, id_new, )
                )
                # Improvável que tenha algo, mas só no caso de eu estar esquecendo algo.
                self.cursor.execute(
                    'UPDATE users_leave SET id_user = ? WHERE id_user = ?',
                    (id_old, id_new, )
                )

            self.cursor.execute(
                'UPDATE users_names SET id_user = ? WHERE id_user = ?',
                (id_old, id_new, )
            )
            self.cursor.execute(
                'UPDATE users_data SET id_user = ? WHERE id_user = ?', 
                (id_old, id_new, )
            )

            # Precisa ser lista (não tupla).
            stats = [stat for stat in self.buscar_estatisticas(id_new)]
            self.adicionar_estatisticas(id_old, stats)

            # Não tem commit porque o deletar_jogador() já commita.
            self.deletar_jogador(id_new)
        except Exception as e:
            print(f'Erro no banco ao unir jogadores: {e}')

    def arquivar_jogador(self, id: int, data: str):
        """Inativa um jogador registrado por seu id, ao invés de deletar."""

        try:
            self.cursor.execute(
                'UPDATE users SET in_clan = 0 WHERE id = ?', 
                (id, )
            )
            self.cursor.execute(
                'INSERT INTO users_leave (id_user, leave_date) VALUES (?, ?)',
                (id, data, )
            )
            self.conn.commit()
        except Exception as e:
            print(f'Erro no banco ao inativar jogador: {e}')

    def deletar_jogador(self, id: int):
        """Apaga todos os registros de dado jogador por id."""

        try:
            # Necessário pra enforçar foreign key e ON CASCADE DELETE funcionar.
            self.cursor.execute('PRAGMA foreign_keys = ON')
            self.cursor.execute('DELETE FROM users WHERE id = ?', (id, ))
            self.conn.commit()
        except Exception as e:
            print(f'Erro no banco ao deletar jogador: {e}')

    def fechar(self):
        if self.conn:
            self.conn.close()