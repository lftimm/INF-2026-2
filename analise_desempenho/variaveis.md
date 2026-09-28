# Dicionário de Variáveis Refatorado - Modelo CFD em CUDA Fortran (`cuda_cfd.cuf`)

Este documento mapeia os nomes de variáveis refatorados no código `src/cuda_cfd.cuf` juntamente com seus nomes originais (legados) e descrições detalhadas.

---

## 1. Parâmetros de Dimensionamento e Estrutura da Malha

| Novo Nome | Nome Legado | Tipo | Descrição |
| :--- | :--- | :--- | :--- |
| `num_elementos_max` | `NEMAX` | `integer(4)` | Número total/máximo de elementos hexaédricos de 8 nós da malha. |
| `num_nos_totais` | `NNOS` | `integer(4)` | Número total de nós da malha. |
| `num_objetos_imersos` | `MNOBJ` | `integer(4)` | Número de objetos/corpos rígidos imersos no escoamento. |
| `num_nos_contorno_solido` | `NNCSX` | `integer(4)` | Número de nós pertencentes ao contorno sólido dos objetos imersos. |
| `num_faces_contorno_solido` | `NFCSX` | `integer(4)` | Número de faces (elementos quadriláteros) do contorno sólido. |
| `num_nos_bc_u` | `NBU` | `integer(4)` | Número de nós com condição de contorno para a velocidade $u$. |
| `num_nos_bc_v` | `NBV` | `integer(4)` | Número de nós com condição de contorno para a velocidade $v$. |
| `num_nos_bc_w` | `NBW` | `integer(4)` | Número de nós com condição de contorno para a velocidade $w$. |
| `num_nos_bc_p` | `NBP` | `integer(4)` | Número de nós com condição de contorno para a pressão $p$. |
| `num_nos_bc_u_dev` | `NBUd` | `integer, constant` | Constante no módulo CUDA para contorno de $u$. |
| `num_nos_bc_v_dev` | `NBVd` | `integer, constant` | Constante no módulo CUDA para contorno de $v$. |
| `num_nos_bc_w_dev` | `NBWd` | `integer, constant` | Constante no módulo CUDA para contorno de $w$. |
| `num_nos_bc_p_dev` | `NBPd` | `integer, constant` | Constante no módulo CUDA para contorno de $p$. |
| `num_faces_bc_max` | `NCMAX` | `integer(4)` | Número máximo de faces de contorno de Neumann. |
| `num_nos_aux_max` | `NNMAX` | `integer(4)` | Número máximo de nós auxiliares. |
| `num_nos` | `NNM` | `integer(4)` | Número de nós da malha ativo na simulação. |

---

## 2. Índices e Contadores Principais

| Novo Nome | Nome Legado | Tipo | Descrição |
| :--- | :--- | :--- | :--- |
| `elem_idx` | `IELEM`, `IELM` | `integer(4)` | Índice do elemento hexaédrico em processamento. |
| `no_idx` | `NODE`, `NNO` | `integer(4)` | Número global de um nó. |
| `obj_idx` | `NOB` | `integer(4)` | Índice do objeto imerso atual em processamento. |
| `num_arquivo` | `NARQ` | `integer(4)` | Contador/número do arquivo de saída ou registro. |

---

## 3. Campos Primários e Conectividade da Malha

