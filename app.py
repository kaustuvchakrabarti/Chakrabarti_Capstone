import time
import json
from pymongo import MongoClient
from pandas import Series, DataFrame
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
#import pickle
#import dill
import matplotlib.pyplot as plt

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
#from dash.dependencies import Input, Output


#import cufflinks as cf

########## Connect to Mongo database
username='datamanager'
password='airtransportationrulez'
url = 'mongodb://%s:%s@167.99.24.166:2700/datamanager'
mongo_client_fs = MongoClient(url % (username, password))
db = mongo_client_fs['datamanager']

########## Create a dataframe for the flight status
def query_flight_statuses_by_dates(airport_list, start_date, end_date, dateUtc=True):
    operational_times_fields_departure = ['publishedDeparture', 'scheduledGateDeparture', 'estimatedGateDeparture',
        'actualGateDeparture',  'flightPlanPlannedDeparture',  'estimatedRunwayDeparture', 'actualRunwayDeparture']

    operational_times_fields_arrival = ['publishedArrival', 'scheduledGateArrival', 'estimatedGateArrival',
        'actualGateArrival', 'flightPlanPlannedArrival', 'estimatedRunwayArrival', 'actualRunwayArrival']


    date_type = "dateUtc" if dateUtc else "dateLocal"

    end_date_parsed = datetime.strptime(end_date,"%Y-%m-%d") + timedelta(days=1)
    end_date_lt = end_date_parsed.strftime("%Y-%m-%d")

    #print (end_date_lt)

    return db.flightStatuses.find (
        {
            "$and" : [
                {
                "$or" :
                    [ {"departureAirportFsCode" : {"$in" : airport_list}},
                        {"arrivalAirportFsCode": {"$in": airport_list}}
                    ]
                },
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
flight_status_df = DataFrame(list(query_flight_statuses_by_dates([user_input_airportFsCode],user_input_date,user_input_date,dateUtc=False)))
list(flight_status_df.columns)

########## Create an airline dictionary, with IATA code with the "english" name (e.g., Delta, United)
query_airlines = db.airlines.find()
airlines_list = list(query_airlines)
airline_dictionary = dict()

for i in airlines_list:
    key_name = i['fs']
    key_value = i['name']
    airline_dictionary[key_name] = key_value

########## Update the flight status dataframe with a field translating the airline IATA code to the "english" anme

flight_status_df['airline_name'] = flight_status_df['carrierFsCode'].map(airline_dictionary)


########## Function to extract from a column the nested field that is in a dictionary form, into their own dataframe columns

def ExtractField(d, k):
    if not isinstance(d, dict):  # for some rows without a value, the entry is not a dictionary,
        return None  # need to account for this to avoid error

    if k in d.keys():  # if the field I want to extract is in the cell, then the value for that field
        return d[k]
    else:
        return None

########## Update flight_status_df with nested fields extracted into own columns
########## airportResources

field_string = ''
field_keys_to_extract = []
field_string = 'airportResources'
x = field_string
field_keys_to_extract = ['departureTerminal','arrivalTerminal','departureGate',
                        'arrivalGate']

for i in field_keys_to_extract:
    flight_status_df[field_string + i] = flight_status_df[field_string].apply(lambda x: ExtractField(x,i))

########## arrivalDate
field_string = ''
field_keys_to_extract = []
field_string = 'arrivalDate'
x = field_string
field_keys_to_extract = ['dateUtc','dateLocal']

for i in field_keys_to_extract:
    flight_status_df[field_string + i] = flight_status_df[field_string].apply(lambda x: ExtractField(x,i))

########## departureDate
field_string = ''
field_keys_to_extract = []
field_string = 'departureDate'
x = field_string
field_keys_to_extract = ['dateUtc','dateLocal']

for i in field_keys_to_extract:
    flight_status_df[field_string + i] = flight_status_df[field_string].apply(lambda x: ExtractField(x,i))

########## delays
field_string = ''
field_keys_to_extract = []
field_string = 'delays'
x = field_string
field_keys_to_extract = ['arrivalGateDelayMinutes','departureGateDelayMinutes','arrivalRunwayDelayMinutes',
                        'departureRunwayDelayMinutes']

for i in field_keys_to_extract:
    flight_status_df[field_string + i] = flight_status_df[field_string].apply(lambda x: ExtractField(x,i))

########## flightStatusUpdates
field_string = ''
field_keys_to_extract = []
field_string = 'flightStatusUpdates'
x = field_string
field_keys_to_extract = ['updatedAt']

for i in field_keys_to_extract:
    flight_status_df[field_string + i] = flight_status_df[field_string].apply(lambda x: ExtractField(x,i))

########## operationalTimes
field_string = ''
field_keys_to_extract = []
field_string = 'operationalTimes'
x = field_string
field_keys_to_extract = ['publishedDeparture','publishedArrival','scheduledGateDeparture','scheduledRunwayDeparture',
                        'estimatedGateDeparture','flightPlanPlannedDeparture','estimatedRunwayDeparture','actualRunwayDeparture',
                         'scheduledRunwayArrival','scheduledGateArrival','scheduledGateArrival','estimatedGateArrival',
                         'actualGateArrival','flightPlanPlannedArrival','estimatedRunwayArrival','actualRunwayArrival']

for i in field_keys_to_extract:
    flight_status_df[field_string + i] = flight_status_df[field_string].apply(lambda x: ExtractField(x,i))

########## flightDurations
field_string = ''
field_keys_to_extract = []
field_string = 'flightDurations'
x = field_string
field_keys_to_extract = ['scheduledTaxiInMinutes','scheduledTaxiOutMinutes','taxiInMinutes',
                        'taxiOutMinutes','scheduledAirMinutes','airMinutes','scheduledBlockMinutes',
                        'blockMinutes']

for i in field_keys_to_extract:
    flight_status_df[field_string + i] = flight_status_df[field_string].apply(lambda x: ExtractField(x,i))

########## Dill dump
#dill.dump(flight_status_df,open('flight_status_df.pkd','wb'))
#flight_status_df=dill.load(open('flight_status_df.pkd','rb'))

########## Dash Section
#cf.go_offline()
#cf.set_config_file(offline=False, world_readable=True)

########## Chart Sources
user_input_airportFsCode_Dash = user_input_airportFsCode

########## flight status df filtered for departure airport
flight_status_df_departure_airport = flight_status_df[flight_status_df['departureAirportFsCode'] == user_input_airportFsCode_Dash]

########## flight status df filtered for arrival airport
flight_status_df_arrival_airport = flight_status_df[flight_status_df['arrivalAirportFsCode'] == user_input_airportFsCode_Dash]
########## source values for Dash charts

########## df of flight number, airline, departure airport, departure city, arrival city, arrival airport
flight_table_df_departure_airport = flight_status_df_departure_airport[['departureAirportFsCode', 'departureDatedateLocal', 'arrivalAirportFsCode', 'airline_name', 'flightDurationsairMinutes', 'flightDurationsscheduledAirMinutes']].sort_values(by = ['departureDatedateLocal'])
flight_table_df_departure_airport=flight_table_df_departure_airport.rename(columns=
                                         {"departureAirportFsCode": "Departure Airport",
                                          "departureDatedateLocal": "Local Time",
                                          "arrivalAirportFsCode": "Arrival Airport",
                                          "airline_name": "Airline",
                                          "flightDurationsairMinutes": "Duration (Actual)",
                                          "flightDurationsscheduledAirMinutes": "Duration (Scheduled)"
                                          })

flight_table_df_arrival_airport = flight_status_df_arrival_airport[['departureAirportFsCode', 'arrivalDatedateLocal', 'arrivalAirportFsCode', 'airline_name', 'flightDurationsairMinutes', 'flightDurationsscheduledAirMinutes']].sort_values(by = ['arrivalDatedateLocal'])
flight_table_df_arrival_airport=flight_table_df_arrival_airport.rename(columns=
                                         {"departureAirportFsCode": "Departure Airport",
                                          "arrivalDatedateLocal": "Local Time",
                                          "arrivalAirportFsCode": "Arrival Airport",
                                          "airline_name": "Airline",
                                          "flightDurationsairMinutes": "Duration (Actual)",
                                          "flightDurationsscheduledAirMinutes": "Duration (Scheduled)"
                                          })


departure_gate_delay_by_fscode_chart_values = (flight_status_df_departure_airport.groupby('airline_name')
['delaysdepartureGateDelayMinutes'].mean().nlargest(10).sort_values(ascending = False))

arrival_gate_delay_by_fscode_chart_values = (flight_status_df_arrival_airport.groupby('airline_name')
['delaysarrivalGateDelayMinutes'].mean().nlargest(10).sort_values(ascending = False))

departure_gate_delay_by_departure_terminal_chart_values = (flight_status_df_departure_airport.groupby('airportResourcesdepartureTerminal')
['delaysdepartureGateDelayMinutes'].mean().nlargest(10).sort_values(ascending = False))

arrival_gate_delay_by_arrival_terminal_chart_values = (flight_status_df_arrival_airport.groupby('airportResourcesarrivalTerminal')
['delaysarrivalGateDelayMinutes'].mean().nlargest(10).sort_values(ascending = False))

departure_count_by_airline_chart_values = flight_status_df_departure_airport.groupby('airline_name')['airline_name'].count().nlargest(10).sort_values(ascending = False)
arrival_count_by_airline_chart_values = flight_status_df_arrival_airport.groupby('airline_name')['airline_name'].count().nlargest(10).sort_values(ascending = False)

departure_count_by_departure_terminal_chart_values = flight_status_df_departure_airport.groupby('airportResourcesdepartureTerminal')['airportResourcesdepartureTerminal'].count().nlargest(10).sort_values(ascending = False)
arrival_count_by_arrival_terminal_chart_values = flight_status_df_arrival_airport.groupby('airportResourcesarrivalTerminal')['airportResourcesarrivalTerminal'].count().nlargest(10).sort_values(ascending = False)

departure_count_by_arriving_at_airport_chart_values = flight_status_df_departure_airport.groupby('arrivalAirportFsCode')['arrivalAirportFsCode'].count().nlargest(10).sort_values(ascending = False)
arrival_count_by_departing_from_airport_chart_values = flight_status_df_arrival_airport.groupby('departureAirportFsCode')['departureAirportFsCode'].count().nlargest(10).sort_values(ascending = False)



########## chart traces for Dash charts
departure_gate_delay_by_fscode_trace = go.Bar(x=list(departure_gate_delay_by_fscode_chart_values.index),
                         y=list(departure_gate_delay_by_fscode_chart_values),
                         name = "departure_gate_delay_by_fscode"#,
                         #line = dict(color="#f44242")
                     )
arrival_gate_delay_by_fscode_trace = go.Bar(x=list(arrival_gate_delay_by_fscode_chart_values.index),
                         y=list(arrival_gate_delay_by_fscode_chart_values),
                         name = "arrival_gate_delay_by_fscode"#,
                         #line = dict(color="#f44242")
                     )
departure_gate_delay_by_departure_terminal_trace = go.Bar(x=list(departure_gate_delay_by_departure_terminal_chart_values.index),
                         y=list(departure_gate_delay_by_departure_terminal_chart_values),
                         name = "departure_gate_delay_by_departure_terminal"#,
                         #line = dict(color="#f44242")
                     )
arrival_gate_delay_by_arrival_terminal_trace = go.Bar(x=list(arrival_gate_delay_by_arrival_terminal_chart_values.index),
                         y=list(arrival_gate_delay_by_arrival_terminal_chart_values),
                         name = "arrival_gate_delay_by_arrival_terminal"#,
                         #line = dict(color="#f44242")
                     )

departure_count_by_airline_trace = go.Bar(x=list(departure_count_by_airline_chart_values.index),
                         y=list(departure_count_by_airline_chart_values),
                         name = "departure_count_by_airline"#,
                         #line = dict(color="#f44242")
                     )
arrival_count_by_airline_trace = go.Bar(x=list(arrival_count_by_airline_chart_values.index),
                         y=list(arrival_count_by_airline_chart_values),
                         name = "arrival_count_by_airline"#,
                         #line = dict(color="#f44242")
                     )

departure_count_by_departure_terminal_trace = go.Bar(x=list(departure_count_by_departure_terminal_chart_values.index),
                         y=list(departure_count_by_departure_terminal_chart_values),
                         name = "departure_count_by_departure_terminal"#,
                         #line = dict(color="#f44242")
                     )

arrival_count_by_arrival_terminal_trace = go.Bar(x=list(arrival_count_by_arrival_terminal_chart_values.index),
                         y=list(arrival_count_by_arrival_terminal_chart_values),
                         name = "arrival_count_by_arrival_terminal"#,
                         #line = dict(color="#f44242")
                     )
departure_count_by_arriving_at_airport_trace = go.Bar(x=list(departure_count_by_arriving_at_airport_chart_values.index),
                         y=list(departure_count_by_arriving_at_airport_chart_values),
                         name = "departure_count_by_arriving_at_airport"#,
                         #line = dict(color="#f44242")
                     )
arrival_count_by_departing_from_airport_trace = go.Bar(x=list(arrival_count_by_departing_from_airport_chart_values.index),
                         y=list(arrival_count_by_departing_from_airport_chart_values),
                         name = "arrival_count_by_departing_from_airport"#,
                         #line = dict(color="#f44242")
                     )

########## Data Variables
departure_gate_delay_by_fscode_data = [departure_gate_delay_by_fscode_trace]
arrival_gate_delay_by_fscode_data = [arrival_gate_delay_by_fscode_trace]
departure_gate_delay_by_departure_terminal_data = [departure_gate_delay_by_departure_terminal_trace]
arrival_gate_delay_by_arrival_terminal_data = [arrival_gate_delay_by_arrival_terminal_trace]
departure_count_by_airline_data = [departure_count_by_airline_trace]
arrival_count_by_airline_data = [arrival_count_by_airline_trace]
departure_count_by_departure_terminal_data = [departure_count_by_departure_terminal_trace]
arrival_count_by_arrival_terminal_data = [arrival_count_by_arrival_terminal_trace]
departure_count_by_arriving_at_airport_data = [departure_count_by_arriving_at_airport_trace]
arrival_count_by_departing_from_airport_data = [arrival_count_by_departing_from_airport_trace]

########## Dash chart layouts
departure_gate_delay_by_fscode_layout = dict(title = "Departure Gate Delay by Airline", showlegend = False,
                                                             xaxis={'title': 'Airline'},
                                                              yaxis={'title': 'Average Minutes'})

arrival_gate_delay_by_fscode_layout = dict(title = "Arrival Gate Delay by Airline", showlegend = False,
                                                             xaxis={'title': 'Airline'},
                                                              yaxis={'title': 'Average Minutes'})

departure_gate_delay_by_departure_terminal_layout = dict(title = "Departure Gate Delay by Terminal", showlegend = False,
                                                            xaxis={'title': 'Departure Terminal'},
                                                             yaxis={'title': 'Average Minutes'})

arrival_gate_delay_by_arrival_terminal_layout = dict(title = "Arrival Gate Delay by Terminal", showlegend = False,
                                                            xaxis={'title': 'Arrival Terminal'},
                                                             yaxis={'title': 'Average Minutes'})

departure_count_by_airline_layout = dict(title = "Number of Depatures, by Airline", showlegend = False,
                                                            xaxis={'title': 'Airline'},
                                                             yaxis={'title': 'Number of Flights'})

arrival_count_by_airline_layout = dict(title = "Number of Arrivals, by Airline", showlegend = False,
                                                            xaxis={'title': 'Airline'},
                                                             yaxis={'title': 'Number of Flights'})

departure_count_by_departure_terminal_layout = dict(title = "Number of Departures, by Departure Terminal", showlegend = False,
                                                            xaxis={'title': 'Terminal'},
                                                             yaxis={'title': 'Number of Flights'})

arrival_count_by_arrival_terminal_layout = dict(title = "Number of Arrivals, by Arrival Terminal", showlegend = False,
                                                            xaxis={'title': 'Terminal'},
                                                             yaxis={'title': 'Number of Flights'})

departure_count_by_arriving_at_airport_layout = dict(title = "Number of Departures, by Arriving-At Airport", showlegend = False,
                                                            xaxis={'title': 'Terminal'},
                                                             yaxis={'title': 'Number of Flights'})

arrival_count_by_departing_from_airport_layout = dict(title = "Number of Arrivals, by Departing-From Airport", showlegend = False,
                                                            xaxis={'title': 'Terminal'},
                                                             yaxis={'title': 'Number of Flights'},color='lifeExp')

########## Dash figures
departure_gate_delay_by_fscode_figure = dict(data = departure_gate_delay_by_fscode_data, layout = departure_gate_delay_by_fscode_layout)
arrival_gate_delay_by_fscode_figure = dict(data = arrival_gate_delay_by_fscode_data, layout = arrival_gate_delay_by_fscode_layout)

departure_gate_delay_by_departure_terminal_figure = dict(data = departure_gate_delay_by_departure_terminal_data, layout = departure_gate_delay_by_departure_terminal_layout)
arrival_gate_delay_by_arrival_terminal_figure = dict(data = arrival_gate_delay_by_arrival_terminal_data, layout = arrival_gate_delay_by_arrival_terminal_layout)

departure_count_by_airline_figure = dict(data = departure_count_by_airline_data, layout = departure_count_by_airline_layout)
arrival_count_by_airline_figure = dict(data = arrival_count_by_airline_data, layout = arrival_count_by_airline_layout)

departure_count_by_departure_terminal_figure = dict(data = departure_count_by_departure_terminal_data, layout = departure_count_by_departure_terminal_layout)
arrival_count_by_arrival_terminal_figure = dict(data = arrival_count_by_arrival_terminal_data, layout = arrival_count_by_arrival_terminal_layout)

departure_count_by_arriving_at_airport_figure = dict(data = departure_count_by_arriving_at_airport_data, layout = departure_count_by_arriving_at_airport_layout)
arrival_count_by_departing_from_airport_figure = dict(data = arrival_count_by_departing_from_airport_data, layout = arrival_count_by_departing_from_airport_layout)




########### Dash tables
########## Generate table function
def generate_table(dataframe, max_rows=50):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
#
# app = dash.Dash(__name__, external_stylesheets=external_stylesheets)



# if __name__ == '__main__':
#     app.run_server(debug=True)

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/2011_february_us_airport_traffic.csv')
df.head()

df['text'] = df['airport'] + '' + df['city'] + ', ' + df['state'] + '' + 'Arrivals: ' + df['cnt'].astype(str)

scl = [ [0,"rgb(5, 10, 172)"],[0.35,"rgb(40, 60, 190)"],[0.5,"rgb(70, 100, 245)"],\
    [0.6,"rgb(90, 120, 245)"],[0.7,"rgb(106, 137, 247)"],[1,"rgb(220, 220, 220)"] ]

data = [ dict(
        type = 'scattergeo',
        locationmode = 'USA-states',
        lon = df['long'],
        lat = df['lat'],
        text = df['text'],
        mode = 'markers',
        marker = dict(
            size = 8,
            opacity = 0.8,
            reversescale = True,
            autocolorscale = False,
            symbol = 'square',
            line = dict(
                width=1,
                color='rgba(102, 102, 102)'
            ),
            colorscale = scl,
            cmin = 0,
            color = df['cnt'],
            cmax = df['cnt'].max(),
            colorbar=dict(
                title="Incoming flightsFebruary 2011"
            )
        ))]

layout = dict(
        title = 'Most trafficked US airports<br>(Hover for airport names)',
        colorbar = True,
        geo = dict(
            scope='usa',
            projection=dict( type='albers usa' ),
            showland = True,
            landcolor = "rgb(250, 250, 250)",
            subunitcolor = "rgb(217, 217, 217)",
            countrycolor = "rgb(217, 217, 217)",
            countrywidth = 0.5,
            subunitwidth = 0.5
        ),
    )

fig_map = dict( data=data, layout=layout )

########## Dash website layout

#app = dash.Dash() old line of code
app = dash.Dash(__name__) # new line of code, which now allows us to access assets folder
server = app.server

app.layout = html.Div([
    html.Div([
        html.H2("The Data Incubator Fellowship Capstone Project:  Kaustuv Chakrabarti"),
        html.Img(src="/assets/Airport_Image.jpg")
    ], className = "banner", style={'backgroundColor':'blue'}),
    # html.Div([
    #     dcc.Input(id = "Airport Performance Dashboard", value = user_input_airportFsCode_Dash, type = "text")
    # ]),
    html.Div(html.H1(children = "Airport Operational Performance Live Dashboard")),

    html.Label("Airport: Los Angeles International (LAX)"),
    # html.Label("Select Date:  June 23, 2019"),

    html.Div(
        dcc.Input(
            id = "airport_input",
            placeholder = "Enter an airport code",
            type = "text",
            value = ''
            )
    ),
    # html.Div(
    #     dcc.Dropdown(
    #         options = [
    #             {'label':'Candlestick','value':'Candlestick'},
    #             {'label': 'Line', 'value': 'Line'}
    #         ]
    #     )
    # ),
    html.Div(children='''
        Business Objective: The airline industry constitutes a major portion of the U.S. economy and 
        serves passengers through a vast, complicated network of operations.  U.S. airlines accounted 
        for 889 million passenger-trips in 2018, an average of 2.4 million trips per day.
        
        Operating revenue for U.S. airlines was $171 billion in 2018.  Over 5,000 airports are located in the U.S.
        
        Providing decision-makers the tools to monitor performance (e.g., delay and congestion within 
        airports) can help improve operations, driving financial success and passenger satisfaction.
        '''),

    html.Div(children='''
                                              
        '''),
    html.Div(children='''
        Data Ingestion: The Flight Status Developer Center provides daily information on thousands of flights, 
        such as arrival and departure times, flight durations, flight delays, by flight number, airline, airport, 
        and airport gate and terminal.
        '''),
    html.Div(children='''
        This dashboard connects (live) to the MongoDB database that hosts the data and converts the JSON data through
        Python into Pandas dataframes.  Data is sourced from multiple MongoDB collections, such as flight status and 
        airline collections.  These dataframes were linked/combined (e.g., translating airline IATA codes to airline names)
        and further modified into subsequent dataframes providing information on flight volumes, delays, etc.
    '''),
    html.Div(children='''                                               

        '''),
    html.Div(children='''
        Visualizations: This dashboard provides several types of visualizations, including bar charts and Pandas-based
        tables.
        '''),
    html.Div(children='''                                       

        '''),
    html.Div(children='''
        User Interactivity: The dashboard allows (will allow) a user to select an airport after which the visualizations
        will update.
        '''),

#########  Section of charts
    # html.Div([
    #     html.Div([
    #         dcc.Graph(id="abc",
    #               figure=fig_map
    #               )
    #     ],className="six columns", style={'width': '49%', 'float':'right','display': 'block','vertical-align':'middle'}
    #     ),
    #     html.Div([
    #         dcc.Graph(id="def",
    #               figure = arrival_count_by_departing_from_airport_figure
    #               )
    #     ], className="six columns",style={'width': '49%', 'float':'right','display': 'block','vertical-align':'middle'}
    #     )
    # ],className = "row"),



#########  Section of charts
    html.Div([
        html.Div([
            dcc.Graph(id="departure_count_by_arriving_at_airport_figure",
                  figure=departure_count_by_arriving_at_airport_figure
                  )
        ],className="six columns", style={'width': '49%', 'float':'right','display': 'block','vertical-align':'middle'}
        ),
        html.Div([
            dcc.Graph(id="arrival_count_by_departing_from_airport_figure",
                  figure = arrival_count_by_departing_from_airport_figure
                  )
        ], className="six columns",style={'width': '49%', 'float':'right','display': 'block','vertical-align':'middle'}
        )
    ],className = "row"),
#########  Section of charts
    html.Div([
        html.Div([
            dcc.Graph(id="departure_count_by_airline_figure",
                  figure=departure_count_by_airline_figure
                  )
        ],className="six columns", style={'width': '49%', 'float':'right','display': 'block','vertical-align':'middle'}
        ),
        html.Div([
            dcc.Graph(id="arrival_count_by_airline_figure",
                  figure = arrival_count_by_airline_figure
                  )
        ], className="six columns",style={'width': '49%', 'float':'right','display': 'block','vertical-align':'middle'}
        )
    ],className = "row"),
#########  Section of charts
    html.Div([
        html.Div([
            dcc.Graph(id="departure_count_by_departure_terminal_figure",
                      figure=departure_count_by_departure_terminal_figure
                      )
        ], className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        ),
        html.Div([
            dcc.Graph(id="arrival_count_by_arrival_terminal_figure",
                      figure=arrival_count_by_arrival_terminal_figure
                      )
        ], className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        )
    ], className="row"),
#########  Section of charts
    html.Div([
        html.Div([
            dcc.Graph(id="departure_gate_delay_by_fscode_figure",
                  figure=departure_gate_delay_by_fscode_figure
                  )
        ],className="six columns", style={'width': '49%', 'float':'right','display': 'block','vertical-align':'middle'}
        ),
        html.Div([
            dcc.Graph(id="arrival_gate_delay_by_fscode_figure",
                  figure = arrival_gate_delay_by_fscode_figure
                  )
        ], className="six columns",style={'width': '49%', 'float':'right','display': 'block','vertical-align':'middle'}
        )
    ],className = "row"),
#########  Section of charts
    html.Div([
        html.Div([
            dcc.Graph(id="departure_gate_delay_by_departure_terminal_figure",
                      figure=departure_gate_delay_by_departure_terminal_figure
                      )
        ], className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        ),
        html.Div([
            dcc.Graph(id="arrival_gate_delay_by_arrival_terminal_figure",
                      figure=arrival_gate_delay_by_arrival_terminal_figure
                      )
        ], className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle'}
        )
    ], className="row"),

# app.layout = html.Div(children=[
#     html.H4(children='US Agriculture Exports (2011)'),
#     generate_table(df)
# ])
#########  Section of tables
    html.Div([
        html.Div(
            html.Div(
                generate_table(flight_table_df_departure_airport))
        , className="six columns",
            style={'width': '49%', 'float': 'right', 'display': 'block', 'vertical-align': 'middle', 'maxHeight': '50','overflowY': 'scroll'}
        ),
        html.Div(
            html.Div(
                generate_table(flight_table_df_arrival_airport))
        , className="six columns",
            style={'width': '49%', 'height': '50%','overflowY': 'scroll'}
        )
    ], className="row")

])

app.css.append_css({
    "external_url":"https://codepen.io/chriddyp/pen/bWLwgP.css"
})

# @app.callback(dash.dependencies.Output("fig_departure_gate_delay_by_departure_terminal","figure"),
#                [dash.dependencies.Input("airport_input","text")]
#                )

# @app.callback(
#     Output(user_input_airportFsCode_Dash, component_property='value'),
#     Input(component_id='airport_input', component_property='value'))
# def update_airport(input_value):
#     user_input_airportFsCode_Dash = input_value

### Keep this last in the code?
if __name__ == "__main__":
    app.run_server(debug=True)







