import pandas as pd
from os.path import join, dirname
import time

import csv, os, json
from bokeh.io import curdoc
from bokeh.models.widgets import Tabs

# import own Python files from 'scripts' subfolder:
from scripts.draw_map import make_map
from scripts.data_table import make_datatable


# import data
bikeshare = pd.read_csv(join(dirname(__file__), 'data', 'Q3-2016_BikeShare.csv'))
stations = pd.read_csv(join(dirname(__file__), 'data', 'stations_locations.csv'))
#
# API_key = open(join(dirname(__file__), 'data', 'GoogleAPI_Key.txt'), "r")

# Bit of cleaning...
bikeshare['trip_duration_mins'] = [i / 60 for i in list(bikeshare['trip_duration_seconds'])]
bikeshare['day_num'] = [time.strptime(x, '%A').tm_wday for x in list(bikeshare['day'])]
    # Clean stations which have a missing value
bikeshare.loc[bikeshare['from_station_name'].isnull(), 'from_station_name'] = 'Unknown'
bikeshare.loc[bikeshare['to_station_name'].isnull(), 'to_station_name'] = 'Unknown'

# Create tab per Bokeh script:
tab1 = make_map(bikeshare, stations)
tab2 = make_datatable(bikeshare)

# Create master tab:
tabs = Tabs(tabs=[tab1, tab2])

# Display tabs
curdoc().add_root(tabs)
curdoc().title = "Bikeshare Analytics"