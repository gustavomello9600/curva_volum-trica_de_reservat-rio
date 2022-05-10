from pathlib import Path
from typing import Union, Tuple, Optional

from toolz import curry
import numpy as np
import pandas as pd


# Tipos para as variáveis e efeitos das funções
Número           = Union[int, float]
TabelaDeDados    = pd.DataFrame
EscritaEmArquivo = None


def otimizar_orifício() -> EscritaEmArquivo:
    exportar_para_csv("busca_por_a_e_b_ótimos.csv",
                      obter_curva_ótima())

def gerar_curva_volumétrica() -> EscritaEmArquivo:
    exportar_para_csv("simulação.csv",
                      simular_reservatório(**parâmetros_de_entrada))

def exportar_para_csv(nome_do_arquivo: str, dados: TabelaDeDados) -> EscritaEmArquivo:
    with open(Path(nome_do_arquivo), "w") as arquivo:
        dados.to_csv(arquivo)

@curry # Permite a criação de funções parciais com alguns dos argumentos fixos
def simular_reservatório(t_c: Número,
                         V1: Número,
                         V2: Número,
                         V3: Número,
                         Q_pico: Número,
                         C_d: Número,
                         g: Número,
                         a: Número,
                         b: Número) -> TabelaDeDados:
    estado_inicial = {"t": (t := 0),
                      "V": (V := 0)}
    registro = [estado_inicial]

    # Volume até o qual o orifício opera como vertedor
    V_a = 3600*a

    # Altura da lâmina d'água como função do volume de água no reservatório
    h = lambda V: V/3600            if V < V1      \
             else (V + 5400)/9000   if V < V1 + V2 \
             else (V + 29000)/20800

    # Vazão de entrada em função do tempo pelo hidrograma unitário
    Q_e = lambda t: (Q_pico/t_c)*t           if t < t_c   \
               else (Q_pico/t_c)*(2*t_c - t) if t < 2*t_c \
               else 0

    # Vazão de saída em função do volume
    Q_s = lambda V: C_d * a * b * np.sqrt(2 * g * (h(V) - a/2)) if V > V_a \
               else 1.838*b*(h(V)**(3/2))

    incremento  = 1      #em segundos
    cinco_horas = 5*3600 #em segundos
    V_total = V1 + V2 + V3
    while t < cinco_horas:
        if V < V_total:
            t = t + incremento
            V = V + incremento * (Q_e(t) - Q_s(V)) # Da EDO: dV/dt = Q_e(t) - Q_s(V)
            registro.append({"t": t, "V": V})
        else:
            return TabelaDeDados.from_records(registro)
    return TabelaDeDados.from_records(registro)

parâmetros_de_entrada = {
    "t_c": 3600,        # Tempo de Concentração em segundos
    "V1": 3600,         # Volume do primeiro patamar do reservatório em m³
    "V2": 9000,         # Volume do segundo patamar do reservatório em m³
    "V3": 10400,        # Volume do terceiro patamar do reservatório em m³
    "Q_pico": 29.7738,  # Vazão de pico calculada pelo método racional em m³/s
    "C_d": 0.61,        # Coeficiente de descarga
    "g": 9.78,          # Aceleração da gravidade em m/s²

    "a": 0.5,           # Altura do orifício em metros
    "b": 10             # Largura do orifício em metros
}

def obter_curva_ótima() -> TabelaDeDados:
    resultados = []
    for b in range(1, 20 + 1):
        a, V_máx, t_cheio = buscar_melhor_a_dado(b)
        resultados.append({"b": b, "a": a,
                           "Volume_máximo_atingido": V_máx,
                           "Tempo_até_volume_máximo": t_cheio})

    return TabelaDeDados.from_records(resultados)

def buscar_melhor_a_dado(b: Número) -> Tuple[Optional[Número],
                                             Optional[Número],
                                             Optional[Número]]:
    """Para um dado b, retorna o melhor a, o volume máximo e o tempo até ele"""

    delta      = 0.1
    a_subótimo = 0.2
    a_ótimo    = a_subótimo + delta

    V_máx   = None
    t_cheio = None

    while a_ótimo - a_subótimo > 0.01:
        if a_subótimo > 1:
            return None, None, None
        V_máx, t_cheio = testar(a_ótimo, b)
        if V_máx > 23000:
            a_subótimo = a_ótimo
            a_ótimo += delta
        else:
            delta = (a_ótimo - a_subótimo)/2
            a_ótimo -= delta

    return a_ótimo, V_máx, t_cheio

def testar(a: Número, b: Número) -> Tuple[Número, Número]:
    """Para um dado par (a, b) determina o volume máximo de água
    no reservatório e o tempo em que é atingido"""

    simulação = simular(a=a, b=b)
    V_máx = simulação["V"].max()
    t_cheio = simulação["V"].idxmax()
    return V_máx, t_cheio

# Gera uma nova função de simulação que já absorveu todos os parâmetros de entrada exceto a e b
simular = simular_reservatório(**{k:v for k,v in parâmetros_de_entrada.items() if k not in ("a", "b")})

otimizar_orifício()
# Usado para encontrar melhores dimensões a (altura) e b (largura) para o orifício retangular

gerar_curva_volumétrica()
# Inseridos os valores desejados de a e b nos parâmetros de entrada,
# executa a simulação do volume de água ao longo do tempo