from discord.ext.commands.errors import MissingRequiredArgument, BadArgument
from discord.ext.commands import CommandNotFound
from discord.ext import commands
from random import randint
import datetime
import asyncio
import discord
import nomes

from dados import DKDW

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix = '!', intents = intents)

dkdw = DKDW()

@bot.command()
async def ativar(ctx, opc: str):
    if opc not in ('1', '2'):
        return await ctx.channel.send(
            f'Digite 1 para boas-vindas ou 2 para despedida! {ctx.message.author.mention}'
        )
    
    if opc == '1':
        dkdw.enviar_boas_vindas = not dkdw.enviar_boas_vindas
        dkdw.salvar_dados()
        await ctx.channel.send(
            f'Mensagem de boas-vindas __{"ativada" if dkdw.enviar_boas_vindas else "desativada"}__! {ctx.message.author.mention}'
        )
    else:
        dkdw.enviar_despedida = not dkdw.enviar_despedida
        dkdw.salvar_dados()
        await ctx.channel.send(
            f'Mensagem de despedida __{"ativada" if dkdw.enviar_despedida else "desativada"}__! {ctx.message.author.mention}'
        )

@bot.command()
async def teste(ctx, opc: str):
    if opc not in ('1', '2'):
        return await ctx.channel.send(
            f'Digite 1 para boas-vindas ou 2 para despedida! {ctx.message.author.mention}'
        )
    
    if opc == '1':
        await ctx.channel.send(dkdw.boas_vindas(ctx.message.author.mention))
    else:
        await ctx.channel.send(dkdw.despedida(ctx.message.author.mention))

@bot.command()
async def mensagem(ctx, opc: str):
    if opc not in ('1', '2'):
        return await ctx.channel.send(
            f'Digite 1 para boas-vindas ou 2 para despedida! {ctx.message.author.mention}'
        )

    # Remove o comando da mensagem.
    mensagem = " ".join(ctx.message.content.split(" ")[1:])

    if opc == '1':
        dkdw.msg_bem_vindos = mensagem
        dkdw.salvar_dados()
        await ctx.channel.send(
            f'Uma nova mensagem de boas-vindas foi definida! Use `!teste 1` para ver como ficou. {ctx.message.author.mention}'
        )
    else:
        dkdw.msg_despedida = mensagem
        dkdw.salvar_dados()
        await ctx.channel.send(
            f'Uma nova mensagem de despedida foi definida! Use `!teste 2` para ver como ficou. {ctx.message.author.mention}'
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
        value = 'Testa a mensagem de boas-vindas.\nOpção 1 para boas-vindas; 2 para despedida.', 
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
        check = lambda message: message.author.id == bot.user.id
    ) 

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

    if not membros:
        return

    DKDW = bot.get_guild(296764515335405570)
    MODERACAO = bot.get_channel(710255855316238447)
    CARGO_STAFF = DKDW.get_role(296780203940904960)
    CARGO_MEMBRO = DKDW.get_role(296780850895388672)
    CARGO_GUEST = DKDW.get_role(378242013574987776)
    
    nome = message.author.name
    nome_sv = message.author.display_name

    if meliantes: # Blacklist dos clãs foi abandonada e deixou de ser pública. 
        if any(nome in meliantes for nome in [nome, nome_sv, message.content]):
            return await MODERACAO.send(
                f'Usuário "{nome_sv}" tentou entrar no servidor como meliante da Blacklist dos Clãs {message.content}! {CARGO_STAFF.mention}'
            )
    
    for member in DKDW.members:
        if member == message.author:
            continue
        if member.name in message.content or member.display_name in message.content:
            return await MODERACAO.send(
                f'Usuário "{nome_sv}" tentou entrar no servidor se passando por {member.display_name}! {CARGO_STAFF.mention}'
            )

    if message.content in membros:
        await message.author.add_roles(CARGO_MEMBRO)
    else:
        await message.author.add_roles(CARGO_GUEST)

    await message.author.edit(nick = message.content)

async def enviar_gratz(message):
    if not message.attachments:
        return
    
    for attachment in message.attachments:
        # Print geralmente é salvo em png.
        if not attachment.filename.lower().endswith('png'):
            continue

        # 'message.channel.history' é um async_generator.
        mensagens_hoje = [msg async for msg in message.channel.history(limit = 10)][1:]
        hoje = datetime.datetime.now().date()
        author = message.author.id

        for msg in mensagens_hoje:
            if msg.author.id == author and msg.attachments:
                # Estragar a alegria do Morango tentando spammar o bot.
                if datetime.datetime.now(datetime.timezone.utc) - msg.created_at < datetime.timedelta(minutes = 1):
                    return 

        saques_hoje = sum([
            True
            for index, msg in enumerate(mensagens_hoje)
            if msg.author.id == author 
                and msg.attachments 
                and msg.created_at.date() == hoje
                # Ignora prints que caíram no cooldown de 1 minuto acima.
                and mensagens_hoje[index - 1].author.id == 1023385609466818590 
        ])
        
        return await message.channel.send(
            {
                0 : f'Gratzzzzzzzzzzzzzz! :partying_face: {message.author.mention}',
                1 : f'Gratzzzzzzzzzzzzzzzzzzzzz!! :partying_face: :partying_face: {message.author.mention}',
                2 : f'GRATZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ!!! :partying_face: :partying_face: :partying_face: {message.author.mention}'
            }.get(
                saques_hoje,
                f'w0000000000000000000000000000000t {":exploding_head: " * saques_hoje} {saques_hoje}º drop hoje{"!" * saques_hoje} {message.author.mention}'
            )
        ) 

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
    if dkdw.enviar_boas_vindas:
        await bot.get_guild(296764515335405570).get_channel(589600587742707732).send(
            dkdw.boas_vindas(member.mention)
        )

@bot.event
async def on_member_remove(member):
    if dkdw.enviar_despedida:
        await bot.get_guild(296764515335405570).get_channel(589600587742707732).send(
            dkdw.despedida(member.name)
        )

@bot.event
async def on_ready():
    await bot.change_presence(activity = discord.Game(name = 'no melhor clã BR'))
    print(f'>> {bot.user} on-line!')

@bot.event
async def on_message(message):
    if '@everyone' in message.content or '@here' in message.content:
        ids = [
            296779510089777152, # 'Moderador
            296780203940904960, # 'Staff'
            296780473236193280  # 'BOTS'
        ]
        cargos_id = [role.id for role in message.author.roles]
        cargos_encontrados = [role_id for role_id in cargos_id if role_id in ids]
        if cargos_encontrados:
            return

        links = ["https://", "http://"]
        links_encontrados = [ele for ele in links if(ele in message.content)]
        if not links_encontrados:
            return 
        
        await message.delete()

        # DKDW/moderação
        return await bot.get_channel(1211472248326856724).send(
            f'{message.author.mention} tentou enviar spam no canal {message.channel.mention}.'
        )
            
    if message.author.bot:
        return

    if message.channel.id == 866475904905773056: # DKDW/caixa-de-sugestões
        return await enviar_sugestao(message)

    if message.channel.id == 589600587742707732 or message.channel.id == 1123305689574539285: # DKDW/bem-vindos
        return await adicionar_cargo(message)
    
    if message.channel.id == 811639954442420235: # DKDW/drops-e-conquistas
        return await enviar_gratz(message)

    if not message.author.guild_permissions.administrator:
        return

    await bot.process_commands(message)

bot.run(dkdw.token)