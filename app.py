from pymongo import MongoClient
from pandas import Series, DataFrame
import pandas as pd
from datetime import datetime, timedelta
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import dash_table


from dash.dependencies import Input, Output
# import cufflinks as cf
import time
import json
import numpy as np
# import pickle
# import dill
import matplotlib.pyplot as plt

#1. Connect to Mongo database
username = 'datamanager'
password = 'airtransportationrulez'
url = 'mongodb://%s:%s@167.99.24.166:2700/datamanager'
mongo_client_fs = MongoClient(url % (username, password))
db = mongo_client_fs['datamanager']

#2. Query Mongo database
def query_flight_statuses_by_dates(start_date, end_date, dateUtc=True):
    operational_times_fields_departure = ['publishedDeparture', 'scheduledGateDeparture', 'estimatedGateDeparture',
        'actualGateDeparture',  'flightPlanPlannedDeparture',  'estimatedRunwayDeparture', 'actualRunwayDeparture']

    operational_times_fields_arrival = ['publishedArrival', 'scheduledGateArrival', 'estimatedGateArrival',
        'actualGateArrival', 'flightPlanPlannedArrival', 'estimatedRunwayArrival', 'actualRunwayArrival']


    date_type = "dateUtc" if dateUtc else "dateLocal"

    end_date_parsed = datetime.strptime(end_date,"%Y-%m-%d") + timedelta(days=1)
    end_date_lt = end_date_parsed.strftime("%Y-%m-%d")

    print (end_date_lt)

    return db.flightStatuses.find (
        {
            "$and" : [
                {
                "$or" :
                    [ {"operationalTimes.{}.{}".format(dep, date_type) :
                             {"$gte" : start_date}
                      } for dep in operational_times_fields_departure
                    ]
                },
                {
                    "$or":
                        [ {"operationalTimes.{}.{}".format(arr, date_type):
                                 {"$lt": end_date_lt}
                          } for arr in operational_times_fields_arrival
                        ]
                }
            ]
        }
    )

user_input_airportFsCode = 'LAX'
user_input_date = '2019-06-20'
flight_status_df = DataFrame(
    list(query_flight_statuses_by_dates(user_input_date, user_input_date, dateUtc=False)))
list(flight_status_df.columns)

#3. Create an airline dictionary, with IATA code with the "english" name (e.g., Delta, United), and update flight status dataframe
query_airlines = db.airlines.find()
airlines_list = list(query_airlines)
airline_dictionary = dict()

for i in airlines_list:
    key_name = i['fs']
    key_value = i['name']
    airline_dictionary[key_name] = key_value

flight_status_df['airline_name'] = flight_status_df['carrierFsCode'].map(airline_dictionary)

#4. Create function to extract from a column the nested field that is in a dictionary form, into their own dataframe columns

def ExtractField(d, k):
    if not isinstance(d, dict):  # for some rows without a value, the entry is not a dictionary,
        return None  # need to account for this to avoid error

    if k in d.keys():  # if the field I want to extract is in the cell, then the value for that field
        return d[k]
    else:
        return None


#5. Update flight_status_df with nested fields extracted into own columns

field_string = ''
field_keys_to_extract = []
field_string = 'airportResources'
x = field_string
field_keys_to_extract = ['departureTerminal', 'arrivalTerminal', 'departureGate',
                         'arrivalGate']

for i in field_keys_to_extract:
    flight_status_df[field_string + i] = flight_status_df[field_string].apply(lambda x: ExtractField(x, i))

field_string = ''
field_keys_to_extract = []
field_string = 'arrivalDate'
x = field_string
field_keys_to_extract = ['dateUtc', 'dateLocal']

for i in field_keys_to_extract:
    flight_status_df[field_string + i] = flight_status_df[field_string].apply(lambda x: ExtractField(x, i))

field_string = ''
field_keys_to_extract = []
field_string = 'departureDate'
x = field_string
field_keys_to_extract = ['dateUtc', 'dateLocal']

for i in field_keys_to_extract:
    flight_status_df[field_string + i] = flight_status_df[field_string].apply(lambda x: ExtractField(x, i))

field_string = ''
field_keys_to_extract = []
field_string = 'delays'
x = field_string
field_keys_to_extract = ['arrivalGateDelayMinutes', 'departureGateDelayMinutes', 'arrivalRunwayDelayMinutes',
                         'departureRunwayDelayMinutes']

for i in field_keys_to_extract:
    flight_status_df[field_string + i] = flight_status_df[field_string].apply(lambda x: ExtractField(x, i))

