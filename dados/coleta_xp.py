from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cosine
import numpy as np

from datetime import datetime, timedelta, time
from sqlite3 import OperationalError
from asyncio import sleep
from io import StringIO
import pandas as pd
import requests
import re

from dados.database import Database
from dados.fetch import Fetch

class Coleta():
    @staticmethod
    def _tempo_para_nove_horas():
        agora = datetime.now()
        nove_horas = agora.replace(hour = 9)
        diferenca = nove_horas - agora
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
                id, _ = usuario if usuario else db.create_user(nome, hoje)

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
    async def _listar_membros_cla() -> None | list[str]:
        """Retorna o nome dos membros do clã."""

        try:
            response = await Fetch().text('http://services.runescape.com/m=clan-hiscores/members_lite.ws?clanName=Drunken+Dwarf')
            if not response:
                print("Erro ao carregar lista de membros.")
                return None

            request_text = response.replace('\ufffd', ' ')
            cabecinhas = pd.read_csv(StringIO(request_text), header = 0)
            return [cringe['Clanmate'] for _, cringe in cabecinhas.iterrows()]
        except Exception as e:
            print(f'Erro ao puxar membros do clã da API: {e}')
            return None

    @staticmethod
    async def _atualizar_stats():
        """Atualiza a tabela 'users_stats' no banco de dados para todos os jogadores membros."""

        db = Database()
        membros = await Coleta()._listar_membros_cla()
        if membros:
            for nome in membros:
                try:
                    stats = await Fetch().text(f"https://secure.runescape.com/m=hiscore/index_lite.ws?player={nome.replace(' ', '+')}")
                    
                    # Acc saiu dos Hiscores porque tá free, mas não 
                    # importa porque free não pode mudar de nome. 
                    if stats is None:
                        continue
                    
                    stats_formatados = re.split(r'[,\n]+', stats)[0:-1]

                    usuario = db.user_exists(nome)
                    if usuario:
                        db.add_stats(usuario[0], stats_formatados)
                except Exception as e:
                    print(f"Erro atualizando dados de {nome}: {e}")
        db.close()

    @staticmethod
    async def _verificar_alterados():
        """
        Verifica e trata nomes registrados que não estão mais no clã.
            - Quem saiu (não tem `NO_PROFILE` no RuneMetrics)  é eliminado;
            - Quem trocou de nome tem o perfil unido ao seu par mais similar.
        """

        db = Database()
        cabecinhas_registradas = db.get_all_users()
        cabecinhas_atuais = await Coleta()._listar_membros_cla()

        if not cabecinhas_atuais:
            db.close()
            return

        # Registrados que não estão mais no clã.
        desaparecidos = [(id, nome) for id, nome in cabecinhas_registradas if nome not in cabecinhas_atuais]

        for id, nome in desaparecidos:
            try:
                runemetrics = await Fetch().json(f"https://apps.runescape.com/runemetrics/profile/profile?user={nome.replace(' ', '+')}&activities=1")
                if runemetrics.get('error') != 'NO_PROFILE': # Se não for NO_PROFILE, é porque saiu do clã.
                    db.delete_user(id)
                    print(f"Jogador ({id} '{nome}') deletado do Clã por ter saído.")

                desconhecido = db.user_exists(nome)
                id_antigo = desconhecido[0]
                stats_antigo = db.get_user_stats(id_antigo)

                # Pessoa nova que ainda não foi foi coletada.
                if not stats_antigo:
                    continue

                scaler = StandardScaler()
                cabecinhas_stats = np.array(db.get_all_user_stats(id_antigo))
                scaler.fit(cabecinhas_stats)
                dados_historicos = scaler.transform(cabecinhas_stats)

                stats_antigo = np.array(stats_antigo).reshape(1, -1)   # shape (1, 150)
                ultimo_stats = scaler.transform(stats_antigo)[0]       # shape (150,)

                similaridades = []
                for id_conhecido, vetor_conhecido in zip(db.get_all_users_with_data(id_antigo), dados_historicos):
                    sim = 1 - cosine(ultimo_stats, vetor_conhecido)
                    similaridades.append((id_conhecido, sim))

                best_match, score = max(similaridades, key = lambda x: x[1])
                novo_id, novo_nome = best_match

                db.merge_users(id_antigo, novo_id)
                print(f"({id_antigo} '{nome}') trocou para ({novo_id} '{novo_nome}') com similaridade: {(score * 100):.2f}%")
            except Exception as e:
                print(f'Erro atualizando {nome} para novo nome: {e}')
        db.close()

    @staticmethod
    async def iniciar():
        await sleep(15)

        while True:
            agora = datetime.now()

            # Improvável que alguém upe muito/mude de nome de madrugada.
            if agora.time() <= time(9):
                segundos = Coleta._tempo_para_nove_horas()
                print(f'Dormindo {segundos} até as 9 da matina.')
                await sleep(segundos)
                
            db = Database()
            try:
                db.cursor.execute("SELECT xp_date FROM users_data ORDER BY xp_date DESC LIMIT 1")
                result = db.cursor.fetchone()
                sem_col_hoje = agora.date() > datetime.strptime(result[0], '%Y-%m-%d').date()

                if not result or sem_col_hoje:
                    print('Coletando cabecinhas...')
                    Coleta()._coletar_cabecinhas(db)
                    continue
            except OperationalError as e:
                print(f'Erro: {e}') # Primeira execução com db vazia vai cair aqui.
            finally:
                db.close()

            print('Atualizando stats...')
            await Coleta()._atualizar_stats()

            print('Verificando nomes alterados...')
            await Coleta()._verificar_alterados()
                
            HORAS = 3
            print(f'Dormindo por {HORAS} horas.')
            await sleep(HORAS * 3600)