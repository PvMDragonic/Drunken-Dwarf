from lxml import html
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
        return set(re.sub(r"\([^()]*\)", "", nome).strip() for elem in linhas for nome in elem.text_content().split("-"))
    except Exception as e:
        print(e)

print

async def buscar_membros() -> set[str] | None:
    """
    Retorna os nomes dos membros do Drunken Dwarf.

    Retorna:
        set: 
            Conjunto de nomes dos membros.
        None:
            Caso aconteça algum erro durante o scrap.
    """
    
    try:   
        membros = set()
        for i in range(1, 33):
            pagina_dkdw = f'https://secure.runescape.com/m=clan-hiscores/l=3/a=9/members.ws?clanId=26687&ranking=-1&pageSize=15&pageNum={i}'
            requisicao = requests.get(pagina_dkdw).content
            conteudo = html.fromstring(requisicao)
            nomes = conteudo.xpath('.//span[@class="name"]')

            for nome in nomes:
                membros.add(nome.text_content().replace('\xa0', ' '))

        return membros    
    except Exception as e:
        print(e)