| Novo Nome (Host / GPU) | Nome Legado | Tipo | Descrição |
| :--- | :--- | :--- | :--- |
| `conectividade` / `conectividade_d` | `kone` / `kone_d` | `integer(4)` | Vetor de conectividade global da malha hexaédrica. |
| `vel_pressao` / `vel_pressao_d` | `uvw` / `uvw_d` | `real(4)` | Matriz com as componentes de velocidade ($u, v, w$) e pressão ($p$). |
| `vel_media_elem` / `vel_media_elem_d` | `uvwprom` / `uvwprom_d` | `real(4)` | Velocidades médias calculadas no centro dos elementos. |
| `volume_elem` / `volume_elem_d` | `VOLU` / `VOLU_d` | `real(4)` | Vetor de volume de cada elemento hexaédrico da malha. |
| `jacobiana_inv` / `jacobiana_inv_d` | `JIN` / `JIN_d` | `real(4)` | Matriz Jacobiana inversa dos elementos ($9 \times N$). |
| `div_velocidade` / `div_velocidade_d` | `PNV` / `PNV_d` | `real(4)` | Divergência do campo de velocidade ($\nabla \cdot \vec{V}$). |
| `grad_pressao_x`..`z` (`*_d`) | `Gr1P`..`Gr3P` (`*_d`) | `real(4)` | Componentes do gradiente de pressão nas direções $x, y, z$. |
| `massa_nodal` / `massa_nodal_d` | `mlum` / `mlum_d` | `real(4)` | Massa concentrada (*lumped mass*) associada a cada nó. |
| `visc_turbulenta` / `visc_turbulenta_d` | `VDTurb` / `VDTurb_d` | `real(4)` | Viscosidade turbulenta sub-malha ($\nu_t$) por elemento. |
| `grad_medios_elem` / `grad_medios_elem_d` | `pp` / `pp_d` | `real(4)` | Gradientes médios das componentes de velocidade nos elementos. |
| `residuo_u`..`p` / `residuo_u_d`..`p_d` | `rru`..`rrp` (`*_d`) | `real(4)` | Vetores de resíduos nodais das equações de momentum e continuidade. |
| `vel_pressao_atualiz` (`*_d`) | `uvwa` / `uvwa_d` | `real(4)` | Campo de velocidades e pressão atualizado no subpasso de tempo. |
| `residuo_global` / `residuo_global_d` | `rrg` / `rrg_d` | `real(4)` | Matriz de resíduos acumulados globais nos nós da malha. |

---

## 4. Condições de Contorno (Dirichlet)

| Novo Nome (Host / GPU) | Nome Legado | Tipo | Descrição |
| :--- | :--- | :--- | :--- |
| `indices_bc_u`..`p` (`*_d`) | `IBCU`..`IBCP` (`*_d`) | `integer(4)` | Índices nodais com condições de contorno de Dirichlet para $u, v, w, p$. |
| `valores_bc_u`..`p` (`*_d`) | `BCU`..`BCP` (`*_d`) | `real(4)` | Valores prescritos de condição de contorno para $u, v, w, p$. |

---

## 5. Parâmetros Físicos e de Controle Numérico

| Novo Nome | Nome Legado | Tipo | Descrição |
| :--- | :--- | :--- | :--- |
| `vel_infinita` | `VInf` | `real(4)` | Módulo da velocidade do escoamento não perturbado ($V_\infty$). |
| `vel_som` | `VelSom` | `real(4)` | Velocidade do som no fluido (pseudo-compressibilidade). |
| `visc_cinematica` | `ViscCin` | `real(4)` | Viscosidade cinemática do fluido ($\nu$) $[m^2/s]$. |
| `visc_volumetrica` | `ViscVol` | `real(4)` | Viscosidade volumétrica por unidade de massa $[m^2/s]$. |
| `densidade_ref` | `RHOInf` | `real(4)` | Densidade / massa específica de referência ($\rho_\infty$) $[kg/m^3]$. |
| `difusividade_termica` | `Kdif` | `real(4)` | Coeficiente de condutividade/difusividade térmica laminar. |
| `difusividade_massica` | `Dab` | `real(4)` | Coeficiente de difusão mássica de espécies. |
| `modelo_turbulencia` (`*_d`) | `INDTURB` / `IndTurb` | `integer(4)` | Modelo de turbulência sub-malha (0=Sem modelo, 1=Smagorinsky, 2=Dinâmico). |
| `coef_seguranca_cfl` | `CSEGUR` | `real(4)` | Fator de segurança Courant/CFL para passo de tempo. |
| `param_controle_suav` | `CONTROL1` | `real(4)` | Parâmetro de controle para zeramento/suavização. |
| `fator_lumping_continuidade` | `ELUMP1` | `real(4)` | Fator de concentração de massa para continuidade. |
| `fator_lumping_momento` | `ELUMP2` | `real(4)` | Fator de concentração de massa para momento. |
| `fator_lumping_especie` | `ELUMP3` | `real(4)` | Fator de concentração de massa para espécie. |
| `threads_por_bloco` | `tBlock` | `integer(4)` | Número de threads por bloco de execução nos kernels CUDA (GPU). |
