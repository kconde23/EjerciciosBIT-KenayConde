import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, Input, Output
import os


DATA_PATH = "./deaths-illicit-drugs NEW.csv"
df = pd.read_csv(DATA_PATH)

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


default_countries = countries[:5] if len(countries) >= 5 else countries


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
        dbc.Col(
            html.H1(
                "Global Illicit Drug Mortality Dashboard",
                className="text-center my-4"
            )
        )
    ]),

    
    dbc.Card(className="mb-4", children=[
        dbc.CardHeader("Interactive Filters"),
        dbc.CardBody([

            dbc.Row([
                dbc.Col([
                    html.Label("Countries"),
                    dcc.Dropdown(
                        id="country_selector",
                        options=[{"label": c, "value": c} for c in countries],
                        value=default_countries,
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
                    html.Label("Year Range"),
                    dcc.RangeSlider(
                        id="year_selector",
                        min=int(min(years)),
                        max=int(max(years)),
                        value=[int(min(years)), int(max(years))],
                        marks={int(y): str(y) for y in years[::3]},
                        step=1
                    )
                ])
            ])
        ])
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="trend_graph"), md=12)
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="bar_graph"), md=6),
        dbc.Col(dcc.Graph(id="scatter_graph"), md=6)
    ])

])
 dcc.Dropdown(
    ...
    style={"color": "black"}
)
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

    # Safety checks
    if not selected_countries:
        selected_countries = default_countries

    df_filtered = df[
        (df["country"].isin(selected_countries)) &
        (df["year"] >= year_range[0]) &
        (df["year"] <= year_range[1])
    ]

    if df_filtered.empty:
        empty_fig = px.bar(title="No data for selected filters")
        return empty_fig, empty_fig, empty_fig

    # =====================
    # LINE CHART – Yearly Evolution
    # =====================
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
        markers=True,
        title="Yearly Evolution"
    )

    # =====================
    # BAR – Top Countries
    # =====================
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

    # =====================
    # SCATTER – Rate vs Deaths
    # =====================
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
        size="drug_deaths",
        title="Death Rate vs Total Deaths"
    )

    return fig_trend, fig_bar, fig_scatter


# =====================
# RUN (RENDER SAFE)
# =====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port)
