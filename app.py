import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc

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

# =====================
# DASH APP
# =====================
app = Dash(__name__)
server = app.server  # Needed for Render

years = sorted(df["year"].unique())

# =====================
# LAYOUT
# =====================
app.layout = html.Div(
    style={"padding": "20px", "fontFamily": "Arial"},
    children=[

        html.H1("Illicit Drug Deaths Dashboard", style={"textAlign": "center"}),

        # Year Selector
        dcc.Slider(
            id="year-slider",
            min=min(years),
            max=max(years),
            value=max(years),
            marks={int(y): str(y) for y in years[::2]},
            step=1
        ),

        html.Br(),

        # Charts
        dcc.Graph(id="line-trend"),
        dcc.Graph(id="bar-top-countries"),

        html.Div(
            style={"display": "flex"},
            children=[
                dcc.Graph(id="pie-country-share", style={"width": "50%"}),
                dcc.Graph(id="scatter-rate-vs-deaths", style={"width": "50%"})
            ]
        )
    ]
)

# =====================
# CALLBACKS
# =====================
@app.callback(
    Output("line-trend", "figure"),
    Output("bar-top-countries", "figure"),
    Output("pie-country-share", "figure"),
    Output("scatter-rate-vs-deaths", "figure"),
    Input("year-slider", "value")
)
def update_charts(selected_year):

    filtered = df[df["year"] <= selected_year]

    # Line chart – Global trend
    trend = filtered.groupby("year")["drug_deaths"].sum().reset_index()
    fig_line = px.line(
        trend,
        x="year",
        y="drug_deaths",
        title="Global Drug Deaths Over Time"
    )

    # Bar chart – Top 10 countries (selected year)
    top_countries = (
        df[df["year"] == selected_year]
        .groupby("country")["drug_deaths"]
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

    # Pie chart – Country share
    fig_pie = px.pie(
        top_countries,
        names="country",
        values="drug_deaths",
        title="Share of Drug Deaths"
    )

    # Scatter plot – Rate vs deaths
    scatter_data = (
        df[df["year"] == selected_year]
        .groupby("country")[["drug_deaths", "death_rate"]]
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

    return fig_line, fig_bar, fig_pie, fig_scatter


# =====================
# RUN LOCAL
# =====================
if __name__ == "__main__":
    app.run(debug=True)