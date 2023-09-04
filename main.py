from discord.ext.commands.errors import MissingRequiredArgument, BadArgument
from discord.ext.commands import CommandNotFound
from discord.ext import commands
from random import randint
import datetime
import asyncio
import discord
import nomes

TOKEN = open('token.txt', 'r').readline().rstrip()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents = intents)

try:
    with open('dkdw.txt', "r") as arqv:
        msg_bem_vindos = "".join(arqv.readlines())
except FileNotFoundError:
    print("Arquivo 'dkdw.txt' não encontrado!")
    msg_bem_vindos = "Seja bem-vindo(a) {}!"

@bot.command()
async def teste(ctx):
    await ctx.channel.send(msg_bem_vindos.replace("{}", ctx.message.author.mention))

@bot.command()
async def mensagem(ctx):
    global msg_bem_vindos

    # Remove o comando da mensagem.
    msg_bem_vindos = " ".join(ctx.message.content.split(" ")[1:])

    with open('dkdw.txt', "w") as arqv:
        arqv.write(msg_bem_vindos)

    await ctx.channel.send(
        f'Uma nova mensagem de boas-vindas foi definida! Use `!teste` para ver como ficou. {ctx.message.author.mention}'
    )

@bot.command()
async def cmd(ctx):
    embed = discord.Embed(
        title = "LISTA DE COMANDOS",  
        color = 0x7a8ff5
    )

    embed.add_field(
        name = '!sortear [valor mínimo] [valor máximo]', 
        value = 'Soteia um número entre X e Y.\n᲼᲼', 
        inline = False
    )

    embed.add_field(
        name = '!limpar [quantia] [nome]', 
        value = 'Limpa X número de mensagens.\nO nome é opcional para limpar apenas de alguém específico.\n᲼᲼', 
        inline = False
    )

    embed.add_field(
        name = '!mensagem [mensagem]', 
        value = 'Define uma nova mensagem de boas-vindas.\nUse "{}" para definir onde a menção vai ficar.\n᲼᲼', 
        inline = False
    )

    embed.add_field(
        name = '!teste', 
        value = 'Testa a mensagem de boas-vindas.', 
        inline = False
    )

    embed.set_thumbnail(url = bot.user.avatar)

    await ctx.channel.send(
        ctx.message.author.mention, 
        embed = embed
    )

@bot.command()
async def limpar(ctx, quantia: int, *user):
    quantia = int(quantia)

    if user:
        usuario = discord.utils.get(ctx.guild.members, nick = " ".join(user)) or discord.utils.get(ctx.guild.members, global_name = " ".join(user))
        deletados = 0

        def deletar_msg(message):
            nonlocal deletados

            if deletados >= quantia:
                return False

            if message.author.id != usuario.id:
                return False
            
            deletados += 1
            return True

        await ctx.channel.purge(limit = 100, check = deletar_msg)
        await ctx.channel.send(f'{deletados} mensagen(s) deletada(s) com sucesso!')
    else:
        await ctx.channel.purge(limit = quantia + 1)
        await ctx.channel.send(f'{quantia} mensagen(s) deletada(s) com sucesso!')

    await asyncio.sleep(5)
    await ctx.channel.purge(limit = 1) 

@bot.command()
async def sortear(ctx, *args):
    embed = discord.Embed(
        title = "SORTEIO DRUNKEN DWARF", 
        description = f"O número sorteado foi: **{randint(int(args[0]), int(args[1]))}**\n\n__**Parabéns!**__", 
        color = 0x7a8ff5)
    embed.set_thumbnail(url=ctx.guild.icon.url)
    embed.set_footer(text=f"DKDW • {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    await ctx.message.channel.send(embed = embed)

async def enviar_sugestao(message):
    embed = discord.Embed(title = f"{message.author.display_name} sugeriu:", description = message.content, color = 0x7a8ff5)
    embed.set_footer(text=f"Enviado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    await bot.get_channel(866476425061335120).send(embed = embed) # DKDW/reclames-do-povo
    await message.delete()
    await message.author.send("A sugestão foi enviada para a Staff do Clã.") 

def verificar_cargo(cargos_sv, cargos_user):
    membros = discord.utils.get(cargos_sv, name = "Membros")
    visitantes = discord.utils.get(cargos_sv, name = "Visitantes")
    
    return any(role in cargos_user for role in [membros, visitantes])

async def adicionar_cargo(message):
    # Nomes no rune só vão até 12 caracteres.
    if len(message.content) > 12:
        return
    
    if verificar_cargo(message.guild.roles, message.author.roles):
        return
    
    meliantes = await nomes.buscar_meliantes()
    membros = await nomes.buscar_membros()

    if not meliantes or not membros:
        return
    
    DKDW = bot.get_guild(296764515335405570)
    MODERACAO = bot.get_channel(710255855316238447)
    CARGO_STAFF = DKDW.get_role(296780203940904960)
    CARGO_MEMBRO = DKDW.get_role(296780850895388672)
    CARGO_GUEST = DKDW.get_role(378242013574987776)
    
    nome = message.author.name
    nome_sv = message.author.display_name

    if any(nome in meliantes for nome in [nome, nome_sv, message.content]):
        return await MODERACAO.send(f'Usuário "{nome_sv}" tentou entrar no servidor como meliante da Black List {message.content}! {CARGO_STAFF.mention}')
    
    for member in DKDW.members:
        if member == message.author:
            continue
        if member.name in message.content or member.display_name in message.content:
            return await MODERACAO.send(f'Usuário "{nome_sv}" tentou entrar no servidor se passando por {member.display_name}! {CARGO_STAFF.mention}')

    if message.content in membros:
        await message.author.add_roles(CARGO_MEMBRO)
    else:
        await message.author.add_roles(CARGO_GUEST)

    await message.author.edit(nick = message.content)

@bot.event
async def on_command_error(ctx, error):
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

@bot.event
async def on_member_join(member):
    await bot.get_guild(296764515335405570).get_channel(589600587742707732).send(
        msg_bem_vindos.replace("{}", member.mention)
    )

@bot.event
async def on_ready():
    await bot.change_presence(activity = discord.Game(name = 'no melhor clã BR'))
    print(f'>> {bot.user} on-line!')

@bot.event
async def on_message(message):
    if message.mention_everyone or '@here' in message.content:
        msg = message.content.lower()
        if all(palavra in msg for palavra in ['free', 'discord', 'nitro']):
            # DKDW/moderação
            bot.get_channel(710255855316238447).send(
                f'{message.author.display_name} tentou enviar spam de Discord Nitro no canal {message.channel}.'
            )
            return await message.delete()
            
    if message.author.bot:
        return

    if message.channel.id == 866475904905773056: # DKDW/caixa-de-sugestões
        return await enviar_sugestao(message)

    if message.channel.id == 589600587742707732: # DKDW/bem-vindos
        return await adicionar_cargo(message)

    if not message.author.guild_permissions.administrator:
        return

    await bot.process_commands(message)

bot.run(TOKEN)