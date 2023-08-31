import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import requests
from io import BytesIO
from zipfile import ZipFile

# Fetch and prepare the data
cot_file = requests.get('https://www.cftc.gov/files/dea/history/com_disagg_xls_2023.zip')

with BytesIO(cot_file.content) as cot_zip:
    with ZipFile(cot_zip) as cot_data:
        filenames = cot_data.namelist()
        cot_xls = filenames[0]
        with cot_data.open(cot_xls) as xls_file:
            xls_bytes = BytesIO(xls_file.read())
            df = pd.read_excel(xls_bytes)

# Filter out string columns
def filter_and_convert(df):
    df_filtered = df.select_dtypes(include=['number'])
    df_float = df_filtered.iloc[:, 2:].applymap(lambda x: float(x) if not isinstance(x, str) else 0.0)
    return df_float

# Create a list of unique 'Market_and_Exchange_Names'
unique_markets = sorted(df['Market_and_Exchange_Names'].dropna().unique().tolist())

# Initialize the Dash app
app = dash.Dash(__name__,assets_folder='assets')

app.layout = html.Div(children=[
    html.H1('CFTC: Commitment Of Traders Weekly Reports', style={'color': '#7FDBFF'}),
    dcc.Dropdown(
        id='market-dropdown',
        options=[{'label': market, 'value': market} for market in unique_markets],
        value=unique_markets[0],
        style={'backgroundColor': 'white', 'color': 'black'}  # default value
    ),
    dcc.Graph(id='line-plot')
])

@app.callback(
    Output('line-plot', 'figure'),
    [Input('market-dropdown', 'value')]
)
def update_graph(selected_market):
    plot_df = df[df['Market_and_Exchange_Names'] == selected_market]
    df_float = filter_and_convert(plot_df)
    fig = px.line(df_float, x=plot_df['Report_Date_as_MM_DD_YYYY'], y=df_float.columns, template='plotly_dark')
    fig.update_layout(height = 1000)

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
