import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc

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

# =====================
# APP
# =====================
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Global Illicit Drug Deaths Analysis"
)
server = app.server

# =====================
# PRE-COMPUTE YEARLY DEATHS (NON-CUMULATIVE)
# =====================
yearly_deaths = (
    df.groupby("year")["drug_deaths"]
    .sum()
    .reset_index()
)

# =====================
# LAYOUT
# =====================
app.layout = dbc.Container([

    html.H1(
        "Global Illicit Drug Deaths Analysis",
        className="text-center my-4"
    ),

    dcc.Slider(
        id="year-slider",
        min=min(years),
        max=max(years),
        value=max(years),
        marks={int(y): str(y) for y in years[::2]},
        step=1
    ),

    html.Br(),

    dbc.Row([
        dbc.Col(dbc.Card(
            dbc.CardBody([
                html.H4("Total Deaths (Selected Year)", className="card-title"),
                html.H2(id="kpi-total", className="text-danger")
            ])
        ), width=4)
    ]),

    html.Br(),

    dcc.Graph(
        id="line-trend",
        figure=px.line(
            yearly_deaths,
            x="year",
            y="drug_deaths",
            title="Global Drug Deaths Per Year (Non-Cumulative)"
        )
    ),

    dcc.Graph(id="bar-top-countries"),

    dbc.Row([
        dbc.Col(dcc.Graph(id="pie-country-share"), width=6),
        dbc.Col(dcc.Graph(id="scatter-rate-vs-deaths"), width=6)
    ])

], fluid=True)

# =====================
# CALLBACK
# =====================
@app.callback(
    Output("bar-top-countries", "figure"),
    Output("pie-country-share", "figure"),
    Output("scatter-rate-vs-deaths", "figure"),
    Output("kpi-total", "children"),
    Input("year-slider", "value")
)
def update_charts(selected_year):

    year_df = df[df["year"] == selected_year]

    # KPI
    total_deaths = int(year_df["drug_deaths"].sum())

    # Bar
    top_countries = (
        year_df.groupby("country")["drug_deaths"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    fig_bar = px.bar(
        top_countries,
        x="country",
        y="drug_deaths",
        title=f"Top 10 Countries by Drug Deaths ({selected_year})"
    )

    # Pie
    fig_pie = px.pie(
        top_countries,
        names="country",
        values="drug_deaths",
        title="Country Share of Deaths"
    )

    # Scatter
    scatter_data = (
        year_df.groupby("country")[["drug_deaths", "death_rate"]]
        .mean()
        .reset_index()
    )

    fig_scatter = px.scatter(
        scatter_data,
        x="drug_deaths",
        y="death_rate",
        hover_name="country",
        title="Death Rate vs Total Deaths"
    )

    return fig_bar, fig_pie, fig_scatter, f"{total_deaths:,}"

# =====================
# RUN
# =====================
if __name__ == "__main__":
    app.run(debug=True)
