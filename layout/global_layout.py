from dash import html, dcc
import dash_bootstrap_components as dbc
from config.layout_config import *
import dash
from layout.layout_general import my_img


sidebar = html.Div(children=
[
    dbc.Row(children=
    [
        html.H3('Load Data'),
        html.Br(),
        html.Br(style={'margin': '8px'}),
        #html.Hr(style={'height': '2px', 'opacity': '1', 'margin': '8px'}),
    ]),

    dbc.Row(children=
            [
                html.Div(id='container', children=[]),
            ]),

    dbc.Row(children=[
        dbc.Col(children=[
            dbc.Button('Add',
                       id='add',
                       n_clicks=0,
                       style=BUTTON,
                       outline=True,
                       color="primary",
                       className="d-grid"
                       )
        ]),
        dbc.Col(children=[
            dbc.Button('Save',
                       id='save',
                       n_clicks=0,
                       style=BUTTON,
                       color="primary",
                       outline=True,
                       className="d-grid"
                       ),
            dcc.Loading(
                id="loading-1",
                type="circle",
                children=html.Div(id="loading-output-1")
            ),
        ])

    ], style={'margin-top': '1rem'}),
], style=SIDEBAR_STYLE)

content = html.Div(children=
[
    dbc.Row(children=[dbc.Col(children=html.H2('GENeSYS-MOD Dashboard',
                                               className="bg-primary text-white p-2 mb-2 text-center"), style={'margin': '8px'}),
                      ]),
    dbc.Row(children=
    [
        dbc.Col(children=html.H5('Result:'),  width={"size": 2}),
        dbc.Col(children=[dcc.Dropdown(
            options=[
                {'label': 'Installed Capacities [GW]', 'value': 'capacities'},
                {'label': 'Production [TWh]', 'value': 'operation'},
                {'label': 'Export 2050 [TWh]', 'value': 'export'},
                {'label': 'Total System Costs [MEUR]', 'value': 'costs'},
                {'label': 'Demand [TWh]', 'value': 'Demand [TWh]', 'disabled': True},
                {'label': 'Hydrogen Infrastructure', 'value': 'hydrogen_infrastructure', 'disabled': False},
                {'label': 'Trade Capacity Power [GW]', 'value': 'trade_map'}
            ],
            id="dropdownmenu",
            placeholder="Select:"
        )], width={"size": 3})
    ], style={'margin': '12px'}),
    dbc.Row(children=[], id="fuel", style={'margin': '12px'}),
    dbc.Row(children=[], id="my_tabs"),

    ], style=CONTENT_STYLE)

