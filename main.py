from discord.ext.commands.errors import MissingRequiredArgument, BadArgument
from discord.ext.commands import CommandNotFound
from discord.ext import commands
import discord

from dados.coleta_xp import Coleta
from dados.dkdw import DKDW

class DrunkenDwarf(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix = '!', 
            intents = intents
        )

        self.dkdw = DKDW()

    async def setup_hook(self):
        extensions = (
            'cogs.autenticacao',
            'cogs.moderacao',
            'cogs.diversos',
            'cogs.inativos'
        )

        for ext in extensions:
            await self.load_extension(ext)

    async def on_command_error(self, ctx, error):
        if isinstance(error, CommandNotFound):
            return
        if isinstance(error, MissingRequiredArgument):
            await ctx.channel.send(
                f'Você esqueceu de especificar um ou mais parâmetros para o comando! {ctx.message.author.mention}'
            )
        if isinstance(error, BadArgument):
            await ctx.channel.send(
                f'Você precisa especificar uma quantia válida para as mensagens! {ctx.message.author.mention}'
            )
        raise error

    async def on_guild_join(self, guild):
        if guild.id != 296764515335405570:
            print(f'Saindo de servidor não-autorizado: {guild.name} ({guild.id})')
            await guild.leave()

    async def on_member_join(self, member):
        if self.dkdw.enviar_boas_vindas:
            await self.get_guild(296764515335405570).get_channel(589600587742707732).send(
                self.dkdw.boas_vindas(member.mention)
            )

    async def on_member_remove(self, member):
        if self.dkdw.enviar_despedida:
            await self.get_guild(296764515335405570).get_channel(589600587742707732).send(
                self.dkdw.despedida(member.name)
            )

    async def on_ready(self):
        await self.change_presence(activity = discord.Game(name = 'no melhor clã BR'))
        print(f'>> {self.user} on-line!')

        # Coletar dados do povo do clã.
        await Coleta().iniciar()

    async def on_message(self, message):
        if '@everyone' in message.content or '@here' in message.content:
            cargos_id = [role.id for role in message.author.roles]
            cargos_encontrados = [role_id for role_id in cargos_id if role_id in (
                296779510089777152, # 'Moderador
                296780203940904960, # 'Staff'
                296780473236193280  # 'BOTS'
            )]

            if cargos_encontrados:
                return

            links_encontrados = [ele for ele in ["https://", "http://"] if ele in message.content]
            if not links_encontrados:
                return 
            
            await message.delete()

            # DKDW/moderação
            return await self.get_channel(1211472248326856724).send(
                f'{message.author.mention} tentou enviar spam no canal {message.channel.mention}.'
            )
                
        if message.author.bot:
            return

        if message.channel.id == 866475904905773056: # DKDW/caixa-de-sugestões
            return await self.get_cog('Diversos').enviar_sugestao(message)

        if message.channel.id == 589600587742707732: # DKDW/bem-vindos
            return await self.get_cog('Autenticacao').adicionar_cargo(message)
        
        if message.channel.id == 811639954442420235: # DKDW/drops-e-conquistas
            return await self.get_cog('Diversos').enviar_gratz(message)

        if not message.author.guild_permissions.administrator:
            return

        await self.process_commands(message)

    def run(self):
        super().run(self.dkdw.token)

if __name__ == '__main__':
    DrunkenDwarf().run()