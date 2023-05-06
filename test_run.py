import dash
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import time

app = dash.Dash(__name__)

app.layout = html.Div([
     dcc.Input(id='input'),
     dcc.Store(id='data'),
     html.Div(id='output'),
     dcc.Loading(dcc.Graph(id='graph-1')),
     dcc.Loading(dcc.Graph(id='graph-2'))
])

@app.callback(
    Output('data', 'data'),
    Output('output', 'children'),
    Output('graph-1', 'className'),  # dummy output just to trigger the loading state on `graph-1`
    Output('graph-2', 'className'),  # dummy output just to trigger the loading state on `graph-2`
    Input('input', 'value')
)
def update_data(value):
    time.sleep(2)
    return value, value, dash.no_update, dash.no_update

@app.callback(Output('graph-1', 'figure'), Input('data', 'data'))
def display_graph_1(value):
    time.sleep(3)
    return {'layout': {'title': value}}

@app.callback(Output('graph-2', 'figure'), Input('data', 'data'))
def display_graph_2(value):
    time.sleep(3)
    return {'layout': {'title': value}}
    
if __name__ == '__main__':
    app.run_server(debug=True)