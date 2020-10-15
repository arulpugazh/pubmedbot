from haystack import Finder
from haystack.reader.farm import FARMReader

from haystack.document_store.elasticsearch import ElasticsearchDocumentStore
from haystack.retriever.sparse import ElasticsearchRetriever
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import dash_table
from gcputils import get_elastic_ip
from dbutils import get_new_db_connection

elastic_ip = get_elastic_ip()
document_store = ElasticsearchDocumentStore(host=elastic_ip, username="", password="", index="articles")
retriever = ElasticsearchRetriever(document_store=document_store)
reader = FARMReader(model_name_or_path="deepset/roberta-base-squad2", use_gpu=False, num_processes=10)
finder = Finder(reader, retriever)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', dbc.themes.BOOTSTRAP]
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
              'maxWidth': '300px',
              'fontSize': 12,
              'font-family': 'sans-serif',
              }
style_header = {'textAlign': 'center',
                'padding-left': '20px',
                'backgroundColor': 'white',
                'fontWeight': 'bold'}
style_data_conditional = [{'if': {'row_index': 'odd'},
                           'backgroundColor': 'rgb(248, 248, 248)'}]
# fixed_columns = {'headers': True, 'data': 0}

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
                style={'width': '100%', 'padding': '20px', 'justify-content': 'center', 'display': 'flex',
                       'align-items': 'center'},
                id='answers_list',
                children=[
                    dbc.Card(color='dark', outline=True,
                             children=[
                                 dbc.CardHeader([
                                     html.H4('Results')
                                 ]),
                                 dbc.CardBody([
                                     dash_table.DataTable(
                                         id='answers_table',
                                         columns=[{"name": i, "id": i} for i in
                                                  ['Answer', 'Probability', 'Context', 'Article']],
                                         style_table=style_table,
                                         style_cell=style_cell,
                                         style_as_list_view=True,
                                         style_header=style_header,
                                         style_data_conditional=style_data_conditional,
                                         # fixed_columns=fixed_columns,
                                         row_selectable='single',
                                     )
                                 ])
                             ])
                ]),
            html.Div(
                style={'justify-content': 'center', 'display': 'flex', 'align-items': 'end', 'padding': '20px'},
                id='feedback_div',
                children=[
                    dcc.Input(id='suggestion_box', placeholder='Type your feedback here'),
                    dcc.Input(id='correct_answer',
                              placeholder='If none of the answers are accurate, please type your answer here'),
                    html.Button('Submit Feedback', id='feedback_submit_btn', )

                ]
            )
        ], style={'width': '100%', 'padding': '20px'}
    )])


def is_triggered(id):
    ctx = dash.callback_context
    element_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if element_id == id:
        return True
    else:
        return False


@app.callback(Output('answers_table', 'data'),
              [Input('question_box', 'value'),
               Input('submit_question', 'n_clicks')],
              [State('answers_table', 'data')])
def get_answer(question, n_clicks, data):
    print("in callback")
    if is_triggered('submit_question'):
        prediction = finder.get_answers(question=question,
                                        top_k_retriever=5,
                                        top_k_reader=5)

        prediction = [{'Answer': ans['answer'],
                       'Probability': "{:10.2f}".format(ans['probability']),
                       'Context': ans['context'],
                       'Article': 'https://pubmed.ncbi.nlm.nih.gov/' + ans['meta']['pmid']}
                      for ans in prediction['answers']]
        return prediction


@app.callback(Output('feedback_div', 'children'),
              [Input('question_box', 'value'),
               Input('suggestion_box', 'value'),
               Input('correct_answer', 'value'),
               Input('feedback_submit_btn', 'n_clicks'),
               Input('answers_table', 'selected_rows')],
              [State('answers_table', 'data'), ])
def get_feedback(question, feedback, user_answer, n_clicks, selected_rows, data):
    if n_clicks > 0 and is_triggered('feedback_submit_btn'):
        answers = []
        for d in data:
            answers.append(d['Answer'])
        if len(selected_rows) != 0:
            correct_answer = data[selected_rows[0]]['Answer']
            correct_context = data[selected_rows[0]]['Context']
        else:
            correct_answer = user_answer
            correct_context = user_answer
        conn, cur = get_new_db_connection()
        cur.execute(
            '''INSERT INTO feedback(question, answer_one, answer_two, answer_three, answer_four, answer_five, suggestions, correct_answer, correct_context)
             VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
            (question, answers[0], answers[1], answers[2], answers[3], answers[4], feedback, correct_answer,
             correct_context)
        )
        conn.commit()
        conn.close()
        return [html.P('Thanks for the feedback')]


if __name__ == '__main__':
    app.run_server(host='0.0.0.0',
                   port=80,
                   debug=False,
                   # ssl_context=('cert.pem', 'key.pem')
                   )
