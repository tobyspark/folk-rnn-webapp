from channels.routing import route

from composer import consumers

channel_routing = [
    route('folk_rnn', consumers.folk_rnn_task),
]
