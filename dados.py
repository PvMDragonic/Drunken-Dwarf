import json

class DKDW():
    def __init__(self):
        try:
            with open('dkdw.json', 'r') as arqv:
                self.__dict__.update(json.load(arqv))
        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo 'dkdw.json' não foi encontrado.")

    def salvar_dados(self): 
        with open('dkdw.json', 'w') as arqv:
            json.dump(self.__dict__, arqv, indent = 4)

    def boas_vindas(self, mention: str):
        return self.msg_bem_vindos.replace("{}", mention)