field_string = ''
field_keys_to_extract = []
field_string = 'flightStatusUpdates'
x = field_string
field_keys_to_extract = ['updatedAt']

for i in field_keys_to_extract:
    flight_status_df[field_string + i] = flight_status_df[field_string].apply(lambda x: ExtractField(x, i))

field_string = ''
field_keys_to_extract = []
field_string = 'operationalTimes'
x = field_string
field_keys_to_extract = ['publishedDeparture', 'publishedArrival', 'scheduledGateDeparture', 'scheduledRunwayDeparture',
                         'estimatedGateDeparture', 'flightPlanPlannedDeparture', 'estimatedRunwayDeparture',
                         'actualRunwayDeparture',
                         'scheduledRunwayArrival', 'scheduledGateArrival', 'scheduledGateArrival',
                         'estimatedGateArrival',
                         'actualGateArrival', 'flightPlanPlannedArrival', 'estimatedRunwayArrival',
                         'actualRunwayArrival']

for i in field_keys_to_extract:
    flight_status_df[field_string + i] = flight_status_df[field_string].apply(lambda x: ExtractField(x, i))

field_string = ''
field_keys_to_extract = []
field_string = 'flightDurations'
x = field_string
field_keys_to_extract = ['scheduledTaxiInMinutes', 'scheduledTaxiOutMinutes', 'taxiInMinutes',
                         'taxiOutMinutes', 'scheduledAirMinutes', 'airMinutes', 'scheduledBlockMinutes',
                         'blockMinutes']

for i in field_keys_to_extract:
    flight_status_df[field_string + i] = flight_status_df[field_string].apply(lambda x: ExtractField(x, i))


#5. Add dep and arrival hours
flight_status_df['departure_local_hour'] = flight_status_df.apply(lambda row: datetime.strptime(row.departureDatedateLocal,'%Y-%m-%dT%H:%M:%S.%f').hour, axis = 1)
flight_status_df['arrival_local_hour'] = flight_status_df.apply(lambda row: datetime.strptime(row.arrivalDatedateLocal,'%Y-%m-%dT%H:%M:%S.%f').hour, axis = 1)

#6. Dill dump
# dill.dump(flight_status_df,open('flight_status_df.pkd','wb'))
# flight_status_df=dill.load(open('flight_status_df.pkd','rb'))

#7. Dash Plot.ly
# cf.go_offline()
# cf.set_config_file(offline=False, world_readable=True)

user_input_airportFsCode = 'LAX'
user_input_airportFsCode_Dash = user_input_airportFsCode

flight_status_df_departure_airport = flight_status_df[
    flight_status_df['departureAirportFsCode'] == user_input_airportFsCode_Dash]

departure_gate_delay_by_fscode_chart_values = (flight_status_df_departure_airport.groupby('airline_name')
                                               ['delaysdepartureGateDelayMinutes'].mean().nlargest(10).sort_values(
    ascending=False))


departure_gate_delay_by_fscode_trace = go.Bar(x=list(departure_gate_delay_by_fscode_chart_values.index),
                                              y=list(departure_gate_delay_by_fscode_chart_values),
                                              name="departure_gate_delay_by_fscode")

departure_gate_delay_by_fscode_data = [departure_gate_delay_by_fscode_trace]

departure_gate_delay_by_fscode_layout = dict(title="Departure Gate Delay by Airline", showlegend=False,
                                             xaxis={'title': 'Airline'},
                                             yaxis={'title': 'Average Minutes'})


departure_gate_delay_by_fscode_figure = dict(data=departure_gate_delay_by_fscode_data,
                                             layout=departure_gate_delay_by_fscode_layout)

def generate_table(dataframe, max_rows=50):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )

app = dash.Dash(__name__)  # new line of code, which now allows us to access assets folder
server = app.server

