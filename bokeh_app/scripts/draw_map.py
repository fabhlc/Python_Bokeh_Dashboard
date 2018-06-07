from collections import Counter
from bokeh.layouts import widgetbox, row
from bokeh.models import ColumnDataSource, GMapOptions, HoverTool, Panel
from bokeh.models.widgets import CheckboxGroup, MultiSelect, RangeSlider
from bokeh.palettes import YlOrRd9
from bokeh.plotting import gmap

from os.path import join, dirname
import pandas as pd

YlOrRd9.reverse()

def make_map(bikeshare, stations):

    def make_dataset(selected_stations, selected_days, min_selected_time=5,max_selected_time=15):

        # Create skeleton for dataframe:
        df = pd.DataFrame(columns=['origin', 'destination', 'lat', 'lon', 'trips', 'color', 'avg_duration'])

        # Put each selected_day into dataframe:
        for station in selected_stations:
            subset = bikeshare[(bikeshare['from_station_name'] == station) &
                                bikeshare['day'].isin(selected_days) &
                               (bikeshare['trip_duration_mins'] <= max_selected_time) &
                               (bikeshare['trip_duration_mins'] >= min_selected_time)]

            dest_count = Counter(subset['to_station_name']).most_common()

            mini_df = pd.DataFrame({'origin': station,
                                    'destination': [dest for dest, count in dest_count],
                                    'trips': [count for dest, count in dest_count]})
            mini_df = pd.merge(left=mini_df, right=stations[['name', 'lat', 'lon']], left_on='destination', right_on='name')

            # Calculate average duration of trip from origin to each destination:
            duration_calc = subset.groupby('to_station_name')['trip_duration_mins'].mean()
            mini_df['avg_duration'] = [duration_calc[i] for i in mini_df['name']]

            # Set colour scheme:
            max_trips = mini_df['trips'].max()
            mini_df['color'] = [YlOrRd9[int((i / max_trips) * 8)] for i in mini_df['trips']]
            mini_df['proportion'] = mini_df['trips'] / mini_df['trips'].sum()

            df = df.append(mini_df)

        df_origins = pd.DataFrame({'origin': selected_stations})
        df_origins = pd.merge(left=df_origins, right=stations[['name', 'lat', 'lon']], left_on='origin', right_on='name')

        return ColumnDataSource(df), ColumnDataSource(df_origins)


    def plot_map(data_sauce, origin_data_sauce, fig_sauce):
        # map_sauce is ColumnDataSource output of make_dataset()

        origins_glyph = fig_sauce.circle_cross(x='lon', y= 'lat', alpha = 0.7,
                                        size = 20, line_color = 'white', line_alpha = 0.8, fill_color = 'blue',
                                               source = origin_data_sauce)

        circles_glyph = fig_sauce.circle(x='lon', y='lat', alpha=1, size=12, line_color='black', line_alpha=0.5,
                        source=data_sauce, fill_color='color')

        fig_sauce.renderers.append(origins_glyph)
        fig_sauce.renderers.append(circles_glyph)

        hover = HoverTool(tooltips=[('Station', '@destination'),
                                    ('Origin', '@origin'),
                                    ('No. of Trips', '@trips'),
                                    ('Avg. Duration (mins)', '@avg_duration{0.0}'),
                                    ('Share of Trips from Origin', '@proportion{0%}')])
        fig_sauce.add_tools(hover)
        return fig_sauce


    def update(attr, old, new):
        assert len(selected_stations.value) < 6, 'More than 5 stations selected. Please deselect some stations!'

        stations_to_plot = selected_stations.value
        days_to_plot = [days_of_week[i] for i in selected_days.active]
        duration_to_plot = selected_duration.value

        new_data_sauce, new_origin_data_sauce = make_dataset(stations_to_plot, days_to_plot, duration_to_plot[0],duration_to_plot[1])

        data_sauce.data.update(new_data_sauce.data)
        origin_data_sauce.data.update(new_origin_data_sauce.data)

        print("Updated!")


    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    all_stations = sorted(list(set(bikeshare['from_station_name'])))


    # ## Widgets:

    selected_stations = MultiSelect(value=['Union Station'],
                                    options=all_stations,
                                    title="Select up to five origin stations:",
                                    size = 20)
    selected_stations.on_change('value', update)

    selected_days = CheckboxGroup(active=[i for i in range(0,7)],
                                  labels=days_of_week)
    selected_days.on_change('active', update)

    selected_duration = RangeSlider(start=5, end=60,
                            step = 5, value = (5,15),
                            title = 'Max Duration of Bike Trips (mins)')
    selected_duration.on_change('value', update)


    # ## Deploy

    initial_stations = ['Union Station']
    initial_days = [selected_days.labels[i] for i in selected_days.active]
    min_time = selected_duration.value[0]
    max_time = selected_duration.value[1]

    # Set to Toronto:
    map_options = GMapOptions(lat=43.6540, lng=-79.3832, map_type="roadmap",
                              zoom=13, scale_control=True)

    with open(join(dirname(__file__), 'GoogleAPI_Key.txt'), "r") as txt:
        API_key = txt.readline()

    fig_sauce = gmap(API_key, map_options,
                     title="Toronto Bike Share Trip Destinations by Origin (Q3-2016)",
                     plot_width=800)

    fig_sauce.xaxis.visible = False
    fig_sauce.yaxis.visible = False
    fig_sauce.title.align = 'center'
    fig_sauce.title.text_font_size = '16pt'

    data_sauce, origin_data_sauce = make_dataset(initial_stations, initial_days, min_time, max_time)

    fig = plot_map(data_sauce, origin_data_sauce, fig_sauce)

    controls = widgetbox(selected_stations, selected_days,selected_duration)

    layout = row(controls, fig)

    tab = Panel(child = layout, title = "Destination Map")

    return tab
