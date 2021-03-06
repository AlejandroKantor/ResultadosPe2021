import pandas as pd
import numpy as np
import streamlit as st
from plotnine import *
from plotnine.data import mtcars
import altair as alt
from vega_datasets import data
from plotnine import *
import statsmodels.api as sm
lowess = sm.nonparametric.lowess
from typing import List
from urllib import request
import json


def prep_data_2016(df_data: pd.DataFrame, candidatos):

    #key = ["Encuestadora", "Fecha_inicio", "Fecha_fin", "Poblacion"]
    df_data = df_data.copy()
    df_data["Blanco_viciado"] = df_data["Blanco_viciado"].fillna(0)
    df_data["No_sabe_no_opina"] = df_data["No_sabe_no_opina"].fillna(0)
    df_data["ninguno"] = df_data["Blanco_viciado"] + df_data["No_sabe_no_opina"]
    df_data["otros"] =  100 - df_data[candidatos+ ["ninguno"]].sum(axis=1).values
    df_data["Fecha_inicio"] = pd.to_datetime(df_data["Fecha_inicio"], format="%Y%m%d")
    df_data["fecha"] = df_data["Fecha_inicio"]
    df_data["poblacion"] = df_data["Poblacion"]
    df_data = df_data[df_data["fecha"]>="2015-12-01"]
    df_data = df_data.sort_values("fecha")
    df_data["encuesta"] = np.arange(df_data.shape[0])
    df_data = df_data.reset_index(drop=True)
    return df_data

"""
Todo:
* Orden en la leyenda
* algo para mostrar que último resultado es de la elección
* fondo del gráfico
* quitar título leyenda
* rango y axis 
"""

