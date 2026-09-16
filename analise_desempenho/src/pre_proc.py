from pathlib import Path
from datetime import datetime
import numpy as np
import yaml
import gmsh

def preprocess_mesh(model, pname, dir='.', config_file=None):
    """
    Exporta um modelo Gmsh para:
        pname000.cor
        pname.con
        pname.bv
        pname.bp
        pname000.v
        pname000.pr
    
    Gera arquivos adicionais:
        inicia.par
        pname.pro
        PARAMETER.dat

    Parâmetros:
        model : gmsh.model
        pname : string de 6 caracteres
        dir   : string do diretório
    """

    if len(pname) != 6:
        raise ValueError("pname deve possuir exatamente 6 caracteres")
    
    # Criar diretório se ele não existir
    output_dir = Path(dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # Escrever dados dos grupos físicos no console
    print_physical_groups(model)

    # Faz query dos dados
    if config_file is None:
        print(f"Sem arquivo config - Executando em modo manual\n")
        bc = query_boundary_conditions(model)
        parameters = query_parameters()
        fluid_properties = query_fluid_properties()
    else:
        print(f"Arquivo config {config_file} - Executando em modo automático\n")
        bc, parameters, fluid_properties = load_config(config_file)

    # Arquivo de coordenadas 000.cor
    write_cor_file(model, pname, output_dir)

    # Arquivo de conectividade .con
    write_con_file(model, pname, output_dir)

    # Converte condições de contorno físicas em valores nodais
    node_bc = get_nodal_boundary_conditions(model, bc)

    # Arquivos de condição de contorno CC.bv e CC.bp
    write_bc_files(node_bc, pname, output_dir)

    # Arquivos de condição inicial 000.v e 000.pr
    write_initial_conditions(model, pname, output_dir)

    # Arquivos de objetos imersos CS##.nnn e CS##.sup
    write_immersed_object_files(model, bc, pname, output_dir)

    # Arquivo de parâmetro de simulação inicia.par
    write_inicia_par(parameters, pname, output_dir)

    # Arquivo de parâmetro de simulação .pro
    write_properties_file(model, fluid_properties, bc, pname, output_dir)

    # Arquivo auxiliar com o bloco PARAMETER para inclusão no código .cuf
    write_parameters_dat(pname, model, bc, node_bc, output_dir)

    # Salvar config
    if config_file is None:
        config = {
            "boundary_conditions": bc,
            "parameters": parameters,
            "fluid_properties": fluid_properties
        }

        save_config_file(config, output_dir)

def write_cor_file(model, pname, output_dir):
    """
    Escreve o arquivo de coordenadas dos nós - pname000.cor

    Parâmetros:
        model: gmsh.model ativo
        pname: nome do projeto
        output_dir: diretório de destino
    """

    # Obtém todos os nós
    node_tags, coords, _ = model.mesh.getNodes()

    with open(output_dir / f"{pname}000.cor", "w") as f:

        # Número de nós
        f.write(f"{len(node_tags)}\n")

        # Coordenadas dos nós
        for i in range(len(node_tags)):
            x = coords[3*i]
            y = coords[3*i+1]
            z = coords[3*i+2]

            f.write(
                f"{x:.16e} {y:.16e} {z:.16e}\n"
            )

def write_con_file(model, pname, output_dir):
    """
    Escreve o arquivo de conectividade da malha - pname.con

    Parâmetros:
        model: gmsh.model ativo
        pname: nome do projeto
        output_dir: diretório de destino
    """

    # Pega elementos de dimensão 3
    elem_types, elem_tags, elem_nodes = model.mesh.getElements(3)

    # Verificar se há somente 1 tipo de elemento
    if len(elem_types) != 1:
        raise RuntimeError(
            "A malha deve possuir apenas um tipo de elemento de dimensão 3"
        )

    elem_type = elem_types[0]

    # Verificar se é hexaedro de 8 nós
    if elem_type != 5:
        raise RuntimeError(
            f"Elemento {elem_type} encontrado. "
            "Esperado hexaedro Gmsh tipo 5."
        )

    # Extrair IDs dos elementos e conectividade
    elements = elem_tags[0]
    connectivity = elem_nodes[0]

    nodes_per_element = 8
    n_elements = len(elements)

    # Armazenar no arquivo .con
    with open(output_dir / f"{pname}.con", "w") as f:

        # Número de elementos
        f.write(f"{n_elements}\n")

        for i in range(n_elements):

            # Pega os nós do elemento i
            nodes = connectivity[i*nodes_per_element:(i+1)*nodes_per_element]

            # Escreve as IDs lado a lado, separado por espaço
            f.write(" ".join(str(n) for n in nodes) + "\n")

def print_physical_groups(model):
    """
    Lista os grupos físicos presentes no modelo Gmsh.

    Parâmetros:
        model: gmsh.model ativo
    """

    # Pega todos os grupos físicos
    physical_groups = model.getPhysicalGroups()

    if not physical_groups:
        print("Nenhum grupo físico encontrado.")
        return

    # Escreve a lista de grupos físicos
    print("\nGrupos físicos encontrados:")
    print("-" * 70)

    # Para cada grupo físico
    for dim, phys_id in physical_groups:

        # Nome
        name = model.getPhysicalName(dim, phys_id)

        # Tipo (superfície ou volume)
        if dim == 2:
            kind = "Superfície"
        elif dim == 3:
            kind = "Volume"
        else:
            kind = f"Dimensão {dim}"

        # Entidades geométricas associadas
        entities = model.getEntitiesForPhysicalGroup(dim, phys_id)

        # Inicia conjunto sem duplicatas, função nativa do Python
        node_set = set()
        element_count = 0

        # Para cada entidade geométrica do grupo físico (superfícies, curvas, etc)
        for entity in entities:

            # Pegar todos os elementos da entidade e suas componentes
            _, elem_tags, elem_nodes = (
                model.mesh.getElements(
                    dim,
                    entity
                )
            )

            # Para cada elemento e seus nós
            for tags, nodes in zip(
                elem_tags,
                elem_nodes
            ):
                # Adiciona um ao número de elementos
                element_count += len(tags)

                # Adiciona os nós ao conjunto, automaticamente descarta duplicatas
                for n in nodes:
                    node_set.add(n)

        # Escreve resultados
        print(f"Nome:      {name}")
        print(f"ID:        {phys_id}")
        print(f"Tipo:      {kind}")
        print(f"Elementos: {element_count}")
        print(f"Nós:       {len(node_set)}")
        print("-" * 70)

def query_bc_from_group(group_name):
    """
    Pergunta ao usuário qual condição de contorno
    deve ser aplicada a um grupo físico.

    Retorna um dicionário com as condições nodais.
    None significa componente livre.

    Parâmetros:
        group_name: nome do grupo físico
    """

    # Lista de opções
    options = {
        1: "Wall",
        2: "Slip Wall / Simetria",
        3: "Moving Wall",
        4: "Inlet Constante",
        5: "Inlet Lei de Potência",
        6: "Pressure Outlet",
        7: "Objeto Imerso"
    }

    # Escreve qual o grupo
    print("\nGrupo físico:", group_name)

    # Escreve as opções
    for key, name in options.items():
        print(f"{key} - {name}")

    # Faz querry
    choice = int(input("Escolha a condição: "))

    # -------------------------
    # Wall
    # -------------------------

    if choice == 1:

        bc = {
            "type": "nodal",

            "u": 0.0,
            "v": 0.0,
            "w": 0.0,
            "p": None
        }

    # -------------------------
    # Slip Wall
    # -------------------------

    elif choice == 2:

        # Perguntar a normal da parede pra ver qual velocidade zerar
        print("\nDireção da normal:")
        print("1 - X")
        print("2 - Y")
        print("3 - Z")

        normal = int(
            input("Escolha: ")
        )

        if normal == 1:
            bc = {
                "type": "nodal",

                "u": 0.0,
                "v": None,
                "w": None,
                "p": None
            }

        elif normal == 2:
            bc = {
                "type": "nodal",

                "u": None,
                "v": 0.0,
                "w": None,
                "p": None
            }

        elif normal == 3:
            bc = {
                "type": "nodal",

                "u": None,
                "v": None,
                "w": 0.0,
                "p": None
            }

        else:
            raise ValueError(
                "Normal inválida"
            )

    # -------------------------
    # Moving Wall
    # -------------------------

    elif choice == 3:

        # Perguntar a direção do movimento pra ver qual velocidade setar
        print("\nDireção do movimento:")
        print("1 - X")
        print("2 - Y")
        print("3 - Z")

        direction = int(
            input("Escolha: ")
        )

        # Perguntar velocidade
        value = float(
            input("Velocidade da parede: ")
        )

        if direction == 1:
            bc = {
                "type": "nodal",

                "u": value,
                "v": 0.0,
                "w": 0.0,
                "p": None
            }

        elif direction == 2:
            bc = {
                "type": "nodal",

                "u": 0.0,
                "v": value,
                "w": 0.0,
                "p": None
            }

        elif direction == 3:
            bc = {
                "type": "nodal",

                "u": 0.0,
                "v": 0.0,
                "w": value,
                "p": None
            }

        else:
            raise ValueError(
                "Direção inválida"
            )

    # -------------------------
    # Inlet Constante
    # -------------------------

    elif choice == 4:

        # Perguntar a direção da velocidade pra ver qual velocidade setar
        print("\nDireção da velocidade:")
        print("1 - X")
        print("2 - Y")
        print("3 - Z")

        direction = int(
            input("Escolha: ")
        )

        # Perguntar velocidade
        value = float(
            input("Velocidade: ")
        )

        if direction == 1:
            bc = {
                "type": "nodal",

                "u": value,
                "v": None,
                "w": None,
                "p": None
            }

        elif direction == 2:
            bc = {
                "type": "nodal",

                "u": None,
                "v": value,
                "w": None,
                "p": None
            }

        elif direction == 3:
            bc = {
                "type": "nodal",

                "u": None,
                "v": None,
                "w": value,
                "p": None
            }

        else:
            raise ValueError(
                "Direção inválida"
            )

    # -------------------------
    # Inlet Lei de Potência
    # -------------------------

    elif choice == 5:

        # -------------------------
        # Direção de crescimento
        # -------------------------

        print("\nDireção de crescimento do perfil")

        gx = float(
            input("gx: ")
        )

        gy = float(
            input("gy: ")
        )

        gz = float(
            input("gz: ")
        )

        # -------------------------
        # Direção do escoamento
        # -------------------------

        print("\nDireção do escoamento")

        dx = float(
            input("dx: ")
        )

        dy = float(
            input("dy: ")
        )

        dz = float(
            input("dz: ")
        )

        # -------------------------
        # Parâmetros do perfil
        # -------------------------

        hmin = float(
            input("Altura zero (h_min): ")
        )

        href = float(
            input("Altura de referência (h_ref): ")
        )

        uref = float(
            input("Velocidade de referência (U_ref): ")
        )

        exponent = float(
            input("Expoente da lei de potência: ")
        )

        # Normalizar a direção do crescimento e verificar se é válida
        growth = np.asarray([gx, gy, gz], dtype=float)

        norm = np.linalg.norm(growth)

        if norm == 0:
            raise ValueError(
                "Direção de crescimento não pode ser nula"
            )

        growth /= norm

        # Normalizar a direção da velocidade e verificar se é válida
        direction = np.asarray([dx, dy, dz], dtype=float)

        norm = np.linalg.norm(growth)

        if norm == 0:
            raise ValueError(
                "Direção da velocidade não pode ser nula"
            )

        direction /= norm

        # Armazenar condições
        bc = {
            "type": "power_law",
            "growth_direction": growth,
            "flow_direction": direction,
            "h_min": hmin,
            "h_ref": href,
            "U_ref": uref,
            "exponent": exponent
        }

    # -------------------------
    # Pressure Outlet
    # -------------------------

    elif choice == 6:

        # Perguntar pressão
        pressure = float(
            input("Pressão prescrita: ")
        )

        bc = {
                "type": "nodal",

                "u": None,
                "v": None,
                "w": None,
                "p": pressure
            }
    
    # -------------------------
    # Objeto Imerso
    # -------------------------

    elif choice == 7:

        # Perguntar Dchar e Lchar
        Dchar = float(
            input("Diâmetro característico: ")
        )

        Lchar = float(
            input("Comprimento característico: ")
        )

        bc = {
            "type": "object",

            "Dchar": Dchar,
            "Lchar": Lchar,
        }

    else:
        raise ValueError(
            "Condição inválida"
        )

    return bc

def query_boundary_conditions(model):
    """
    Organiza para fazer o query de todos os
    grupos físicos do modelo.

    Parâmetros:
        model: gmsh.model ativo
    """

    # Dict com as condições de contorno
    bc = {}

    # Percorre grupos físicos
    for dim, tag in model.getPhysicalGroups():

        # Somente superfícies
        if dim != 2:
            continue

        # Pega o nome
        name = model.getPhysicalName(
            dim,
            tag
        )

        # Faz o querry
        bc[tag] = query_bc_from_group(name)
    
    return bc

def get_physical_group_nodes(model, dim, tag):
    """
    Função auxiliar que retorna todos os nós pertencentes a um grupo físico.

    Parâmetros:
        model: gmsh.model ativo
        dim: dimensão das entidades geométricas e elementos
        tag: ID do grupo físico
    """

    # Pega as entidades geométricas
    entities = model.getEntitiesForPhysicalGroup(
        dim,
        tag
    )

    # Cria um conjunto sem duplicatas
    nodes = set()

    # Para cada entidade
    for entity in entities:

        # Pega os elementos
        _, _, elem_nodes = model.mesh.getElements(
            dim,
            entity
        )

        # Pega os nós do elemento
        for conn in elem_nodes:

            # Adiciona ao conjunto
            for node in conn:
                nodes.add(node)

    return nodes

def get_physical_group_quads(model, dim, tag):
    """
    Função auxiliar que retorna todos os quads pertencentes a um grupo físico.

    Parâmetros:
        model: gmsh.model ativo
        dim: dimensão das entidades geométricas e elementos
        tag: ID do grupo físico
    """

    # Pega as entidades geométricas
    entities = model.getEntitiesForPhysicalGroup(
        dim,
        tag
    )

    # Listas acumuladoras
    all_elem_tags = []
    all_elem_nodes = []

    # Para cada entidade
    for entity in entities:

        # Pega os elementos
        elem_types, elem_tags, elem_nodes = model.mesh.getElements(
            dim,
            entity
        )

        # Verificar se há somente 1 tipo de elemento
        if len(elem_types) != 1:
            raise RuntimeError(
                "A malha deve possuir apenas um tipo de elemento de dimensão 2"
            )

        elem_type = elem_types[0]

        # Verificar se é hexaedro de 8 nós
        if elem_type != 3:
            raise RuntimeError(
                f"Elemento {elem_type} encontrado. "
                "Esperado quadrilátero Gmsh tipo 3."
            )
        
        # Acumula os dados
        all_elem_tags.extend(elem_tags[0])
        all_elem_nodes.extend(elem_nodes[0])

    return all_elem_tags, all_elem_nodes

def get_phys_group_center(model, dim, tag):
    """
    Função auxiliar que retorna o centro geométrico de um grupo físico.
    Por padrão, ele usa o centro da bouding box.
    Para geometrias mais complexas, isso pode não corresponder exatamente ao centroide.

    Parâmetros:
        model: gmsh.model ativo
        dim: dimensão das entidades geométricas e elementos
        tag: ID do grupo físico
    """

    # Pega as entidades geométricas
    entities = model.getEntitiesForPhysicalGroup(
        dim,
        tag
    )

    xmin = ymin = zmin = 1e30
    xmax = ymax = zmax = -1e30

    # Para cada entidade
    for entity in entities:
        x0, y0, z0, x1, y1, z1 = model.getBoundingBox(dim, entity)

        # Atualizar mínimos e máximos do grupo
        xmin = min(xmin, x0)
        ymin = min(ymin, y0)
        zmin = min(zmin, z0)

        xmax = max(xmax, x1)
        ymax = max(ymax, y1)
        zmax = max(zmax, z1)

    # Centro vai ser o midpoint entre mínimo e máximo
    xobj = 0.5 * (xmin + xmax)
    yobj = 0.5 * (ymin + ymax)
    zobj = 0.5 * (zmin + zmax)

    return xobj, yobj, zobj

def nodal_bc_values(model, nodes, bc):
    """
    Função auxiliar que transforma o dict das
    condições de contorno de um único grupo em valores nodais

    Parâmetros:
        model: gmsh.model ativo
        nodes: conjunto de nós com condição de contorno
        bc: dict com as condições de contorno
    """

    # Dict
    node_values = {}

    # Caso as condições originais sejam do tipo nodal
    if bc["type"] == "nodal":

        # Para cada nó
        for node in nodes:

            # Copiar o valor correspondente
            node_values[node] = {
                "u": bc["u"],
                "v": bc["v"],
                "w": bc["w"],
                "p": bc["p"]
            }

        return node_values

    # Caso as condições originais sejam do tipo Lei de Potência
    elif bc["type"] == "power_law":

        # Obtém lista de nós e coordenadas
        node_tags, coords, _ = model.mesh.getNodes()

        # Dicionário ID -> coordenada
        node_coord = {}

        # Para cada nó
        for i, tag in enumerate(node_tags):

            # Extrair coordenadas como um Vetor 3D
            node_coord[tag] = np.asarray(
                [
                    coords[3*i],
                    coords[3*i+1],
                    coords[3*i+2]
                ],
                dtype=float
            )

        # Extrair valores para a fórmula da Lei de Potência
        growth = bc["growth_direction"]
        direction = bc["flow_direction"]

        h_min = bc["h_min"]
        h_ref = bc["h_ref"]

        u_ref = bc["U_ref"]
        exponent = bc["exponent"]

        # Para cada nó
        for node in nodes:

            # Vetor posição do nó
            x = node_coord[node]

            # Altura na direção de crescimento
            h = np.dot(x, growth)

            # Se for maior que o mínimo
            if h > h_min:

                # Aplicar lei de potência
                magnitude = u_ref * ((h - h_min) / h_ref) ** exponent

            # Caso contrário
            else:

                # Velocidade zero
                magnitude = 0.0

            # Velocidade vetorial
            velocity = magnitude * direction

            # Armazenar componentes
            node_values[node] = {
                "u": velocity[0],
                "v": velocity[1],
                "w": velocity[2],
                "p": None
            }
        
        return node_values
    
    # Caso as condições originais sejam do tipo objeto imerso
    elif bc["type"] == "object":

        # Para cada nó
        for node in nodes:

            # Usar as condições de parede
            node_values[node] = {
                "u": 0.0,
                "v": 0.0,
                "w": 0.0,
                "p": None
            }

        return node_values

    else:
        raise ValueError(
            f"Tipo de condição desconhecido: {bc['type']}"
        )

def merge_condition(old, new):
    """
    Função auxiliar que define qual a condição de contorno é mais restritiva.

    None  -> livre
    float -> valor imposto

    Parâmetros:
        old: condição de contorno existente
        new: condição de contorno nova
    """

    # Se apenas uma condição não for none, é simplesmente ela
    if old is None:
        return new

    if new is None:
        return old

    # Se ambas são condições impostas: escolhe o menor módulo
    if abs(new) < abs(old):
        return new
    return old

def merge_nodal_bc(old_bc, new_bc):
    """
    Função auxiliar que combina condições de contorno nodais
    
    Parâmetros:
        old_bc: condição de contorno existente
        new_bc: condição de contorno nova
    """

    # Dict
    result = {}

    # Para cada componente
    for comp in ["u", "v", "w", "p"]:

        # Utiliza a lógica de restritividade para decidir qual manter
        result[comp] = merge_condition(
            old_bc[comp],
            new_bc[comp]
        )

    return result

def get_nodal_boundary_conditions(model, bc):
    """
    Obtém os valores nodais numéricos das condições de contorno.
    
    Parâmetros:
        model: gmsh.model ativo
        bc: dict com as condições de contorno
    """

    # Dict com as condições de contorno
    node_bc = {}

    # Percorre grupos físicos
    for dim, tag in model.getPhysicalGroups():

        # Somente superfícies
        if dim != 2:
            continue

        # Obtém os nós
        nodes = get_physical_group_nodes(
            model,
            dim,
            tag
        )

        # Obter os valores nodais correspondentes às condições de contorno
        node_values = nodal_bc_values(
            model,
            nodes,
            bc[tag]
        )

        # Para cada nó que pertence ao grupo físico
        for node in nodes:

            # Se o nó não estiver na lista, adicionar com condição de contorno livre como padrão
            if node not in node_bc:

                node_bc[node] = {
                    "u": None,
                    "v": None,
                    "w": None,
                    "p": None
                }

            # Combina as condições de contorno do nó da lista com as do grupo físico
            # Mantém sempre a condição mais restritiva
            node_bc[node] = merge_nodal_bc(
                node_bc[node],
                node_values[node]
            )
    
    return node_bc

def write_bc_files(node_bc, pname, output_dir):
    """
    Escreve os arquivos de condição de contorno - pname.bv, pname.bp

    Parâmetros:
        model: gmsh.model ativo
        pname: nome do projeto
        output_dir: diretório de destino
    """

    # Verificar se o nome tem o comprimento correto
    if len(pname) != 6:
        raise ValueError(
            "pname deve ter exatamente 6 caracteres"
        )

    # --------------------------
    # Arquivo .bv
    # --------------------------

    with open(output_dir / f"{pname}CC.bv", "w") as f:

        # Opera em cada componente separadamente
        for comp in ["u", "v", "w"]:

            # Pega todos os nos em que a componente não é Livre/None
            data = [
                (node, bc[comp])
                for node, bc in node_bc.items()
                if bc[comp] is not None
            ]

            # Escreve o número de nós com condição naquela componente
            f.write(
                f"{len(data)}\n"
            )

            # Para cada nó
            for node, value in data:

                # Armazenar número do nó e valor da condição
                f.write(
                    f"{node} {value:.17e}\n"
                )

    # --------------------------
    # Arquivo .bp
    # --------------------------

    # Pega todos os nos em que a pressão não é Livre/None
    data = [
        (node, bc["p"])
        for node, bc in node_bc.items()
        if bc["p"] is not None
    ]

    with open(output_dir / f"{pname}CC.bp", "w") as f:

        # Escreve o número de nós com condição na pressão
        f.write(
            f"{len(data)}\n"
        )

        # Para cada nó
        for node, value in data:

            # Armazenar número do nó e valor da condição de pressão
            f.write(
                f"{node} {value:.17e}\n"
            )
    
    return node_bc

def write_initial_conditions(model, pname, output_dir):
    """
    Exporta condições iniciais:

        pname000.v
        pname000.pr

    Procura por NodeData no modelo gmsh:
        "Initial Velocity"
        "Initial Pressure"

    Caso não existam, usa zero em todo domínio.

    Parâmetros:
        model: gmsh.model ativo
        pname: nome do projeto
        output_dir: diretório de destino
    """

    # -------------------------
    # Nós
    # -------------------------

    node_tags, _, _ = model.mesh.getNodes()

    node_tags = list(node_tags)

    #n_nodes = len(node_tags)

    # Dict com valores padrão usados se os blocos não forem encontrados
    velocity_ic = {
        node: [0.0, 0.0, 0.0]
        for node in node_tags
    }

    pressure_ic = {
        node: 0.0
        for node in node_tags
    }

    # Booleans pra registrar se os blocos foram encontrados
    initial_velocity_found = False
    initial_pressure_found = False

    # -------------------------
    # Procura NodeData
    # -------------------------

    # As views incluem NodeData, ElementData e ElementNodeData
    for view in gmsh.view.getTags():

        # Pegamos o nome da view
        name = gmsh.option.getString(f'View[{gmsh.view.getIndex(view)}].Name')

        # Se for "Initial Velocity", é o campo inicial de velocidade
        if name == "Initial Velocity":

            # Encontrado
            initial_velocity_found = True

            # Pega todos os dados da view
            data = gmsh.view.getModelData(view, 0)

            # Extrai somente IDs e valores
            _, tags, values, _, _ = data

            # Para cada nó
            for node, value in zip(tags, values):

                # Armazena a velocidade
                velocity_ic[node] = [
                    float(value[0]),
                    float(value[1]),
                    float(value[2])
                ]

        # Se for "Initial Pressure", é o campo inicial de pressão
        elif name == "Initial Pressure":

            # Encontrado
            initial_pressure_found = True

            # Pega todos os dados da view
            data = gmsh.view.getModelData(view, 0)

            # Extrai somente IDs e valores
            _, tags, values, _, _ = data

            # Para cada nó
            for node, value in zip(tags, values):
                
                # Armazena a pressão
                pressure_ic[node] = value[0]
        
    # Avisa se um campo não for encontrado
    if initial_velocity_found is False:
        print('Campo inicial de velocidades não encontrado no arquivo .msh, adotou-se condição inicial nula.')
    
    if initial_pressure_found is False:
        print('Campo inicial de pressões não encontrado no arquivo .msh, adotou-se condição inicial nula.')

    # -------------------------
    # Arquivos
    # -------------------------

    # Velocidade
    with open(output_dir / f"{pname}000.v", "w") as f:

        for node in node_tags:

            u, v, w = velocity_ic[node]

            f.write(
                f"{u:.16e} "
                f"{v:.16e} "
                f"{w:.16e}\n"
            )


    # Pressão
    with open(output_dir / f"{pname}000.pr", "w") as f:

        for node in node_tags:

            p = pressure_ic[node]

            f.write(
                f"{p:.16e}\n"
            )

def write_immersed_object_files(model, bc, pname, output_dir):
    """
    Escreve os arquivos de objetos imersos:

        pnameCS##.nnn
        pnameCS##.sup

    onde ## é o número sequencial do objeto.

    Arquivo .nnn:
        NODE nx ny nz

    Arquivo .sup:
        ID
        Area N1 N2 N3 N4

    Parâmetros:
        model: gmsh.model ativo
        bc: dict de condições de contorno
        pname: nome do projeto
        output_dir: diretório de destino
    """

    object_id = 1

    for tag, group in bc.items():

        if group["type"] != "object":
            continue

        # Nós da superfície sólida
        node_tags = get_physical_group_nodes(
            model,
            2,
            tag
        )

        # Quads da superfície sólida
        quad_tags, quad_nodes = get_physical_group_quads(
            model,
            2,
            tag
        )

        # Guarda as coordenadas dos nós
        coords = {}

        for node in node_tags:
            xyz = model.mesh.getNode(node)[0]
            coords[node] = np.array(xyz)
        
        # Centro da bouding box para reorientação das normais
        obj_center = np.asarray(get_phys_group_center(model, 2, tag))

        # Acumulador de normais nodais ponderadas pela área
        node_normals = {
            node: np.zeros(3)
            for node in node_tags
        }

        # Dados das faces para escrever depois
        sup_data = []

        for i, quad_id in enumerate(quad_tags):

            # Conectividade
            local_quad_nodes = quad_nodes[4*i:4*i+4]
            n1, n2, n3, n4 = local_quad_nodes

            # Coordenadas
            p1 = coords[n1]
            p2 = coords[n2]
            p3 = coords[n3]
            p4 = coords[n4]

            # Divide o quad em dois triângulos
            a1 = 0.5 * np.cross(
                p2 - p1,
                p3 - p1
            )

            a2 = 0.5 * np.cross(
                p3 - p1,
                p4 - p1
            )

            # Vetor área da face
            Avec = a1 + a2
            area = np.linalg.norm(Avec)

            if area == 0.0:
                continue

            # Centro do quad
            quad_center = np.mean([p1, p2, p3, p4], axis=0)

            # Vetor do centro do objeto para a face
            d = quad_center - obj_center

            # Verificar e ajustar orientação

            # PS: A orientação é verificada de acordo com o centro da bouding box do objeto imerso,
            # nesse caso adota-se a normal apontando para DENTRO DO DOMÍNIO FLUIDO como padrão,
            # objetos com formas mais complexas que não forem reduzidos a formas simples podem apresentar problemas.
            # Mais especificamente, a reorientação pode dar problema se o objeto não for estrela-convexo em relação
            # ao centro da bounding box. Objetos geométricos simples como caixas, cilindros, esferas, pirâmides
            # prismas e paralelepípedos não devem dar problema.

            # PS2: Seria possível, e talvez até desejável, que a orientação da normal seja definida
            # durante a própria confecção da malha usando a ordem de conectividade do elemento, mas
            # as ferramentas do gmsh para isso parecem um pouco limitadas.
            if np.dot(d, Avec) < 0.0:
                Avec *= -1

            # Soma contribuição nos nós
            for node in local_quad_nodes:
                node_normals[node] += Avec

            # Armazena dados do quad
            sup_data.append(
                (
                    quad_id,
                    area,
                    local_quad_nodes
                )
            )

        # Normaliza normais nodais
        for node in node_normals:

            norm = np.linalg.norm(
                node_normals[node]
            )

            if norm > 0:
                node_normals[node] /= norm


        # -------------------------------------------------
        # Escreve .nnn
        # -------------------------------------------------

        with open(output_dir / f"{pname}CS{object_id:02d}.nnn", "w") as f:

            for node in node_tags:

                nx, ny, nz = node_normals[node]

                f.write(
                    f"{node} "
                    f"{nx:.16E} "
                    f"{ny:.16E} "
                    f"{nz:.16E}\n"
                )


        # -------------------------------------------------
        # Escreve .sup
        # -------------------------------------------------

        with open(output_dir / f"{pname}CS{object_id:02d}.sup", "w") as f:

            for quad_id, area, quad_nodes in sup_data:

                n1, n2, n3, n4 = quad_nodes

                f.write(
                    f"{quad_id}\n"
                )

                f.write(
                    f"{area:.16E} "
                    f"{n1} "
                    f"{n2} "
                    f"{n3} "
                    f"{n4}\n"
                )

        object_id += 1

def query_parameters():
    """
    Questionário dos dados do inicia.par
    """

    # Querry padrão para dados inteiros
    def ask_int(message, default):

        value = input(
            f"{message} [{default}]: "
        )

        if value.strip() == "":
            return default

        return int(value)

    # Querry padrão para dados float
    def ask_float(message, default):

        value = input(
            f"{message} [{default}]: "
        )

        if value.strip() == "":
            return default

        return float(value)


    print("\n=== Parametros inicia.par ===\n")

    # Dict
    params = {}


    params["NCOEF"] = ask_int(
        """
NCOEF:
Numero de intervalos entre registros dos coeficientes aerodinamicos.
Valores menores aumentam a frequencia de armazenamento.
""",
        100
    )


    params["NIR"] = ask_int(
        """
NIR:
Numero de passos de tempo entre registros dos campos
de velocidade e pressao.
""",
        10000
    )


    params["NTR"] = ask_int(
        """
NTR:
Numero total de registros da simulacao.

O tempo total sera:
Ttot = NIR * NTR * DtMAX
""",
        10
    )


    params["NFILE"] = ask_int(
        """
NFILE:
Numero do arquivo de restart utilizado.

Use 0 para uma simulacao nova.
""",
        0
    )


    params["DtMAX"] = ask_float(
        """
DtMAX:
Estimativa inicial do incremento de tempo.

Normalmente relacionado a:
Dt < DeltaX / (c + V)

Valores maiores podem comprometer estabilidade.
""",
        0.0001
    )


    params["TPOAC"] = ask_float(
        """
TPOAC:
Tempo atual da simulacao.

Normalmente 0 para uma simulacao nova.
""",
        0.0
    )


    params["TOLTPO"] = ask_float(
        """
TOLTPO:
Tolerancia de residuo temporal.

Usado para detectar regime estacionario.
""",
        1.0e-6
    )


    params["NROTPO"] = ask_int(
        """
NROTPO:
Numero de passos adicionais apos atingir a tolerancia.
""",
        100
    )


    params["CSEGUR"] = ask_float(
        """
CSEGUR:
Coeficiente de seguranca temporal.

Valores menores aumentam estabilidade.
Laminar: ~0.7
Turbulento: 0.1-0.3
""",
        0.2
    )


    params["CONTROL1"] = ask_float(
        """
CONTROL1:
Controle de integracao reduzida para controle de modos espurios.

0 = desativado
1 = ativado
""",
        1.0
    )


    params["NPASS"] = ask_int(
        """
NPASS:
Numero de passos de tempo a partir do qual
sao calculados campos medios.
""",
        50000
    )


    params["INDTURB"] = ask_int(
        """
INDTURB:
Modelo de turbulencia.

0 = sem turbulencia
1 = modelo sub-malha classico
2 = modelo dinamico com 1 ponto
3 = modelo dinamico com 8 pontos
""",
        2
    )


    params["ELUMP1"] = ask_float(
        """
ELUMP1:
Parametro seletivo de massa da equacao de continuidade.
""",
        0.9
    )


    params["ELUMP2"] = ask_float(
        """
ELUMP2:
Parametro seletivo de massa da equacao de energia.
""",
        0.9
    )


    params["ELUMP3"] = ask_float(
        """
ELUMP3:
Parametro seletivo de massa da equacao de especie.
""",
        0.9
    )


    params["NTHREADS"] = ask_int(
        """
NTHREADS:
Numero de threads por bloco de processamento.
Recomendado utilizar potencia de 2.
""",
        128
    )


    return params

def write_inicia_par(params, pname, output_dir):
    """
    Escreve o arquivo inicia.par
    
    Parâmetros:
        params: dict com os parâmetros
        pname: nome do projeto
        output_dir: diretório de destino
    """

    with open(output_dir / f"inicia.par", "w") as f:

        f.write(f"{pname} ! PNAME\n")

        f.write(f"{params['NCOEF']:17d} ! NCOEF\n")
        f.write(f"{params['NIR']:17d} ! NIR\n")
        f.write(f"{params['NTR']:17d} ! NTR\n")
        f.write(f"{params['NFILE']:17d} ! NFILE\n")

        f.write(f"{params['DtMAX']:17.12E} ! DtMAX\n")
        f.write(f"{params['TPOAC']:17.12E} ! TPOAC\n")
        f.write(f"{params['TOLTPO']:17.12E} ! TOLTPO\n")

        f.write(f"{params['NROTPO']:17d} ! NROTPO\n")

        f.write(f"{params['CSEGUR']:17.12E} ! CSEGUR\n")
        f.write(f"{params['CONTROL1']:17.12E} ! CONTROL1\n")

        f.write(f"{params['NPASS']:17d} ! NPASS\n")

        f.write(f"{params['INDTURB']:17d} ! INDTURB\n")

        f.write(f"{params['ELUMP1']:17.12E} ! ELUMP1\n")
        f.write(f"{params['ELUMP2']:17.12E} ! ELUMP2\n")
        f.write(f"{params['ELUMP3']:17.12E} ! ELUMP3\n")

        f.write(f"{params['NTHREADS']:17d} ! NTHREADS\n")

def query_fluid_properties():
    """
    Questionário das propriedades físicas do fluido
    """

    # Querry padrão para dados float
    def ask_float(message, default):

        value = input(
            f"{message} [{default}]: "
        )

        if value.strip() == "":
            return default

        return float(value)


    print("\n=== Propriedades do fluido (.pro) ===\n")

    # Dict
    prop = {}


    prop["VInf"] = ask_float(
        """
VInf:
Velocidade de referencia do escoamento.

Define a escala de velocidade do problema.
""",
        10.0
    )


    prop["VelSom"] = ask_float(
        """
VelSom:
Velocidade do som utilizada pelo solver.

Frequentemente ajustada artificialmente para
controlar o passo de tempo.
""",
        50.0
    )


    prop["ViscCin"] = ask_float(
        """
ViscCin:
Viscosidade cinematica do fluido [m2/s].

Tipicamente ajustada para obter o número de Reynolds desejado.

Exemplos físicos:
Ar ~1.5e-5
Agua ~1.0e-6
""",
        0.01
    )


    prop["ViscVol"] = ask_float(
        """
ViscVol:
Viscosidade volumetrica.

Pode-se adotar zero para escoamentos incompressíveis.
""",
        0.0
    )


    prop["RHOInf"] = ask_float(
        """
RHOInf:
Densidade do fluido [kg/m3].

Tipicamente adotada como unitária.

Exemplos físicos:
Ar ~1.2
Agua ~997
""",
        1.0
    )


    prop["Cv"] = ask_float(
        """
Cv:
Calor especifico a volume constante.

Nao utilizado atualmente.
""",
        1.0e-8
    )


    prop["Kdif"] = ask_float(
        """
Kdif:
Coeficiente de condutividade termica.

Nao utilizado atualmente.
""",
        1.0e-8
    )


    prop["Cs"] = ask_float(
        """
Cs:
Constante de Smagorinsky.

Usada somente em modelos LES com Smagorinsky Clássico.
""",
        0.15
    )


    prop["Prtlt"] = ask_float(
        """
Prtlt:
Numero de Prandtl turbulento.

Nao utilizado atualmente.
""",
        1.0e-8
    )


    prop["Dab"] = ask_float(
        """
Dab:
Coeficiente de difusividade massica.

Nao utilizado atualmente.
""",
        1.0e-8
    )


    return prop

def write_properties_file(model, prop, bc, pname, output_dir):
    """
    Escreve o arquivo pname.pro
    
    Parâmetros:
        model: gmsh.model ativo
        prop: dict com os parâmetros
        bc: dict com as condições de contorno
        pname: nome do projeto
        output_dir: diretório de destino
    """

    with open(output_dir / f"{pname}.pro", "w") as f:

        values = [
            ("VInf",   prop["VInf"]),
            ("VelSom", prop["VelSom"]),
            ("ViscCin", prop["ViscCin"]),
            ("ViscVol", prop["ViscVol"]),
            ("RHOInf", prop["RHOInf"]),
            ("Cv", prop["Cv"]),
            ("Kdif", prop["Kdif"]),
            ("Cs", prop["Cs"]),
            ("Prtlt", prop["Prtlt"]),
            ("Dab", prop["Dab"]),
        ]


        for name, value in values:

            f.write(
                f"{value:17.12E} ! {name}\n"
            )
        
        # Objeto imersos
        for tag, group in bc.items():

            # Pular se não for objeto imerso
            if group["type"] != "object":
                continue

            # Lchar
            f.write(
                f"{group["Lchar"]} ! Lchar\n"
            )

            # Dchar
            f.write(
                f"{group["Dchar"]} ! Dchar\n"
            )

            # Coordenadas do centro geométrico
            xobj, yobj, zobj = get_phys_group_center(model, 2, tag)

            # Coordenadas
            f.write(
                f"{xobj} ! xobj\n"\
                f"{yobj} ! yobj\n"\
                f"{zobj} ! zobj\n"
            )

            # Pegar os quads do grupo físico
            quads, _ = get_physical_group_quads(model, 2, tag)

            # NFCN
            f.write(
                f"{len(quads)} ! NFCN\n"
            )

            # Pegar os nós do contorno sólido
            nodes = get_physical_group_nodes(model, 2, tag)

            # NNCN
            f.write(
                f"{len(nodes)} ! NNCN\n"
            )

def write_parameters_dat(pname, model, bc, node_bc, output_dir):
    """
    Gera arquivo auxiliar parameters.dat contendo o bloco PARAMETER
    utilizado pelo código Fortran.

    Parâmetros:
        pname       : identificador do caso
        model       : gmsh.model
        bc          : dict com as condições de contorno
        node_bc     : dicionário de condições nodais
        output_dir  : diretório do arquivo
    """

    # -------------------------
    # Contagem da malha
    # -------------------------

    # Nós
    node_tags, _, _ = model.mesh.getNodes()

    NNOS = len(node_tags)


    # Elementos hexaédricos
    elem_types, elem_tags, _ = (
        model.mesh.getElements(3)
    )

    if len(elem_types) != 1:

        raise RuntimeError(
            "A malha deve possuir apenas um tipo de elemento"
        )

    NEMAX = len(elem_tags[0])

    # -------------------------
    # Condições de contorno
    # -------------------------

    NBU = 0
    NBV = 0
    NBW = 0
    NBP = 0

    # Faz a contagem de quantos nós tem cada condição de contorno
    for nbc in node_bc.values():

        if nbc["u"] is not None:
            NBU += 1

        if nbc["v"] is not None:
            NBV += 1

        if nbc["w"] is not None:
            NBW += 1

        if nbc["p"] is not None:
            NBP += 1

    # -------------------------
    # Objetos imersos
    # -------------------------

    MNOBJ = 0
    NNCSX = 0
    NFCSX = 0

    # Faz a contagem de quantos nós tem cada condição de contorno
    for tag, group in bc.items():

        # Se o grupo não for objeto imerso, pular
        if group["type"] != "object":
            continue
        
        MNOBJ += 1

        # Número de nós do objeto
        node_count = len(get_physical_group_nodes(model, 2, tag))

        # Número de quads do objeto
        quads, _ = get_physical_group_quads(model, 2, tag)
        quad_count = len(quads)

        # Atualizar valores
        NNCSX = max(NNCSX, node_count)
        NFCSX = max(NFCSX, quad_count)

    # -------------------------
    # Valores fixos
    # -------------------------

    NCMAX = 0
    NNMAX = 0

    # -------------------------
    # Escrita
    # -------------------------

    with open(output_dir / f"PARAMETER.dat", "w") as f:

        f.write(
            "\n"
            "! NEMAX: Numero de elementos hexaedricos da malha;\n"
            "! NNOS: Numero de nos da malha;\n"
            "! MNOBJ: Numero de objetos imersos no escoamento;\n"
            "! NNCSX: Numero de nos de contorno solido;\n"
            "! NFCSX: Numero de faces de contorno solido;\n"
            "! NBU: Numero de nos com condicao de velocidade U;\n"
            "! NBV: Numero de nos com condicao de velocidade V;\n"
            "! NBW: Numero de nos com condicao de velocidade W;\n"
            "! NBP: Numero de nos com condicao de pressao;\n"
            "\n"
        )

        f.write(
            f"! {pname}\n"
        )

        f.write(
            "PARAMETER (\n"
        )

        f.write(
            f"    NEMAX={NEMAX}, "
            f"NNOS={NNOS}, &\n"
        )

        f.write(
            f"    MNOBJ={MNOBJ}, "
            f"NNCSX={NNCSX}, "
            f"NFCSX={NFCSX}, &\n"
        )

        f.write(
            f"    NBU={NBU}, "
            f"NBV={NBV}, "
            f"NBW={NBW}, "
            f"NBP={NBP}, &\n"
        )

        f.write(
            f"    NCMAX={NCMAX}, "
            f"NNMAX={NNMAX})\n"
        )

def convert_to_serializable(obj):
    """
    Converte objetos numpy para tipos compatíveis com YAML.
    """

    import numpy as np

    if isinstance(obj, np.ndarray):
        return obj.tolist()

    elif isinstance(obj, np.generic):
        return obj.item()

    elif isinstance(obj, dict):
        return {
            key: convert_to_serializable(value)
            for key, value in obj.items()
        }

    elif isinstance(obj, list):
        return [
            convert_to_serializable(value)
            for value in obj
        ]

    elif isinstance(obj, tuple):
        return tuple(
            convert_to_serializable(value)
            for value in obj
        )

    else:
        return obj

def save_config_file(config, output_dir):
    """
    Salva um arquivo de configuração no diretório do script.

    O nome contém timestamp para evitar sobrescrever arquivos existentes.
    """

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filepath = output_dir / f"config_{timestamp}.yaml"

    with open(filepath, "w") as f:

        yaml.dump(
            convert_to_serializable(config),
            f,
            sort_keys=False,
            default_flow_style=False
        )

    print(
        f"Arquivo de configuração salvo em:\n{filepath}"
    )

    return filepath

def restore_numpy_types(boundary_conditions):
    """
    Função auxiliar que restaura os tipos numpy da leitura dos BC do YAML
    """

    vector_fields = [
        "growth_direction",
        "flow_direction"
    ]

    for bc in boundary_conditions.values():

        for field in vector_fields:

            if field in bc and bc[field] is not None:
                bc[field] = np.asarray(
                    bc[field],
                    dtype=float
                )

    return boundary_conditions

def load_config(config_file):
    """
    Carrega os dados de execução a partir de um arquivo YAML.
    """

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    boundary_conditions = config["boundary_conditions"]
    parameters = config["parameters"]
    fluid_properties = config["fluid_properties"]

    boundary_conditions = restore_numpy_types(
        boundary_conditions
    )

    return boundary_conditions, parameters, fluid_properties

def open_msh(filename, show=False):
    """
    Abre um arquivo .msh no Gmsh e retorna o modelo.

    Parâmetros:
        filename : caminho do arquivo .msh
        show     : abre a interface gráfica do Gmsh

    Retorno:
        gmsh.model
    """

    gmsh.open(filename)

    if show:
        gmsh.fltk.run()

    return gmsh.model

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Script de pré-processamento para código CFD Taylor-Galerkin de 2 passos. " \
        "Funciona com malhas em formato .msh 2.2, só suporta malhas 3D e hexaedros. " \
        "Permite execução manual ou automática via arquivo YAML. " \
        "Feito para o algoritmo CUDA_HEXA_IGOR_v1, não inclui temperatura, transporte de espécie e turbulência no inflow. " \
        "Pode funcionar com outras versões do código, mas talvez requeira leves ajustes."
    )

    # Argumentos obrigatórios
    parser.add_argument(
        "mesh_file",
        type=str,
        help="Arquivo .msh de entrada"
    )

    parser.add_argument(
        "pname",
        type=str,
        help="Nome do problema (6 caracteres)"
    )

    # Argumentos opcionais
    parser.add_argument(
        "--show",
        action="store_true",
        help="Abre a malha no Gmsh para visualização"
    )

    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Diretório para salvar arquivos gerados"
    )

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Arquivo YAML de configuração"
    )

    args = parser.parse_args()

    # Validação do pname
    if len(args.pname) != 6:
        raise ValueError(
            "pname deve possuir exatamente 6 caracteres"
        )

    if " " in args.pname:
        raise ValueError(
            "pname não pode conter espaços"
        )
    
    gmsh.initialize()

    # Fluxo principal
    model = open_msh(
        args.mesh_file,
        show=args.show
    )

    preprocess_mesh(
        model,
        args.pname,
        dir=args.dir,
        config_file=args.config
    )

    gmsh.finalize()
