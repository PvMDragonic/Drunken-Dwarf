from discord.ext.commands import CommandNotFound
from discord.ext import commands
from random import randint
import discord
import datetime

TOKEN = open('token.txt', 'r').readline().rstrip()

intents = discord.Intents.default()
intents.message_content = True
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
    embed = discord.Embed(title = f"{message.author} sugeriu:", description = message.content, color = 0x7a8ff5)
    embed.set_footer(text=f"Enviado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    await bot.get_channel(866476425061335120).send(embed = embed) # DKDW/reclames-do-povo
    await message.delete()
    await message.author.send("A sugestão foi enviada para a Staff do Clã.") 

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
    if message.channel.id == 866475904905773056: # DKDW/caixa-de-sugestões
        await enviar_sugestao(message)
        return

    if message.mention_everyone or '@here' in message.content:
        msg = message.content.lower()
        if 'nitro' in msg and 'link' in msg:
            await message.delete()
            return

    await bot.process_commands(message)

bot.run(TOKEN)