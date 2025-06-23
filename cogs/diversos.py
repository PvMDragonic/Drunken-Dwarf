from discord.ext import commands
import datetime
import discord

class Diversos(commands.Cog):
    """Cog responsável por comandos diversos."""

    def __init__(self, bot):
        self.bot = bot

    async def enviar_sugestao(self, message):
        embed = discord.Embed(title = f"{message.author.display_name} sugeriu:", description = message.content, color = 0x7a8ff5)
        embed.set_footer(text=f"Enviado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        await self.bot.get_channel(866476425061335120).send(embed = embed) # DKDW/reclames-do-povo
        await message.delete()
        await message.author.send("A sugestão foi enviada para a Staff do Clã.")

    async def enviar_gratz(self, message):
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

async def setup(bot):
    await bot.add_cog(Diversos(bot))