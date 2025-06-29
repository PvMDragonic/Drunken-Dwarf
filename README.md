# Drunken-Dwarf
Bot responsável pela moderação do Discord do Clã [Drunken Dwarf](https://secure.runescape.com/m=clan-home/clan/Drunken%20Dwarf) do RuneScape.

## Funcionalidades
* Triagem e designação automática de cargos para membros e visitantes;
* Mensagem de 'gratzzzz' automática para quem envia print de conquista;
* Mensagem de boas-vindas & despedida automática;
* Prevenção de spam (links de phishing/anúncios);
* Comando para ver histórico de nomes de membros do clã;
* Comando para ver membros do clã inativos;
* Comando para limpar x linhas de chat;
* Comando para sortear número entre x e y;
* Comando para prévia de mensagens de saída & despedida.

### Mudança de nomes
O bot é capaz de acompanhar quem trocou de nome para manter o comando `!inativos` em dia.

Como a API desse jogo é estupidamente incompleta e mal-feita, isso é alcançado coletando os dados de todos os _membros_ do clã pela API do RuneScape, que retorna uma lista de 150 dados (integers) de dado jogador assinante:

```
https://secure.runescape.com/m=hiscore/index_lite.ws?player=PvM+Dragonic
``` 

Com dados dos membros atuais do clã, quando um nome deixa de existir na lista geral de integrantes (mas ainda está registrado), é possível bater as estatísticas dessa pessoa contra o restante das conhecidas para achar o seu par mais similar via:

```python
scaler = StandardScaler()
scaler.fit(todos_membros_stats)
dados_historicos = scaler.transform(todos_membros_stats)

stats_antigo = np.array(stats_jogador).reshape(1, -1)   # shape (1, 150)
ultimo_stats = scaler.transform(stats_antigo)[0]        # shape (150,)

similaridades = []
for id_conhecido, vetor_conhecido in zip(usuarios_com_stats, dados_historicos):
    sim = 1 - cosine(ultimo_stats, vetor_conhecido)
    similaridades.append((id_conhecido, sim))

best_match, score = max(similaridades, key = lambda x: x[1])
``` 

O `score` vai ser um valor de 1 à -1, onde o `best_match` é aquele elemento de `usuarios_com_stats` que tem o equivalente em `dados_historicos` mais próximo de `stats_jogador`.

### Saída do clã
Para descobrir quem (registrado) que não está mais do clã, basta checar se dado jogador não retorna o erro `NO_PROFILE` pela API do RuneMetrics:

```
https://apps.runescape.com/runemetrics/profile/profile?user=PvM+Dragonic&activities=1
```

Se o jogador mudou de nome, seu nome antigo (que está registrado no banco de dados do bot) não existirá mais, logo, dará "NO_PROFILE". Se o jogador ainda existe mas saiu do clã, retornará um erro como "PROFILE_PRIVATE" ou "NOT_A_MEMBER".

## Instalação
O bot é feito em Python e requer as seguintes bibliotecas:
```
pip install discord.py requests lxml pandas table2ascii scikit-learn
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
Este projeto está licenciado sob a Licença Pública Geral GNU versão 3 (GPLv3). Veja o arquivo [LICENSE](LICENSE) para mais detalhes.