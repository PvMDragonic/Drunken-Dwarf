from discord.ext import commands
from datetime import datetime
import discord

from dados.database import Database

class DoubleXP(commands.Cog):
    """Cog responsável pelo ranking interno do Double XP."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def double(self, ctx, date1: str, date2: str):
        try:
            dxp_start = datetime.strptime(date1, "%d/%m/%Y").date()
            dxp_end = datetime.strptime(date2, "%d/%m/%Y").date()

            if dxp_end < dxp_start:
                return await ctx.send(
                    f"Você enviou uma data de encerramento que antecede a de início! {ctx.author.mention}"
                )

            dxp_start = dxp_start.strftime("%Y-%m-%d")
            dxp_end = dxp_end.strftime("%Y-%m-%d")
        except ValueError:
            return await ctx.send(
                f"Formato inválido de datas! Use: `!double dd/mm/aaaa dd/mm/aaaa` {ctx.author.mention}"
            ) 

        db = Database()
        xp_start = db.buscar_xp_todos_data(dxp_start)
        xp_end = db.buscar_xp_todos_data(dxp_end)

        print(len(xp_start))
        print(len(xp_end))

        dxp = {}
        for username, xp in xp_end.items():
            # Newfag entrou depois do começo do DXP, logo, seu xp_end é o tanto que upou no Double.
            if username not in xp_start:
                dxp[username] = xp
            else:   
                double_xp = int(xp) - int(xp_start[username])
                if double_xp > 0:
                    dxp[username] = double_xp

        dxp = {
            username: f"{xp:,.0f}".replace(",", "_").replace(".", ",").replace("_", ".")
            for username, xp in sorted(
                dxp.items(),
                key = lambda item: item[1],
                reverse = True
            )[:10]
        }

        embed = discord.Embed(
                title = f"Ranking interno entre `{date1}` & `{date2}`", 
                description = f"__Top 10 membros:__", 
                color = 0x7a8ff5
            )

        for index, (username, xp) in enumerate(dxp.items()):
            embed.add_field(
                name = f'*{index + 1}º — {username}*',
                value = xp.replace(",","."),
                inline = False
            )

        await ctx.message.channel.send(embed = embed)
        
async def setup(bot):
    await bot.add_cog(DoubleXP(bot))