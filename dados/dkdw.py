import json

class DKDW():
    """Responsável por carregar e manter os dados e configurações do bot."""
    def __init__(self):
        try:
            with open('dados/dkdw.json', 'r') as arqv:
                self.__dict__.update(json.load(arqv))
        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo 'dkdw.json' não foi encontrado.")

        atributos_json = {
            'token': str,
            'msg_bem_vindos': str,
            'enviar_boas_vindas': bool,
            'msg_despedida': str,
            'enviar_despedida': bool,
            'enviar_relatorio': bool
        }

        for atributo, tipo in atributos_json.items():
            if not hasattr(self, atributo):
                raise ValueError(f"O campo obrigatório '{atributo}' está faltando no arquivo 'dkdw.json'.")

            value = getattr(self, atributo)

            if not isinstance(value, tipo):
                raise ValueError(
                    f"O campo '{atributo}' tem tipo inválido. Esperado: {tipo.__name__}, "
                    f"Recebido: {type(value).__name__}."
                )

            if tipo == str and value.strip() == "":
                raise ValueError(f"O campo '{atributo}' não pode ser uma string vazia.")

    def salvar_dados(self):
        with open('dados/dkdw.json', 'w') as arqv:
            json.dump(self.__dict__, arqv, indent = 4)

    def boas_vindas(self, mention: str):
        return self.msg_bem_vindos.replace("{}", mention)
    
    def despedida(self, mention: str):
        return self.msg_despedida.replace("{}", mention)