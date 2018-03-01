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
    folkrnn.fieldStartABC = document.getElementById("id_start_abc");
    folkrnn.composeButton = document.getElementById("compose_button");
    
    folkrnn.div_about = document.getElementById("header");
    folkrnn.div_tune = document.getElementById("tune");
    
    folkrnn.updateKeyMeter();
    
    folkrnn.fieldModel.addEventListener("change", folkrnn.updateKeyMeter);
    
    folkrnn.fieldStartABC.addEventListener("input", folkrnn.validateStartABC);
    
    folkrnn.composeButton.addEventListener("click", folkrnn.generateRequest);
    
    folkrnn.div_tune.setAttribute('style', 'display: none');
    
    folkrnn.websocketConnect();
};

folkrnn.tuneManager = {
    'tune_ids': [],
    'add_tune': function (tune_id) {
        "use strict";
        folkrnn.tuneManager.tune_ids.unshift(tune_id);
        
        // Temp while we're single-tune only
        while (folkrnn.tuneManager.tune_ids.length > 1)
            folkrnn.tuneManager.remove_tune(folkrnn.tuneManager.tune_ids[folkrnn.tuneManager.tune_ids.length-1]);
        
        folkrnn.websocketSend({
                    command: "register_for_tune", 
                    tune_id: tune_id
                    });
        
        folkrnn.div_about.setAttribute('style', 'display: none');
        folkrnn.div_tune.removeAttribute('style');
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
        folkrnn.updateTuneDiv(folkrnn.emptyTune);
        folkrnn.clearABCJS()
        
        if (folkrnn.tuneManager.tune_ids.length == 0) {
            folkrnn.div_tune.setAttribute('style', 'display: none');
            folkrnn.div_about.removeAttribute('style');
        } 
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
    valid = valid && folkrnn.fieldStartABC.reportValidity();
    if (valid) {
        const formData = {};
        formData.model = folkrnn.fieldModel.value;
        formData.temp = folkrnn.fieldTemp.value;
        formData.seed = folkrnn.fieldSeed.value;
        formData.key = folkrnn.fieldKey.value;
        formData.meter = folkrnn.fieldMeter.value;
        formData.start_abc = folkrnn.parseABC(folkrnn.fieldStartABC.value).tokens.join(' ');
        
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

folkrnn.clearABCJS = function() {
    "use strict";
    delete folkrnn.abcEditor;
    document.getElementById("notation").innerHTML="";
    document.getElementById("midi").innerHTML="";
    document.getElementById("midi-download").innerHTML="";
}

folkrnn.validateStartABC = function() {
    "use strict";
    const abc = folkrnn.fieldStartABC.value;
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

folkrnn.updateTuneDiv = function(tune) {
    const el_abc = document.getElementById("abc");
    const el_model = document.getElementById("rnn_model_name");
    const el_seed = document.getElementById("seed");
    const el_temp = document.getElementById("temp");
    const el_prime_tokens = document.getElementById("prime_tokens");
    const el_requested = document.getElementById("requested");
    const el_generated = document.getElementById("generated");
    const el_archive_form = document.getElementById("archive_form");
    const el_archive_title = document.getElementById("id_title");
    
    el_abc.innerHTML = tune.abc;
    el_abc.setAttribute('rows', tune.abc.split(/\r\n|\r|\n/).length - 1);
    el_model.innerHTML = tune.rnn_model_name;
    el_seed.innerHTML = tune.seed;
    el_temp.innerHTML = tune.temp;
    el_prime_tokens.innerHTML = tune.prime_tokens;
    el_requested.innerHTML = tune.requested;
    el_generated.innerHTML = tune.rnn_finished;
    if (tune.rnn_finished) {
        el_generated.innerHTML = new Date(tune.rnn_finished).toLocaleString();
        el_requested.parentNode.setAttribute('style', 'display: none');
        el_generated.parentNode.removeAttribute('style');
        
        el_archive_title.value = tune.title;
        el_archive_form.setAttribute('action', tune.archive_url);
        el_archive_form.removeAttribute('style');
    } else {
        el_requested.innerHTML = new Date(tune.requested).toLocaleString();
        el_requested.parentNode.removeAttribute('style');
        el_generated.parentNode.setAttribute('style', 'display: none');
        
        el_archive_form.setAttribute('style', 'display: none');
    }
}