app.layout = html.Div([
    html.Div([
        html.H2("The Data Incubator Capstone Project: Kaustuv Chakrabarti")],
        className="banner",
        style={'backgroundColor': 'blue', 'fontColor': 'white'}
    ),
    html.Div([
        html.H2("Project Background")],
        className="banner",
        style={'backgroundColor': 'green', 'fontColor': 'white'}
    ),
    html.Div([
        html.P('''
        Industry Background: 
        The airline industry constitutes a major portion of the U.S. economy and 
        serves passengers through a vast, complicated network of operations.  U.S. airlines accounted 
        for 889 million passenger-trips in 2018, an average of 2.4 million trips per day.  
        Operating revenue for U.S. airlines was $171 billion in 2018.  
        Over 5,000 airports are located in the U.S.  Providing decision-makers the tools to monitor performance (e.g., delay and congestion within 
        airports) can help improve operations, driving financial success and passenger satisfaction.
        ''')
        ], style = {
                #'font-family': 'cursive',
                'font-size': '18px',
                'text-align': 'left'}
    ),
    html.Div([
        html.P('''Data Sources: The Flight Status Developer Center provides daily information on thousands of flights, 
        such as arrival and departure times, flight durations, flight delays, by flight number, airline, airport, 
        and airport gate and terminal.
        '''),
    ], style = {
     #           'font-family': 'cursive',
                'font-size': '18px',
                'text-align': 'left'}
    ),
    html.Div([
        html.P('''Data Ingestion:  This dashboard connects (live) to the MongoDB database that hosts the data and converts the JSON data through
        Python into Pandas dataframes.  Data is sourced from multiple MongoDB collections, such as flight status and 
        airline collections.  These dataframes were linked/combined (e.g., translating airline IATA codes to airline names)
        and further modified into subsequent dataframes providing information on flight volumes, delays, etc.
    '''),
    ], style = {
              #  'font-family': 'cursive',
                'font-size': '18px',
                'text-align': 'left'}
    ),
    html.Div([
        html.P('''Visualization: This dashboard provides several types of visualizations, including bar charts and Pandas-based
        tables.
        '''),
    ], style = {
    #            'font-family': 'cursive',
                'font-size': '18px',
                'text-align': 'left'}
    ),
    html.Div([
        html.H2("Performance Metrics")],
        className="banner",
        style={'backgroundColor': 'purple', 'fontColor': 'white'}
        ),
    html.Label(["User Selection:  Choose Airport:"], style = {'font-size': '25px', 'fontColor': 'red'}),
    html.Div(
        dcc.RadioItems(
            id = "airport_radio_button",
            options=[
                {'label': 'Los Angeles (LAX), United States', 'value': 'LAX'},
                {'label': 'Shanghai (PVG), China', 'value': 'PVG'},
                {'label': 'Kansai (KIX), Japan', 'value': 'KIX'},
                {'label':  'Itami (ITM), Japan', 'value': 'ITM'}
            ],
            labelStyle = {
                'display': 'inline-block',
                'margin-right': 15},
            value='LAX',
        )
    ),
    html.Div(
        html.Label(["Performance Metrics:  Time of Day"], style={'font-size': '25px'})
    ),
    html.Div([
        html.Div([
            dcc.Graph(
                id="FlightVolumebyArrivingHour",
            )
        ],
            className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        ),
        html.Div([
            dcc.Graph(
                id="FlightVolumebyDepartingHour",
            )
        ],
            className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        )
    ], className="row"
    ),
    html.Div([
        html.Div([
            dcc.Graph(
                id="RunwayDelaybyArrivingHour",
            )
        ],
            className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        ),
        html.Div([
            dcc.Graph(
                id="RunwayDelaybyDepartingHour",
            )
        ],
            className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        )
    ], className="row"
    ),
    html.Div([
        html.Div([
            dcc.Graph(
                id="GateDelaybyArrivingHour",
            )
        ],
            className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        ),
        html.Div([
            dcc.Graph(
                id="GateDelaybyDepartingHour",
            )
        ],
            className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        )
    ], className="row"
    ),
    html.Div([
        html.Div([
            dcc.Graph(
                id="TaxiTimebyArrivingHour",
            )
        ],
            className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        ),
        html.Div([
            dcc.Graph(
                id="TaxiTimebyDepartingHour",
            )
        ],
            className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        )
    ], className="row"
    ),
    html.Label(["User Selection:  Choose 'Top X' results for charts"], style={'font-size': '25px'}),
    html.Label(["       "], style={'font-size': '15px'}),
    html.Div(
        dcc.RadioItems(
            id='top_x_dropdown',
            options=[
                {'label': '5', 'value': '5'},
                {'label': '10', 'value': '10'},
                {'label': '20', 'value': '20'},
                {'label': '50', 'value': '50'},
                {'label': '100', 'value': '100'}
            ],
            labelStyle={
                'display': 'inline-block',
                'margin-right': 15},
            value='10'
        )
    ),
    html.Div(
        html.Label(["Performance Metrics: By Partner Airport"], style={'font-size': '25px'})
    ),
    html.Div([
        html.Div([
            dcc.Graph(
                id="FlightVolumebyArrivingFromAirport",
            )
        ],
            className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        ),
        html.Div([
            dcc.Graph(
                id="FlightVolumebyDepartingToAirport",
            )
        ],
            className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        )
    ], className="row"
    ),
    html.Div([

        html.Div([
            dcc.Graph(
                id="FlightDurationbyDepartureAirport_Longest",
            )
        ],
            className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        ),
        html.Div([
            dcc.Graph(
                id="FlightDurationbyArrivalAirport_Longest",
            )
        ],
            className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        )
    ], className="row"
    ),
    html.Div(
        html.Label(["Performance Metrics:  Gate Delay"], style={'font-size': '25px'})
    ),

    html.Div([
        html.Div([
            dcc.Graph(
                id="ArrGateDelaybyAirline_Longest",
            )
        ],
            className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        ),
        html.Div([
            dcc.Graph(
                id="DepGateDelaybyAirline_Longest",
            )
        ],
            className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        )
    ], className="row"
    ),
    html.Div([
        html.Div([
            dcc.Graph(
                id="ArrGateDelaybyAirline_Shortest",
            )
        ],
            className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        ),
        html.Div([
            dcc.Graph(
                id="DepGateDelaybyAirline_Shortest",
            )
        ],
            className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        )
    ], className="row"
    ),
])

