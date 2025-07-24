from datetime import datetime
from discord.ext import commands
from discord.ui import View
import discord

from dados.database import Database
from dados.utils import formatar_xp

def formatar_mudancas(mudancas: list[str]) -> str:
    texto_embed = []
    for nick, nick_anterior, xp, tipo, data in mudancas: 
        data_formatada = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
        if tipo == 'nome':
            if nick_anterior == None:
                continue
            texto_embed.append(f"`{nick_anterior}` → `{nick}` ({data_formatada})")
        elif tipo == 'entrou':
            texto_embed.append(f"`Entrou no clã` ({data_formatada})")
        elif tipo == 'saiu':
            texto_embed.append(f"`Saiu do clã ({formatar_xp(xp)} XP)` ({data_formatada})")
    return '\n'.join(texto_embed)

class HistoricoPaginator(View):
    def __init__(self, historico, titulo):
        super().__init__(timeout = None)
        self.titulo = titulo
        self.historico = historico
        self.pag_atual = 0
        self.pag_quantia = 10
        self.pag_total = (len(historico) - 1) // 10 + 1

    def criar_embed(self):
        embed = discord.Embed(
            title = f"Histórico {self.titulo} ({self.pag_atual + 1}/{self.pag_total})",
            color = discord.Color.blue()
        )

        comeco = self.pag_atual * self.pag_quantia
        fim = comeco + self.pag_quantia
        
        for _, mudancas in list(self.historico.items())[comeco:fim]:
            embed.add_field(
                name = mudancas[0][1] or mudancas[0][0], # Nome antigo ou nome atual.
                value = formatar_mudancas(mudancas),
                inline = False
            )

        return embed

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

class Historico(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name = 'historico', aliases = ['histórico'])
    async def historico(self, ctx: commands.Context, *args):
        if len(args) == 0:
            return await ctx.send(f'Espeficique um número ou nome específico de um jogador! {ctx.author.mention}')
        
        db = Database()
         
        dias = args[0]
        if len(args) == 1 and dias.isdigit():
            titulo = f"{'de' if dias == 1 else 'dos'} {'últimos ' if dias != 1 else ''}{dias} {'dia atrás' if dias == 1 else 'dias'}"

            embed = discord.Embed(
                title = f"Histórico {titulo}",
                color = discord.Color.blue()
            )

            historico = db.historico_geral(dias)
            if not historico:
                return await ctx.send(f'Algo deu errado! Tente novamente mais tarde. {ctx.author.mention}')

            if len(historico) <= 10:
                for _, mudancas in historico.items():
                    embed.add_field(
                        name = mudancas[0][1] or mudancas[0][0], # Nome antigo ou nome atual.
                        value = formatar_mudancas(mudancas),
                        inline = False
                    )
                return await ctx.send(embed = embed)
            
            paginator = HistoricoPaginator(historico, titulo)
            await paginator.msg_inicial(ctx)
        else:
            nome = ' '.join(args)
            historico = db.buscar_historico_jogador(nome)
            db.fechar()

            if historico:
                description = []
                for nick, nick_anterior, xp, tipo, data in historico: 
                    data_formatada = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
                    if tipo == 'nome':
                        if nick_anterior == None:
                            continue
                        description.append(f"`{nick_anterior}` → `{nick}` ({data_formatada})")
                    elif tipo == 'entrou':
                        description.append(f"`Entrou no clã` ({data_formatada})")
                    elif tipo == 'saiu':
                        description.append(f"`Saiu do clã ({formatar_xp(xp)} XP)` ({data_formatada})")
                    
                await ctx.send(embed = discord.Embed(
                    title = f"Histórico de __{nome}__:",
                    description = '\n'.join(description),
                    color = discord.Color.blue()
                ))
            else:
                await ctx.send(f'Não há histórico para "{nome}"! {ctx.author.mention}')

async def setup(bot):
    await bot.add_cog(Historico(bot))