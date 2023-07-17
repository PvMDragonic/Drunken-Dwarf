from discord.ext.commands import CommandNotFound
from discord.ext import commands
from random import randint
import discord
import datetime
import nomes

TOKEN = open('token.txt', 'r').readline().rstrip()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents = intents)

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

async def adicionar_cargo(message):
    # Nomes no rune só vão até 12 caracteres.
    if len(message.content) > 12:
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
    raise error

@bot.event
async def on_ready():
    print(f'>> {bot.user} on-line!')

@bot.event
async def on_message(message):
    if message.mention_everyone or '@here' in message.content:
        msg = message.content.lower()
        if all(palavra in msg for palavra in ['free', 'discord', 'nitro']):
            # DKDW/moderação
            bot.get_channel(710255855316238447).send(f'{message.author.display_name} tentou enviar spam de Discord Nitro no canal {message.channel}.')
            return await message.delete()
            
    if message.channel.id == 866475904905773056: # DKDW/caixa-de-sugestões
        return await enviar_sugestao(message)

    if message.channel.id == 589600587742707732: # DKDW/bem-vindos
        return await adicionar_cargo(message)

    await bot.process_commands(message)

bot.run(TOKEN)