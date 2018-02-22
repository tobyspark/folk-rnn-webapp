from channels.routing import ProtocolTypeRouter, ChannelNameRouter

from composer import consumers

application = ProtocolTypeRouter({
    # Empty for now (http->django views is added by default)
    'channel': ChannelNameRouter({
        'folk_rnn': consumers.FolkRNNConsumer,
        })
})
