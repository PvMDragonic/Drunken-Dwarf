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
from dados.utils import formatar_xp

class Coleta():
    @staticmethod
    def _tempo_para_nove_horas():
        agora = datetime.now()
        nove_horas = agora.replace(hour = 9)
        diferenca = nove_horas - agora
        return diferenca.total_seconds()
    
    @staticmethod
    async def _coletar_cabecinhas() -> list:
        """
        Coleta e armazena os membros do clã e retorna\n
        aqueles que apareceram desde a última vez.
        """

        cabecinhas = await Coleta()._listar_membros_cla(completo = True)
        if cabecinhas is None:
            return 
        
        db = Database()
        hoje = datetime.today().strftime('%Y-%m-%d')
        cabecinhas_registradas = db.todos_jogadores(incluir_inativos = True)
        entradas = []
        novos_nomes = []

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
            id = (db.jogador_registrado(nome) or db.registrar_jogador(nome, hoje))[0]

            # Nome novo que não estava registrado até então.
            if not any(nome in entrada for entrada in cabecinhas_registradas):
                nomes_passados = db.buscar_todos_nomes(id)
                nome_recente = nomes_passados[-1]

                # Se for alguém completamente novo, sempre vai ter só 1 nome;
                # se tem mais de um é porque a pessoa voltou pra um passado.
                if len(nomes_passados) > 1:
                    db.adicionar_nome(id, nome, hoje)
                    novos_nomes.append((nome_recente, nome))
                    print(f"({id} '{nome_recente}') voltou para o nome '{nome}'.")
                else:
                    entradas.append(nome)
                    print(f"({id} '{nome_recente}') entrou para o clã.")

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
        return entradas, novos_nomes
            
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
                        db.atualizar_gratuito(True, nome) # Marca como gratuito.
                        continue
                    
                    db.atualizar_gratuito(False, nome) # Marca como membro.

                    stats_formatados = re.split(r'[,\n]+', stats)[0:-1]

                    usuario = db.jogador_registrado(nome)
                    if usuario:
                        db.adicionar_estatisticas(usuario[0], stats_formatados)
                except Exception as e:
                    print(f"Erro atualizando dados de {nome}: {e}")
        db.fechar()

    @staticmethod
    async def _verificar_alterados() -> list:
        """
        Verifica e trata nomes registrados que não estão mais no clã\n
        e retorna uma lista com quem saiu e outra com quem trocou de nome.
        """

        def limite_similaridade(nivel_total: int):
            """
            Retorna um valor entre 0.999 e 0.900 dependendo do nível total do jogador sendo comparado.\n

            Contas de nível mais baixo tendem a ter um grau maior de similaridade,
            enquanto contas mais desenvolvidas possuem mais distinções de uma para a outra.
            """

            val_minimo = 0.999  # 99,9% similar
            val_maximo = 0.950  # 95,0% similar
            nivel_total_limite = 3000.0 
            exponente = 3.5 
            x_normalizado = min(max(nivel_total, 0), nivel_total_limite) / nivel_total_limite
            valor_curva = x_normalizado ** exponente
            return val_minimo + (val_maximo - val_minimo) * valor_curva

        db = Database()
        cabecinhas_registradas = db.todos_jogadores(incluir_inativos = True)
        cabecinhas_atuais = await Coleta()._listar_membros_cla()

        if not cabecinhas_atuais:
            db.fechar()
            return [], []

        # Registrados que não estão mais no clã.
        desaparecidos = [(id, nome) for id, nome in cabecinhas_registradas if nome not in cabecinhas_atuais]

        hoje = datetime.now().date()
        novos_nomes = []
        saidas = []

        for id, nome in desaparecidos:
            try:
                jogador_ativo = (db.jogador_registrado(nome, True))[2]

                # Se o usuário já está desativado, não precisa verificar se ele saiu do clã.
                if jogador_ativo:
                    runemetrics = await Fetch().json(f"https://apps.runescape.com/runemetrics/profile/profile?user={nome.replace(' ', '+')}&activities=1")
                    if runemetrics.get('error') != 'NO_PROFILE': # Se não for NO_PROFILE, é porque saiu do clã.
                        db.arquivar_jogador(id, hoje)
                        saidas.append((db.buscar_xp(id), nome))
                        print(f"Jogador ({id} '{nome}') saiu do clã.")
                        continue

                stats_jogador = db.buscar_estatisticas(id)
                if stats_jogador is None:
                    # Nunca foi Membro enquanto membro do clã, então não está nos hi-scores para ter stats.
                    print(f"Jogador ({id} '{nome}') gratuio e sem estatísticas registradas.")
                    continue

                scaler = StandardScaler()     
                cabecinhas_stats = np.array(db.buscar_todas_estatisticas(id))
                scaler.fit(cabecinhas_stats)
                dados_historicos = scaler.transform(cabecinhas_stats)

                stats_antigo = np.array(stats_jogador).reshape(1, -1)   # shape (1, 152)
                ultimo_stats = scaler.transform(stats_antigo)[0]        # shape (152,)

                similaridades = []
                for id_conhecido, vetor_conhecido in zip(db.todos_jogadores_com_stats(id), dados_historicos):
                    sim = 1 - cosine(ultimo_stats, vetor_conhecido)
                    similaridades.append((id_conhecido, sim))

                best_match, score = max(similaridades, key = lambda x: x[1])

                # Se sair do clã e mudar de nome logo em seguida, cai aqui.
                if score < limite_similaridade(stats_jogador[1]):
                    if jogador_ativo:
                        db.arquivar_jogador(id, hoje)
                        saidas.append((db.buscar_xp(id), nome))
                        print(f"Jogador ({id} '{nome}') saiu do clã.")
                    continue

                novo_id, novo_nome = best_match
                sim = f'{(score * 100):.2f}%'

                db.unir_registros(id, novo_id, jogador_ativo)
                novos_nomes.append((nome, novo_nome))
                print(f"({id} '{nome}') trocou para ({novo_id} '{novo_nome}') com similaridade: {sim}")
            except Exception as e:
                print(f'Erro atualizando {nome} para novo nome: {e}')

        db.fechar()
        return [saidas, novos_nomes]

    @staticmethod
    async def _enviar_relatorio(enviar_relatorio: bool, canal: TextChannel, relatorios: list):
        if not enviar_relatorio:
            return
    
        entradas, saidas, novos_nomes = relatorios

        entradas = [
            nome for nome in entradas if 
            not any(nome in entrada for entrada in saidas) and
            not any(nome in entrada for entrada in novos_nomes)
        ]
        
        if entradas or saidas or novos_nomes:
            embed = Embed(
                title = f"Relatório de entradas, saídas & nomes",
                color = Color.blue()
            )

            todos_relatorios = []

            for cabecinha in entradas:
                todos_relatorios.append((cabecinha, 'Entrou no clã.'))

            for xp, cabecinha in saidas:
                todos_relatorios.append((cabecinha, f'Saiu do clã com {formatar_xp(xp)} de XP.'))

            for nome_antigo, nome_novo in novos_nomes:
                todos_relatorios.append((nome_antigo, f'Trocou de nome para `{nome_novo}`.'))

            for name, value in todos_relatorios[:25]:
                embed.add_field(name = name, value = value, inline = False)

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
            entradas, novos_nomes1 = await Coleta()._coletar_cabecinhas()

            print('Atualizando stats...')
            await Coleta()._atualizar_stats()
 
            print('Verificando nomes alterados...')
            saidas, novos_nomes2 = await Coleta()._verificar_alterados()

            await Coleta()._enviar_relatorio(
                bot.dkdw.enviar_relatorio, 
                moderacao,
                [entradas, saidas, novos_nomes1 + novos_nomes2]
            )
                
            HORAS = 3
            print(f'Dormindo por {HORAS} horas.')
            await sleep(HORAS * 3600)
