/* jshint esversion: 6, strict: true, undef: true, unused: true, varstmt: true */
/* globals folkrnn, ABCJS */

if (typeof folkrnn == 'undefined')
    folkrnn = {};

folkrnn.initialise = function() {
    "use strict";
    folkrnn.fieldModel = document.getElementById("id_model");
    folkrnn.fieldTemp = document.getElementById("id_temp");
    folkrnn.fieldSeed = document.getElementById("id_seed");
    folkrnn.fieldKey = document.getElementById("id_key");
    folkrnn.fieldMeter = document.getElementById("id_meter");
    folkrnn.fieldTokens = document.getElementById("id_prime_tokens");
    folkrnn.composeButton = document.getElementById("compose_button");
    
    folkrnn.updateKeyMeter();
    
    folkrnn.fieldModel.addEventListener("change", folkrnn.updateKeyMeter);
    
    folkrnn.fieldTokens.addEventListener("input", folkrnn.validateStartABC);
    
    folkrnn.composeButton.addEventListener("click", folkrnn.generateRequest);
    
    folkrnn.initABCJS();
    
    folkrnn.websocketConnect();
};

folkrnn.tuneManager = {
    'tune_ids': [],
    'add_tune': function (tune_id) {
        "use strict";
        folkrnn.tuneManager.tune_ids.unshift(tune_id);
        
        // Temp while we're single-tune only
        while (folkrnn.tuneManager.tune_ids.length > 1)
            folkrnn.tuneManager.remove_tune(folkrnn.tuneManager.tune_ids[folkrnn.tuneManager.tune_ids.length-1])
        
        folkrnn.websocketSend({
                    command: "register_for_tune", 
                    tune_id: tune_id
                    });
        // Add to DOM...
        const el_tune = document.getElementById("tune");
        const el_abc = document.getElementById("abc");
        el_abc.innerHTML = "Waiting for folk-rnn..."
    },
    'remove_tune': function (tune_id) {
        "use strict";
        const index = folkrnn.tuneManager.tune_ids.indexOf(tune_id);
        if (index > -1)
            folkrnn.tuneManager.tune_ids.splice(index, 1);
        folkrnn.websocketSend({
                    command: "unregister_for_tune", 
                    tune_id: tune_id
                    });
        // Remove from DOM...
    }
};

folkrnn.generateRequest = function () {
    "use strict";
    let valid = true;
    valid = valid && folkrnn.fieldModel.reportValidity();
    valid = valid && folkrnn.fieldTemp.reportValidity();
    valid = valid && folkrnn.fieldSeed.reportValidity();
    valid = valid && folkrnn.fieldKey.reportValidity();
    valid = valid && folkrnn.fieldMeter.reportValidity();
    valid = valid && folkrnn.fieldTokens.reportValidity();
    if (valid) {
        const formData = {};
        formData.model = folkrnn.fieldModel.value;
        formData.temp = folkrnn.fieldTemp.value;
        formData.seed = folkrnn.fieldSeed.value;
        formData.key = folkrnn.fieldKey.value;
        formData.meter = folkrnn.fieldMeter.value;
        formData.startABC = folkrnn.fieldTokens.value;
        
        folkrnn.websocketSend({
                    'command': 'compose',
                    'data': formData,
        });
    }
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

