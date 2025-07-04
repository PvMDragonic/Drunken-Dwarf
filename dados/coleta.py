from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cosine
import numpy as np

from discord import TextChannel, Embed, Color
from datetime import datetime, time
from asyncio import sleep
from io import StringIO
import pandas as pd
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
    async def _coletar_cabecinhas():
        cabecinhas = await Coleta()._listar_membros_cla(completo = True)
        if cabecinhas is None:
            return 
        
        hoje = datetime.today().strftime('%Y-%m-%d')
        db = Database()

        RANKS = {
            'Owner': 1,
            'Deputy Owner': 2,
            'Overseer': 3,
            'Coordinator': 4,
            'Organiser': 5,
            'Admin': 6,
            'General': 7,
            'Captain': 8,
            'Lieutenant': 9,
            'Sergeant': 10,
            'Corporal': 11,
            'Recruit': 12
        }

        for _, cringe in cabecinhas.iterrows():
            nome = cringe['Clanmate']
            xp_atual = cringe[' Total XP'] # Sim, tem espaço.
            rank = RANKS[cringe[' Clan Rank']]
            kills = cringe[' Kills']
            id, _ = db.jogador_registrado(nome) or db.registrar_jogador(nome, hoje)

            ultimo_registro = db.buscar_ultimo_xp(id)
            if not ultimo_registro:
                db.adicionar_xp(id, rank, xp_atual, kills, hoje)
                continue

            ultimo_xp, data_xp, _ = ultimo_registro 

            # Não precisa de mais de um registro por dia.
            if data_xp == hoje:
                continue

            if xp_atual > ultimo_xp:
                db.adicionar_xp(id, rank, xp_atual, kills, hoje)
        db.fechar()
            
    @staticmethod
    async def _listar_membros_cla(completo: bool = False) -> None | list[str] | pd.DataFrame:
        """Retorna o nome dos membros do clã."""

        try:
            response = await Fetch().text('http://services.runescape.com/m=clan-hiscores/members_lite.ws?clanName=Drunken+Dwarf')
            if not response:
                print("Erro ao carregar lista de membros.")
                return None

            request_text = response.replace('\ufffd', ' ')
            cabecinhas = pd.read_csv(StringIO(request_text), header = 0)
            
            return [cringe['Clanmate'] for _, cringe in cabecinhas.iterrows()] if not completo else cabecinhas
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

                    usuario = db.jogador_registrado(nome)
                    if usuario:
                        db.adicionar_estatisticas(usuario[0], stats_formatados)
                except Exception as e:
                    print(f"Erro atualizando dados de {nome}: {e}")
        db.fechar()

    @staticmethod
    async def _verificar_alterados(enviar_relatorio: bool, canal: TextChannel):
        """
        Verifica e trata nomes registrados que não estão mais no clã.
            - Quem saiu (não tem `NO_PROFILE` no RuneMetrics)  é eliminado;
            - Quem trocou de nome tem o perfil unido ao seu par mais similar.
        """

        db = Database()
        cabecinhas_registradas = db.todos_jogadores(incluir_inativos = True)
        cabecinhas_atuais = await Coleta()._listar_membros_cla()

        if not cabecinhas_atuais:
            db.fechar()
            return

        # Registrados que não estão mais no clã.
        desaparecidos = [(id, nome) for id, nome in cabecinhas_registradas if nome not in cabecinhas_atuais]

        saidas = []
        novos_nomes = []

        for id, nome in desaparecidos:
            try:
                runemetrics = await Fetch().json(f"https://apps.runescape.com/runemetrics/profile/profile?user={nome.replace(' ', '+')}&activities=1")
                if runemetrics.get('error') != 'NO_PROFILE': # Se não for NO_PROFILE, é porque saiu do clã.
                    db.arquivar_jogador(id)
                    saidas.append(nome)
                    print(f"Jogador ({id} '{nome}') deletado do Clã por ter saído.")

                desconhecido = db.jogador_registrado(nome)
                if not desconhecido:
                    continue # Usuário desativado.
                
                id_antigo = desconhecido[0]
                stats_antigo = db.buscar_estatisticas(id_antigo)

                scaler = StandardScaler()
                cabecinhas_stats = np.array(db.buscar_todas_estatísticas(id_antigo))
                scaler.fit(cabecinhas_stats)
                dados_historicos = scaler.transform(cabecinhas_stats)

                stats_antigo = np.array(stats_antigo).reshape(1, -1)   # shape (1, 150)
                ultimo_stats = scaler.transform(stats_antigo)[0]       # shape (150,)

                similaridades = []
                for id_conhecido, vetor_conhecido in zip(db.todos_jogadores_com_stats(id_antigo), dados_historicos):
                    sim = 1 - cosine(ultimo_stats, vetor_conhecido)
                    similaridades.append((id_conhecido, sim))

                best_match, score = max(similaridades, key = lambda x: x[1])

                # Se sair do clã e mudar de nome logo em seguida, cai aqui.
                if score < 0.85: 
                    db.arquivar_jogador(id)
                    saidas.append(nome)
                    print(f"Jogador ({id} '{nome}') deletado do Clã por ter saído.")

                novo_id, novo_nome = best_match
                sim = f'{(score * 100):.2f}%'

                db.unir_registros(id_antigo, novo_id)
                novos_nomes.append((nome, novo_nome, sim))
                print(f"({id_antigo} '{nome}') trocou para ({novo_id} '{novo_nome}') com similaridade: {sim}")
            except Exception as e:
                print(f'Erro atualizando {nome} para novo nome: {e}')
        db.fechar()

        if not enviar_relatorio:
            return
        
        if saidas or novos_nomes:
            embed = Embed(
                title = f"Relatório de jogadores",
                description = 'Lista de quem saiu e/ou trocou de nome.',
                color = Color.blue()
            )

            for cabecinha in saidas:
                embed.add_field(
                    name = cabecinha,
                    value = 'Saiu do clã.', 
                    inline = False
                )
            for nome_antigo, nome_novo, sim in novos_nomes:
                embed.add_field(
                    name = nome_antigo, 
                    value = f'Trocou de nome para `{nome_novo}`.', 
                    inline = False
                )

            await canal.send(embed = embed)

    @staticmethod
    async def iniciar(bot):
        # 'DKDW/Moderação' ou disc de testes.
        moderacao = bot.get_channel(1211472248326856724) or bot.get_channel(1123305689574539285)

        while True:
            agora = datetime.now()

            # Improvável que alguém upe muito/mude de nome de madrugada.
            if agora.time() <= time(9):
                segundos = Coleta._tempo_para_nove_horas()
                print(f'Dormindo {segundos} até as 9 da matina.')
                await sleep(segundos)
                
            print('Coletando cabecinhas...')
            await Coleta()._coletar_cabecinhas()

            print('Atualizando stats...')
            await Coleta()._atualizar_stats()
 
            print('Verificando nomes alterados...')
            await Coleta()._verificar_alterados(bot.dkdw.enviar_relatorio, moderacao)
                
            HORAS = 3
            print(f'Dormindo por {HORAS} horas.')
            await sleep(HORAS * 3600)