app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})
@app.callback(
    Output(component_id='DepGateDelaybyAirline_Longest', component_property='figure'),
    [Input(component_id='airport_radio_button', component_property='value'),
    Input(component_id='top_x_dropdown', component_property='value')]
)
def update_DepGateDelaybyAirline_Longest(user_input_airportFsCode_Dash, top_x_results):
    top_x_results = int(top_x_results)
    return {
        'data': [
            go.Bar(
                x = list((flight_status_df[
                    flight_status_df['departureAirportFsCode'] == user_input_airportFsCode_Dash].groupby('airline_name')
                    ['delaysdepartureGateDelayMinutes'].mean().nlargest(top_x_results).sort_values(
                    ascending=False)).index),
                y = list((flight_status_df[
                    flight_status_df['departureAirportFsCode'] == user_input_airportFsCode_Dash].groupby('airline_name')
                    ['delaysdepartureGateDelayMinutes'].mean().nlargest(top_x_results).sort_values(
                ascending=False)))
            )
        ],
        'layout': go.Layout(
            title="Airlines with Longest Average Departure Gate Delay: Top " + str(top_x_results),
            xaxis={'title': 'Airline'},
            yaxis={'title': 'Delay (Minutes)'},
            colorscale = {"diverging": 'Rainbow'}
          )
    }
@app.callback(
    Output(component_id='ArrGateDelaybyAirline_Longest', component_property='figure'),
    [Input(component_id='airport_radio_button', component_property='value'),
    Input(component_id='top_x_dropdown', component_property='value')]
)
def update_ArrGateDelaybyAirline_Longest(user_input_airportFsCode_Dash, top_x_results):
    top_x_results = int(top_x_results)
    return {
        'data': [
            go.Bar(
                x = list((flight_status_df[
                    flight_status_df['arrivalAirportFsCode'] == user_input_airportFsCode_Dash].groupby('airline_name')
                    ['delaysarrivalGateDelayMinutes'].mean().nlargest(top_x_results).sort_values(
                    ascending=False)).index),
                y = list((flight_status_df[
                    flight_status_df['arrivalAirportFsCode'] == user_input_airportFsCode_Dash].groupby('airline_name')
                    ['delaysarrivalGateDelayMinutes'].mean().nlargest(top_x_results).sort_values(
                ascending=False)))
            )
        ],
        'layout': go.Layout(
            title="Airlines with Longest Average Arrival Gate Delay: Top " + str(top_x_results),
            xaxis={'title': 'Airline'},
            yaxis={'title': 'Delay (Minutes)'},
            colorscale = {"diverging": 'Rainbow'}
          )
    }
@app.callback(
    Output(component_id='DepGateDelaybyAirline_Shortest', component_property='figure'),
    [Input(component_id='airport_radio_button', component_property='value'),
    Input(component_id='top_x_dropdown', component_property='value')]
)
def update_DepGateDelaybyAirline_Shortest(user_input_airportFsCode_Dash, top_x_results):
    top_x_results = int(top_x_results)
    return {
        'data': [
            go.Bar(
                x = list((flight_status_df[
                    flight_status_df['departureAirportFsCode'] == user_input_airportFsCode_Dash].groupby('airline_name')
                    ['delaysdepartureGateDelayMinutes'].mean().nsmallest(top_x_results).sort_values(
                    ascending=False)).index),
                y = list((flight_status_df[
                    flight_status_df['departureAirportFsCode'] == user_input_airportFsCode_Dash].groupby('airline_name')
                    ['delaysdepartureGateDelayMinutes'].mean().nsmallest(top_x_results).sort_values(
                ascending=False))),
            )
        ],
        'layout': go.Layout(
            title="Airlines with Shortest Average Departure Gate Delay: Top " + str(top_x_results),
            xaxis={'title': 'Airline'},
            yaxis={'title': 'Delay (Minutes)'},
            colorscale = {"diverging": 'Rainbow'}
          )
    }
