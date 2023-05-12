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
from dash import dcc
from dash import  html
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output
from dash.long_callback import DiskcacheLongCallbackManager

from dash_extensions.enrich import FileSystemStore, Dash

import diskcache
cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)


output_defaults = dict(backend=FileSystemStore(
    cache_dir="./some_path"), session_check=True)
# app = dash.Dash(__name__, background_callback_manager=background_callback_manager)
app = Dash(__name__, output_defaults=output_defaults, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True,long_callback_manager=long_callback_manager)

app.title = "Real-Time RSC Monitoring"

server = app.server

