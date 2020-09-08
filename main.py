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
def read_data(file):
    with open(file, 'r') as input_data_file:
        input_data = input_data_file.read()
    # Reescrever restrição para de icms, de modo a ser definida no arco e não no vértice.
    # # Rever como identificar crédito presumido

    # Define as tuplas de entrada para ler os dados
    UF = namedtuple("UF", ['index', 'nome'])
    Vertice = namedtuple("vertice", ['index', 'nome', 'demanda', 'uf'])
    Produto = namedtuple("produto", ['index', 'nome'])
    Arco = namedtuple("arco",
                      ['index', 'org', 'dest', 'produto', 'capacidade', 'custo_fixo', 'custo_var', 'custo_var_icms'])
    Credito = namedtuple("credito", ['index', 'uf', 'produto', 'custo_icms'])

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
    if DEBUG >= 2:
        print(f"quantidade de UFs = {qnt_ufs}")
        print(f"quantidade de vértices = {qnt_vertices}")
        print(f"quantidade de produtos= {qnt_produtos}")
        print(f"quantidade de arcos= {qnt_arcos}")
    # O CRÉDITO PRESUMIDO DEVE SER UM PAR UF PRODUTO.

    # UFs
    posi_linha = 1
    linha_inicial = posi_linha
    for i in range(posi_linha, posi_linha + qnt_ufs):
        linha = linhas[i]
        partes = linha.split()
        posi_linha = i
        ufs.append(UF(i - linha_inicial, str(partes[0])))
        if DEBUG >= 2: print(f"{ufs[i - linha_inicial]}")

    # vertices
    linha_inicial = posi_linha + 1
    for i in range(posi_linha + 1, posi_linha + qnt_vertices + 1):
        linha = linhas[i]
        partes = linha.split()
        posi_linha = i
        vertices.append(Vertice(i - linha_inicial, str(partes[0]), int(partes[1]), str(partes[2])))
        if DEBUG >= 2: print(f"{vertices[i - linha_inicial]}")

    # produtos
    linha_inicial = posi_linha + 1
    for i in range(posi_linha + 1, posi_linha + qnt_produtos + 1):
        linha = linhas[i]
        partes = linha.split()
        posi_linha = i
        produtos.append(Produto(i - linha_inicial, str(partes[0])))
        if DEBUG >= 2: print(f"{produtos[i - linha_inicial]}")

    # credito presumido
    # PRECISA DEFINIR COM FAZER FAZER O BOOL DO MODELO
    linha_inicial = posi_linha + 1
    for i in range(posi_linha + 1, posi_linha + qnt_credito + 1):
        linha = linhas[i]
        partes = linha.split()
        posi_linha = i
        creditos.append(Credito(i - linha_inicial, str(partes[0]), str(partes[1]), int(partes[2])))
        if DEBUG >= 2: print(f"{creditos[i - linha_inicial]}")

    # arcos
    linha_inicial = posi_linha + 1
    for i in range(posi_linha + 1, posi_linha + qnt_arcos + 1):
        linha = linhas[i]
        partes = linha.split()
        posi_linha = i
        arcos.append(Arco(i - linha_inicial,
                          str(partes[0]),  # origem
                          str(partes[1]),  # destino
                          str(partes[2]),  # produto
                          float(partes[3]),  # capacidade
                          float(partes[4]),  # custo fixo
                          float(partes[5]),  # custo var de frete ou cd
                          float(partes[6])))  # custo var de icms (já calculado)
        if DEBUG >= 2: print(f"{arcos[i - linha_inicial]}")

    input = {"vertices": vertices,
             "produtos":produtos,
             "creditos":creditos,
             "arcos":arcos,
             "qnt_ufs":qnt_ufs,
             "qnt_vertices":qnt_vertices,
             "qnt_produtos":qnt_produtos,
             "qnt_credito":qnt_credito,
             "qnt_arcos": qnt_arcos,
             'qnt_fluxos': qnt_arcos * qnt_produtos}
    return input


