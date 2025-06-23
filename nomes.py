from lxml import html
from requests.exceptions import RequestException
import requests
import re

# Elas precisam ser non-blocking pra evitar do discord.client desconectar.

async def buscar_meliantes() -> set[str] | None:
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

async def buscar_membros() -> set[str] | None:
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