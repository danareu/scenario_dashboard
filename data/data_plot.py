import pandas as pd
from data.config import colour_codes, header_mapping, key_to_julia
from itertools import cycle
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from data.data_class import read_geojson_file


class PlotObject:

    def __init__(self, key, df_list, scenarios, year=None, sector="Power"):
        self.df_list = df_list
        self.year = year if year is not None else self.df_list[0]['Year'].unique()
        self.key = key_to_julia[key]
        self.sector = sector
        self.scenarios = scenarios
        self.color_to_tech = self.create_col_palette() if key not in ["trade_map", "hydrogen_infrastructure",
                                                                      "export"] else ""

    def create_col_palette(self):

        ## cycle through color palette
        palette = cycle(px.colors.qualitative.Light24)
        technology_list = []

        for df in self.df_list:
            technology_list += list(df['Technology'].unique())

        return {t: colour_codes[t] if t in colour_codes.keys() else next(palette) for t in
                pd.Series(technology_list).unique()}

    def stacked_bar_integrated(self, aggregation=True):

        fig = make_subplots(rows=len(self.year),
                            cols=1,
                            subplot_titles=[f'{self.key}_{int(y)}_{self.sector}' for y in
                                            self.year])

        for df, s in zip(self.df_list, self.scenarios):

            # search for better way
            region_col = 'Region'
            if aggregation:
                df = df.groupby(by=['Year', 'Technology', 'Region_agg'], as_index=False).sum(numeric_only=True)
                region_col = 'Region_agg'
            df['Scenario'] = s
            for j, y in enumerate(self.year, start=1):
                for t in df[df['Year'] == y]['Technology'].unique():
                    fig.add_trace(go.Bar(x=[df[(df['Year'] == y) & (df['Technology'] == t)][region_col],
                                            df[(df['Year'] == y) & (df['Technology'] == t)]['Scenario']],
                                         y=df[(df['Year'] == y) & (df['Technology'] == t)]['Value'],
                                         name=t,
                                         marker_color=self.color_to_tech[t],
                                         legendgroup=t,
                                         showlegend=True if j == 1 else False,
                                         ), row=j, col=1)

        fig.update_layout(barmode='stack', height=2700, font=dict(size=26))
        fig.update_yaxes(title_text=header_mapping[self.key]["units"])
        # fig.update_yaxes(range=[0, self.df_list[0]['Value'].max()])
        return fig

    def stacked_bar_side(self, x="Year"):

        # make subplot titles
        region_list = pd.Series([i for df in self.df_list for i in df['Region']]).unique()
        fig = make_subplots(rows=len(region_list),
                            cols=len(self.scenarios),
                            subplot_titles=[f"{r}_{s}" for r in region_list for s in self.scenarios])

        for i, df in enumerate(self.df_list, start=1):
            for j, r in enumerate(region_list, start=1):
                # check if region is in data
                if df['Region'].str.contains(r).any():
                    # sum and sort
                    technologies = \
                    df[df['Region'] == r].groupby(by=['Technology'], as_index=False).sum().sort_values(by="Value")[
                        'Technology'].unique()
                    for t in technologies:
                        fig.add_trace(go.Scatter(x=df[(df['Region'] == r) & (df['Technology'] == t)][x],
                                                 y=df[(df['Region'] == r) & (df['Technology'] == t)]['Value'],
                                                 name=t,
                                                 mode='lines',
                                                 fillcolor=self.color_to_tech[t],
                                                 line_color=self.color_to_tech[t],
                                                 legendgroup=t,
                                                 stackgroup=r,
                                                 showlegend=True if j == 2 else False,
                                                 ), row=j, col=i)

        fig.update_yaxes(title_text=header_mapping[self.key]["units"])
        fig.update_layout(height=13700,
                          barmode='stack',
                          font=dict(size=22)
                          )


        return fig

    def create_dict_tade_geo_fig(self, capacities=[]):
        """
        Create dictionary with scenario key word
        Workaround bc multi-plots are too complicated for scatter_geo
        capacities: list of hydrogen capacities
        """
        scenario_to_year = {}
        self.year = [2018, 2050]
        if not capacities:
            for df, s in zip(self.df_list, self.scenarios):
                scenario_to_year[s] = [
                    self.plot_trade_capacity(df=df[df['Year'] == y], year=y, scenario=s, geojson=read_geojson_file(),
                                             pie_chart=True)
                    for y in self.year]
        else:
            for df, s, c in zip(self.df_list, self.scenarios, capacities):
                scenario_to_year[s] = [
                    self.plot_trade_capacity(df=df[df['Year'] == y], year=y, capacities=c, scenario=s,
                                             geojson=read_geojson_file(), pie_chart=True)
                    for y in self.year]

        return scenario_to_year

    def plot_trade_capacity(self, df, year, scenario, geojson, show_marker=False, capacities=None, pie_chart=False):
        fig = go.Figure()
        lataxis = [35, 70]
        lonaxis = [-9.7, 38]
        df.reset_index(inplace=True)
        for index, row in df.iterrows():
            # when there is no line back for offshore nodes
            try:
                i = max(row['Value'],
                        df[(df['Region1'] == row['Region2']) & (df['Region2'] == row['Region1'])]['Value'].values[0])
            except IndexError:
                i = row['Value']

            try:
                lat = geojson[row['Region2']]['latitude'], geojson[row['Region1']]['latitude']
                lon = geojson[row['Region2']]['longitude'], geojson[row['Region1']]['longitude']
            except KeyError:
                print(f"{row['Region2'], row['Region1']} Key not found in available data")

            fig.add_trace(go.Scattergeo(
                locationmode='country names',
                lat=[geojson[row['Region2']]['latitude'], geojson[row['Region1']]['latitude']],
                lon=[geojson[row['Region2']]['longitude'], geojson[row['Region1']]['longitude']],
                mode='lines+markers',
                name=f'{i: .2f} GW',
                text=f'{i: .2f} GW',
                legendgroup=row["Value"],
                showlegend=True if (index == 0) | (index == (df.shape[0]-1)) else False,
                line=dict(width=1 if show_marker else i,
                          color='grey'),# if (capacities is None and pie_chart is False) else "rgb(0,191,191)"),
                marker=dict(size=5 if (capacities is None and pie_chart is False) else 1,
                            color="black",
                            line_color='black',
                            line_width=0.5,
                            sizemode='area')))

            if show_marker:
                fig.add_trace(go.Scattergeo(
                    locationmode='country names',
                    lat=[(geojson[row['Region2']]['latitude'] + geojson[row['Region1']]['latitude']) / 2],
                    lon=[(geojson[row['Region2']]['longitude'] + geojson[row['Region1']]['longitude']) / 2],
                    mode='text',
                    name=f'<b>{i: .2f}</b>',
                    showlegend=False,
                    textfont=dict(color='black', size=9),
                    # textposition='middle center',
                    text=f'{i: .1f}', ))
        if (capacities is not None) and (pie_chart is False):
            for index, row in capacities.iterrows():
                fig.add_trace(go.Scattergeo(
                    locationmode='country names',
                    lat=[geojson[row['Region']]['latitude']],
                    lon=[geojson[row['Region']]['longitude']],
                    mode='markers',
                    name=f'{row["Region"]}, {row["Value"]: .2f} GW',
                    # text=f'{i: .2f} GW',
                    legendgroup=row["Value"],
                    showlegend=True if (index == 0) | (index == capacities.shape[0] - 1) else False,
                    marker=dict(size=row['Value'] / 3,
                                color=colour_codes['Hydrogen'] if row['Value'] > 0 else "rgb(229,229,229)",
                                line_width=0.5,
                                sizemode='area')))

        fig.update_layout(height=2000)
        if pie_chart:
            capacities = capacities[capacities["Technology"].isin(colour_codes.keys())]

            # determine size of pie rel to sum of inst capacities
            max_capa_df = capacities.groupby(by=["Region", "Year"], as_index=False).sum()
            max_capa = max_capa_df[max_capa_df['Year']==year]['Value'].max()
            for r in capacities["Region"].unique():
                x_domain = (geojson[r]['longitude'] - lonaxis[0]) / (lonaxis[1] - lonaxis[0])
                y_domain = (geojson[r]['latitude'] - lataxis[0]) / (lataxis[1] - lataxis[0])  # no negative number there
                colors = [colour_codes[c] for c in
                          capacities[(capacities['Region'] == r) & (capacities["Year"] == year)]['Technology']]
                # factor to determine rel size of pie
                if capacities[(capacities['Region'] == r) & (capacities["Year"] == year)]['Value'].sum() > 0:
                    #factor = capacities[(capacities['Region'] == r) & (capacities["Year"] == year)]['Value'].sum()/max_capa
                    pie_trace = go.Pie(
                        labels=capacities[(capacities['Region'] == r) & (capacities["Year"] == year)]['Technology'],
                        values=capacities[(capacities['Region'] == r) & (capacities["Year"] == year)]['Value'],
                        marker=dict(colors=colors),
                        textinfo='none',
                        domain=dict(x=[max(0, x_domain - 0.02), x_domain + 0.02],
                                    y=[max(0, y_domain - 0.02), y_domain + 0.02])
                    )
                    fig.add_trace(pie_trace)

        fig.update_layout(title_text=f'Total Trade Capacities [GW] for {scenario} in {year}',
                          #width=450,
                          height=2000,
                          geo=(go.layout.Geo(  # scope='europe',
                              lataxis=dict(range=[lataxis[0], lataxis[1]]),
                              lonaxis=dict(range=[lonaxis[0], lonaxis[1]]),
                              showland=True,
                              countrycolor='white',
                              #oceancolor="rgb(0,35,74)",
                              #showframe=False,
                              showlakes=True,
                              #lakecolor="rgb(0,35,74)",
                              #coastlinecolor='rgb(0,35,74)',
                              showcoastlines=False,
                              landcolor='rgb(229, 229, 229)')))


        return fig
