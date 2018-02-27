var fieldModel = document.getElementById("id_model");
var fieldKey = document.getElementById("id_key");
var fieldMeter = document.getElementById("id_meter");
var fieldTokens = document.getElementById("id_prime_tokens");

window.onLoad = rnnUpdateKeyMeter();
fieldModel.addEventListener("change", rnnUpdateKeyMeter);

fieldTokens.addEventListener("input", function() {
    const abc = fieldTokens.value
    const abcParsed = rnnParseABC(abc)
    this.setCustomValidity('');
    
    if (abcParsed['invalidIndexes'].length > 0 ) {
        let markedUpABC = ""
        let pos = 0
        for (const invalidIndex of abcParsed['invalidIndexes']) {
            markedUpABC += abc.slice(pos, invalidIndex)
            markedUpABC += ' >'
            markedUpABC += abc.slice(invalidIndex, invalidIndex+1)
            markedUpABC += '< '
            pos = invalidIndex+1
        }
        markedUpABC += abc.slice(pos)
        this.setCustomValidity('Invalid: ' + markedUpABC);
    } 
    
    const invalidTokens = rnnInvalidTokens(abcParsed['tokens'], fieldModel.value)
    if (invalidTokens.length == 1 ) {
        this.setCustomValidity('Invalid token: ' + invalidTokens[0]);
    } else if (invalidTokens.length > 1 ) {
        this.setCustomValidity('Invalid tokens: ' + invalidTokens.join(', '));
    }
});

function rnnUpdateKeyMeter() {
    while (fieldMeter.lastChild) {
        fieldMeter.removeChild(fieldMeter.lastChild);
    }
    for (const m of rnnModels[fieldModel.value]['header_m_tokens']) {
        fieldMeter.appendChild(new Option(m.slice(2), m));
        if (m == 'M:4/4') {
            fieldMeter.lastChild.selected = true;
        }
    }

    
    while (fieldKey.lastChild) {
        fieldKey.removeChild(fieldKey.lastChild);
    }
    for (const k of rnnModels[fieldModel.value]['header_k_tokens']) {
        key_map = {
            'K:Cmaj': 'C Major',		
            'K:Cmin': 'C Minor',		
            'K:Cdor': 'C Dorian',		
            'K:Cmix': 'C Mixolydian',
        }
        fieldKey.appendChild(new Option(key_map[k], k));
        if (k == 'K:Cmaj') {
            fieldKey.lastChild.selected = true;
        }
    }
}

function rnnWebsocketConnect(tune_id) {
    const ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    const ws_path = ws_scheme + '://' + window.location.host;
    
    const webSocketBridge = new channels.WebSocketBridge();
    webSocketBridge.connect(ws_path);
    webSocketBridge.listen(rnnWebsocketReceive);
    
    webSocketBridge.socket.addEventListener('open', function() {
        console.log("Connected to WebSocket");
        webSocketBridge.send({
                    command: "register_for_tune", 
                    tune_id: tune_id
                    });
    })
}

function rnnWebsocketReceive(action, stream) {
    const el_abc = document.getElementById("abc");
    if( typeof rnnWebsocketReceive.bars == 'undefined' ) {
        rnnWebsocketReceive.bars = 0;
    }
    if (action["command"] == "generation_status") {
        if (action["status"] == "complete") {
            window.location.reload()
        }
    }
    if (action["command"] == "add_token") {
        if (el_abc.innerHTML == "Waiting for folk-rnn...") {
            el_abc.innerHTML = ""
        }
        if (action["token"] == "|") {
            rnnWebsocketReceive.bars += 1;
            if (rnnWebsocketReceive.bars > 3) {
                rnnWebsocketReceive.bars = 0;
                el_abc.innerHTML += '\n';
            }
        }
        el_abc.innerHTML += action["token"]
    }
}