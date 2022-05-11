import dash
import pandas as pd
from dash import Dash, Input, Output, callback, dash_table, html, dcc, no_update
import dash_bootstrap_components as dbc
from difflib import SequenceMatcher
from colour import RGB_color_picker


import plotly.graph_objs as go

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


data_source = pd.read_xml("cleaned_translations.xml")

available_languages = ["de", "en"]

translation_languages = ["de", "en", "ti-ET", "pl", "tr"]
color_list = list(map(lambda c: RGB_color_picker(c).hex, translation_languages))
color_lookup = dict(zip(translation_languages, color_list))


def get_overall_stats():
    return data_source["t_language"].value_counts()


app.layout = html.Div(
    [
        html.Div(
            className="header",
            children=[
                html.Div(
                    className="div-info",
                    children=[
                        html.H2(
                            className="title", children="Translation Memory Analysis"
                        ),
                        html.P(
                            """
                            This App provides a graphic visualization of given TMX files and provide some basic search functions.
                            """
                        ),
                    ],
                )
            ],
        ),
        html.Div(
            className="input-section",
            children=[
                html.I("Select a origin Language, enter desired text and press Enter"),
                html.Br(),
                html.Label("Origin Language"),
                dcc.Dropdown(
                    id="language-selected",
                    options=[{"label": i, "value": i} for i in available_languages],
                ),
                html.Label("Desired Segment"),
                dcc.Input(
                    id="segment-text",
                    type="text",
                    placeholder="Enter segment text for analysis",
                    debounce=True,
                ),
                html.Div(
                    [dcc.Graph(id="my-graph", clear_on_unhover=True)], className="row"
                ),
                dcc.Tooltip(id="graph-tooltip"),
            ],
        ),
    ]
)


def get_closest_matches(segment, lang):
    language_selection = data_source[data_source["o_language"] == lang]
    found_matches = []
    for index, row in language_selection.iterrows():
        if row["o_segment"] is not None:
            if SequenceMatcher(None, segment, row["o_segment"]).ratio() > 0.50:
                found_matches.append(
                    {
                        "row": row,
                        "score": SequenceMatcher(
                            None, segment, row["o_segment"]
                        ).ratio(),
                    }
                )
    return found_matches


@app.callback(
    Output("my-graph", "figure"),
    Input("language-selected", "value"),
    Input("segment-text", "value"),
)
def render_table(lang, segment):
    if segment is None:
        return no_update
    x = []
    y = []
    for entry in get_closest_matches(segment, lang):
        y.append(entry["row"]["o_segment"])
        x.append(entry["score"])


    trace = [go.Bar(x=x, y=y, orientation="h")]
    figure = {"data": trace, "layout": plot_layout}
    return figure


@app.callback(
    Output("graph-tooltip", "show"),
    Output("graph-tooltip", "bbox"),
    Output("graph-tooltip", "children"),
    Input("my-graph", "hoverData"),
)
def display_hover(hoverData):
    if hoverData is None:
        return False, no_update, no_update

    pt = hoverData["points"][0]
    label = pt["label"]

    df_row = data_source[data_source["o_segment"] == label].iloc[0]

    lang = df_row["t_language"]
    translation = df_row["t_segment"]
    pre = df_row["o_context_pre"]
    post = df_row["o_context_post"]

    bbox = pt["bbox"]

    children = [
        html.Div(
            [
                html.H2(f"{translation}", style={"color": "darkblue"}),
                html.I(f"Language {lang}"),
                html.H3("Context"),
                html.P(f"{pre}"),
                html.P(f"{label}"),
                html.P(f"{post}"),
            ],
            style={"width": "300px", "white-space": "normal"},
        )
    ]

    return True, bbox, children


plot_layout = go.Layout(
    autosize=True,
    xaxis=dict(
        showgrid=False,
        showline=False,
        zeroline=True,
        side="top",
        title="Similarity",
        domain=[0, 1],
    ),
    yaxis=dict(
        showgrid=False,
        showline=False,
        zeroline=True,
        autorange="reversed",
        title="Found Matches",
    ),
    margin=dict(l=150, r=10, t=50, b=80),
    showlegend=False,
)


if __name__ == "__main__":
    app.run_server(debug=True)