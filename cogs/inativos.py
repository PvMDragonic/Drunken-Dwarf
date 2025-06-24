from table2ascii import table2ascii as t2a, PresetStyle, Alignment
from datetime import datetime
from discord.ext import commands
from discord.ui import View
import discord

from dados.database import Database

class InativosPaginator(View):
    def __init__(self, inativos, filtro_tempo):
        super().__init__(timeout = None)
        self.filtro = filtro_tempo
        self.inativos = inativos
        self.pag_atual = 0
        self.pag_quantia = 10
        self.pag_total = (len(inativos) - 1) // 10 + 1

    def carregar_tabela(self):
        comeco = self.pag_atual * self.pag_quantia
        end = comeco + self.pag_quantia
        pagina = self.inativos[comeco:end]

        tabela = t2a(
            header = ["Nome", "Rank", "XP", "Inativo"],
            body = pagina,
            style = PresetStyle.ascii_box,
            alignments = Alignment.LEFT,
        )
        return f"```{tabela}```"

    def atualizar_btns(self):
        self.anterior.disabled = self.pag_atual == 0
        self.proximo.disabled = self.pag_atual >= self.pag_total - 1

    async def msg_inicial(self, ctx: commands.Context):
        embed = discord.Embed(
            title = f"Jogadores inativos há {self.filtro} ({self.pag_atual + 1}/{self.pag_total})",
            description = self.carregar_tabela(),
            color = discord.Color.blue()
        )
        self.atualizar_btns()
        await ctx.send(embed = embed, view = self)

    @discord.ui.button(label = "Anterior", style = discord.ButtonStyle.primary, disabled = True)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pag_atual -= 1
        embed = discord.Embed(
            title = f"Jogadores inativos há {self.filtro} ({self.pag_atual + 1}/{self.pag_total})",
            description = self.carregar_tabela(),
            color = discord.Color.blue()
        )
        self.atualizar_btns()
        await interaction.response.edit_message(embed = embed, view = self)

    @discord.ui.button(label = "Próximo", style = discord.ButtonStyle.primary)
    async def proximo(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pag_atual += 1
        embed = discord.Embed(
            title = f"Jogadores inativos há {self.filtro} ({self.pag_atual + 1}/{self.pag_total})",
            description = self.carregar_tabela(),
            color = discord.Color.blue()
        )
        self.atualizar_btns()
        await interaction.response.edit_message(embed = embed, view=self)


class Inativos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def _formatar_xp(xp: int):
        virgulas = f'{xp:,}'
        separado = virgulas.split(',')

        if len(separado) == 2: # 2 vírgulas (100,000)
            ultimo_digito = separado[1][0]
            formatado = f'{separado[0]}.{ultimo_digito}K' if ultimo_digito != '0' else f'{separado[0]}K'
            return formatado
        elif len(separado) == 3: # 3 vírgulas (100,000,000)
            ultimo_digito = separado[1][0]
            formatado = f'{separado[0]}.{ultimo_digito}M' if ultimo_digito != '0' else f'{separado[0]}M'
            return formatado
        elif len(separado) == 4: # 4 vírgulas (100,000,000,000)
            return f'{separado[0]}.{separado[1]}B'

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
                inativos.append((
                    nome, 
                    rank, 
                    Inativos._formatar_xp(xp), 
                    f'{tempo_inativo} dia(s)'
                ))

        filtro_tempo = f"{filtro_tempo} dia{'s' if filtro_tempo != 1 else ''}"

        if len(inativos) >= 1:
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