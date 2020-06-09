import sys
import dash
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
import dash_table as dt
import datetime
import io
import os
import pandas as pd
import webbrowser
from dash.dependencies import Input, State, Output
from dateutil.relativedelta import relativedelta
from flask import request
import logging
from utils.logger import format_logs
import base64
from utils.comparison import Comparison
from flask_caching import Cache

# Set up the app

app = dash.Dash(__name__)
cache = Cache(app.server, config={'CACHE_TYPE': 'filesystem', 'CACHE_DIR': 'cache'})
app.title = 'Image Excel Comparison App'
server = app.server
app_url = 'http://127.0.0.1:8050/'





input_area_style = {
    'width': '23%',
    'display': 'inline-block',
    'vertical-align': 'top'
}
separator_area_style = {
    'width': '2%',
    'display': 'inline-block',
    'vertical-align': 'middle',
}
output_area_style = {
    'width': '75%',
    'display': 'inline-block',
    'vertical-align': 'middle',
    'margin': 'auto'
}

app.layout = html.Div(
    children=[
        dcc.Location(id='url', refresh=False),
        dcc.Link('Navigate to "/shutdown"', href='/shutdown'),
        html.Div(id='page-content'),
        html.H1('Image Checking Process', style={'textAlign': 'center','color': '#7FDBFF'}),

        html.H2('Dash: A web application framework for checking image description based on the masterfile.',
                style={'textAlign': 'center', 'color': '#244c66'}),

        html.Div([
            html.Div(style={'padding-bottom': '20px'}),
            html.Div('Type folder location.'),
            html.Div([
                    dcc.Input(style={'width': '99%'},placeholder='Enter Your File Path Here', id='file-path', type='text', value=''),
            ], ),
            html.Div(style = {'padding-bottom': '20px'}),
            html.Div('Choose category.'),
            html.Div([dcc.Dropdown(
                        id='my-dropdown',
                        options=[
                            {'label': "Shoes", 'value': 'Shoe'},
                            {'label': "Belt", 'value': 'Belt'},
                            {'label': "Strap", 'value': 'Strap'},
                            {'label': "Bags", 'value': 'Bag'},
                            {'label': "Bracelets", 'value': 'Bracelet'},
                            {'label': "Shades", 'value': 'Shade'}],
                        value='Shoe')]),
            html.Div(style={'padding-bottom': '20px'}),
            html.Div(' Choose entity. '),
            html.Div([dcc.Dropdown(
                        id='entity_prefix',
                        options=[
                            {'label': "CK1", 'value': 'CK1'},
                            {'label': "SL1", 'value': 'SL1'},
                            {'label': "CK2", 'value': 'CK2'},
                            {'label': "SL2", 'value': 'SL2'},
                            {'label': "CK3", 'value': 'CK3'},
                            {'label': "CK4", 'value': 'CK4'},
                            {'label': "CK5", 'value': 'CK5'},
                            {'label': "CK6", 'value': 'CK6'}],
                        placeholder="Select a entity", value='CK1'), ]),

            html.Div(style={'padding-bottom': '20px'}),
            html.Div(' Choose launch.'),
            html.Div([
                    dcc.Dropdown(id='launch', options=
                                    [{'label': "Spring 2020", 'value': 'Spring 2020'},
                                     {'label': "Summer 2020", 'value': 'Summer 2020'},
                                     {'label': "Fall 2020", 'value': 'Fall 2020'},
                                     {'label': "Winter 2020", 'value': 'Winter 2020'},
                                     {'label': "Spring 2021", 'value': 'Spring 2021'},
                                     {'label': "Summer 2021", 'value': 'Summer 2021'}],
                                 placeholder="Select a launch", value='Winter 2020'),
            ]),

            html.Div(style={'padding-bottom': '20px'}),
            html.Button(id='submit-button', n_clicks=0, children='Submit', type='submit'),
            html.Div(style={'padding-bottom': '20px'}),
            # html.Button(id='save-button', n_clicks=0, children='Save Data', type='submit'),
            html.Div(style={'padding-bottom': '20px'}),
            html.Div(id='output-container-date'),
            ], style=input_area_style),

        html.Div([
            html.Div(id='settings-separator-area')
            ], style=separator_area_style
                ),

        html.Div([
            html.Div(style={'padding-bottom': '20px'}),
            html.Div(id='output-data-upload'),
            html.Div(id='output-container-2'),
            html.Div(style={'padding-bottom': '20px'}),
            dcc.Loading(id="loading-2",children=html.Div(html.Table(id='match-results'), className='four columns'),type="circle",)
                 ], style=output_area_style)
                 ]
                 )


@app.callback(
    Output('output-container-date', 'children'),[Input('submit-button', 'n_clicks'), Input('file-path', "value")])
def update_data(n_clicks, value):
    date = datetime.datetime.now()
    return u'''You have submitted "{}" times at "{}". '''.format(n_clicks, str(date))


@app.callback(
    Output(component_id='output-container-2', component_property='children'),
    [Input('submit-button', 'n_clicks'), ])
def update_upload(n_clicks):
    if int(n_clicks) >= 1:
        return u'''Processing "{}" times. Please be patient while the images are being read. '''.format(n_clicks)

def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.callback(
    Output(component_id='match-results', component_property='children'),
    [Input('submit-button', 'n_clicks'),dash.dependencies.Input('url', 'pathname')],
    [State('my-dropdown', 'value'), State('file-path', 'value'), State('entity_prefix', 'value'),
     State('launch', 'value')])
def generate_match_results(n_clicks, pathname, value1, value2, value3, value4):
    '''
    Input:
        value1 =eg.Shoe, Belt, Strap, Bag, Bracelet, Shade
        value2 = root_path
        value3 =entity_prefix
        value4=launch
    '''
    if pathname =='/shutdown':
        shutdown()
    if n_clicks == 0:
        cache.clear()
    if n_clicks != 0:
        value2 = value2.replace("\\", "/")
        try:
            compare_class = Comparison(parameters={'root_path': value2, 'entity_prefix': value3, 'category': value1,'Launch': value4})
        except ValueError:
            return 'File path may be wrong! Please check that you have the right path.'
        except:
            return "Unexpected error:", sys.exc_info()[0]
        else:
            try:
                diff_df = compare_class.comparison_result()
                if type(diff_df) == str:
                    return diff_df
            except:
                return "Unexpected error:", sys.exc_info()[0]
                # return ('Folder content may be wrong! Please check that you have the right setting and retry.')
            else:
                return html.Table(
                        # Header
                        [html.Tr([html.Th(col) for col in diff_df.columns])] +
                        # Body
                        [html.Tr([html.Td(diff_df.iloc[i][col]) for col in diff_df.columns
                                  ]) for i in range(min(len(diff_df), 100))])



if __name__ == '__main__':
    print("RUN====================================================================")
    format_logs('Image comparison', True)
    webbrowser.open(app_url)
    app.run_server(debug=False)
