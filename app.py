import shiny
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shiny import App, ui, render

file_path = '/Users/wuzhenhan/Desktop/final-project-xy-wz/data/anunemp.csv'
unemployment_data = pd.read_csv(file_path)

unemployment_data_filtered = unemployment_data.loc[unemployment_data['State'] != "United States"].copy()
unemployment_data_filtered['State'] = unemployment_data_filtered['State'].str.strip().str.title()

shapefile_path = '/Users/wuzhenhan/Desktop/final-project-xy-wz/cb_2018_us_state_500k/cb_2018_us_state_500k.shp'
gdf_states = gpd.read_file(shapefile_path)
gdf_states['NAME'] = gdf_states['NAME'].str.strip().str.title()

app_ui = ui.page_fluid(
    ui.h2("Unemployment Rate by State"),
    ui.input_select("year", "Select Year", choices=[2018, 2019, 2020, 2021, 2022, 2023,2024]),
    ui.output_plot("plot"),
    ui.output_table("top_3_states")
)

def server(input, output, session):
    @output
    @render.plot
    def plot():
        year = input.year()
        year_column = f'Rate_{year}'

        gdf_merged = gdf_states.merge(unemployment_data_filtered, how='left', left_on='NAME', right_on='State').copy()
        gdf_merged[year_column] = gdf_merged[year_column].fillna(0)

        fig, ax = plt.subplots(1, 1, figsize=(10, 7))
        gdf_merged.boundary.plot(ax=ax, linewidth=1, edgecolor='black')
        gdf_merged.plot(column=year_column, cmap='OrRd', linewidth=0.8, ax=ax, edgecolor='black', legend=True,
                        legend_kwds={'label': f"Unemployment Rate in {year} (%)",
                                     'shrink': 0.6},
                        vmin=0, vmax=10)

        plt.title(f'Unemployment Rate by State ({year})', fontsize=15)
        plt.axis('off')
        ax.set_aspect('equal')
        ax.set_xlim(-180, -50)
        ax.set_ylim(15, 75)

        return fig

    @output
    @render.table
    def top_3_states():
        year = input.year()
        year_column = f'Rate_{year}'

        gdf_merged = gdf_states.merge(unemployment_data_filtered, how='left', left_on='NAME', right_on='State').copy()
        gdf_merged[year_column] = gdf_merged[year_column].fillna(0)

        top_3_states = gdf_merged.nlargest(3, year_column)[['NAME', year_column]].reset_index(drop=True)
        return top_3_states

app = App(app_ui, server)

if __name__ == '__main__':
    app.run()
