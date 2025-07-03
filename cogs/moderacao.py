from discord.ext import commands
from random import randint
from datetime import datetime
import discord
import asyncio

from dados.database import Database

class Moderacao(commands.Cog):
    """Cog responsável por comandos da Moderação/Staff."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def cmd(self, ctx):
        embed = discord.Embed(
            title = "LISTA DE COMANDOS",  
            color = 0x7a8ff5
        )

        embed.add_field(
            name = '!inativos [dias]', 
            value = 'Lista membros do clã inativos há x dias.\n᲼᲼', 
            inline = False
        )

        embed.add_field(
            name = '!historico [pessoa]', 
            value = 'Lista o histórico de nomes conhecidos de [pessoa].\n᲼᲼', 
            inline = False
        )

        embed.add_field(
            name = '!sortear [valor mínimo] [valor máximo]', 
            value = 'Soteia um número entre X e Y.\n᲼᲼', 
            inline = False
        )

        embed.add_field(
            name = '!limpar [quantia] [nome/marcação]', 
            value = 'Limpa X número de mensagens.\nO nome/marcação é opcional para limpar apenas de alguém específico.\n᲼᲼', 
            inline = False
        )

        embed.add_field(
            name = '!ativar [opção]', 
            value = 'Ativa (ou desativa, se já estiver ativado) mensagem de boas-vindas/despedida.\nOpção 1 para boas-vindas; 2 para despedida.\n᲼᲼', 
            inline = False
        )

        embed.add_field(
            name = '!mensagem [mensagem] [opção]', 
            value = 'Define uma nova mensagem de boas-vindas.\nUse "{}" para definir onde a menção vai ficar.\nOpção 1 para boas-vindas; 2 para despedida.\n᲼᲼', 
            inline = False
        )

        embed.add_field(
            name = '!teste [opção]', 
            value = 'Testa a mensagem de boas-vindas.\nOpção 1 para boas-vindas; 2 para despedida.᲼᲼', 
            inline = False
        )

        embed.add_field(
            name = '!relatórios', 
            value = 'Ativa ou desativa (inverte) o envio de relatórios\nde quando alguém sai do clã ou muda de nome.', 
            inline = False
        )

        embed.set_thumbnail(url = self.bot.user.avatar)

        await ctx.channel.send(
            ctx.message.author.mention, 
            embed = embed
        )

    @commands.command(name = 'historico', aliases = ['histórico'])
    async def historico(self, ctx: commands.Context, *args):
        if len(args) == 0:
            return await ctx.send(f'Você precisa informar o nome de quem você quer saber o histórico! {ctx.author.mention}')
        
        db = Database()
        nome = ' '.join(args)
        historico = db.buscar_historico_nomes(nome)
        db.fechar()

        if historico:
            embed = discord.Embed(
                title = f"Histórico de nomes de {nome}:",
                color = discord.Color.blue()
            )
            for nick, data in historico: 
                data_formatada = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
                embed.add_field(
                    name = nick, 
                    value = f'Alterado em **{data_formatada}**',
                    inline = False
                )
            await ctx.send(embed = embed)
        else:
            await ctx.send(f'Não há histórico para "{nome}"! {ctx.author.mention}')

    @commands.command()
    async def limpar(self, ctx, quantia: int, *user):    
        quantia = int(quantia)

        if user:
            if user[0].startswith('<@'):
                usuario = int(user[0][2:-1])
            else:
                usuario = discord.utils.get(ctx.guild.members, nick = " ".join(user)) or discord.utils.get(ctx.guild.members, global_name = " ".join(user))
                usuario = usuario.id

            deletados = 0

            def deletar_msg(message):
                nonlocal deletados

                if deletados >= quantia:
                    return False

                if message.author.id != usuario:
                    return False
                
                deletados += 1
                return True

            await ctx.channel.purge(limit = 1) # Limpa o comando de limpar.
            await ctx.channel.purge(limit = 100, check = deletar_msg)
            await ctx.channel.send(f'{deletados} mensagen(s) deletada(s) com sucesso!')
        else:
            await ctx.channel.purge(limit = quantia + 1)
            await ctx.channel.send(f'{quantia} mensagen(s) deletada(s) com sucesso!')

        await asyncio.sleep(5)
        await ctx.channel.purge(
            limit = 5, 
            check = lambda message: message.author.id == self.bot.user.id
        ) 

    @commands.command()
    async def sortear(self, ctx, *args):
        embed = discord.Embed(
            title = "SORTEIO DRUNKEN DWARF", 
            description = f"O número sorteado foi: **{randint(int(args[0]), int(args[1]))}**\n\n__**Parabéns!**__", 
            color = 0x7a8ff5)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text=f"DKDW • {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        await ctx.message.channel.send(embed = embed)

    @commands.command()
    async def ativar(self, ctx, opc: str):
        if opc not in ('1', '2'):
            return await ctx.channel.send(
                f'Digite 1 para boas-vindas ou 2 para despedida! {ctx.message.author.mention}'
            )
        
        if opc == '1':
            self.bot.enviar_boas_vindas = not self.bot.dkdw.enviar_boas_vindas
            self.bot.dkdw.salvar_dados()
            await ctx.channel.send(
                f'Mensagem de boas-vindas __{"ativada" if self.bot.dkdw.enviar_boas_vindas else "desativada"}__! {ctx.message.author.mention}'
            )
        else:
            self.bot.dkdw.enviar_despedida = not self.bot.dkdw.enviar_despedida
            self.bot.dkdw.salvar_dados()
            msg = "ativada" if self.bot.dkdw.enviar_despedida else "desativada"
            await ctx.channel.send(
                f'Mensagem de despedida __{msg}__! {ctx.message.author.mention}'
            )

    @commands.command()
    async def teste(self, ctx, opc: str):
        if opc not in ('1', '2'):
            return await ctx.channel.send(
                f'Digite 1 para boas-vindas ou 2 para despedida! {ctx.message.author.mention}'
            )
        
        if opc == '1':
            await ctx.channel.send(self.bot.dkdw.boas_vindas(ctx.message.author.mention))
        else:
            await ctx.channel.send(self.bot.dkdw.despedida(ctx.message.author.mention))

    @commands.command()
    async def mensagem(self, ctx, opc: str):
        if opc not in ('1', '2'):
            return await ctx.channel.send(
                f'Digite 1 para boas-vindas ou 2 para despedida! {ctx.message.author.mention}'
            )

        # Remove o comando da mensagem.
        mensagem = " ".join(ctx.message.content.split(" ")[1:])

        if opc == '1':
            self.bot.dkdw.msg_bem_vindos = mensagem
            self.bot.dkdw.salvar_dados()
            await ctx.channel.send(
                f'Uma nova mensagem de boas-vindas foi definida! Use `!teste 1` para ver como ficou. {ctx.message.author.mention}'
            )
        else:
            self.bot.dkdw.msg_despedida = mensagem
            self.bot.dkdw.salvar_dados()
            await ctx.channel.send(
                f'Uma nova mensagem de despedida foi definida! Use `!teste 2` para ver como ficou. {ctx.message.author.mention}'
            )

    @commands.command(name = 'relatorios', aliases = ['relatórios'])
    async def relatorios(self, ctx: commands.Context):
        self.bot.dkdw.enviar_relatorio = not self.bot.dkdw.enviar_relatorio
        self.bot.dkdw.salvar_dados()
        await ctx.channel.send(
                f"Relatórios de saídas e/ou mudanças de nome **{'ativadas' if self.bot.dkdw.enviar_relatorio else 'desativadas'}**! {ctx.message.author.mention}"
            )

async def setup(bot):
    await bot.add_cog(Moderacao(bot))