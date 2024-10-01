import tkinter
from tkinter import filedialog
import pandas as pd
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from data.data_class import DataRaw
from config.layout_config import *
from data.data_plot import PlotObject
from data.config import hydrogen_technologies
from layout.layout_general import discrete_background_color_bins
import sys

def get_callbacks(app):

    @app.callback(Output(component_id={'type': 'dynamic-directory', 'index': MATCH}, component_property='children'),
                  Input(component_id={'type': 'dynamic-path', 'index': MATCH}, component_property='n_clicks'),
                  prevent_initial_call=True)
    def select_directory(n_clicks):
        """
        n_clicks: button from File Brows
        :return File directory as text
        """
        if n_clicks:
            root = tkinter.Tk()
            root.attributes("-topmost", True)
            root.withdraw()
            file_directory = filedialog.askopenfilename(title='Select Solution File',
                                                        initialdir='/cluster/home/danare/git/dana/results/spatial',
                                                        filetypes=(
                                                        ('text files', '*.txt'), ('solution files', '*.sol')))
            root.destroy()

            return file_directory



    @app.callback(
        Output('container', 'children'),
        [Input('add', 'n_clicks')],
        [State('container', 'children')], prevent_initial_call=True
    )
    def show_input_cards(n_clicks, div_children):
        new_child = html.Div(
            dbc.Card(children=
            [
                dbc.Row(children=[
                dbc.Row(children=[
                    dbc.Col(children=[html.P('Scenario:', style=HEADER)]),
                    dbc.Col(children=[dbc.Input(id={'type': 'dynamic-scenario', 'index': n_clicks},
                                                placeholder='Name',
                                                required=True,
                                                type='text')])
                ], style={'margin': '8px'}),
                dbc.Row(children=[
                    dbc.Col(children=[html.P('Folder Path:', style=HEADER, )]),
                    # dbc.Col(children=[dbc.Input(id={'type': 'dynamic-directory', 'index': n_clicks},
                    #                             placeholder='Name',
                    #                             required=True,
                    #                             type='text'),])
                    dbc.Col(children=[
                        dbc.Button('Browse',
                                   id={'type': 'dynamic-path', 'index': n_clicks},
                                   n_clicks=0,
                                   style=BUTTON,
                                   className="d-grid"),
                        html.P(id={'type': 'dynamic-directory', 'index': n_clicks}, children='')])
                ], style={'margin': '8px'}),
            ], style=CARD_STYLE),]
        ))

        div_children.append(new_child)
        return div_children

    @app.callback(
        Output('fuel', 'children'),
        [Input(component_id='dropdownmenu', component_property='value')], prevent_initial_call=True
    )
    def add_drop_down_fuel(key):
        if key == "trade_map":
            new_child = [
                dbc.Col(children=html.H5('Fuel:'),  width={"size": 2}),
                dbc.Col(children=[dcc.Dropdown(
                    options=[
                        {'label': 'Power', 'value': 'Power'},
                        {'label': 'Natural Gas', 'value': 'gas_natural', 'disabled': True},
                        {'label': 'H2', 'value': 'H2', 'disabled': True},
                    ],
                    id="fuels",
                    value='power')], width={"size": 3})
            ]
        else:
            #TODO better way to only consider if field is there
            new_child = [dbc.Col(children=html.H5(),
                                 id="fuels"),
                         dbc.Col(children=[])]

        return new_child

    @app.callback(
        [Output(component_id='summary', component_property='children'),
         Output(component_id='individual', component_property='children'),
         Output(component_id='yearly', component_property='children'),
         Output(component_id="loading-output-1", component_property="children")],
        [Input(component_id={'type': 'dynamic-scenario', 'index': ALL}, component_property='value'),
         Input(component_id={'type': 'dynamic-directory', 'index': ALL}, component_property='children'),
         #Input(component_id={'type': 'dynamic-directory', 'index': ALL}, component_property='value'),
         Input(component_id='dropdownmenu', component_property='value'),
         Input(component_id='fuels', component_property='value'),
         Input(component_id='save', component_property='n_clicks')], prevent_initial_call=True
    )
    def update_graph(scenario, directory, key, fuel, n_clicks):
        if n_clicks:
            # create list for dfs
            list_dfs = []
            capacities = []
            for s, d in zip(scenario, directory):
                data_rw = DataRaw(directory=d, key=key, sector="Power")
                if key in ["capacities", "operation"]:
                    data_rw.filter_sector()
                    data_rw.aggregate_technologies()
                    data_rw.aggregate_regions()
                    if key == "operation":
                        demand = DataRaw(directory=d, key="demand", sector="Power")
                        data_rw.add_demand(demand_df=demand.df)
                elif key in ["hydrogen_infrastructure"]:
                    # data_rw.aggregate_column(column="TS", method="sum")
                    data_rw.filter_column(column="Fuel", by_filter=["H2"])
                    data_rw.replace_offshore()
                    df = DataRaw(directory=d, key='capacities')
                    df.replace_offshore()
                    df.filter_column(column="Technology", by_filter=hydrogen_technologies)
                    df.aggregate_column(column="Technology", method="sum")
                    capacities.append(df.df)
                elif key in ['trade_map']:
                    data_rw.filter_column(column="Fuel", by_filter=[fuel])
                    data_rw.replace_offshore()
                    #prepare data for the pie chart
                    df = DataRaw(directory=d, key='capacities')
                    df.replace_offshore()
                    df.filter_sector()
                    df.aggregate_technologies()
                    capacities.append(df.df)
                elif key in ["export"]:
                    data_rw.aggregate_column(column="TS", method="sum")
                    data_rw.filter_column(column="Fuel", by_filter=["Power"])
                    data_rw.filter_column(column="Year", by_filter=[2050])
                    data_rw.pivot_table()
                list_dfs.append(data_rw.df)

                ## group the data
                if key in ["capacities", "operation"]:
                    df_list_yearly = [df.groupby(by=['Year', 'Technology', 'Region'], as_index=False).sum(numeric_only=True) for df in list_dfs]


            # plot the graphs
            plt_obj = PlotObject(key=key, year=[2018, 2030, 2040, 2050], sector="Power", df_list=list_dfs,
                                 scenarios=scenario)

            if key in ["capacities"]:
                return [[dcc.Graph(figure=plt_obj.stacked_bar_integrated(aggregation=True))],
                        [dcc.Graph(figure=plt_obj.stacked_bar_side(list_dfs=list_dfs))],
                        [],
                        []]
            elif key in ["operation"]:
                return [[dcc.Graph(figure=plt_obj.stacked_bar_integrated(aggregation=True))],
                        [dcc.Graph(figure=plt_obj.stacked_bar_side(list_dfs=df_list_yearly, x="Year", yearly=False))],
                        [dcc.Graph(figure=plt_obj.stacked_bar_side(list_dfs=list_dfs, x="TS", yearly=True,))],
                        []
                        ]
            elif key in ['trade_map', 'hydrogen_infrastructure']:
                figure_dict = plt_obj.create_dict_tade_geo_fig(capacities=capacities)
                lis = [dbc.Col(children=[dbc.Row(children=[dcc.Graph(figure=y) for y in figure_dict[s]])]) for s in
                       scenario]
                return [[dbc.Row(children=lis, style={"height":2000})],
                        # return [[dbc.Row(children=[dbc.Col(children=[html.P('Scenario:', style=HEADER)]),
                        # dbc.Col(children=[html.P('Scenario:', style=HEADER)])])],
                        [],
                        [],
                        []]
            elif key in ["export"]:
                tables = []
                for df in list_dfs:
                    (styles, legend) = discrete_background_color_bins(df)
                    tables.append(dbc.Col(children=[dbc.Row(children=[dash_table.DataTable(data=df.to_dict('records'),
                                                                                           columns=[{"name": i, "id": i}
                                                                                                    for i in
                                                                                                    df.columns],
                                                                                           style_data_conditional=styles)])]))

                # lis = [dbc.Col(children=[dbc.Row(children=[dash_table.DataTable(df.to_dict('records'), [{"name": i, "id": i} for i in df.columns])])]) for df in list_dfs]
                return [[dbc.Row(children=tables)],
                        [],
                        [],
                        []]

            else:
                return [[], [], []]

## TODO LOADING https://dash.plotly.com/dash-core-components/loading
