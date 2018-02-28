/* jshint esversion: 6, strict: true, undef: true, unused: true, varstmt: true */
/* globals folkrnn, channels, ABCJS */

if (typeof folkrnn == 'undefined')
    folkrnn = {};

folkrnn.initialise = function() {
    "use strict";
    folkrnn.fieldModel = document.getElementById("id_model");
    folkrnn.fieldKey = document.getElementById("id_key");
    folkrnn.fieldMeter = document.getElementById("id_meter");
    folkrnn.fieldTokens = document.getElementById("id_prime_tokens");
    
    folkrnn.updateKeyMeter();
    
    folkrnn.fieldModel.addEventListener("change", folkrnn.updateKeyMeter);
    
    folkrnn.fieldTokens.addEventListener("input", folkrnn.validateStartABC);
    
    folkrnn.fieldTokens.addEventListener("change", function() {
        this.value = folkrnn.parseABC(this.value).tokens.join(' ');
        console.log(this.value);
    });
    
    folkrnn.initABCJS();
};

folkrnn.abcjsModelChangedCallback = function (abcelem) {
    "use strict";
    console.log('abcjsModelChangedCallback');
    console.log(abcelem);
};

folkrnn.abcjsSelectionCallback = function (abcelem) {
    "use strict";
    console.log('abcjsSelectionCallback');
    console.log(abcelem);
};

folkrnn.initABCJS = function() {
    "use strict";
    folkrnn.abcEditor = new ABCJS.Editor("abc", { paper_id: "notation",
        generate_midi: true,
        midi_id:"midi",
        midi_download_id: "midi-download",
        generate_warnings: true,
        warnings_id:"warnings",
        midi_options: {
            generateDownload: true,
            downloadLabel:"Download MIDI"
        },
        render_options: {
            paddingleft:0,
            paddingright:0,
            responsive: "resize",
            listener: { 
                highlight: folkrnn.abcjsSelectionCallback,
                modelChanged:  folkrnn.abcjsModelChangedCallback
                }
        }
    });
};

folkrnn.validateStartABC = function() {
    "use strict";
    const abc = folkrnn.fieldTokens.value;
    const abcParsed = folkrnn.parseABC(abc);

    this.setCustomValidity('');

    if (abcParsed.invalidIndexes.length > 0 ) {
        let markedUpABC = "";
        let pos = 0;
        for (const invalidIndex of abcParsed.invalidIndexes) {
            markedUpABC += abc.slice(pos, invalidIndex);
            markedUpABC += ' >';
            markedUpABC += abc.slice(invalidIndex, invalidIndex+1);
            markedUpABC += '< ';
            pos = invalidIndex+1;
        }
        markedUpABC += abc.slice(pos);
        this.setCustomValidity('Invalid: ' + markedUpABC);
    } 

    const invalidTokens = folkrnn.invalidTokens(abcParsed.tokens, folkrnn.fieldModel.value);
    if (invalidTokens.length == 1 ) {
        this.setCustomValidity('Invalid token: ' + invalidTokens[0]);
    } else if (invalidTokens.length > 1 ) {
        this.setCustomValidity('Invalid tokens: ' + invalidTokens.join(', '));
    } 
};

folkrnn.updateKeyMeter = function() {
    "use strict";
    while (folkrnn.fieldMeter.lastChild) {
        folkrnn.fieldMeter.removeChild(folkrnn.fieldMeter.lastChild);
    }
    for (const m of folkrnn.models[folkrnn.fieldModel.value].header_m_tokens) {
        folkrnn.fieldMeter.appendChild(new Option(m.slice(2), m));
        if (m == 'M:4/4') {
            folkrnn.fieldMeter.lastChild.selected = true;
        }
    }


    while (folkrnn.fieldKey.lastChild) {
        folkrnn.fieldKey.removeChild(folkrnn.fieldKey.lastChild);
    }
    for (const k of folkrnn.models[folkrnn.fieldModel.value].header_k_tokens) {
        let key_map = {
            'K:Cmaj': 'C Major',		
            'K:Cmin': 'C Minor',		
            'K:Cdor': 'C Dorian',		
            'K:Cmix': 'C Mixolydian',
        };
        folkrnn.fieldKey.appendChild(new Option(key_map[k], k));
        if (k == 'K:Cmaj') {
            folkrnn.fieldKey.lastChild.selected = true;
        }
    }
};

folkrnn.websocketConnect = function(tune_id) {
    "use strict";
    const ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    const ws_path = ws_scheme + '://' + window.location.host;

    const webSocketBridge = new channels.WebSocketBridge();
    webSocketBridge.connect(ws_path);
    webSocketBridge.listen(folkrnn.websocketReceive);

    webSocketBridge.socket.addEventListener('open', function() {
        console.log("Connected to WebSocket");
        webSocketBridge.send({
                    command: "register_for_tune", 
                    tune_id: tune_id
                    });
    });
};

folkrnn.websocketReceive = function(action, stream) {
    "use strict";
    const el_abc = document.getElementById("abc");
    if ('bars' in folkrnn.websocketReceive === false) {
        folkrnn.websocketReceive.bars = 0;
    }
    if (action.command == "generation_status") {
        if (action.status == "complete") {
            window.location.reload();
        }
    }
    if (action.command == "add_token") {
        if (el_abc.innerHTML == "Waiting for folk-rnn...") {
            el_abc.innerHTML = "";
        }
        if (action.token == "|") {
            folkrnn.websocketReceive.bars += 1;
            if (folkrnn.websocketReceive.bars > 3) {
                folkrnn.websocketReceive.bars = 0;
                el_abc.innerHTML += '\n';
            }
        }
        el_abc.innerHTML += action.token;
    }
};
