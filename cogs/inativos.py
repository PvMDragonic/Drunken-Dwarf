from table2ascii import table2ascii as t2a, PresetStyle, Alignment
from datetime import datetime
from discord.ext import commands
from discord.ui import View
import discord

from dados.database import Database

class InativosPaginator(View):
    ORDEM_RANKS = {
        'Dono': 0,
        'Vice-Dono': 1,
        'Fiscal': 2,
        'Coord.': 3,
        'Org.': 4,
        'Admin.': 5,
        'General': 6,
        'Capitão': 7,
        'Tenente': 8,
        'Sargento': 9,
        'Cabo': 10,
        'Recruta': 11
    }

    def __init__(self, inativos, filtro_tempo):
        super().__init__(timeout = None)
        self.filtro = filtro_tempo
        self.inativos = inativos
        self.pag_atual = 0
        self.pag_quantia = 10
        self.pag_total = (len(inativos) - 1) // 10 + 1

        self.modo_ordenar = 3 # Padrão é ordem por tempo de inatividade.
        self.crescente = True
        
        # Ordena por XP como fallback caso tenha dois valores iguais.
        self.modos_ordenar = (
            ("Ordem: Nome", lambda inativo: (inativo[0], inativo[2])),   
            ("Ordem: Rank", lambda inativo: (self.ORDEM_RANKS.get(inativo[1], 999), inativo[2])),  
            ("Ordem: XP", lambda inativo: (inativo[2], inativo[3])),
            ("Ordem: Tempo", lambda inativo: (inativo[3], inativo[2])),
        )

    @staticmethod
    def formatar_xp(xp: int):
        if xp == 0:
            return "Zero"
        
        virgulas = f'{xp:,}'
        separado = virgulas.split(',')

        # 1 vírgula (100,000)
        if len(separado) == 2: 
            ultimo_digito = separado[1][0]
            if ultimo_digito != '0':
                return f'{separado[0]}.{ultimo_digito}K'
            return f'{separado[0]}K'
        
        # 2 vírgulas (100,000,000)
        if len(separado) == 3: 
            ultimo_digito = separado[1][0]
            if ultimo_digito != '0':
                return f'{separado[0]}.{ultimo_digito}M'
            return f'{separado[0]}M'
        
        # 3 vírgulas (100,000,000,000)
        if len(separado) == 4: 
            return f'{separado[0]}.{separado[1]}B'
        
    @staticmethod
    def formatar_dia(dias: int):
        unidade = "dia" if dias == 1 else "dias"
        return f"{dias} {unidade}"

    def carregar_tabela(self):
        comeco = self.pag_atual * self.pag_quantia
        fim = comeco + self.pag_quantia
        pagina = [(
            nome, 
            rank, 
            InativosPaginator.formatar_xp(xp), 
            InativosPaginator.formatar_dia(inativo)
        ) for nome, rank, xp, inativo in self.inativos[comeco:fim]]

        tabela = t2a(
            header = ["Nome", "Rank", "XP", "Inativo"],
            body = pagina,
            style = PresetStyle.ascii_box,
            alignments = Alignment.LEFT,
        )
        return f"```{tabela}```"

    def criar_embed(self):
        return discord.Embed(
            title = f"Jogadores inativos há {self.filtro} ({self.pag_atual + 1}/{self.pag_total})",
            description = self.carregar_tabela(),
            color = discord.Color.blue()
        )

    async def msg_inicial(self, ctx: commands.Context):
        await ctx.send(embed = self.criar_embed(), view = self)

    @discord.ui.button(label = "Anterior", style = discord.ButtonStyle.primary)
    async def anterior(self, interacao: discord.Interaction, _):
        self.pag_atual = (self.pag_atual - 1) % self.pag_total
        await interacao.response.edit_message(embed = self.criar_embed(), view = self)

    @discord.ui.button(label = "Próximo", style = discord.ButtonStyle.primary)
    async def proximo(self, interacao: discord.Interaction, _):
        self.pag_atual = (self.pag_atual + 1) % self.pag_total
        await interacao.response.edit_message(embed = self.criar_embed(), view = self)

    @discord.ui.button(label = "Ordem: Tempo", style = discord.ButtonStyle.secondary)
    async def ordenar(self, interacao: discord.Interaction, botao: discord.ui.Button):
        self.modo_ordenar = (self.modo_ordenar + 1) % len(self.modos_ordenar)
        botao.label = self.modos_ordenar[self.modo_ordenar][0]

        self.inativos.sort(
            key = self.modos_ordenar[self.modo_ordenar][1], 
            reverse = self.crescente
        )

        await interacao.response.edit_message(embed = self.criar_embed(), view = self)

    @discord.ui.button(label = "Decrescente", style = discord.ButtonStyle.secondary)
    async def direcao(self, interacao: discord.Interaction, botao: discord.ui.Button):
        self.crescente = not self.crescente
        botao.label = 'Crescente' if self.crescente else 'Decrescente'

        self.inativos.sort(
            key = self.modos_ordenar[self.modo_ordenar][1], 
            reverse = self.crescente
        )
        
        await interacao.response.edit_message(embed = self.criar_embed(), view = self)

class Inativos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def inativos(self, ctx, *args):
        hoje = datetime.now().date()
        db = Database()
        membros = db.get_all_users()

        try:
            filtro_tempo = int(args[0])
        except (ValueError, IndexError):
            filtro_tempo = 1

        EXCLUIDOS = (
            'Org.', 'Coord.', 'Fiscal', 'Vice-Dono', 'Dono'
        )

        inativos = []
        for id, nome in membros:
            xp, xp_data, rank = db.get_last_xp(id)
            xp_data = datetime.strptime(xp_data, '%Y-%m-%d').date()
            tempo_inativo = (hoje - xp_data).days 

            # 1 dia inativo pode ser porque rodou antes da coleta diária.
            if tempo_inativo >= filtro_tempo and rank not in EXCLUIDOS: 
                inativos.append((nome, rank, xp, tempo_inativo))

        filtro_tempo = f"{filtro_tempo} dia{'s' if filtro_tempo != 1 else ''}"

        if len(inativos) >= 1:
            # Por padrão ordena pelo tempo de inatividade decrescente e depois por XP.
            inativos.sort(
                key = lambda inativo: (inativo[3], inativo[2]), 
                reverse = True
            )

            paginator = InativosPaginator(inativos, filtro_tempo)
            await paginator.msg_inicial(ctx)
        else:
            await ctx.send(embed = discord.Embed(
                title = f"Jogadores inativos há {filtro_tempo}",
                description = 'Nenhum inativo dentro do período especificado!',
                color = discord.Color.blue()
            ))

async def setup(bot):
    await bot.add_cog(Inativos(bot))