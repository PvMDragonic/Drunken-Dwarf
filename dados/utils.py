def formatar_xp(xp: int) -> str:
    """
    Formata um número para ficar truncado igual no RuneScape,\n
    trucando as casas de milhares, milhão e bilhão em troca\n
    das letras K, M e B.
    """

    if xp == 0:
        return "Zero"
    
    virgulas = f'{xp:,}'
    separado = virgulas.split(',')

    # 1 vírgula (100,000)
    if len(separado) == 2: 
        ultimo_digito = separado[1][0]
        if ultimo_digito != '0':
            return f'{separado[0]}.{ultimo_digito}K'
        return f'{separado[0]}K'
    
    # 2 vírgulas (100,000,000)
    if len(separado) == 3: 
        ultimo_digito = separado[1][0]
        if ultimo_digito != '0':
            return f'{separado[0]}.{ultimo_digito}M'
        return f'{separado[0]}M'
    
    # 3 vírgulas (100,000,000,000)
    if len(separado) == 4: 
        return f'{separado[0]}.{separado[1]}B'
    
def formatar_dia(dias: int) -> str:
    """Adiciona 'dia' à um número, levando em conta singular ou plural."""

    unidade = "dia" if dias == 1 else "dias"
    return f"{dias} {unidade}"