@app.callback(
    Output(component_id='ArrGateDelaybyAirline_Shortest', component_property='figure'),
    [Input(component_id='airport_radio_button', component_property='value'),
    Input(component_id='top_x_dropdown', component_property='value')]
)
def update_ArrGateDelaybyAirline_Shortest(user_input_airportFsCode_Dash, top_x_results):
    top_x_results = int(top_x_results)
    return {
        'data': [
            go.Bar(
                x = list((flight_status_df[
                    flight_status_df['arrivalAirportFsCode'] == user_input_airportFsCode_Dash].groupby('airline_name')
                    ['delaysarrivalGateDelayMinutes'].mean().nsmallest(top_x_results).sort_values(
                    ascending=False)).index),
                y = list((flight_status_df[
                    flight_status_df['arrivalAirportFsCode'] == user_input_airportFsCode_Dash].groupby('airline_name')
                    ['delaysarrivalGateDelayMinutes'].mean().nsmallest(top_x_results).sort_values(
                ascending=False))),
            )
        ],
        'layout': go.Layout(
            title="Airlines with Shortest Average Arrival Gate Delay: Top " + str(top_x_results),
            xaxis={'title': 'Airline'},
            yaxis={'title': 'Delay (Minutes)'},
            colorscale = {"diverging": 'Rainbow'}
          )
    }
@app.callback(
    Output(component_id='FlightDurationbyArrivalAirport_Longest', component_property='figure'),
    [Input(component_id='airport_radio_button', component_property='value'),
    Input(component_id='top_x_dropdown', component_property='value')]
)
def update_FlightDurationbyArrivalAirport_Longest(user_input_airportFsCode_Dash, top_x_results):
    top_x_results = int(top_x_results)
    return {
        'data': [
            go.Bar(
                y = list((flight_status_df[
                    flight_status_df['departureAirportFsCode'] == user_input_airportFsCode_Dash].groupby('arrivalAirportFsCode')
                    ['flightDurationsairMinutes'].mean().nlargest(top_x_results).sort_values(
                    ascending=False)).index),
                x = list((flight_status_df[
                    flight_status_df['departureAirportFsCode'] == user_input_airportFsCode_Dash].groupby('arrivalAirportFsCode')
                    ['flightDurationsairMinutes'].mean().nlargest(top_x_results).sort_values(
                ascending=True))),
                orientation = 'h',
                marker=dict(
                    color='green',
                    line=dict(color='green', width=3))
            )
        ],
        'layout': go.Layout(
            title="Departing-To Airports with Longest Average Flight Durations: Top " + str(top_x_results),
            yaxis={'title': 'Departing-To Airport'},
            xaxis={'title': 'Flight Duration (Minutes)'},
            colorscale = {"diverging": 'Rainbow'}
          )
    }
@app.callback(
    Output(component_id='FlightDurationbyDepartureAirport_Longest', component_property='figure'),
    [Input(component_id='airport_radio_button', component_property='value'),
    Input(component_id='top_x_dropdown', component_property='value')]
)
def update_FlightDurationbyDepartureAirport_Longest(user_input_airportFsCode_Dash, top_x_results):
    top_x_results = int(top_x_results)
    return {
        'data': [
            go.Bar(
                y = list((flight_status_df[
                    flight_status_df['arrivalAirportFsCode'] == user_input_airportFsCode_Dash].groupby('departureAirportFsCode')
                    ['flightDurationsairMinutes'].mean().nlargest(top_x_results).sort_values(
                    ascending=False)).index),
                x = list((flight_status_df[
                    flight_status_df['arrivalAirportFsCode'] == user_input_airportFsCode_Dash].groupby('departureAirportFsCode')
                    ['flightDurationsairMinutes'].mean().nlargest(top_x_results).sort_values(
                ascending=True))),
                orientation = 'h',
                marker=dict(
                    color='green',
                    line=dict(color='green', width=3))
            )
        ],
        'layout': go.Layout(
            title="Arriving-From Airports with Longest Average Flight Durations: Top " + str(top_x_results),
            yaxis={'title': 'Arriving-From Airport'},
            xaxis={'title': 'Flight Duration (Minutes)'},
            colorscale = {"diverging": 'Rainbow'}
          )
    }
