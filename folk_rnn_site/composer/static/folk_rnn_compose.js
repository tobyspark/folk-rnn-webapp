var fieldModel = document.getElementById("id_model");
var fieldKey = document.getElementById("id_key");
var fieldMeter = document.getElementById("id_meter");
var fieldTokens = document.getElementById("id_prime_tokens");

window.onLoad = rnnUpdateKeyMeter();
fieldModel.addEventListener("change", rnnUpdateKeyMeter);

fieldTokens.addEventListener("input", function() {
    var userTokens = fieldTokens.value.split(' ');
    if (rnnValidateTokens(userTokens, fieldModel.value)) {
        this.setCustomValidity('');
    } else {
        this.setCustomValidity('Enter valid ABC, tokens separated by spaces');
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

function rnnValidateTokens(userTokens, modelFileName) {
    const modelTokens = rnnModels[modelFileName]['tokens'];
    for (const token of userTokens) {
        if (token=='') continue
        if (modelTokens.indexOf(token) == -1) {
            return false;
        }
    }
    return true;
}