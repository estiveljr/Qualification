import pandas as pd
import numpy as np
from collections import namedtuple
import cplex as cp
import rlcompleter
import readline
import docplex as cpx
from docplex.mp.model import Model
import docplex

DEBUG = 1

file = 'dados.txt'
with open(file, 'r') as input_data_file:
    input_data = input_data_file.read()

# Reescrever restrição para de icms, de modo a ser definida no arco e não no vértice.
# # Rever como identificar crédito presumido
UF = namedtuple("UF", ['index','nome'])
Vertice = namedtuple("vertice", ['index','nome', 'demanda','uf'])
Produto = namedtuple("produto",['index','nome'])
Arco = namedtuple("arco",['index','org','dest','produto','capacidade','custo_fixo','custo_var','custo_var_icms'])
Credito = namedtuple("credito",['index','uf','produto','custo_icms'])

# parse the input
linhas = input_data.split('\n')
primeira_linha = linhas[0].split()

qnt_ufs = int(primeira_linha[0])
qnt_vertices = int(primeira_linha[1])
qnt_produtos = int(primeira_linha[2])
qnt_credito = int(primeira_linha[3])
qnt_arcos = int(primeira_linha[4])

ufs = []
vertices = []
produtos = []
creditos = []
arcos = []

if DEBUG >= 1:
    print(f"quantidade de UFs = {qnt_ufs}")
    print(f"quantidade de vértices = {qnt_vertices}")
    print(f"quantidade de produtos= {qnt_produtos}")
    print(f"quantidade de arcos= {qnt_arcos}")

# O CRÉDITO PRESUMIDO DEVE SER UM PAR UF PRODUTO.
#UFs
posi_linha = 1
linha_inicial = posi_linha 
for i in range(posi_linha, posi_linha + qnt_ufs):
    linha = linhas[i]
    partes = linha.split()
    posi_linha = i
    ufs.append(UF(i- linha_inicial, str(partes[0])))
    if DEBUG >= 1: print(f"{ufs[i - linha_inicial]}")

#vertices
linha_inicial = posi_linha + 1
for i in range(posi_linha + 1,posi_linha + qnt_vertices +1 ):
    linha = linhas[i]
    partes = linha.split()
    posi_linha = i
    vertices.append(Vertice(i - linha_inicial , str(partes[0]), int(partes[1]), str(partes[2])))
    if DEBUG >= 1: print(f"{vertices[i - linha_inicial]}")

#produtos
linha_inicial = posi_linha + 1
for i in range(posi_linha + 1,posi_linha + qnt_produtos + 1):
    linha = linhas[i]
    partes = linha.split()
    posi_linha = i
    produtos.append(Produto(i - linha_inicial , str(partes[0])))
    if DEBUG >= 1: print(f"{produtos[i - linha_inicial]}")

#credito presumido
# PRECISA DEFINIR COM FAZER FAZER O BOOL DO MODELO
linha_inicial = posi_linha + 1
for i in range(posi_linha + 1,posi_linha + qnt_credito + 1):
    linha = linhas[i]
    partes = linha.split()
    posi_linha = i
    creditos.append(Credito(i - linha_inicial , str(partes[0]),  str(partes[1]),  int(partes[2])))
    if DEBUG >= 1: print(f"{creditos[i - linha_inicial]}")

#arcos
linha_inicial = posi_linha + 1
for i in range(posi_linha + 1,posi_linha + qnt_arcos + 1):
    linha = linhas[i]
    partes = linha.split()
    posi_linha = i
    arcos.append(Arco(i-posi_linha,
                str(partes[0]), # origem
                str(partes[1]), # destino
                str(partes[2]), # produto
                float(partes[3]), # capacidade
                float(partes[4]), # custo fixo
                float(partes[5]), # custo var de frete ou cd
                float(partes[6]))) # custo var de icms (já calculado)
    if DEBUG >= 1: print(f"{arcos[i - linha_inicial]}")



modelo = Model()
Model.var_list
#  CONSTRUINDO O MODELO

# Build model
model = cp.Cplex()
model.set_problem_name("rede_logistica")
model.objective.set_sense(model.objective.sense.minimize)



print("termino de leitura")
# if __name__ == '__main__':
#     import sys
#     if len(sys.argv) > 1:
#         file_location = sys.argv[1].strip()
#         with open(file_location, 'r') as input_data_file:
#             input_data = input_data_file.read()
#         output_data = solve_it(input_data)
#         print(output_data)
#         solution_file = open(file_location + ".sol", "w")
#         solution_file.write(output_data)
#         solution_file.close()
#     else:
#         print('This test requires an input file.  Please select one from the data directory. (i.e. python main.py ./data/ks_4_0)')
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    solver()
