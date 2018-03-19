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
    
    folkrnn.fieldModel.addEventListener("change", function() {
        folkrnn.updateKeyMeter();
        folkrnn.stateManager.updateState(false);
    });
    folkrnn.fieldTemp.addEventListener("change", function() {
        folkrnn.stateManager.updateState(false);
    });
    folkrnn.fieldSeed.addEventListener("change", function() {
        folkrnn.stateManager.updateState(false);
    });
    folkrnn.fieldKey.addEventListener("change", function() {
        folkrnn.stateManager.updateState(false);
    });
    folkrnn.fieldMeter.addEventListener("change", function() {
        folkrnn.stateManager.updateState(false);
    }); 
    folkrnn.fieldStartABC.addEventListener("input", function() {
        folkrnn.validateStartABC();
        folkrnn.stateManager.updateState(false);
    });
    
    folkrnn.composeButton.addEventListener("click", folkrnn.generateRequest);
    
    folkrnn.div_tune.setAttribute('hidden', '');
    
    folkrnn.stateManager.applyState(window.history.state);
    window.addEventListener('popstate', function(event) {
        folkrnn.stateManager.applyState(event.state);
    });
    window.addEventListener('unload', function(event) {
      folkrnn.stateManager.updateState(false);
    });
};

folkrnn.stateManager = {
    'addTune': function(tune_id) {
        "use strict";
        // Hide about div, now there is a tune
        folkrnn.div_about.setAttribute('hidden', '');
        
        // Add tune to page
        folkrnn.tuneManager.addTune(tune_id);
        
        // Register new URL
        folkrnn.stateManager.updateState(true);
    },
    'removeTune': function(tune_id) {
        "use strict";
        // Remove tune from page
        folkrnn.tuneManager.removeTune(tune_id);
        
        // Register new URL
        folkrnn.stateManager.updateState(true);
        
        // Reveal about div, if there are no tunes
        if (Object.keys(folkrnn.tuneManager.tunes).length === 0) {
            folkrnn.div_about.removeAttribute('hidden');
        }
    },
    'updateState': function(newState) {
        "use strict";
        const state = {
            'model': folkrnn.fieldModel.value,
            'temp': folkrnn.fieldTemp.value,
            'seed': folkrnn.fieldSeed.value,
            'key': folkrnn.fieldKey.value,
            'meter': folkrnn.fieldMeter.value,
            'start_abc': folkrnn.fieldStartABC.value,
            'tunes': Object.keys(folkrnn.tuneManager.tunes),
        };
        if ('session' in folkrnn) state.session = folkrnn.session;
        const title = "";
        const tune_ids = Object.keys(folkrnn.tuneManager.tunes);
        const url = (tune_ids.length === 0) ? "/" : "/tune/" + Math.max(...tune_ids);
        if (newState)
            window.history.pushState(state, title, url);
        else
            window.history.replaceState(state, title, url);
        folkrnn.websocketSend({
                        command: "notification",
                        type: "state_change",
                        state: state,
                        url: url,
                    });
    },
    'applyState': function(state) {
        "use strict";
        if (!state) return;
        
        // Restore session id
        if ('session' in state) folkrnn.session = state.session;
        
        // Apply to composition UI
        folkrnn.utilities.setSelectByValue(folkrnn.fieldModel, state.model);
        folkrnn.fieldTemp.value = state.temp;
        folkrnn.fieldSeed.value = state.seed;
        folkrnn.utilities.setSelectByValue(folkrnn.fieldKey, state.key);
        folkrnn.utilities.setSelectByValue(folkrnn.fieldMeter, state.meter);
        folkrnn.fieldStartABC.value = state.start_abc;
        
        // Apply to tuneManager (i.e. sync tunes on page with state)
        for (const tune_id of state.tunes) {
            folkrnn.tuneManager.addTune(tune_id);
        }
        for (const tune_id of Object.keys(folkrnn.tuneManager.tunes)) {
            if (state.tunes.indexOf(tune_id) === -1)
                folkrnn.tuneManager.removeTune(tune_id);
        }
    },
};

