import pytest # Channels consumer require tests to be run with `pytest`
import json
from channels.testing import ApplicationCommunicator, WebsocketCommunicator
from channels.layers import get_channel_layer
from datetime import timedelta

from composer import TUNE_PATH
from composer.consumers import FolkRNNConsumer, ComposerConsumer
from composer.models import RNNTune
from folk_rnn_site.tests import FOLKRNN_IN, FOLKRNN_OUT, FOLKRNN_OUT_RAW

@pytest.mark.django_db(transaction=True)  
@pytest.mark.asyncio
async def test_folkrnn_consumer():
    tune = RNNTune.objects.create(**FOLKRNN_IN)

    scope = {'type': 'channel', 'channel': 'folk_rnn'}
    communicator = ApplicationCommunicator(FolkRNNConsumer, scope)

    await communicator.send_input({
        'type': 'folkrnn.generate', 
        'id': tune.id,
    })
    await communicator.wait(timeout=5)

    with open(TUNE_PATH + f'/with_repeats_{tune.id}_raw') as f:
        assert f.read() == FOLKRNN_OUT_RAW

    correct_out = FOLKRNN_OUT\
                    .replace('X:1', f'X:{tune.id}')\
                    .replace('№1', f'№{tune.id}')
    with open(TUNE_PATH + f'/with_repeats_{tune.id}') as f:
        assert f.read() == correct_out

    tune = RNNTune.objects.last()
    assert tune.rnn_started is not None
    assert tune.rnn_started is not None
    assert tune.rnn_started < tune.rnn_finished
    assert tune.rnn_finished - tune.rnn_started < timedelta(seconds=5)
    assert tune.abc == correct_out

@pytest.mark.asyncio
async def test_generation_status():
    communicator = WebsocketCommunicator(ComposerConsumer, '/')
    connected, subprotocol = await communicator.connect()
    assert connected
    
    # Register. This should add the consumer to the tune groups
    await communicator.send_to(json.dumps({
        'command': 'register_for_tune',
        'tune_id': 1,
        }))
    await communicator.send_to(json.dumps({
        'command': 'register_for_tune',
        'tune_id': 2,
        }))
    
    # This sleep is critical. The design of the consumer means the add_token command
    # will have all pending abc, but testing output based on the non-deterministic point 
    # of first receiving the group messages muddies the procedural test logic.
    import asyncio; await asyncio.sleep(3)
    
    channel_layer = get_channel_layer()
     
    # Send the consumer complete ABC via tune group. 
    # Check it gets back incremental ABC.
    # And do this for two tunes, to check isolation.
    await channel_layer.group_send('tune_1', {
        'type': 'generation_status',
        'status': 'new_abc',
        'abc': 'a b c',
        'tune_id': 1,
        })
    response = await communicator.receive_from()
    assert json.loads(response) == {
        'command': 'add_token',
        'token': 'a b c',
        'tune_id': 1,
    }
    
    await channel_layer.group_send('tune_2', {
        'type': 'generation_status',
        'status': 'new_abc',
        'abc': 'A B C',
        'tune_id': 2,
        })
    response = await communicator.receive_from()
    assert json.loads(response) == {
        'command': 'add_token',
        'token': 'A B C',
        'tune_id': 2,
    }
    
    await channel_layer.group_send('tune_1', {
        'type': 'generation_status',
        'status': 'new_abc',
        'abc': 'a b c d e f',
        'tune_id': 1,
        })
    response = await communicator.receive_from()
    assert json.loads(response) == {
        'command': 'add_token',
        'token': ' d e f',
        'tune_id': 1,
    }
    
    await channel_layer.group_send('tune_2', {
        'type': 'generation_status',
        'status': 'new_abc',
        'abc': 'A B C D E F',
        'tune_id': 2,
        })
    response = await communicator.receive_from()
    assert json.loads(response) == {
        'command': 'add_token',
        'token': ' D E F',
        'tune_id': 2,
    }
    
    await communicator.disconnect()
    
@pytest.mark.django_db()    
@pytest.mark.asyncio
async def test_receive_json_compose_valid():
    communicator = WebsocketCommunicator(ComposerConsumer, '/')
    connected, subprotocol = await communicator.connect()
    assert connected
    
    content = {
        'command': 'compose',
        'data': {
            'model': 'with_repeats.pickle',
            'temp': 0.1,
            'seed': 123,
            'meter': 'M:4/4',
            'key': 'K:Cmaj',
            'start_abc': 'a b c',
            }
    }
    await communicator.send_to(json.dumps(content))
    response = await communicator.receive_from()
    
    tune = RNNTune.objects.last()
    assert json.loads(response) == {
        'command': 'add_tune',
        'tune_id': tune.id
    }
    assert tune.rnn_model_name == 'with_repeats.pickle'
    assert tune.temp == 0.1
    assert tune.seed == 123
    assert tune.prime_tokens == 'M:4/4 K:Cmaj a b c'
    await communicator.disconnect()
    
@pytest.mark.django_db()    
@pytest.mark.asyncio
async def test_receive_json_compose_invalid():
    communicator = WebsocketCommunicator(ComposerConsumer, '/')
    connected, subprotocol = await communicator.connect()
    assert connected
    
    count_before = RNNTune.objects.count()

    content = {
        'command': 'compose',
        'data': {
            'model': 'with_repeats.pickle',
            'temp': 0.1,
            'seed': -1,
            'meter': 'M:4/4',
            'key': 'K:Cmaj',
            'start_abc': 'slarty bartfast',
            }
    }
    await communicator.send_to(json.dumps(content))
    assert count_before == RNNTune.objects.count()

    content = {
        'command': 'compose',
        'data': {
            'model': 'with_repeats.pickle',
            'temp': 0.1,
            'seed': -1,
            'meter': 'M:4/4',
            'key': 'K:Cmaj',
            'start_abc': 'a b c',
            }
    }
    await communicator.send_to(json.dumps(content))
    assert count_before == RNNTune.objects.count()
    
    content = {
        'command': 'compose',
        'data': {
            'model': 'with_repeats.pickle',
            'temp': 11,
            'seed': 123,
            'meter': 'M:4/4',
            'key': 'K:Cmaj',
            'start_abc': 'a b c',
            }
    }
    await communicator.send_to(json.dumps(content))
    assert count_before == RNNTune.objects.count()
    
    await communicator.disconnect()
    
