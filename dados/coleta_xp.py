from datetime import datetime, timedelta, time
from sqlite3 import OperationalError
from asyncio import sleep
from io import StringIO
import pandas as pd
import requests

from dados.database import Database

class Coleta():
    @staticmethod
    def _tempo_para_nove_horas(prox_dia = True):
        agr = datetime.now()
        nove_horas = agr.replace(hour = 9, minute = 5)
        
        if prox_dia:
            nove_horas = nove_horas + timedelta(days = 1)
        
        diferenca = nove_horas - agr
        return diferenca.total_seconds()
    
    @staticmethod
    def _coletar_cabecinhas(db: Database):
        response = requests.get('http://services.runescape.com/m=clan-hiscores/members_lite.ws?clanName=Drunken+Dwarf')

        if response.status_code == 200:
            request_text = response.content.decode('utf-8', errors = 'replace').replace('\ufffd', ' ')
            cabecinhas = pd.read_csv(StringIO(request_text), header = 0)
            hoje = datetime.today().strftime('%Y-%m-%d')

            RANKS = {
                'Owner': 'Dono',
                'Deputy Owner': 'Vice-Dono',
                'Overseer': 'Fiscal',
                'Coordinator': 'Coord.',
                'Organiser': 'Org.',
                'Admin': 'Admin.',
                'General': 'General',
                'Captain': 'Capitão',
                'Lieutenant': 'Tenente',
                'Sergeant': 'Sargento',
                'Corporal': 'Cabo',
                'Recruit': 'Recruta'
            }

            for _, cringe in cabecinhas.iterrows():
                nome = cringe['Clanmate']
                usuario = db.user_exists(nome)
                xp_atual = cringe[' Total XP'] # Sim, tem espaço.
                rank = RANKS[cringe[' Clan Rank']]
                kills = cringe[' Kills']
                id, _ = usuario if usuario else db.create_user(nome)

                try:
                    ultimo_xp = db.get_last_xp(id)[0]
                except TypeError: # Não tem registro prévio.
                    db.add_xp(id, rank, xp_atual, kills, hoje)
                    continue

                if xp_atual > ultimo_xp:
                    db.add_xp(id, rank, xp_atual, kills, hoje)
        else:
            print("Erro na coleta de membros: ", response.status_code)
    
    @staticmethod
    async def iniciar():
        while True:
            agora = datetime.now() 

            # Bot foi iniciado antes das nove da manhã.
            if agora.time() <= time(9, 5):
                segundos = Coleta._tempo_para_nove_horas(prox_dia = False)
                print(f'Dormindo {segundos} até as 9 da matina.')
                await sleep()
                continue

            db = Database()

            try:
                db.cursor.execute("SELECT xp_date FROM users_data ORDER BY xp_date DESC LIMIT 1")
                result = db.cursor.fetchone()
                sem_col_hoje = agora.date() > datetime.strptime(result[0], '%Y-%m-%d').date()

                if not result or sem_col_hoje:
                    Coleta()._coletar_cabecinhas(db)
            except OperationalError as e:
                print(f'Erro: {e}') # Primeira execução com db vazia vai cair aqui.

            db.close()

            segundos = Coleta._tempo_para_nove_horas()
            print(f'Dormindo {segundos} até o dia seguinte.')
            await sleep(segundos)