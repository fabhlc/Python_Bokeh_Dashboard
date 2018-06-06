from bokeh.models.widgets import DataTable, TableColumn, NumberFormatter
from bokeh.models import ColumnDataSource, Panel

import pandas as pd

def make_datatable(bikeshare):
    ''' Table shows number of trips from their origin stations'''

    def make_dataset(bikeshare):
        # Create skeleton for dataframe:
        df = pd.DataFrame(columns=['origin', 'trips'])
        df_count = bikeshare.groupby('from_station_name')['trip_id'].count().sort_values(ascending=False)
        df['origin'] = df_count.index
        df['trips'] = df_count.values

        grouped = bikeshare.groupby('from_station_name')

        # Calculate average duration from station:
        duration = pd.DataFrame()
        means = pd.DataFrame(grouped['trip_duration_mins'].mean())
        duration['from_station_name'] = means.index
        duration['avg_duration_mins'] = means.values
        df = df.merge(right=duration, left_on='origin', right_on='from_station_name', how='left')

        df.drop('from_station_name', axis=1, inplace=True)
        df.set_index('origin', inplace=True)

        # Calculate top three destinations for each station:
        df['top_one'] = None
        df['top_two'] = None
        df['top_three'] = None

        for station in df.index:
            subset = bikeshare[bikeshare['from_station_name'] == station]
            counts = subset.groupby('to_station_name')['to_station_name'].count().sort_values(ascending=False)
            top = pd.DataFrame(columns=['to_station_name', 'trips'])
            top['to_station_name'] = counts.index
            top['trips'] = counts.values
            top['proportion'] = counts.values / counts.sum()

            top_five = ['%s, %.2f' % (index, val) for (index, val) in
                        zip(top[:5]['to_station_name'], top[:5]['proportion'])]

            df.loc[[station], ['top_one']] = top_five[0]
            df.loc[[station], ['top_two']] = top_five[1]
            df.loc[[station], ['top_three']] = top_five[2]

        return ColumnDataSource(df)

    def make_table(df):
        columns = [
            TableColumn(field='origin', title="Origin"),
            TableColumn(field="trips", title="No. of Trips", formatter = NumberFormatter(format='0,0')),
            TableColumn(field="avg_duration_mins", title="Avg. Duration (mins)", formatter = NumberFormatter(format='0.0')),
            TableColumn(field="top_one", title="Top Destination (1)"),
            TableColumn(field="top_two", title="Top Destination (2)"),
            TableColumn(field="top_three", title="Top Destination (3)"), ]

        data_table = DataTable(source=df, index_position=0, columns=columns, width = 1200, height = 800)
        return data_table

    # ## Deploy

    data_sauce = make_dataset(bikeshare)
    table_sauce = make_table(data_sauce)

    tab = Panel(child = table_sauce, title = "Summary Table")

    return tab