folkrnn.tuneManager = {
    'tunes': {},
    'addTune': function (tune_id) {
        "use strict";
        if (tune_id in folkrnn.tuneManager.tunes) {
            console.log('Attempt to add tune already in tuneManager');
            return;
        }
        
        // Add tune to manager
        const div_tune_new = folkrnn.div_tune.cloneNode(true);
        div_tune_new.id = "tune_" + tune_id;
        div_tune_new.querySelector('#abc').id = 'abc-' + tune_id;
        div_tune_new.querySelector('#rnn_model_name').id = 'rnn_model_name-' + tune_id;
        div_tune_new.querySelector('#seed').id = 'seed-' + tune_id;
        div_tune_new.querySelector('#temp').id = 'temp-' + tune_id;
        div_tune_new.querySelector('#prime_tokens').id = 'prime_tokens-' + tune_id;
        div_tune_new.querySelector('#requested').id = 'requested-' + tune_id;
        div_tune_new.querySelector('#generated').id = 'generated-' + tune_id;
        div_tune_new.querySelector('#midi').id = 'midi-' + tune_id;
        div_tune_new.querySelector('#midi-download').id = 'midi-download-' + tune_id;
        div_tune_new.querySelector('#notation').id = 'notation-' + tune_id;
        div_tune_new.querySelector('#archive_form').id = 'archive_form-' + tune_id;
        div_tune_new.querySelector('#id_title').id = 'id_title-' + tune_id;
        div_tune_new.querySelector('#remove_button').addEventListener("click", function () {
            folkrnn.stateManager.removeTune(tune_id);
        });
        folkrnn.tuneManager.tunes[tune_id] = { 'div': div_tune_new };
        
        // Place on page
        folkrnn.div_tune.parentNode.insertBefore(div_tune_new, folkrnn.div_tune);
        div_tune_new.removeAttribute('hidden');
        div_tune_new.scrollIntoView();
        
        // Register for updates
        folkrnn.websocketSend({
                    command: "register_for_tune", 
                    tune_id: tune_id
                    });
    },
    'tuneDiv': function (tune_id) {
        "use strict";
        return folkrnn.tuneManager.tunes[tune_id].div;
    },
    'enableABCJS': function (tune_id) {
        "use strict";
        folkrnn.tuneManager.tunes[tune_id].abcjs = new ABCJS.Editor("abc-" + tune_id, { 
            paper_id: "notation-" + tune_id,
            generate_midi: true,
            midi_id:"midi-" + tune_id,
            midi_download_id: "midi-download-" + tune_id,
            generate_warnings: true,
            warnings_id:"warnings",
            midi_options: {
                generateDownload: true,
                downloadLabel:"Download MIDI",
                inlineControls: {
                    tempo: true,
                },
                //selectionToggle: true, // not yet implemented according to https://github.com/paulrosen/abcjs/blob/master/docs/api.md
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
        
        const midi_download_link = document.body.querySelector('#midi-download-' + tune_id + ' > div > a');
        midi_download_link.addEventListener('click', function() {
            folkrnn.websocketSend({
                command: "notification",
                type: "midi_download",
            });
        });
        const midi_play_button = document.body.querySelector('#midi-' + tune_id + ' > div > button.abcjs-midi-start.abcjs-btn');
        midi_play_button.addEventListener('click', function() {
            folkrnn.websocketSend({
                command: "notification",
                type: "midi_play",
            });
        });
    },
    'removeTune': function (tune_id) {
        "use strict";
        // Unregister for updates
        folkrnn.websocketSend({
                    command: "unregister_for_tune", 
                    tune_id: tune_id
                    });
        
        // Remove from page
        folkrnn.div_tune.parentNode.removeChild(folkrnn.tuneManager.tunes[tune_id].div);
        delete folkrnn.tuneManager.tunes[tune_id];
    },
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

folkrnn.validateStartABC = function() {
    "use strict";
    const abc = folkrnn.fieldStartABC.value;
    const abcParsed = folkrnn.parseABC(abc);

    folkrnn.fieldStartABC.setCustomValidity('');

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
        folkrnn.fieldStartABC.setCustomValidity('Invalid: ' + markedUpABC);
    } 

    const invalidTokens = folkrnn.invalidTokens(abcParsed.tokens, folkrnn.fieldModel.value);
    if (invalidTokens.length == 1 ) {
        folkrnn.fieldStartABC.setCustomValidity('Invalid token: ' + invalidTokens[0]);
    } else if (invalidTokens.length > 1 ) {
        folkrnn.fieldStartABC.setCustomValidity('Invalid tokens: ' + invalidTokens.join(', '));
    } 
};

folkrnn.updateKeyMeter = function() {
    "use strict";
    // Update key, meter options per new model's vocab
    
    // Keep selected value if possible
    const meter = folkrnn.fieldMeter.value;
    const key = folkrnn.fieldKey.value;

    // Set Meter options from model
    while (folkrnn.fieldMeter.lastChild) {
        folkrnn.fieldMeter.removeChild(folkrnn.fieldMeter.lastChild);
    }
    for (const m of folkrnn.models[folkrnn.fieldModel.value].header_m_tokens) {
        folkrnn.fieldMeter.appendChild(new Option(m.slice(2), m));
    }
    folkrnn.utilities.setSelectByValue(folkrnn.fieldMeter, meter, 'M:4/4');

    // Set Key options from model
    while (folkrnn.fieldKey.lastChild) {
        folkrnn.fieldKey.removeChild(folkrnn.fieldKey.lastChild);
    }
    let key_map = {
        'K:Cmaj': 'C Major',		
        'K:Cmin': 'C Minor',		
        'K:Cdor': 'C Dorian',		
        'K:Cmix': 'C Mixolydian',
    };
    for (const k of folkrnn.models[folkrnn.fieldModel.value].header_k_tokens) {
        folkrnn.fieldKey.appendChild(new Option(key_map[k], k));
    }
    folkrnn.utilities.setSelectByValue(folkrnn.fieldKey, key, 'K:Cmaj');
};

folkrnn.updateTuneDiv = function(tune) {
    "use strict";
    const el_abc = document.getElementById("abc-" + tune.id);
    const el_model = document.getElementById("rnn_model_name-" + tune.id);
    const el_seed = document.getElementById("seed-" + tune.id);
    const el_temp = document.getElementById("temp-" + tune.id);
    const el_prime_tokens = document.getElementById("prime_tokens-" + tune.id);
    const el_requested = document.getElementById("requested-" + tune.id);
    const el_generated = document.getElementById("generated-" + tune.id);
    const el_archive_form = document.getElementById("archive_form-" + tune.id);
    const el_archive_title = document.getElementById("id_title-" + tune.id);
    
    el_abc.innerHTML = tune.abc;
    el_abc.setAttribute('rows', tune.abc.split(/\r\n|\r|\n/).length - 1);
    el_model.innerHTML = tune.rnn_model_name.replace('.pickle', '');
    el_seed.innerHTML = tune.seed;
    el_temp.innerHTML = tune.temp;
    el_prime_tokens.innerHTML = tune.prime_tokens;
    el_requested.innerHTML = tune.requested;
    el_generated.innerHTML = tune.rnn_finished;
    if (tune.rnn_finished) {
        el_generated.innerHTML = new Date(tune.rnn_finished).toLocaleString();
        el_requested.parentNode.setAttribute('hidden', '');
        el_generated.parentNode.removeAttribute('hidden');
        
        el_archive_title.value = tune.title;
        el_archive_form.setAttribute('action', tune.archive_url);
        el_archive_form.removeAttribute('hidden');
    } else {
        el_requested.innerHTML = new Date(tune.requested).toLocaleString();
        el_requested.parentNode.removeAttribute('hidden');
        el_generated.parentNode.setAttribute('hidden', '');
        
        el_archive_form.setAttribute('hidden', '');
        
        if (!tune.rnn_started) {
            el_abc.innerHTML = folkrnn.waitingABC;
        }
    }
};

folkrnn.utilities = {};
folkrnn.utilities.setSelectByValue = function(element, value, default_value) {
    "use strict";
    for(let i = 0, j = element.options.length; i < j; ++i) {
        if(element.options[i].value === value) {
           element.selectedIndex = i;
           return;
        }
    }
    for(let i = 0, j = element.options.length; i < j; ++i) {
        if(element.options[i].value === default_value) {
           element.selectedIndex = i;
           return;
        }
    }
};