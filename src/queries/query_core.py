# src/queries/query_core.py
# ============================================================
# QUERIES CORE (instrumento estable por canal)
# ============================================================

from __future__ import annotations

QUERY_CORE: dict[str, str] = {
    "TIPO_A_ACTORES": """( petrogustavo OR "Gustavo Petro" OR FranciaMarquezM OR "Francia Marquez" OR "Pacto Historico"
        OR AlvaroUribeVel OR "Alvaro Uribe" OR "Centro Democratico" OR MariaFdaCabal OR "Maria Fernanda Cabal"
        OR FicoGutierrez OR "Federico Gutierrez" OR ClaudiaLopez OR "Claudia Lopez" OR SergioFajardo OR "Sergio Fajardo"
        OR "Partido Liberal" OR "Partido Conservador" OR "Alianza Verde" OR "Cambio Radical" )""",

    "TIPO_B_FRAMES": """( Congreso OR Senado OR "Camara de Representantes" OR "Corte Constitucional" OR Fiscalia OR Procuraduria OR Policia
        OR seguridad OR "orden publico" OR violencia OR democracia OR instituciones OR "estado de derecho"
        OR inflacion OR empleo OR dolar OR corrupcion OR impunidad OR "paz total" OR protesta OR marchas )""",

    "TIPO_B2_MEDIOS": """( ELTIEMPO OR RevistaSemana OR elespectador OR BluRadioCo OR WRadioColombia OR lafm
        OR NoticiasCaracol OR NoticiasRCN )""",

    "TIPO_C_MIXTA": """( petrogustavo OR "Gustavo Petro" OR AlvaroUribeVel OR "Alvaro Uribe" OR ClaudiaLopez OR "Claudia Lopez"
        OR MariaFdaCabal OR "Maria Fernanda Cabal" OR FicoGutierrez OR "Federico Gutierrez" )
        AND
        ( seguridad OR violencia OR democracia OR instituciones OR inflacion OR corrupcion OR "paz total" OR protesta )""",

    "TIPO_D_INTENSIDAD": """( dictadura OR narcoestado OR fascismo OR comunismo OR guerrillero OR paramilitar
        OR vendido OR traidor OR corrupto OR asesino OR terrorista OR golpista )""",
}

CHANNELS = list(QUERY_CORE.keys())
