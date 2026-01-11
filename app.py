import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, Input, Output

# =====================
# DATA
# =====================
df = pd.read_csv("deaths-illicit-drugs NEW.csv")

df = df.rename(columns={
    "COUNTRY": "country",
    "Code": "country_code",
    "Year": "year",
    "Deaths - Drug use disorders - Sex: Both - Age: All Ages (Number)": "drug_deaths",
    "Deaths that are from all causes attributed to drug use, in both sexes aged all ages": "death_rate"
})

df["drug_deaths"] = pd.to_numeric(df["drug_deaths"], errors="coerce")
df["death_rate"] = (
    df["death_rate"]
    .astype(str)
    .str.replace(".", "", regex=False)
    .astype(float)
)

df = df.dropna()

years = sorted(df["year"].unique())
countries = sorted(df["country"].unique())

# =====================
# APP
# =====================
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    title="Global Illicit Drug Mortality Analysis"
)
server = app.server

# =====================
# LAYOUT
# =====================
app.layout = dbc.Container(fluid=True, children=[

    dbc.Row([
        html.H1(
            "Global Illicit Drug Mortality Dashboard",
            className="text-center my-3"
        )
    ]),

    # FILTER CARD
    dbc.Card(className="mb-4", children=[
        dbc.CardHeader("Analysis Filters"),
        dbc.CardBody([

            dbc.Row([
                dbc.Col([
                    html.Label("Country selection"),
                    dcc.Dropdown(
                        id="country_selector",
                        options=[{"label": c, "value": c} for c in countries],
                        value=countries[:5],
                        multi=True
                    )
                ], md=6),

                dbc.Col([
                    html.Label("Metric"),
                    dcc.RadioItems(
                        id="metric_selector",
                        options=[
                            {"label": "Total Deaths", "value": "drug_deaths"},
                            {"label": "Death Rate", "value": "death_rate"}
                        ],
                        value="drug_deaths",
                        inline=True
                    )
                ], md=6),
            ]),

            dbc.Row([
                dbc.Col([
                    html.Label("Year range"),
                    dcc.RangeSlider(
                        id="year_selector",
                        min=min(years),
                        max=max(years),
                        value=[min(years), max(years)],
                        marks={y: str(y) for y in years[::3]},
                        step=1
                    )
                ])
            ])
        ])
    ]),

    # VISUALS
    dbc.Row([
        dbc.Col(dcc.Graph(id="trend_graph"), md=12)
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="bar_graph"), md=6),
        dbc.Col(dcc.Graph(id="scatter_graph"), md=6)
    ])
])

# =====================
# CALLBACK
# =====================
@app.callback(
    Output("trend_graph", "figure"),
    Output("bar_graph", "figure"),
    Output("scatter_graph", "figure"),
    Input("country_selector", "value"),
    Input("metric_selector", "value"),
    Input("year_selector", "value")
)
def update_dashboard(selected_countries, metric, year_range):

    df_filtered = df[
        (df["country"].isin(selected_countries)) &
        (df["year"] >= year_range[0]) &
        (df["year"] <= year_range[1])
    ]

    if df_filtered.empty:
        empty_fig = px.bar(title="No data for selected filters")
        return empty_fig, empty_fig, empty_fig

    # LINE – trend per year (NON cumulative)
    yearly = (
        df_filtered
        .groupby("year")[metric]
        .sum()
        .reset_index()
    )

    fig_trend = px.line(
        yearly,
        x="year",
        y=metric,
        title="Yearly Evolution",
        markers=True
    )

    # BAR – top countries in range
    bar_data = (
        df_filtered
        .groupby("country")[metric]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    fig_bar = px.bar(
        bar_data,
        x="country",
        y=metric,
        title="Top Countries in Selected Period"
    )

    # SCATTER – rate vs deaths
    scatter_data = (
        df_filtered
        .groupby("country")[["drug_deaths", "death_rate"]]
        .mean()
        .reset_index()
    )

    fig_scatter = px.scatter(
        scatter_data,
        x="drug_deaths",
        y="death_rate",
        hover_name="country",
        title="Death Rate vs Total Deaths",
        size="drug_deaths"
    )

    return fig_trend, fig_bar, fig_scatter


# =====================
# RUN
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