def solve(input):
    model = cp.Cplex()
    model.set_problem_name("network_design")
    model.objective.set_sense(model.objective.sense.minimize)

    # f := variável continua, fluxo que passa pelo arco
    model.variables.add(
        names = [f'f_{a.org}_{a.dest}_{p.nome}' for a in input['arcos'] for p in input['produtos']],
        lb = [0] * input['qnt_arcos'] * input['qnt_produtos'],
        ub = [cp.infinity] * input['qnt_arcos'] * input['qnt_produtos'],
        types = [model.variables.type.continuous] * input['qnt_arcos'] * input['qnt_produtos']
    )

    # x := variável binária, 0 para arco utilizado, 1 para os arcos não utilizados.
    model.variables.add(
        names = [f'x_{a.org}_{a.dest}' for a in input['arcos']],
        # lb = [0] * input['qnt_arcos'],
        # ub = [1] * input['qnt_arcos'],
        types = [model.variables.type.binary] * input['qnt_arcos']
    )

    # balanço de massa
    for v in input['vertices']:
        for p in input['produtos']:
            arcos_entrada = []
            arcos_saida = []
            for a in input['arcos']:
                if a.dest == v.nome: arcos_entrada.append(a)
                if a.org == v.nome: arcos_saida.append(a)
            ind = [f'f_{a.org}_{a.dest}_{p.nome}' for a in arcos_entrada] \
                 + [f'f_{a.org}_{a.dest}_{p.nome}' for a in arcos_saida]
            val = [1] * len(arcos_entrada) + [-1] * len(arcos_saida)
            lhs = [cp.SparsePair(ind, val)]
            name = [f'bal_{v.nome}_{p.nome}']
            model.linear_constraints.add(names = name, lin_expr=lhs, senses=["E"], rhs=[v.demanda])

    for a in input['arcos']:
        # Fluxo deve respeitar a capacidade
        ind = [f'f_{a.org}_{a.dest}_{p.nome}' for p in range(input['qnt_produtos'])] + [f'x_{a.org}_{a.dest}']
        val = [1] * input['qnt_produtos'] + [a.capacidade]
        lhs = [cp.SparsePair(ind,val)]
        name = [f'cap_{a.org}_{a.dest}']
        model.linear_constraints.add(names = name, lin_expr = lhs, senses = ["L"], rhs = [0])


        # fluxo deve ser maior do que zero
        for p in range(input['qnt_produtos']):
            lhs = [cp.SparsePair([f'f_{a.org}_{a.dest}_{p.nome}'],[1])]
            name = [f'pos_{a.org}_{a.dest}_{p.nome}']
            model.linear_constraints.add(names = name, lin_expr = lhs, senses = ["G"], rhs = [0])


    #Obj function
    var = [f'f_{a.org}_{a.dest}_{p.nome.index}' for a in input['arcos'] for p in input['produtos']] + \
          [f'x_{a.org}_{a.dest}' for a in input['arcos']]
    val = [a.custo_var for a in input['arcos'] for p in input['produtos']] + \
          [a.custo_fixo for a in input['arcos']]

    for a in zip(var,val):
        print(a)

    print("#" * 10 + 'FO antes' + "#" * 10 )
    print(model.objective.get_linear())

    model.objective.set_linear(zip(var,val))

    print("#" * 10 + 'FO depois' + "#" * 10)
    print(model.objective.get_linear())

    #resolve o problema
    print(model.write('modelo.lp'))
    model.solve()

    print("#" * 10 + ' Valor da solução '+ "#" * 10)
    print(model.solution.get_objective_value())
    print("#" * 10 + ' Valores das variáveis ' + "#" * 10)


    fluxos = [f'f_{a.org}_{a.dest}_{p.nome}' for a in input['arcos'] for p in input['produtos']] + \
          [f'x_{a.org}_{a.dest}' for a in input['arcos']]
    output = model.solution.get_values()
    print(output)
    for i in range(len(output)):
        if output[i] != 0:
            print(str(fluxos[i]) + ": " + str(output[i]))

    for i in range(input['qnt_arcos']):
        print(model.solution.get_values(f'x_{i}'))


    # model.linear_constraints.add()
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
    file = 'dados.txt'
    input = read_data(file)
    solve(input)