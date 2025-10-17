# %%
import os
#!pip install pandas
import pandas as pd
import seaborn as sns
import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go

# Load and prepare data
df = pd.read_csv("pipelineList.csv").iloc[:, :4]
df['value'] = 1  # Each row represents one unit of flow


# Aggregate flows
aggregates = df.groupby(['from', 'to'], as_index=False).agg({'value': 'sum'})

# Identify loss links
loss_links = aggregates[aggregates['to'].str.endswith(' Loss')].copy()

# Compute source-level loss %
total_by_source = aggregates.groupby('from')['value'].sum().rename('total')
loss_by_source = loss_links.groupby('from')['value'].sum().rename('loss')
loss_metrics = pd.concat([total_by_source, loss_by_source], axis=1).fillna(0)   
loss_metrics['loss_pct'] = (loss_metrics['loss'] / loss_metrics['total']) * 100

# Compute system-level loss %
total_loss = loss_links['value'].sum()
loss_links['loss_pct_of_total'] = (loss_links['value'] / total_loss) * 100      

# Build node list and index mapping
nodes = pd.unique(aggregates[['from', 'to']].values.ravel()).tolist()
node_indices = {name: i for i, name in enumerate(nodes)}

# Assign node labels and colors
label_dict = {name: name.upper() for name in nodes}
palette = sns.color_palette("crest", len(nodes))
color_dict = dict(zip(nodes, palette))

# Map node indices
aggregates['from_idx'] = aggregates['from'].map(node_indices)
aggregates['to_idx'] = aggregates['to'].map(node_indices)

# Build link label dictionary with both metrics
loss_label_dict = {
    (row['from'], row['to']): (
        f"Loss: {loss_metrics.loc[row['from'], 'loss_pct']:.1f}%"
        + f" | {row['loss_pct_of_total']:.1f}% of total loss"
    )
    for _, row in loss_links.iterrows()
    if row['from'] in loss_metrics.index
}

# Build link labels for Dash app
source_loss_labels = {
    (row['from'], row['to']): f"Loss: {loss_metrics.loc[row['from'], 'loss_pct']:.1f}%"
    for _, row in loss_links.iterrows()
    if row['from'] in loss_metrics.index
}

system_loss_labels = {
    (row['from'], row['to']): f"{row['loss_pct_of_total']:.1f}% of total loss"
    for _, row in loss_links.iterrows()
}
# Apply labels to all links
aggregates['link_label'] = aggregates.apply(
    lambda row: loss_label_dict.get((row['from'], row['to']), ''),
    axis=1
)

fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=[label_dict[n] for n in nodes],
        color=["rgba({},{},{},0.8)".format(int(r*255), int(g*255), int(b*255)) for r, g, b in color_dict.values()]
    ),
    link=dict(
        source=aggregates['from_idx'],
        target=aggregates['to_idx'],
        label=aggregates['link_label'].tolist(),        # not working - no metrics
        value=aggregates['value']
    )
)])

# build bar charts for loss reasons
loss_df = df[df['to'].str.endswith(' Loss')].copy()
reason_counts = (
    loss_df.groupby(['from', 'to', 'reason'])
    .size()
    .reset_index(name='count')
)
top_reasons = (
    reason_counts
    .sort_values(['from', 'to', 'count'], ascending=[True, True, False])
    .groupby(['from', 'to'])
    .head(5)
)

def make_reason_chart(from_node, to_node):
    subset = top_reasons[(top_reasons['from'] == from_node) & (top_reasons['to'] == to_node)]

    # Sort by count descending
    subset = subset.sort_values('count', ascending=True)  # reverse for horizontal bar order

    fig = px.bar(
        subset,
        x='count',
        y='reason',
        orientation='h',
        title=f"Top Reasons: {from_node} → {to_node}",
        labels={'count': '', 'reason': 'Reason'},
        height=250,
        color_discrete_sequence=['black']
    )

    # Add data labels outside the bars
    fig.update_traces(
        text=subset['count'],
        textposition='outside',
        marker_color='black'
    )

    # Clean layout
    fig.update_layout(
        margin=dict(l=80, r=20, t=30, b=30),
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(categoryorder='array', categoryarray=subset['reason'].tolist())
    )

    return fig

reason_charts = {
    (row['from'], row['to']): make_reason_chart(row['from'], row['to'])
    for _, row in loss_links.iterrows()
}

fig.show()

#configure for Dash
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.Div([
        dcc.Graph(id='sankey-chart'),
        html.Button("See Top Loss Codes", id='toggle-chart-button', n_clicks=0),
        html.Button("Toggle Loss % Metric", id='toggle-metric-button', n_clicks=0),
        html.Div(id='active-metric-label', style={'marginTop': '10px', 'fontWeight': 'bold'})
    ], style={'position': 'relative'}),

    html.Div(id='bar-chart-container', style={'position': 'absolute', 'top': '100px', 'left': '50px', 'display': 'none'})
])

@app.callback(
    Output('bar-chart-container', 'style'),
    Input('toggle-button', 'n_clicks'),
    State('bar-chart-container', 'style')
)
def toggle_bar_chart(n_clicks, current_style):
    if n_clicks % 2 == 1:
        return {**current_style, 'display': 'block'}
    else:
        return {**current_style, 'display': 'none'}
    
@app.callback(
    Output('bar-chart-container', 'children'),
    Input('toggle-chart-button', 'n_clicks')
)
def render_bar_charts(n_clicks):
    if n_clicks % 2 == 0:
        return []  # hide charts when toggled off

    charts = []
    for (from_node, to_node), chart in reason_charts.items():
        charts.append(
            html.Div([
                html.H5(f"{from_node} → {to_node}"),
                dcc.Graph(figure=chart)
            ], style={'marginBottom': '20px'})
        )
    return charts

@app.callback(
    Output('sankey-chart', 'figure'),
    Output('active-metric-label', 'children'),
    Input('toggle-metric-button', 'n_clicks')
)
def update_sankey_labels(n_clicks):
    use_system_metric = n_clicks % 2 == 1

    label_dict = system_loss_labels if use_system_metric else source_loss_labels
    label_text = "Showing: System-level loss %" if use_system_metric else "Showing: Source-level loss %"

    aggregates['link_label'] = aggregates.apply(
        lambda row: label_dict.get((row['from'], row['to']), ''),
        axis=1
    )

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=[label_dict.get(n, n.upper()) for n in nodes],
            color=["rgba({},{},{},0.8)".format(int(r*255), int(g*255), int(b*255)) for r, g, b in color_dict.values()]
        ),
        link=dict(
            source=aggregates['from_idx'],
            target=aggregates['to_idx'],
            value=aggregates['value'],
            label=aggregates['link_label'].tolist()
        )
    )])

    return fig, label_text
