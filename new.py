import numpy as np
from collections import Counter
import os
import random
import sys

# ============================
# "Configuração" de cores ANSI
# (se não funcionar, culpa o terminal)
# ============================
VERDE = "\033[42m\033[30m"   # fundo verde, texto preto
AMARELO = "\033[43m\033[30m" # fundo amarelo, texto preto
CINZA = "\033[47m\033[30m"   # fundo cinza claro
RESET = "\033[0m"

# ============================
# Gambiarra pra carregar palavras
# ============================
def carregar_lista_palavras(nome_arquivo="palavras.txt"):
    palavras = []

    if os.path.exists(nome_arquivo):
        try:
            with open(nome_arquivo, "r", encoding="utf-8") as f:
                for linha in f:
                    w = linha.strip().lower()
                    # só pega palavras de 5 letras sem espaço
                    if len(w) == 5 and w.isalpha():
                        palavras.append(w)
        except Exception as e:
            print("Deu ruim lendo o arquivo de palavras:", e)
    else:
        print(f"[AVISO] Arquivo '{nome_arquivo}' não encontrado.")
        print("[AVISO] Usando lista mínima interna só pra não quebrar tudo...\n")
        # fallback básico (mini lista)
        palavras = [
            "tares", "lares", "rales", "rates", "teras",
            "nares", "soare", "tales", "reais", "tears",
            "carta", "tanto", "certo", "antes", "falar"
        ]

    # tira duplicadas na marra
    palavras = list(dict.fromkeys(palavras))

    if not palavras:
        print("Nenhuma palavra carregada. Melhor revisar o arquivo.")
        sys.exit(1)

    print(f"[INFO] Carregadas {len(palavras)} palavras.")
    return palavras

# ============================
# Converte chute x solução em padrão (cores codificadas)
# ============================
def calcular_padrao(chute, alvo):
    # gambiarra: confia que tem 5 letras, se não tiver quebra mesmo
    padrao = [0] * 5
    letras_alvo = list(alvo)

    # primeiro marca verdes
    for i in range(5):
        if chute[i] == letras_alvo[i]:
            padrao[i] = 2
            letras_alvo[i] = None  # "queima" a letra

    # depois amarelos
    for i in range(5):
        if padrao[i] == 0 and chute[i] in letras_alvo:
            padrao[i] = 1
            idx = letras_alvo.index(chute[i])
            letras_alvo[idx] = None

    # transforma lista [2,0,1,...] em número em base-3
    codigo = 0
    for i, cor in enumerate(padrao):
        codigo += cor * (3 ** (4 - i))
    return codigo

# ============================
# Faz entropia ser "a estrela"
# ============================
def entropia_da_palavra(palavra, universo):
    # pra cada possível solução, vê qual padrão daria
    padroes = [calcular_padrao(palavra, sol) for sol in universo]
    contagem = Counter(padroes)

    probs = np.array(list(contagem.values()), dtype=float) / len(universo)
    # gambiarra: evita log2(0) pelo caminho normal (não deveria ter zero aqui)
    ent = -np.sum(probs * np.log2(probs))
    return ent

def ranking_por_entropia(lista_palavras):
    # jeitinho: faz um dicionário, depois converte
    mapa = {}
    for w in lista_palavras:
        mapa[w] = entropia_da_palavra(w, lista_palavras)
    # ordena do maior pro menor
    ordenado = sorted(mapa.items(), key=lambda x: x[1], reverse=True)
    return ordenado

# ============================
# Exibe uma linha colorida igual Termo
# ============================
def mostrar_linha_colorida(chute, codigo_padrao):
    # converte número base-10 para 5 "dígitos" em base-3
    pattern = []
    resto = codigo_padrao
    for i in range(5):
        pot = 3 ** (4 - i)
        dig = resto // pot
        resto = resto % pot
        pattern.append(dig)

    # imprime letra por letra com cor
    linha = []
    for i, letra in enumerate(chute):
        if pattern[i] == 2:
            bloco = f"{VERDE} {letra.upper()} {RESET}"
        elif pattern[i] == 1:
            bloco = f"{AMARELO} {letra.upper()} {RESET}"
        else:
            bloco = f"{CINZA} {letra.upper()} {RESET}"
        linha.append(bloco)

    print(" ".join(linha))

# ============================
# Jogo automático usando entropia
# ============================
def jogar_automatico(alvo, universo, chute_inicial=None):
    # só pra ficar feio: copia pra não estragar a original
    candidatos = np.array(universo)

    if chute_inicial is None:
        # pega o top-1 do ranking (gambiarra: assume já calculado)
        # se não tiver ranking, escolhe qualquer
        chute_inicial = random.choice(universo)

    chute = chute_inicial
    print("\n==========================")
    print("  SIMULAÇÃO AUTOMÁTICA")
    print("==========================")
    print(f"Alvo (escondido na vida real): {alvo.upper()}\n")

    for tentativa in range(1, 10):
        padrao = calcular_padrao(chute, alvo)

        print(f"Tentativa {tentativa}: {chute.upper()}")
        mostrar_linha_colorida(chute, padrao)
        print()

        if padrao == 242:  # 22222 em base-3 = tudo verde
            print("✔ Acertou a palavra!")
            return tentativa

        # filtra candidatos compatíveis com o mesmo padrão
        mascara = np.array([calcular_padrao(chute, w) == padrao for w in candidatos])
        candidatos = candidatos[mascara]

        if len(candidatos) == 0:
            print("❌ Não sobrou nenhuma palavra compatível. Deu ruim.")
            return -1

        # escolhe próxima palavra mais informativa (a famosa "força bruta elegante")
        scores = {}
        for w in candidatos:
            scores[w] = entropia_da_palavra(w, candidatos)

        chute = max(scores, key=scores.get)

    print("❌ Passou do limite de tentativas.")
    return -1

# ============================
# "Main" cheio de textinho
# ============================
if __name__ == "__main__":
    # carrega palavras de arquivo externo (ou fallback interno)
    lista_palavras = carregar_lista_palavras("palavras.txt")

    # mostra um ranking só das 15 primeiras (senão vira tese)
    print("\n=== RANKING (amostra) – melhores palavras pra começar ===\n")
    ranking = ranking_por_entropia(lista_palavras[:200])  # gambiarra: corta pra não demorar demais

    for i, (pal, h) in enumerate(ranking[:15], start=1):
        print(f"{i:2}. {pal.upper():<6} -> {h:.4f} bits")

    # escolhe uma palavra alvo aleatória pra simulação
    alvo_escolhido = random.choice(lista_palavras)

    # dá pra fixar um alvo se quiser:
    # alvo_escolhido = "reais"

    # opcional: chute inicial = melhor do ranking
    melhor_inicial = ranking[0][0] if ranking else lista_palavras[0]

    print("\nUsando como chute inicial:", melhor_inicial.upper())

    jogar_automatico(alvo_escolhido, lista_palavras, chute_inicial=melhor_inicial)

    print("\n[FIM DA EXECUÇÃO] Se rodou até aqui, tá vivo 😎")