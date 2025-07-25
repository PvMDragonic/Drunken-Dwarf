from table2ascii import table2ascii as t2a, PresetStyle, Alignment
from datetime import datetime, date
from discord.ext import commands
from discord.ui import View
import discord

from dados.database import Database
from dados.utils import formatar_xp, formatar_dia

class GratuitosPaginator(View):
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

    def __init__(self, gratuitos):
        super().__init__(timeout = None)
        self.gratuitos = gratuitos
        self.pag_atual = 0
        self.pag_quantia = 10
        self.pag_total = (len(gratuitos) - 1) // 10 + 1

        self.modo_ordenar = 2 # Padrão é ordem por XP.
        self.crescente = True
        
        # Ordena por XP como fallback caso tenha dois valores iguais.
        self.modos_ordenar = (
            ("Ordem: Nome", lambda inativo: (inativo[0], inativo[2])),   
            ("Ordem: Rank", lambda inativo: (self.ORDEM_RANKS.get(inativo[2], 999), inativo[1])),  
            ("Ordem: XP", lambda inativo: (inativo[1], inativo[2])),
        )

    def carregar_tabela(self):
        comeco = self.pag_atual * self.pag_quantia
        fim = comeco + self.pag_quantia

        gratuitos = [(
            nome, 
            formatar_xp(xp),
            rank, 
            formatar_dia(data)
        ) for nome, xp, data, rank in self.gratuitos[comeco:fim]]

        tabela = t2a(
            header = ["Nome", "XP", "Rank", "Inativo"],
            body = gratuitos,
            style = PresetStyle.ascii_box,
            alignments = Alignment.LEFT,
        )
        return f"```{tabela}```"

    def criar_embed(self):
        return discord.Embed(
            title = f"Jogadores gratuitos ({self.pag_atual + 1}/{self.pag_total})",
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

    @discord.ui.button(label = "Ordem: XP", style = discord.ButtonStyle.secondary)
    async def ordenar(self, interacao: discord.Interaction, botao: discord.ui.Button):
        self.modo_ordenar = (self.modo_ordenar + 1) % len(self.modos_ordenar)
        botao.label = self.modos_ordenar[self.modo_ordenar][0]

        self.gratuitos.sort(
            key = self.modos_ordenar[self.modo_ordenar][1], 
            reverse = not self.crescente
        )

        await interacao.response.edit_message(embed = self.criar_embed(), view = self)

    @discord.ui.button(label = "Decrescente", style = discord.ButtonStyle.secondary)
    async def direcao(self, interacao: discord.Interaction, botao: discord.ui.Button):
        self.crescente = not self.crescente
        botao.label = 'Crescente' if self.crescente else 'Decrescente'

        self.gratuitos.sort(
            key = self.modos_ordenar[self.modo_ordenar][1], 
            reverse = not self.crescente
        )
        
        await interacao.response.edit_message(embed = self.criar_embed(), view = self)

class Gratuitos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def gratuitos(self, ctx):
        db = Database()
        gratuitos = db.buscar_gratuitos()
        db.fechar()

        if len(gratuitos) >= 1:
            gratuitos.sort(key = lambda inativo: inativo[1], reverse = True)
            paginator = GratuitosPaginator(gratuitos)
            await paginator.msg_inicial(ctx)
        else:
            await ctx.send(embed = discord.Embed(
                title = f"Jogadores gratuitos",
                description = 'Nenhum jogador gratuito no clã!',
                color = discord.Color.blue()
            ))

async def setup(bot):
    await bot.add_cog(Gratuitos(bot))