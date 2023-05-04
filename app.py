# import diskcache
# cache = diskcache.Cache("./cache")
# background_callback_manager = DiskcacheManager(cache)
from datetime import datetime as dt
from datetime import date, timedelta
import os
from statistics import mean
from random import randint, shuffle

import pandas as pd
import plotly.graph_objs as go
import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output


# app = dash.Dash(__name__, background_callback_manager=background_callback_manager)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)

app.title = "Real-Time RSC Monitoring"

server = app.server
