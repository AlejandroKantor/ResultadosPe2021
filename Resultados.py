
import streamlit as st
from plotnine import *
from plotnine.data import mtcars
import altair as alt
from vega_datasets import data
import pandas as pd
from plotnine import *
import statsmodels.api as sm
from typing import List
import numpy as np
from elections import prep_data_2016, Elecciones
import os

from urllib import request
import json

# fetch & enable a German format & timeFormat locales.




df_elecciones2016 = pd.read_csv("input/encuestasPrimeraVuelta2016.csv")
df_elecciones2016 = prep_data_2016(df_elecciones2016, candidatos = ['Keiko_Fujimori', 'Julio_Guzman',
       'Pedro_Pablo_Kuczynski', 'Cesar_Acuna', 'Alan_Garcia',
       'Alfredo_Barnechea', 'Veronika_Mendoza'])

df_elecciones2021 = pd.read_csv("input/encuestasPrimeraVuelta2021.csv")

df_elecciones2021 = prep_data_2016(df_elecciones2021, candidatos= ['Keiko_Fujimori', 'Julio_Guzman',
                               'George_Forsyth', 'Yonhy_Lescano',
                            'Daniel_Urresti', 'Veronika_Mendoza', "Hernando_de_Soto", "Rafael_Lopez_Aliaga"])


df_color = pd.read_csv("input/colorCandidato.csv", sep="\t")

cand_2016 =  ['Keiko_Fujimori', 'Julio_Guzman',
                               'Pedro_Pablo_Kuczynski', 'Cesar_Acuna', 'Alan_Garcia',
                            'Alfredo_Barnechea', 'Veronika_Mendoza',
                             "otros", "ninguno"]

cand_2021 =  ['Keiko_Fujimori', 'Julio_Guzman',
                               'George_Forsyth', 'Yonhy_Lescano',
                            'Daniel_Urresti', 'Veronika_Mendoza', "Hernando_de_Soto", "Rafael_Lopez_Aliaga",
                             "otros", "ninguno"]


df_color2016 = df_color[df_color["candidato"].isin(cand_2016)]
df_color2021 = df_color[df_color["candidato"].isin(cand_2021)]


elecciones2016 = Elecciones(df_elecciones2016,
                            cand_2016,
                            df_color2016,
                            smooth_param=0.5,
                            election_date="2016-04-09")


elecciones2021 = Elecciones(df_elecciones2021,
                            cand_2021,
                            df_color2021,
                            smooth_param=1,
                            election_date="2021-04-11")
def get_about():

    texto = ["Resultados.pe es un proyecto que muestra, de manera resumida, los resultados de las encuestas de elecciones presidenciales del Perú.",
"He sido investigador del Institute for Quantitative Social Science de Harvard University. Cuento con grados académicos en matemáticas, economía, estadística y pronto en ciencias de la computación.",
             "Visiten mi twitter [@AlejandroKantor](https://twitter.com/AlejandroKantor)."]
    return texto


# ---------------------------------------------------------------------
st.markdown("# Resultados.pe")

app_mode = st.sidebar.radio("Navegador", ["Elecciones presidenciales", "Acerca de"])


st.sidebar.info(
        """
        Este proyecto es mantenido por Alejandro Kantor. Visiten mi twitter
        [@AlejandroKantor](https://twitter.com/AlejandroKantor).
"""
    )

st.markdown("""
<style>
.big-font {
    font-size:10px !important;
}
</style>
""", unsafe_allow_html=True)



if app_mode == "Acerca de":
    l_about = get_about()
    for line in l_about:
        st.markdown(line)

elif app_mode == "Elecciones presidenciales":

    #a_2016 = elecciones2016.prop_agg_alt_plot( domain = ("2015-12-01", "2016-04-15"))
    #a_2021 = elecciones2021.prop_agg_alt_plot( domain = ("2020-12-01", "2021-04-15"),


    st.markdown("Actualizado 09-03-2021")
    st.markdown("## Primera vuelta elecciones 2021")


    col1, col2 = st.beta_columns((1,4))

    cand_2021_label = elecciones2021.get_sorted_color()["candidato_label"]
    with col1:
        checked_2021 = []
        count = 0
        for cand in cand_2021_label:
            count += 1
            checked_2021.append(st.checkbox(cand, count<8, cand+"2021"))
    checked_2021 = cand_2021_label[checked_2021]

    col2.altair_chart(elecciones2021.prop_agg_alt_plot_all( domain = ("2020-12-01", "2021-04-15"),
                                                            checked_candaidates = checked_2021,
                                                            move_legend=True), use_container_width=True)
    col2.markdown('<p class="big-font">Fuente: IEP, Ipsos, Datum y CPI</p>', unsafe_allow_html=True)

    st.markdown("## Primera vuelta elecciones 2016")
    col1b, col2b = st.beta_columns((1,4))

    cand_2016_label = elecciones2016.get_sorted_color()["candidato_label"]
    with col1b:
        checked_2016 = []
        for cand in cand_2016_label:
            checked_2016.append(st.checkbox(cand, True))
    checked_2016 = cand_2016_label[checked_2016]

    col2b.altair_chart(elecciones2016.prop_agg_alt_plot_all( domain = ("2015-12-01", "2016-04-15"),
                                                            checked_candaidates = checked_2016), use_container_width=True)
    col2b.markdown('<p class="big-font">Fuente: Ipsos, GFK, Datum y CPI</p>', unsafe_allow_html=True)

    #st.altair_chart(a_2016, use_container_width=True)

    # fetch & enable a German format & timeFormat locales.


elif app_mode == "2016":
    st.markdown("## Ejemplo de tabla")

    st.write(mtcars)


