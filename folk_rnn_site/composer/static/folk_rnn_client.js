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
    folkrnn.seedAutoButton = document.getElementById("seed_auto");
    folkrnn.composeButton = document.getElementById("compose_button");
    
    folkrnn.div_tune = document.getElementById("tune");
    
    folkrnn.updateKeyMeter();
    folkrnn.handleSeedAuto(true);
    
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

    folkrnn.fieldSeed.addEventListener("input", function() {
        folkrnn.handleSeedAuto(false);
    });
    folkrnn.seedAutoButton.addEventListener("click", function() {
        folkrnn.handleSeedAuto(true);
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
    
    // False when generating tunes. True for 'static' /tune/x pages.
    folkrnn.setComposeParametersFromTune = false;
};

folkrnn.stateManager = {
    'addTune': function(tune_id) {
        "use strict";
        // Hide about div, now there is a tune
        folkrnn.showAboutSection(false);
        
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
            folkrnn.showAboutSection(true);
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
        folkrnn.updateKeyMeter()
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
        div_tune_new.querySelector('h1').textContent = folkrnn.tuneTitle + tune_id;
        div_tune_new.querySelector('#abc').id = 'abc-' + tune_id;
        div_tune_new.querySelector('#rnn_model_name').id = 'rnn_model_name-' + tune_id;
        div_tune_new.querySelector('#seed').id = 'seed-' + tune_id;
        div_tune_new.querySelector('#temp').id = 'temp-' + tune_id;
        div_tune_new.querySelector('#prime_tokens').id = 'prime_tokens-' + tune_id;
        div_tune_new.querySelector('#requested').id = 'requested-' + tune_id;
        div_tune_new.querySelector('#generated').id = 'generated-' + tune_id;
        div_tune_new.querySelector('#midi').id = 'midi-' + tune_id;
        div_tune_new.querySelector('#midi-download').id = 'midi-download-' + tune_id;
        div_tune_new.querySelector('#tempo').id = 'tempo-' + tune_id;
        div_tune_new.querySelector('#tempo_input').id = 'tempo_input-' + tune_id;
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
    '_enableABCJS_colorRange': function(range, color) {
        "use strict";
        if (range && range.elements) {
            range.elements.forEach(function (set) {
                set.forEach(function (item) {
                    item.setAttribute("fill", color);
                });
            });
        }
    },
    '_enableABCJS_animateCallback': function(lastRange, currentRange, context) {
        "use strict";
        folkrnn.tuneManager._enableABCJS_colorRange(lastRange, "#000000");
        folkrnn.tuneManager._enableABCJS_colorRange(currentRange, "#3D9AFC");
    },
    'enableABCJS': function (tune_id) {
        "use strict";
        const el_tempo_input = document.getElementById('tempo_input-' + tune_id)
        const tempo = parseInt(el_tempo_input.value)
        folkrnn.tuneManager.tunes[tune_id].abcjs = new ABCJS.Editor("abc-" + tune_id, { 
            canvas_id: "notation-" + tune_id,
            generate_midi: true,
            midi_id:"midi-" + tune_id,
            midi_download_id: "midi-download-" + tune_id,
            abcjsParams: {
                generateInline: true,
                generateDownload: true,
                downloadLabel:"Download MIDI",
                downloadClass:["pure-button", "pure-button-primary", "pure-u-1"],
                paddingleft:0,
                paddingright:0,
                responsive: "resize",
                animate: {
                    listener: folkrnn.tuneManager._enableABCJS_animateCallback, 
                    target: "notation-" + tune_id, 
                },
                qpm: tempo,
            }
        });
        
        document.getElementById('tempo_input-' + tune_id).addEventListener("change", function (event) {
            folkrnn.tuneManager.tunes[tune_id].abcjs.paramChanged({"qpm": parseInt(event.target.value)});
            folkrnn.websocketSend({
                command: "notification",
                type: "tempo",
                value: event.target.value,
                tune_id: tune_id,
            });
        });
        
        const midi_download_link = document.body.querySelector('#midi-download-' + tune_id + ' > div > a');
        midi_download_link.addEventListener('click', function() {
            folkrnn.websocketSend({
                command: "notification",
                type: "midi_download",
                tune_id: tune_id,
            });
        });
        const midi_play_button = document.body.querySelector('#midi-' + tune_id + ' > div > button.abcjs-midi-start.abcjs-btn');
        midi_play_button.addEventListener('click', function() {
            folkrnn.websocketSend({
                command: "notification",
                type: "midi_play",
                tune_id: tune_id,
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
        
        // If last tune, stop any remaining MIDI playback
        if (Object.keys(folkrnn.tuneManager.tunes).length === 0) {
            MIDI.player.stop();
        }
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
        const parsedStartABC = folkrnn.parseABC(folkrnn.fieldStartABC.value)
        const formData = {};
        formData.model = folkrnn.fieldModel.value;
        formData.temp = folkrnn.fieldTemp.value;
        formData.seed = folkrnn.fieldSeed.value;
        formData.unitnotelength = parsedStartABC.header.l || ''
        formData.meter = parsedStartABC.header.m || folkrnn.fieldMeter.value;
        formData.key = parsedStartABC.header.k || folkrnn.fieldKey.value;
        formData.start_abc = parsedStartABC.tokens.join(' ');
        
        folkrnn.websocketSend({
                    'command': 'compose',
                    'data': formData,
        });
        
        folkrnn.setComposeParametersFromTune = false;
    }
    
    if (folkrnn.fieldSeed.dataset.autoseed) {
        folkrnn.fieldSeed.value = Math.floor(Math.random() * Math.floor(folkrnn.maxSeed));
    }
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

    const invalidHeaders = folkrnn.invalidHeaders(abcParsed.header.l, abcParsed.header.m, abcParsed.header.k, folkrnn.fieldModel.value);
    if (invalidHeaders.length == 0) {
        if (abcParsed.header.m) {
            folkrnn.utilities.setSelectByValue(folkrnn.fieldMeter, abcParsed.header.m);
            folkrnn.fieldMeter.setAttribute('disabled', '');
        } else {
            folkrnn.fieldMeter.removeAttribute('disabled');
        }
        if (abcParsed.header.k) {
            folkrnn.utilities.setSelectByValue(folkrnn.fieldKey, abcParsed.header.k);
            folkrnn.fieldKey.setAttribute('disabled', '');
        } else {
            folkrnn.fieldKey.removeAttribute('disabled');
        }
    } else {
        folkrnn.fieldMeter.removeAttribute('disabled');
        folkrnn.fieldKey.removeAttribute('disabled');
    }
    
    const invalidTokens = folkrnn.invalidTokens(abcParsed.tokens, folkrnn.fieldModel.value);
    const allInvalidTokens = invalidHeaders.concat(invalidTokens)
    if (allInvalidTokens.length == 1 ) {
        folkrnn.fieldStartABC.setCustomValidity('Invalid token: ' + allInvalidTokens[0]);
    } else if (allInvalidTokens.length > 1 ) {
        folkrnn.fieldStartABC.setCustomValidity('Invalid tokens: ' + allInvalidTokens.join(', '));
    } 
};

folkrnn.updateKeyMeter = function() {
    "use strict";
    // Update key, meter options per new model's vocab
    // If the meter, mode tokens in new model are the same as the old, don't do anything.
    // Else update key, meter options per new model's vocabset and defaults.
    
    const m_values_old = Array.from(folkrnn.fieldMeter.childNodes).map(x => x.value);
    const m_values_new = folkrnn.models[folkrnn.fieldModel.value].header_m_tokens;
    const k_values_old = Array.from(folkrnn.fieldKey.childNodes).map(x => x.value);
    const k_values_new = folkrnn.models[folkrnn.fieldModel.value].header_k_tokens;
        
    if (!folkrnn.utilities.isEqual(m_values_old, m_values_new)) {
        while (folkrnn.fieldMeter.lastChild) {
            folkrnn.fieldMeter.removeChild(folkrnn.fieldMeter.lastChild);
        }
        for (const m of m_values_new) {
            const label = (m === '*') ? '?/?' : m.slice(2);
            folkrnn.fieldMeter.appendChild(new Option(label, m));
        }
        const m_default = 'M:' + folkrnn.models[folkrnn.fieldModel.value].default_meter;
        folkrnn.utilities.setSelectByValue(folkrnn.fieldMeter, m_default, '');
    }
    if (!folkrnn.utilities.isEqual(k_values_old, k_values_new)) {
        while (folkrnn.fieldKey.lastChild) {
            folkrnn.fieldKey.removeChild(folkrnn.fieldKey.lastChild);
        }
        const key_map = {
            'maj': 'Major',		
            'min': 'Minor',		
            'dor': 'Dorian',		
            'mix': 'Mixolydian',
            'lyd': 'Lydian',
        };
        for (const k of k_values_new) {
            const label = (k === '*') ? '? ???' : k.slice(2,-3) + " " + key_map[k.slice(-3).toLowerCase()];
            folkrnn.fieldKey.appendChild(new Option(label, k));
        }
        const k_default = 'K:' + folkrnn.models[folkrnn.fieldModel.value].default_mode;
        folkrnn.utilities.setSelectByValue(folkrnn.fieldKey, k_default, '');
    }
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
    const el_tempo = document.getElementById("tempo-" + tune.id);
    const el_tempo_input = document.getElementById('tempo_input-' + tune.id)
    const el_archive_form = document.getElementById("archive_form-" + tune.id);
    const el_archive_title = document.getElementById("id_title-" + tune.id);
    
    el_abc.value = tune.abc;
    el_abc.setAttribute('rows', tune.abc.split(/\r\n|\r|\n/).length - 1);
    el_model.textContent = tune.rnn_model_name.replace('.pickle', '');
    el_seed.textContent = tune.seed;
    el_temp.textContent = tune.temp;
    el_prime_tokens.textContent = tune.prime_tokens;
    el_requested.textContent = tune.requested;
    el_generated.textContent = tune.rnn_finished;
    el_tempo_input.value = folkrnn.models[tune.rnn_model_name].default_tempo;
    if (tune.rnn_finished) {
        el_generated.textContent = new Date(tune.rnn_finished).toLocaleString();
        el_requested.parentNode.setAttribute('hidden', '');
        el_generated.parentNode.removeAttribute('hidden');
        
        el_tempo.removeAttribute('hidden');
        
        el_archive_title.value = folkrnn.tuneTitle + tune.id;
        el_archive_form.setAttribute('action', tune.archive_url);
        el_archive_form.removeAttribute('hidden');
        
        if (folkrnn.setComposeParametersFromTune) {
            folkrnn.utilities.setSelectByValue(folkrnn.fieldModel, tune.rnn_model_name, '');
            folkrnn.updateKeyMeter();
            folkrnn.fieldTemp.value = tune.temp;
            folkrnn.fieldSeed.value = tune.seed;
            folkrnn.utilities.setSelectByValue(folkrnn.fieldKey, tune.key);
            folkrnn.utilities.setSelectByValue(folkrnn.fieldMeter, tune.meter);
            folkrnn.fieldStartABC.value = tune.start_abc;
        }
    } else {
        el_requested.textContent = new Date(tune.requested).toLocaleString();
        el_requested.parentNode.removeAttribute('hidden');
        el_generated.parentNode.setAttribute('hidden', '');
        
        el_archive_form.setAttribute('hidden', '');
        
        if (!tune.rnn_started) {
            el_abc.value = folkrnn.waitingABC;
        }
    }
};

folkrnn.showAboutSection = function(toShow) {
    "use strict";
    const div_about = document.getElementById("header");
    if (toShow) {
        div_about.removeAttribute('hidden');
        const el_demo_embed = document.getElementById("demo-embed");
        // lazy load embed, i.e. when about section should be visible
        if (el_demo_embed.getAttribute("src") === "") {
            el_demo_embed.setAttribute("src", el_demo_embed.dataset.src);
        }
    } else {
        div_about.setAttribute('hidden', '');
    }
};

folkrnn.handleSeedAuto = function(autoSeedOn) {
    "use strict";
    const seed_field_div = document.getElementById('seed_field_div');
    if (autoSeedOn) {
        seed_field_div.className = 'pure-u-1';
        folkrnn.fieldSeed.dataset.autoseed = "truthy";
    } else {
        seed_field_div.className = 'pure-u-7-8';
        delete folkrnn.fieldSeed.dataset.autoseed;
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

folkrnn.utilities.isEqual = function(array1, array2) {
    "use strict";
    // A shallow, scalar comparison of arrays
    return array1.length === array2.length && array1.every((value, index) => value === array2[index]);
};