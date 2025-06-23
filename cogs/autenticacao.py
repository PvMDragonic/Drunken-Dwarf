from requests.exceptions import RequestException
from discord.ext import commands
from lxml import html
import requests
import discord
import re

class Autenticacao(commands.Cog):
    """Cog responsável por comandos da Moderação/Staff."""

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def _buscar_meliantes() -> set[str] | None:
        """
        Retorna os nomes que constam na Black List dos clãs.

        Retorna:
            set: 
                Conjunto de nomes dos meliantes.
            None:
                Caso aconteça algum erro durante o scrap.
        """

        try:
            black_list = 'https://docs.google.com/spreadsheets/d/1_laGspB1mbFGOkXBuGLS3ZWk4QXe69mt'
            requisicao = requests.get(black_list).content
            conteudo = html.fromstring(requisicao)
            linhas = conteudo.xpath('.//td')
            
            if not linhas:
                raise ValueError('Blacklist indisponivel.')

            return set(
                re.sub(r"\([^()]*\)", "", nome).strip() 
                for elem in linhas 
                for nome in elem.text_content().split("-")
            )
        except (RequestException, ValueError) as erro:
            print(erro)
            return None

    @staticmethod
    async def _buscar_membros() -> set[str] | None:
        """
        Retorna os nomes dos membros do Drunken Dwarf.

        Retorna:
            set: 
                Conjunto de nomes dos membros.
            None:
                Caso aconteça algum erro durante o scrap.
        """

        response = requests.get('http://services.runescape.com/m=clan-hiscores/members_lite.ws?clanName=Drunken+Dwarf')

        if response.status_code == 200:
            clan = response.content.decode('utf-8', errors='replace').replace('\ufffd', ' ')
            nomes = clan.split('\n')
            nomes = [nome.split(',')[0] for nome in nomes]
            return nomes[1:-1]
        else:
            print("Erro na coleta de membros: ", response.status_code)
            return None

    @staticmethod
    def _verificar_cargo(cargos_sv, cargos_user) -> bool:
        """Verifica se o usuário já tem cargo de membro ou visitante."""

        membros = discord.utils.get(cargos_sv, name = "Membros")
        visitantes = discord.utils.get(cargos_sv, name = "Visitantes")
        
        return any(role in cargos_user for role in [membros, visitantes])

    async def adicionar_cargo(self, message):
        if len(message.content) > 12: # Nomes no rune só vão até 12 caracteres.
            return
        
        if self._verificar_cargo(message.guild.roles, message.author.roles):
            return
        
        meliantes = await self._buscar_meliantes()
        membros = await self._buscar_membros()

        if not membros:
            return

        DKDW = self.bot.get_guild(296764515335405570)
        MODERACAO = self.bot.get_channel(710255855316238447)
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

        try:
            await message.author.edit(nick = message.content)
        except discord.errors.Forbidden: # Não pode mudar o nome de dono do servidor.
            pass

async def setup(bot):
    await bot.add_cog(Autenticacao(bot))