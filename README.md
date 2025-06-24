# Drunken-Dwarf
Bot responsável pela moderação do Discord do Clã [Drunken Dwarf](https://secure.runescape.com/m=clan-home/clan/Drunken%20Dwarf) do RuneScape.

## Funcionalidades
* Triagem e designação automática de cargos para membros e visitantes;
* Mensagem de 'gratzzzz' automática para quem envia print de conquista;
* Mensagem de boas-vindas & despedida automática;
* Prevenção de spam (links de phishing/anúncios);
* Comando para ver membros do clã inativos;
* Comando para limpar x linhas de chat;
* Comando para sortear número entre x e y.

### Instalação
O bot é feito em Python e requer as seguintes bibliotecas:
```
pip install discord.py requests lxml pandas table2ascii
```

Para executar o bot, é necessário um arquivo `dkdw.json` na pasta `/dados` contendo:
```json
{
    "token": "seu_token_aqui",
    "msg_bem_vindos": "Bem-vindo(a), {}!",
    "enviar_boas_vindas": true,
    "msg_despedida": "Adeus, {}.",
    "enviar_despedida": false
}
```

## Licença
GPL v3