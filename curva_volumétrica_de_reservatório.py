from pathlib import Path
from typing import Dict, Union, Optional, Callable

from toolz import curry
import numpy as np
import pandas as pd

IO = None
Número = Union[int, float]


def gerar_curva_volumétrica() -> IO:
    exportar_para_csv("simulação.csv",
                      simular_reservatório(**parâmetros_de_entrada))

def otimizar_orifício() -> IO:
    exportar_para_csv("busca_por_a_e_b_ótimos.csv",
                      obter_curva_ótima())

def exportar_para_csv(nome_do_arquivo: str, dados: pd.DataFrame) -> IO:
    with open(Path(nome_do_arquivo), "w") as arquivo:
        dados.to_csv(arquivo)

@curry
def simular_reservatório(t_c: Número,
                         V1: Número,
                         V2: Número,
                         V3: Número,
                         Q_pico: Número,
                         C_d: Número,
                         g: Número,
                         a: Número,
                         b: Número) -> Optional[pd.DataFrame]:
    estado_inicial = {"t": (t := 0),
                      "V": (V := 0)}
    registro = [estado_inicial]

    V_a = 3600*a
    h = lambda V: V/3600 if V < V1 else (V + 5400)/9000 if V < V1 + V2 else (V + 29000)/20800
    Q_e = lambda t: (Q_pico/t_c)*t if t < t_c else (Q_pico/t_c)*(2*t_c - t) if t < 2*t_c else 0
    Q_s = lambda V: C_d * a * b * np.sqrt(2 * g * (h(V) - a/2)) if V > V_a else 1.838*b*(h(V)**(3/2))

    incremento = 1
    while t < 24*3600*10:
        if V < V1 + V2 + V3:
            t = t + incremento
            V = V + incremento * (Q_e(t) - Q_s(V))
            registro.append({"t": t, "V": V})
        else:
            return pd.DataFrame.from_records(registro)
    return pd.DataFrame.from_records(registro)

parâmetros_de_entrada = {
    "t_c": 3600,
    "V1": 3600,
    "V2": 9000,
    "V3": 10400,
    "Q_pico": 29.7738,
    "C_d": 0.61,
    "g": 9.78,
    "a": 0.5,
    "b": 10
}

def obter_curva_ótima() -> pd.DataFrame:
    simular = simular_reservatório(**{k:v for k,v in parâmetros_de_entrada.items() if k not in ("a", "b")})
    def testar(a, b):
        simulação = simular(a=a, b=b)
        V_máx = simulação["V"].max()
        t_cheio = simulação["V"].idxmax()
        return V_máx, t_cheio

    def buscar_melhor_a_dado(b):
        delta = 0.1
        a_subótimo = 0.2
        a_ótimo = a_subótimo + delta

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

    resultados = []
    for b in range(1, 20 + 1):
        a, V_máx, t_cheio = buscar_melhor_a_dado(b)
        resultados.append({"b": b, "a": a,
                           "Volume_máximo_atingido": V_máx,
                           "Tempo_até_volume_máximo": t_cheio})

    return pd.DataFrame.from_records(resultados)

gerar_curva_volumétrica()
otimizar_orifício()
