from haystack import Finder
from haystack.reader.farm import FARMReader

from haystack.database.elasticsearch import ElasticsearchDocumentStore
from haystack.retriever.sparse import ElasticsearchRetriever
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_table
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

credentials = service_account.Credentials.from_service_account_file(os.environ['GCP_APPLICATION_CREDENTIALS'])
gcp_project_id = os.environ['GCP_PROJECT_ID']
gcp_zone_id = os.environ['GCP_ZONE_ID']
gcp_instance_name = os.environ['GCP_INSTANCE_NAME']


def get_ip_address_gce(project_id, zone, instance_name):
    service = build('compute', 'v1', credentials=credentials)
    response = service.instances().get(project=project_id, zone=zone, instance=instance_name).execute()
    ip = response['networkInterfaces'][0]['accessConfigs'][0]['natIP']
    return ip


ip = get_ip_address_gce(gcp_project_id, gcp_zone_id, gcp_instance_name)
document_store = ElasticsearchDocumentStore(host=ip, username="", password="", index="main")
retriever = ElasticsearchRetriever(document_store=document_store)
reader = FARMReader(model_name_or_path="distilbert-base-uncased-distilled-squad", use_gpu=True, num_processes=5)
finder = Finder(reader, retriever)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.config.suppress_callback_exceptions = True

style_table = {'overflowY': 'scroll',
               'overflowX': 'hidden',
               'padding-left': '20px',
               'maxHeight': '400px'}
style_cell = {'padding-right': '20px',
              'whiteSpace': 'normal',
              'minWidth': '0px',
              'maxWidth': '200px',
              'fontSize': 12,
              'font-family': 'sans-serif',
              }
style_header = {'textAlign': 'center',
                'padding-left': '20px',
                'backgroundColor': 'white',
                'fontWeight': 'bold'}

app.layout = html.Div([
    html.Div(
        [html.H2('PubMed Chatbot')],
        style={'text-align': 'center'}),
    html.Div(
        [
            html.Div([
                html.Div([
                    dcc.Input(
                        id="question_box",
                        type="text",
                        size="50",
                        placeholder="Type your research question"),
                ]),
                html.Div([
                    html.Button(
                        'Submit',
                        id='submit_question',
                        n_clicks=0
                    )
                ]),
            ],
                style={'justify-content': 'center', 'display': 'flex', 'align-items': 'center'}
            ),
            html.Div(
                style={'justify-content': 'center', 'display': 'flex', 'align-items': 'center'},
                id='answers_list')
        ])])


def is_triggered(id):
    ctx = dash.callback_context
    element_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if element_id == id:
        return True
    else:
        return False


@app.callback(Output('answers_list', 'children'),
              [Input('question_box', 'value'),
               Input('submit_question', 'n_clicks')])
def get_answer(question, n_clicks):
    print("in callback")
    if is_triggered('submit_question'):
        prediction = finder.get_answers(question=question,
                                        top_k_retriever=1,
                                        top_k_reader=1)
        prediction = [{'Answer': ans['answer'],
                       'Probability': "{:10.2f}".format(ans['probability']),
                       'Context': ans['context']}
                      for ans in prediction['answers']]

        return [dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in ['Answer', 'Probability', 'Context']],
            data=prediction,
            style_table=style_table,
            style_cell=style_cell,
            style_as_list_view=True,
            style_header=style_header,
        )]


if __name__ == '__main__':
    app.run_server(host='0.0.0.0',
                   port=5000,
                   debug=False)