class Elecciones:
    def __init__(self,
                 df_prop: pd.DataFrame,
                 candidates: List[str],
                 df_color: pd.DataFrame,
                 smooth_param=2/3,
                 election_date=None):
        self.df_prop = df_prop
        self.candidates = candidates
        self.smooth_param = smooth_param
        self.df_color = df_color
        self.election_date = election_date

        self.df_expected = None
        self.make_expected()

        self.make_consolidated()

    def make_expected(self):
        df_prop = self.df_prop.copy()
        df_prop = df_prop[~df_prop["Encuestadora"].str.contains("ONPE")]
        df_prop = df_prop.reset_index(drop=True)
        df_expected = df_prop.copy()

        for col in self.candidates:
            y = df_prop[col].values
            x = df_prop["fecha"].values
            pred = lowess(y, x,
                          frac=self.smooth_param,
                          return_sorted=False)

            df_expected[col] = pred

        self.df_expected = df_expected

    def make_consolidated(self):
        cols = self.candidates
        df_prop_melt = self.df_prop.melt(id_vars=["encuesta", "Encuestadora", "poblacion", "fecha"], value_vars=cols,
                                         value_name="prop")
        df_expected_melt = self.df_expected.melt(id_vars=["encuesta"], value_vars=cols,
                                                 value_name="expected")

        df_data = pd.merge(df_prop_melt, df_expected_melt,
                           on=["encuesta", "variable"],
                           how="left")
        df_data = df_data[df_data["prop"] > 0]
        df_data["label_point"] = df_data["variable"]

        df_candidate_label = self.df_color.copy()
        df_candidate_label = df_candidate_label.rename(columns={"candidato":"variable", "candidato_label":"Candidato/a"})
        df_data = pd.merge(df_data, df_candidate_label, on="variable", how="left")
        df_data["Intención de voto"] = df_data["prop"].round(1).apply(str) + "%"
        df_data["Fecha"] = df_data["fecha"]
        df_data["Promedio"] = df_data["expected"].round(1).apply(str) + "%"

        df_data["election_date"] = pd.to_datetime(self.election_date)
        self.df_consolidated = df_data

    def get_sorted_color(self):
        df_color = self.df_color
        df_order = self.df_consolidated.copy()
        max_date = df_order["fecha"].max()

        df_order = df_order[df_order["fecha"] == max_date]
        df_order = df_order.groupby("variable").agg(prop=("prop", "mean"),
                                                    expected=("expected", "mean"))
        df_order = df_order.reset_index()
        df_order["candidato"] = df_order["variable"]
        cols = ["candidato", "prop", "expected"]
        df_color = pd.merge(df_color, df_order[cols], on="candidato", how="left")
        sort_var = "prop" if df_color["expected"].isna().all() else "expected"

        df_color = df_color.sort_values(sort_var, ascending=False)
        return df_color


    def prop_agg_alt_plot_all(self, domain=None, checked_candaidates=None,
                              move_legend=False,
                              vertical_line=None):
        df_color = self.get_sorted_color()

        source = self.df_consolidated[['Candidato/a','expected','fecha', 'prop']]
        source['Candidato/a'] = source['Candidato/a'].str.replace("\\.", "")
        source['expected'] = source['expected'].round(1)

        if checked_candaidates is not None:
            df_color = df_color[df_color.candidato_label.isin(checked_candaidates)]
            source = source[source["Candidato/a"].isin(checked_candaidates)]
        color = alt.Color('Candidato/a:N',
                          scale=alt.Scale(domain=list(df_color.candidato_label),
                                          range=list(df_color.color)))

        base = alt.Chart(source).encode(x= alt.X("fecha:T", title="",
                axis=alt.Axis(format='%d-%m-%y'),
                scale=alt.Scale(domain=domain)
                ),
        ).properties(
            height=400
        )
        columns = df_color["candidato_label"]
        selection = alt.selection_single(
            fields=['fecha'], nearest=True, on='mouseover', empty='none', clear='mouseout'
        )

        lines = base.mark_line().encode(y='expected:Q', color=color)
        polsters = base.mark_circle(opacity=0.7).encode(
            y=alt.Y('prop', title='Intención de voto (%)'),
            color=color
        )

        points = lines.mark_point().transform_filter(selection)

        rule = base.transform_pivot(
            'Candidato/a', value='expected', groupby=['fecha'], op='mean'
        ).mark_rule().encode(
            opacity=alt.condition(selection, alt.value(0.3), alt.value(0)),
            tooltip=  [alt.Tooltip('fecha', format='%d-%m-%Y')]  + [alt.Tooltip(c, type='quantitative') for c in columns]
        ).add_selection(selection)
        candidate_label = alt.Chart(source).encode(x='fecha:T')
        plot = lines + points + polsters + rule
        if vertical_line is not None:
            df_date = pd.DataFrame(dict(verical_date=[pd.to_datetime(vertical_line)],
                                        y=[0],
                                        text=["""Nota1"""]))
            vertline = alt.Chart(df_date).mark_rule(color="#737373").encode(
                x= "verical_date"
            )
            annotation = alt.Chart(df_date).mark_text(
                align='left',
                baseline='middle',
                fontSize=10,
                dx=7,
                dy=-7,
                lineBreak='\n'
            ).encode(
                x='verical_date',
                y='y',
                text='text'
            )
            plot = plot + vertline + annotation
        if move_legend:
            plot = plot.configure_legend(
                #strokeColor='gray',
                fillColor='#FFFFFF',
                padding=10,
                #cornerRadius=10,
                orient='top-right'
            )
        alt.themes.enable("latimes")
        plot = plot.configure_axis(
            grid=False
        )
        return plot



    def prop_agg_alt_plot(self, domain = ("2015-12-01", "2016-04-15")):

        df_color = self.get_sorted_color()

        selection = alt.selection_multi(fields=['Candidato/a'],
                                        bind='legend'
                                        )

        color = alt.Color('Candidato/a',
                          scale=alt.Scale(domain=list(df_color.candidato_label),
                                          range=list(df_color.color)))
        a_circle = alt.Chart(self.df_consolidated).mark_circle(
            #    opacity=0.3
        ).encode(
            x=alt.X("fecha", title="",
                    axis=alt.Axis(format='%d-%m-%y'),
                    scale=alt.Scale( domain=domain)
                    ),
            y=alt.Y('prop', title='Intención de voto (%)'),
            color=color,
            tooltip=["Candidato/a", "Intención de voto", "Encuestadora", alt.Tooltip('Fecha', format='%d-%m-%Y')],
            opacity=alt.condition(selection, alt.value(0.5), alt.value(0.1))
        ).properties(
            height=400
        )

        a_line = alt.Chart(self.df_consolidated).mark_line(size=3.2).encode(
            x=alt.X("fecha", title=""),
            y=alt.Y('expected', title='Intención de voto (%)'),
            color=color,
            tooltip=["Candidato/a", "Promedio",  alt.Tooltip('Fecha', format='%d-%m-%Y')],
            opacity=alt.condition(selection, alt.value(1), alt.value(0.1))

        ).add_selection(selection)

        a_rules = alt.Chart(self.df_consolidated).mark_rule().encode(
            x=alt.X("election_date", title="",
                    axis=alt.Axis(format='%d-%m-%y')
                    ))

        a = alt.layer(
            a_line, a_circle,  a_rules #, selectors#, text
        )
        #a = a_line
        alt.themes.enable("latimes")
        a = a.configure_axis(
            grid=False
        )
        alt.Scale(nice={'interval': 'month', 'step': 1})
        return a

    def prop_agg_gg_plot(self):
        gg_agg = (ggplot(self.df_consolidated, aes(x="fecha", y="prop", color="variable", group="variable")) + \
                  geom_point() + \
                  geom_line(aes(y="expected")) + \
                  theme_classic() + scale_color_brewer(type="qual", palette="Set1"))
        return gg_agg