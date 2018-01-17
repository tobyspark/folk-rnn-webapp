# folk_rnn_site cannot rely on being on the same server as folk_rnn_task.
# therefore no e.g. MODEL_PATH as per folk_rnn_task
# instead have token set loaded into folk_rnn_site somehow
# currently, manual process
#
# python (2.7)
#
# f = open('/var/opt/folk_rnn_task/models/test_model.pickle_2', 'r')
# d = pickle.load(f)
# d['token2idx'].keys()
#
# ...and copy and paste in, using set literal {x, y,...} notation

models = [
    { 
        'display_name': 'default',
        'file_name': 'test_model.pickle',
        'tokens': {"d'", '=A,', "^c'", '=e', '=d', '=g', '=f', '=a', '=c', '=b', '_G', '_E', '_D', '_C', '_B', '_A', '2<', '2>', '=E', '=D', '_B,', '=F', '=A', '4', '=C', '=B', '_g', '8', '_e', '_d', '_c', '<', '_a', '(9', '|2', 'D', '|1', '(2', '(3', '|:', '(7', '(4', '(5', ':|', 'M:3/4', '3/2', '3/4', "=f'", '2', 'd', '_E,', 'B,', 'f', '|', '^A,', "b'", "_e'", 'M:9/8', 'E,', '</s>', '3', '7', '^F,', '=G,', 'C', 'G', "e'", "_d'", "^f'", '[', 'c', '_A,', 'g', '^G,', '=F,', 'K:Cmin', 'K:Cmix', "=c'", 'C,', '<s>', '^D', '=G', 'M:12/8', '6', '=E,', 'K:Cmaj', '>', 'B', 'F', "c'", '^c', 'e', '5/2', 'b', '16', "=e'", '_b', 'z', 'F,', '/2>', '/2<', "f'", 'M:6/8', '4>', 'M:4/4', 'A,', 'M:2/4', '=C,', '5', '9', 'M:3/2', 'K:Cdor', 'A', 'E', "a'", '(6', '^A', '^C', ']', '^F', '^G', 'a', "g'", 'D,', '/4', '^C,', '^d', '7/2', '=B,', 'G,', '/8', '^a', '12', '/3', '/2', '^f', '^g'},
    },
    ]

def choices():
    return ((x['file_name'], x['display_name']) for x in models)

def validate_tokens(tokens, model_file_name=None):
    model = models[0]
    if model_file_name is not None:
        for candidate in models:
            if candidate['file_name'] == model_file_name:
                model = candidate
    return all(x in model['tokens'] for x in tokens)