@app.callback(
    Output(component_id='FlightVolumebyArrivingFromAirport', component_property='figure'),
    [Input(component_id='airport_radio_button', component_property='value'),
    Input(component_id='top_x_dropdown', component_property='value')]
)
def update_FlightVolumebyArrivingFrom(user_input_airportFsCode_Dash, top_x_results):
    top_x_results = int(top_x_results)
    return {
        'data': [
            go.Bar(
                y = list((flight_status_df[
                    flight_status_df['arrivalAirportFsCode'] == user_input_airportFsCode_Dash].groupby('departureAirportFsCode')
                    ['flightDurationsairMinutes'].count().nlargest(top_x_results).sort_values(
                    ascending=False)).index),
                x = list((flight_status_df[
                    flight_status_df['arrivalAirportFsCode'] == user_input_airportFsCode_Dash].groupby('departureAirportFsCode')
                    ['flightDurationsairMinutes'].count().nlargest(top_x_results).sort_values(
                ascending=True))),
                orientation = 'h',
                marker=dict(
                    color='forestgreen',
                    line=dict(color='forestgreen', width=3))
            )
        ],
        'layout': go.Layout(
            title="Number of Flights by Arriving-From Airport: Top " + str(top_x_results),
            yaxis={'title': 'Arriving-From Airport'},
            xaxis={'title': 'Number of Flights'},
            colorscale = {"diverging": 'Rainbow'}
          )
    }
@app.callback(
    Output(component_id='FlightVolumebyDepartingToAirport', component_property='figure'),
    [Input(component_id='airport_radio_button', component_property='value'),
    Input(component_id='top_x_dropdown', component_property='value')]
)
def update_FlightVolumebyDepartingTo(user_input_airportFsCode_Dash, top_x_results):
    top_x_results = int(top_x_results)
    return {
        'data': [
            go.Bar(
                y = list((flight_status_df[
                    flight_status_df['departureAirportFsCode'] == user_input_airportFsCode_Dash].groupby('arrivalAirportFsCode')
                    ['flightDurationsairMinutes'].count().nlargest(top_x_results).sort_values(
                    ascending=False)).index),
                x = list((flight_status_df[
                    flight_status_df['departureAirportFsCode'] == user_input_airportFsCode_Dash].groupby('arrivalAirportFsCode')
                    ['flightDurationsairMinutes'].count().nlargest(top_x_results).sort_values(
                ascending=True))),
                orientation = 'h',
                marker=dict(
                    color='forestgreen',
                    line=dict(color='forestgreen', width=3))
            )
        ],
        'layout': go.Layout(
            title="Number of Flights by Departing-To Airport: Top " + str(top_x_results),
            yaxis={'title': 'Departing-To Airport'},
            xaxis={'title': 'Number of Flights'},
            colorscale = {"diverging": 'Rainbow'}
          )
    }
@app.callback(
    Output(component_id='FlightVolumebyDepartingHour', component_property='figure'),
    [Input(component_id='airport_radio_button', component_property='value'),
    Input(component_id='top_x_dropdown', component_property='value')]
)
def update_FlightVolumebyDepartingHour(user_input_airportFsCode_Dash, top_x_results):
    top_x_results = int(top_x_results)
    return {
        'data': [
            go.Scatter(
                x = list((flight_status_df[
                    flight_status_df['departureAirportFsCode'] == user_input_airportFsCode_Dash].groupby('departure_local_hour')
                    ['departureAirportFsCode'].count()).index),
                y = list((flight_status_df[
                    flight_status_df['departureAirportFsCode'] == user_input_airportFsCode_Dash].groupby('departure_local_hour')
                    ['departureAirportFsCode'].count())),
                #orientation = 'h',
                marker=dict(
                    color='black',
                    line=dict(color='black', width=3))
            )
        ],
        'layout': go.Layout(
            title="Number of Departure Flights by Time of Day",
            xaxis={'title': 'Time of Day (Military Time)'},
            yaxis={'title': 'Number of Flights'},
            colorscale = {"diverging": 'Rainbow'}
          )
    }

