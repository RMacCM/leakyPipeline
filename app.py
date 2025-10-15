# %%
import os
#!pip install pandas
#!pip install plotly
#!pip install dash
import pandas as pd
import dash
from dash import dcc, html
import plotly.graph_objects as go

df = pd.read_csv("attritionData.csv")
df['node_color'] = df['node_color'].fillna('gray')  
links_data = df.iloc[:, :5]  #these cols will be the links df
nodes_data = df.iloc[:, -2:] # these cols will be the nodes df


df_links = pd.DataFrame(links_data)
df_nodes = pd.DataFrame(nodes_data)


node_labels = df_nodes['node_label'].tolist()
node_colors = df_nodes['node_color'].tolist()

# make nodes integers as required for the Sankey plot
label_to_index = {label: i for i, label in enumerate(node_labels)}

# make links and nodes into dictionaries
link = dict(
    source = df_links['source'].map(label_to_index).tolist(),
    target = df_links['target'].map(label_to_index).tolist(),
    value  = df_links['value'].tolist(),
    label  = df_links['label'].tolist(),
    color  = df_links['color'].tolist()
)
node = dict(
    pad = 15,
    thickness = 15,
    line = dict(color = "black", width = 0.5),
    label = node_labels,
    color = node_colors
)

# Create the graph
fig = go.Figure(data=[go.Sankey(
    valueformat = ".0f",
    valuesuffix = "TWh",
    node = node,
    link = link
)])

fig.update_layout(
    title_text="FY 2025 Accessions Pipeline Attrition", 
    font_size=12,
    hovermode = 'x' # makes the mouse hover show data values in tooltip
    )
fig.show()

# setup graph to display as app using Plotly Dash
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Sankey Test"),
    dcc.Graph(figure=fig)
])

#write requirements.txt
#import pkg_resources
#with open("requirements.txt", "w") as f:
    #for dist in pkg_resources.working_set:
        #f.write(f"{dist.project_name}=={dist.version}\n")






