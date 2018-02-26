import pytest # Channels consumer require tests to be run with `pytest`
from channels.testing import ApplicationCommunicator
from datetime import timedelta

from folk_rnn_site.tests import FOLKRNN_IN, FOLKRNN_OUT, FOLKRNN_OUT_RAW

@pytest.mark.django_db(transaction=True)  
@pytest.mark.asyncio
async def test_folkrnn_consumer():
    RNNTune.objects.create(**FOLKRNN_IN)
    assert RNNTune.objects.count() == 1

    scope = {"type": "channel", 'channel': 'folk_rnn'}
    communicator = ApplicationCommunicator(FolkRNNConsumer, scope)

    await communicator.send_input({
        'type': 'folkrnn.generate', 
        'id': 1,
    })
    await communicator.wait(timeout=3)

    with open(TUNE_PATH + '/with_repeats_1_raw') as f:
        assert f.read() == FOLKRNN_OUT_RAW

    with open(TUNE_PATH + '/with_repeats_1') as f:
        assert f.read() == FOLKRNN_OUT

    tune = RNNTune.objects.first()
    assert tune.rnn_started is not None
    assert tune.rnn_started is not None
    assert tune.rnn_started < tune.rnn_finished
    assert tune.rnn_finished - tune.rnn_started < timedelta(seconds=5)
    assert tune.abc == FOLKRNN_OUT