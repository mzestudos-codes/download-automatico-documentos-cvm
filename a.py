import json
import os

class ExploradorCategoriasCVM:
    """
    Classe responsável por ler o ficheiro categorias.json e 
    retornar as relações de 'pai e filho' entre Categorias, Tipos e Espécies.
    """
    
    def __init__(self, caminho_json="categorias.json"):
        # Passo 1: O construtor lê o ficheiro JSON assim que iniciamos a classe
        if not os.path.exists(caminho_json):
            print(f"Erro: Ficheiro {caminho_json} não encontrado.")
            self.dados = []
        else:
            with open(caminho_json, 'r', encoding='utf-8') as f:
                self.dados = json.load(f)

    def obter_tipos_da_categoria(self, nome_categoria):
        """
        Recebe uma Categoria (pai) e retorna todos os Tipos (filhos) associados.
        """
        tipos_encontrados = set() # Usamos 'set' para garantir que não há nomes repetidos
        
        # Passo 2: Percorremos cada item do nosso banco de dados (JSON)
        for item in self.dados:
            # Se a categoria do item for igual à categoria que estamos a procurar...
            if item.get('categoria', '').strip().upper() == nome_categoria.strip().upper():
                # ...adicionamos o Tipo desse item à nossa lista de resultados
                tipos_encontrados.add(item.get('tipo', ''))
                
        # Passo 3: Retornamos a lista organizada por ordem alfabética
        return sorted(list(tipos_encontrados))

    def obter_especies_do_tipo(self, nome_categoria, nome_tipo):
        """
        Recebe uma Categoria (pai) e um Tipo (filho) e retorna as Espécies (netos).
        """
        especies_encontradas = set()
        
        # Passo 4: O mesmo processo, mas agora verificamos Categoria E Tipo
        for item in self.dados:
            cat_atual = item.get('categoria', '').strip().upper()
            tipo_atual = item.get('tipo', '').strip().upper()
            
            if cat_atual == nome_categoria.strip().upper() and tipo_atual == nome_tipo.strip().upper():
                especies_encontradas.add(item.get('especie', ''))
                
        return sorted(list(especies_encontradas))


# --- TESTE PRÁTICO DO CÓDIGO ---
# Este bloco só corre se executares este ficheiro diretamente
if __name__ == "__main__":
    # Inicializamos o explorador
    explorador = ExploradorCategoriasCVM()
    
    print("=== TESTE 1: FILHOS DE 'ASSEMBLEIA' ===")
    categoria_alvo = "Assembleia"
    tipos = explorador.obter_tipos_da_categoria(categoria_alvo)
    
    print(f"Os tipos (filhos) da Categoria '{categoria_alvo}' são:")
    for t in tipos:
        print(f" ├─ {t}")
        
    print("\n=== TESTE 2: FILHOS DE 'AGCRA' ===")
    tipo_alvo = "AGCRA"
    especies = explorador.obter_especies_do_tipo(categoria_alvo, tipo_alvo)
    
    print(f"As espécies (filhas) do Tipo '{tipo_alvo}' na Categoria '{categoria_alvo}' são:")
    for e in especies:
        print(f" └─ {e}")