import aiohttp

class Fetch():
    """Classe responsável por requisições GET assíncronas com aiohttp."""

    @staticmethod
    async def text(url: str) -> None | str:
        """Retorna response.text() de uma requisição."""

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                return await response.text(encoding = 'utf-8', errors = 'replace')

    @staticmethod
    async def json(url: str) -> None | str:
        """Retorna response.json() de uma requisição."""

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                return await response.json()