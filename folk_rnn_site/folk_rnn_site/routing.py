from channels.routing import ProtocolTypeRouter, ChannelNameRouter

from composer import consumers

application = ProtocolTypeRouter({
    # Empty for now (http->django views is added by default)
    'websocket': consumers.ComposerConsumer,
    'channel': ChannelNameRouter({
        'folk_rnn': consumers.FolkRNNConsumer,
        })
})
