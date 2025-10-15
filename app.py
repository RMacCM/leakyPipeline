# %%
import os
#os.chdir(r'C:\Users\Rob\Desktop\Learn to Code\Datasets')
#!pip install pandas
#!pip install plotly
#!pip install dash
import pandas as pd
import dash
from dash import dcc, html
import plotly.graph_objects as go

df = pd.read_csv("attritionData.csv")
df['node_color'] = df['node_color'].fillna('gray')  
links_data = df.iloc[:, :5]
nodes_data = df.iloc[:, -2:]


df_links = pd.DataFrame(links_data)
df_nodes = pd.DataFrame(nodes_data)


node_labels = df_nodes['node_label'].tolist()
node_colors = df_nodes['node_color'].tolist()

label_to_index = {label: i for i, label in enumerate(node_labels)}

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

# Create figure
fig = go.Figure(data=[go.Sankey(
    valueformat = ".0f",
    valuesuffix = "TWh",
    node = node,
    link = link
)])

fig.update_layout(
    title_text="FY 2025 Accessions Pipeline Attrition", 
    font_size=10,
    hovermode = 'x'
    )
fig.show()

app = dash.Dash(__name__)
server = app.server

# Layout
app.layout = html.Div([
    html.H1("Sankey Test"),
    dcc.Graph(figure=fig)
])

#write requirements.txt
#import pkg_resources
#with open("requirements.txt", "w") as f:
    #for dist in pkg_resources.working_set:
        #f.write(f"{dist.project_name}=={dist.version}\n")





