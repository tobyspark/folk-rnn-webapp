/* jshint esversion: 6, strict: true, undef: true, unused: true, varstmt: true */
/* globals folkrnn, channels */

if (typeof folkrnn == 'undefined')
    folkrnn = {};

folkrnn.websocketSend = function(json) {
    "use strict";
    // Connect on-demand
    // Don't send before connection is ready
    
    // Connect if we haven't already
    if ('socket' in folkrnn === false) {
        const ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
        const ws_session_path = ('session' in folkrnn) ? '/' + folkrnn.session : "";
        const ws_path = ws_scheme + '://' + window.location.host + ws_session_path;
        
        folkrnn.socket = new channels.WebSocketBridge();
        folkrnn.socket.connect(ws_path);
        folkrnn.socket.listen(folkrnn.websocketReceive);
        
        // Empty queue once connected
        folkrnn.socket.socket.addEventListener('open', function() {
            console.log("Connected to WebSocket");
            folkrnn.websocketSend();
        });
    }

    // Enqueue the message
    if ('queue' in folkrnn.websocketSend === false)
        folkrnn.websocketSend.queue = [];
    if (json)
        folkrnn.websocketSend.queue.push(json);
        
    // Send the queue of messages if we can
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
    if (action.command == "set_session") {
        folkrnn.session = action.session_id;
        folkrnn.stateManager.updateState(false);
    }
    if (action.command == "add_tune") {
        folkrnn.stateManager.addTune(action.tune.id);
        folkrnn.updateTuneDiv(action.tune);
    }
    if (action.command == "generation_status") {
        if (action.status == "start") {
            folkrnn.updateTuneDiv(action.tune);
        }   
        if (action.status == "finish") {
            folkrnn.updateTuneDiv(action.tune);
            folkrnn.tuneManager.enableABCJS(action.tune.id);
        }
    }
    if (action.command == "add_token") {
        const el_tune = folkrnn.tuneManager.tuneDiv(action.tune_id);
        const el_abc = el_tune.querySelector('#abc-'+action.tune_id);
        if (el_abc.innerHTML == folkrnn.waitingABC)
            el_abc.innerHTML = "";
        el_abc.innerHTML += action.token;
        if (action.token.includes("|")) 
            if (el_abc.innerHTML.split("|").length % 5 === 0)
                el_abc.innerHTML += '\n';
        el_abc.setAttribute('rows', el_abc.innerHTML.split(/\r\n|\r|\n/).length);
    }
};
