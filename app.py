import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shiny import App, ui, render

file_path_unemployment = '/Users/wuzhenhan/Desktop/final-project-xy-wz/data/anunemp.csv'
shapefile_path = '/Users/wuzhenhan/Desktop/final-project-xy-wz/cb_2018_us_state_500k/cb_2018_us_state_500k.shp'
file_path_gdp_unemployment = '/Users/wuzhenhan/Desktop/final-project-xy-wz/data/merged_data.csv'

unemployment_data = pd.read_csv(file_path_unemployment)
unemployment_data_filtered = unemployment_data.loc[unemployment_data['State'] != "United States"].copy()
unemployment_data_filtered['State'] = unemployment_data_filtered['State'].str.strip().str.title()

gdf_states = gpd.read_file(shapefile_path)
gdf_states['NAME'] = gdf_states['NAME'].str.strip().str.title()

data = pd.read_csv(file_path_gdp_unemployment, parse_dates=['DATE'])

app_ui = ui.page_fluid(
    ui.h2("Unemployment Rate by State"),
    ui.input_select("year", "Select Year", choices=[2018, 2019, 2020, 2021, 2022, 2023, 2024]),
    ui.output_plot("plot"),
    ui.output_table("top_3_states"),

    ui.h2("Trends in Real GDP and Unemployment Rate During the Implementation of the CARES Act"),
    ui.input_checkbox_group(
        "indicator_checklist", 
        "Select Indicators to Display:",
        choices=["Real GDP", "Unemployment Rate"],  
        selected=["Real GDP", "Unemployment Rate"]
    ),
    ui.output_plot("line_chart"),
    
    ui.input_radio_buttons(
        "time_period",
        "Select Time Period:",
        choices={
            'all_periods': 'All Periods (2018 Q1 onwards)',
            'pre_cares': 'Pre-CARES Act (2018 Q1 - 2020 Q1)',
            'cares_implementation': 'CARES Act Implementation (2020 Q2)',
            'post_cares': 'Post-CARES Act (2020 Q3 onwards)'
        },
        selected='all_periods'
    )
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

    @output
    @render.plot
    def line_chart():
        selected_indicators = input.indicator_checklist()
        time_period = input.time_period()
        if time_period == 'all_periods':
            filtered_data = data
        elif time_period == 'pre_cares':
            filtered_data = data[(data['DATE'] >= '2018-01-01') & (data['DATE'] <= '2020-03-31')]
        elif time_period == 'cares_implementation':
            filtered_data = data[(data['DATE'] >= '2020-04-01') & (data['DATE'] <= '2020-07-01')]
        else:
            filtered_data = data[data['DATE'] >= '2020-07-01']
        fig, ax1 = plt.subplots(figsize=(10, 6))
        if 'Real GDP' in selected_indicators:
            line1, = ax1.plot(filtered_data['DATE'], filtered_data['GDPC1'], color='b', label='Real GDP')
            ax1.set_xlabel("Time")
            ax1.set_ylabel("Real GDP", color='b')
            ax1.tick_params(axis='y', labelcolor='b')
        if 'Unemployment Rate' in selected_indicators:
            ax2 = ax1.twinx()  
            line2, = ax2.plot(filtered_data['DATE'], filtered_data['UNRATE'], color='orange', label='Unemployment Rate')
            ax2.set_ylabel("Unemployment Rate (%)", color='orange')
            ax2.tick_params(axis='y', labelcolor='orange')
        cares_act_date = pd.to_datetime('2020-03-27')
        ax1.axvline(cares_act_date, linestyle='--', color='red')
        ax1.text(cares_act_date, 1.0, '2020/03/27', rotation=0, horizontalalignment='right',
                 verticalalignment='bottom', color='red', fontsize=9, fontweight='bold',
                 bbox=dict(facecolor='white', edgecolor='none', pad=1.0),
                 transform=ax1.get_xaxis_transform())
        handles = []
        labels = []
        if 'Real GDP' in selected_indicators:
            handles.append(line1)
            labels.append('Real GDP')
        if 'Unemployment Rate' in selected_indicators:
            handles.append(line2)
            labels.append('Unemployment Rate')
        caret_line = plt.Line2D([0], [0], color='red', linestyle='--')
        handles.append(caret_line)
        labels.append('CARES Act Begins')
        ax1.legend(handles, labels, loc='upper left')
        plt.title(f"Trends in Real GDP and Unemployment Rate ({filtered_data['DATE'].min().strftime('%Y/%m/%d')} to {filtered_data['DATE'].max().strftime('%Y/%m/%d')})")
        fig.tight_layout() 
        return fig

app = App(app_ui, server)

if __name__ == '__main__':
    app.run()