@app.callback(
    Output(component_id='FlightVolumebyArrivingHour', component_property='figure'),
    [Input(component_id='airport_radio_button', component_property='value'),
     Input(component_id='top_x_dropdown', component_property='value')]
)
def update_FlightVolumebyArrivingHour(user_input_airportFsCode_Dash, top_x_results):
    top_x_results = int(top_x_results)
    return {
        'data': [
            go.Scatter(
                x=list((flight_status_df[
                            flight_status_df['arrivalAirportFsCode'] == user_input_airportFsCode_Dash].groupby(
                    'arrival_local_hour')
                        ['arrivalAirportFsCode'].count()).index),
                y=list((flight_status_df[
                            flight_status_df['arrivalAirportFsCode'] == user_input_airportFsCode_Dash].groupby(
                    'arrival_local_hour')
                        ['arrivalAirportFsCode'].count())),
                # orientation = 'h',
                marker=dict(
                    color='black',
                    line=dict(color='black', width=3))
            )
        ],
        'layout': go.Layout(
            title="Number of Arrival Flights by Time of Day",
            xaxis={'title': 'Time of Day (Military Time)'},
            yaxis = {'title': 'Number of Flights'},
            colorscale = {"diverging": 'Rainbow'}
        )
    }
@app.callback(
    Output(component_id='RunwayDelaybyArrivingHour', component_property='figure'),
    [Input(component_id='airport_radio_button', component_property='value'),
     Input(component_id='top_x_dropdown', component_property='value')]
)
def update_RunwayDelaybyArrivingHour(user_input_airportFsCode_Dash, top_x_results):
    top_x_results = int(top_x_results)
    return {
        'data': [
            go.Scatter(
                x=list((flight_status_df[
                            flight_status_df['arrivalAirportFsCode'] == user_input_airportFsCode_Dash].groupby(
                    'arrival_local_hour')
                        ['delaysarrivalRunwayDelayMinutes'].mean()).index),
                y=list((flight_status_df[
                            flight_status_df['arrivalAirportFsCode'] == user_input_airportFsCode_Dash].groupby(
                    'arrival_local_hour')
                        ['delaysarrivalRunwayDelayMinutes'].mean())),
                # orientation = 'h',
                marker=dict(
                    color='black',
                    line=dict(color='black', width=3))
            )
        ],
        'layout': go.Layout(
            title="Average Arrival Runway Delay by Time of Day",
            xaxis={'title': 'Time (Military Time)'},
            yaxis = {'title': 'Runway Delay (Minutes)'},
            colorscale = {"diverging": 'Rainbow'}
        )
    }
@app.callback(
    Output(component_id='RunwayDelaybyDepartingHour', component_property='figure'),
    [Input(component_id='airport_radio_button', component_property='value'),
     Input(component_id='top_x_dropdown', component_property='value')]
)
def update_RunwayDelaybyDepartingHour(user_input_airportFsCode_Dash, top_x_results):
    top_x_results = int(top_x_results)
    return {
        'data': [
            go.Scatter(
                x=list((flight_status_df[
                            flight_status_df['departureAirportFsCode'] == user_input_airportFsCode_Dash].groupby(
                    'departure_local_hour')
                        ['delaysdepartureRunwayDelayMinutes'].mean()).index),
                y=list((flight_status_df[
                            flight_status_df['departureAirportFsCode'] == user_input_airportFsCode_Dash].groupby(
                    'departure_local_hour')
                        ['delaysdepartureRunwayDelayMinutes'].mean())),
                # orientation = 'h',
                marker=dict(
                    color='black',
                    line=dict(color='black', width=3))
            )
        ],
        'layout': go.Layout(
            title="Average Departure Runway Delay by Time of Day",
            xaxis={'title': 'Time of Day (Military Time)'},
            yaxis = {'title': 'Runway Delay (Minutes)'},
            colorscale = {"diverging": 'Rainbow'}
        )
    }
@app.callback(
    Output(component_id='GateDelaybyArrivingHour', component_property='figure'),
    [Input(component_id='airport_radio_button', component_property='value'),
     Input(component_id='top_x_dropdown', component_property='value')]
)
def update_GateDelaybyArrivingHour(user_input_airportFsCode_Dash, top_x_results):
    top_x_results = int(top_x_results)
    return {
        'data': [
            go.Scatter(
                x=list((flight_status_df[
                            flight_status_df['arrivalAirportFsCode'] == user_input_airportFsCode_Dash].groupby(
                    'arrival_local_hour')
                        ['delaysarrivalGateDelayMinutes'].mean()).index),
                y=list((flight_status_df[
                            flight_status_df['arrivalAirportFsCode'] == user_input_airportFsCode_Dash].groupby(
                    'arrival_local_hour')
                        ['delaysarrivalGateDelayMinutes'].mean())),
                # orientation = 'h',
                marker=dict(
                    color='black',
                    line=dict(color='black', width=3))
            )
        ],
        'layout': go.Layout(
            title="Average Arrival Gate Delay by Time of Day",
            xaxis={'title': 'Time (Military Time)'},
            yaxis = {'title': 'Gate Delay (Minutes)'},
            colorscale = {"diverging": 'Rainbow'}
        )
    }

