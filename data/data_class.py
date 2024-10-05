from data.config import header_mapping, aggregation, key_to_julia, hydrogen_technologies
import pandas as pd
import json
import os




def read_geojson_file():
    """
    Returns: Reads json with geolocations for regions
    """
    path = os.getcwd() + "/config/geolocation.json"
    with open(path, 'r') as fp:
        return json.load(fp)


class DataRaw:

    def __init__(self, directory, key, sector="Power"):
        self.directory = directory
        self.key = key_to_julia[key]
        self.sector = sector
        self.df = self.read_sol_file(key=self.key)

    def read_sol_file(self, key):
        with open(self.directory, "r") as f:
            lines = f.read().splitlines()
            data_list = []
            for i, l in enumerate(lines, start=-1):
                if l.startswith(f"{key}["):
                    m = l.split('[', 1)[1].split(']')[0].split(",")
                    m.append(l.split(" ")[-1])
                    data_list.append(m)
                    if not lines[i + 1].startswith(key):
                        break
        return self.create_df(data_list, key)

    def filter_sector(self):
        # filter only POWER sector technologies
        # TO more dynamic user input
        df_input = pd.read_csv('/cluster/home/danare/git/scenario_dashboard/config/Tag_Technology_to_Sector.csv',
            delimiter=";")
        self.df = pd.merge(right=self.df, left=df_input, left_on="Technology", right_on="Technology", how="outer")
        # consider storages if power sector
        if self.sector == "Power":
            self.df = self.df[(self.df['Sector'] == self.sector) | (self.df['Sector'] == "Storages")]
        else:
            self.df = self.df[self.df['Sector'] == self.sector]
        return self.df

    def aggregate_technologies(self):
        # aggregate technologies
        self.df.replace(aggregation, inplace=True)
        self.df = self.df.groupby(by=header_mapping[self.key]["columns"][:-1], as_index=False).sum(numeric_only=True)
        return self.df

    def create_df(self, data_list, key):
        # create data frame
        df = pd.DataFrame(columns=header_mapping[key]["columns"],
                          data=data_list)

        df['Year'] = pd.to_numeric(df['Year'])
        df['Value'] = pd.to_numeric(df['Value'])

        # convert unit if required from PJ to TWh
        if key in ["ProductionByTechnologyAnnual", "Export", "UseAnnual", "RateOfActivity", "ProductionByTechnology", "ProductionByTechnology"]:
            df['Value'] = (df['Value'] / 3.6)#.round(0)

        # adapt storage charging and discharging
        # if key == "ProductionByTechnology":
        #     for s in ["D_PHS", "D_Battery_Li-Ion", "D_Battery_Redox"]:
        #         if s in df["Technology"].unique():
        #             df.loc[(df["Mode"] == 1) & (df["Technology"] == s), "Value"] *= -1

        return df

    def aggregate_regions(self):
        # aggregate regions & offshore nodes
        self.df.replace({"OFFGBMid": "OFFUKMid", "OFFGBScot": "OFFUKScot", "OFFGBSor": "OFFUKSor"}, inplace=True)
        self.df['Region_agg'] = [r[3:5] if "OFF" in r else r[:2] for r in self.df['Region']]
        self.df = self.df.groupby(by=header_mapping[self.key]["columns"][:-1] + ["Region_agg"], as_index=False).sum(
            numeric_only=True)

    def replace_offshore(self):
        # replace uk with gb
        self.df.replace({"OFFGBMid": "OFFUKMid", "OFFGBScot": "OFFUKScot", "OFFGBSor": "OFFUKSor"}, inplace=True)

    def aggregate_column(self, column, method="sum"):
        # aggregate columns
        agg_cols = [c for c in header_mapping[self.key]["columns"][:-1] if c != column]
        if method == "sum":
            self.df = self.df.groupby(by=agg_cols, as_index=False).sum(numeric_only=True)
        elif method == "max":
            self.df = self.df.groupby(by=agg_cols, as_index=False).max(numeric_only=True)

    def filter_column(self, column, by_filter):
        # filter column
        self.df = self.df[self.df[column].isin(by_filter)]
        self.sort_reindex_values()

    def sort_reindex_values(self):
        self.df = self.df.sort_values(by='Value', ascending=True)
        self.df.reset_index(inplace=True, drop=True)

    def pivot_table(self):
        self.df = self.df.pivot(index='Region1', columns='Region2', values='Value')
        self.df.reset_index(inplace=True, drop=False)
    def add_storage(self):

         self.df['TS'] = self.df['TS'].astype('float64')
         # multiply with output activity ration and timeslices



         #self.df.sort_values(by="TS", ascending=True, inplace=True)
         # TO DO add storage
         #strg = self.read_sol_file(key="StorageLevelTSStart")
         #merged_df = pd.concat([self.df, strg])
         #merged_df.to_csv("test.csv")

    def add_demand(self, demand_df):

        # rename columns
        demand_df.replace(to_replace="Power", value="Demand", inplace=True)
        demand_df["Value"] = demand_df["Value"]/3.6
        self.df = pd.concat([self.df, demand_df])
        self.df['TS'] = pd.to_numeric(self.df['TS'])
