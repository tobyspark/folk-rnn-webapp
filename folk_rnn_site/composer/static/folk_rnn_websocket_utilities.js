/* jshint esversion: 6, strict: true, undef: true, unused: true, varstmt: true */
/* globals folkrnn, channels */

if (typeof folkrnn == 'undefined')
    folkrnn = {};

folkrnn.websocketConnect = function() {
    "use strict";
    const ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    const ws_path = ws_scheme + '://' + window.location.host;

    folkrnn.socket = new channels.WebSocketBridge();
    folkrnn.socket.connect(ws_path);
    folkrnn.socket.listen(folkrnn.websocketReceive);

    folkrnn.socket.socket.addEventListener('open', function() {
        console.log("Connected to WebSocket");
        folkrnn.websocketSend();
    });
};

folkrnn.websocketSend = function(json) {
    "use strict";
    if ('queue' in folkrnn.websocketSend === false)
        folkrnn.websocketSend.queue = [];
    if (json)
        folkrnn.websocketSend.queue.push(json);

    // CONNECTING	0	The connection is not yet open.
    // OPEN	        1	The connection is open and ready to communicate.
    // CLOSING	    2	The connection is in the process of closing.
    // CLOSED	    3	The connection is closed or couldn't be opened.
    while (folkrnn.socket.socket.readyState === 1 && folkrnn.websocketSend.queue.length > 0) {
        folkrnn.socket.send(folkrnn.websocketSend.queue.shift());
    }
};

folkrnn.websocketReceive = function(action, stream) {
    "use strict";
    
    const el_abc = document.getElementById("abc");
    if ('bars' in folkrnn.websocketReceive === false) {
        folkrnn.websocketReceive.bars = 0;
    }
    if (action.command == "add_tune") {
        folkrnn.tuneManager.add_tune(action.tune_id);
    }
    if (action.command == "generation_status") {
        if (action.status == "start") {
            folkrnn.updateTuneDiv(action.tune)
        }
        
        if (action.status == "finish") {
            folkrnn.updateTuneDiv(action.tune)
            folkrnn.initABCJS();
        }
    }
    if (action.command == "add_token") {
        if (el_abc.innerHTML == folkrnn.emptyTune.abc) {
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
        el_abc.setAttribute('rows', el_abc.innerHTML.split(/\r\n|\r|\n/).length);
    }
};