@app.callback(
    Output(component_id='GateDelaybyDepartingHour', component_property='figure'),
    [Input(component_id='airport_radio_button', component_property='value'),
     Input(component_id='top_x_dropdown', component_property='value')]
)
def update_GateDelaybyDepartingHour(user_input_airportFsCode_Dash, top_x_results):
    top_x_results = int(top_x_results)
    return {
        'data': [
            go.Scatter(
                x=list((flight_status_df[
                            flight_status_df['departureAirportFsCode'] == user_input_airportFsCode_Dash].groupby(
                    'departure_local_hour')
                        ['delaysdepartureGateDelayMinutes'].mean()).index),
                y=list((flight_status_df[
                            flight_status_df['departureAirportFsCode'] == user_input_airportFsCode_Dash].groupby(
                    'departure_local_hour')
                        ['delaysdepartureGateDelayMinutes'].mean())),
                # orientation = 'h',
                marker=dict(
                    color='black',
                    line=dict(color='black', width=3))
            )
        ],
        'layout': go.Layout(
            title="Average Gate Runway Delay by Time of Day",
            xaxis={'title': 'Time of Day (Military Time)'},
            yaxis = {'title': 'Gate Delay (Minutes)'},
            colorscale = {"diverging": 'Rainbow'}
        )
    }
@app.callback(
    Output(component_id='TaxiTimebyArrivingHour', component_property='figure'),
    [Input(component_id='airport_radio_button', component_property='value'),
     Input(component_id='top_x_dropdown', component_property='value')]
)
def update_TaxiTimebyArrivingHour(user_input_airportFsCode_Dash, top_x_results):
    top_x_results = int(top_x_results)
    return {
        'data': [
            go.Scatter(
                x=list((flight_status_df[
                            flight_status_df['arrivalAirportFsCode'] == user_input_airportFsCode_Dash].groupby(
                    'arrival_local_hour')
                        ['flightDurationstaxiInMinutes'].mean()).index),
                y=list((flight_status_df[
                            flight_status_df['arrivalAirportFsCode'] == user_input_airportFsCode_Dash].groupby(
                    'arrival_local_hour')
                        ['flightDurationstaxiInMinutes'].mean())),
                # orientation = 'h',
                marker=dict(
                    color='black',
                    line=dict(color='black', width=3))
            )
        ],
        'layout': go.Layout(
            title="Average Arrival Taxi Time by Time of Day",
            xaxis={'title': 'Time (Military Time)'},
            yaxis = {'title': 'Taxi Time (Minutes)'},
            colorscale = {"diverging": 'Rainbow'}
        )
    }

@app.callback(
    Output(component_id='TaxiTimebyDepartingHour', component_property='figure'),
    [Input(component_id='airport_radio_button', component_property='value'),
     Input(component_id='top_x_dropdown', component_property='value')]
)
def update_TaxiTimebyDepartingHour(user_input_airportFsCode_Dash, top_x_results):
    top_x_results = int(top_x_results)
    return {
        'data': [
            go.Scatter(
                x=list((flight_status_df[
                            flight_status_df['departureAirportFsCode'] == user_input_airportFsCode_Dash].groupby(
                    'departure_local_hour')
                        ['flightDurationstaxiOutMinutes'].mean()).index),
                y=list((flight_status_df[
                            flight_status_df['departureAirportFsCode'] == user_input_airportFsCode_Dash].groupby(
                    'departure_local_hour')
                        ['flightDurationstaxiOutMinutes'].mean())),
                # orientation = 'h',
                marker=dict(
                    color='black',
                    line=dict(color='black', width=3))
            )
        ],
        'layout': go.Layout(
            title="Average Departure Taxi Time by Time of Day",
            xaxis={'title': 'Time of Day (Military Time)'},
            yaxis = {'title': 'Taxi Time (Minutes)'},
            colorscale = {"diverging": 'Rainbow'}
        )
    }









if __name__ == "__main__":
    app.run_server(debug=True)













