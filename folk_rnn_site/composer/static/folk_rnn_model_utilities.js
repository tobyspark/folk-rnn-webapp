/* jshint esversion: 6, strict: true, undef: true, unused: true, varstmt: true */
/* globals folkrnn */

if (typeof folkrnn == 'undefined') {
    folkrnn = {};
}

folkrnn.invalidHeaders = function(l, m, k, modelFileName) {
    "use strict";
    let invalidTokens = [];
    if (l && folkrnn.models[modelFileName].header_l_tokens.indexOf(l) == -1)
        invalidTokens.push(l);
    if (m && folkrnn.models[modelFileName].header_m_tokens.indexOf(m) == -1)
        invalidTokens.push(m);
    if (k && folkrnn.models[modelFileName].header_k_tokens.indexOf(k) == -1)
        invalidTokens.push(k);    
    return invalidTokens;
};

folkrnn.invalidTokens = function(userTokens, modelFileName) {
    "use strict";
    const modelTokens = folkrnn.models[modelFileName].tokens;
    let invalidTokens = [];
    for (const token of userTokens) {
        if (token==='') 
            continue;
        if (modelTokens.indexOf(token) == -1) 
            invalidTokens.push(token);
    }
    return invalidTokens;
};

folkrnn.parseABC = function(abc) {
    "use strict";
    
    // HEADER
    
    let header = {};
    let body_start_index = 0;
    
    let header_regex = /\[?(L:\d+\/\d+)]?\n\[?(M:\d+\/\d+)\]?\n\[?(K:[A-G][b#]?[A-Za-z]{3})\]?\n?/g;
    let match = header_regex.exec(abc);
    if (match !== null) {
        header.l = match[1];
        header.m = match[2];
        header.k = match[3];
        body_start_index = header_regex.lastIndex
    } else {
        header_regex = /\[?(M:\d+\/\d+)\]?\n\[?(K:[A-G][b#]?[A-Za-z]{3})\]?\n?/g;
        match = header_regex.exec(abc);
        if (match !== null) {
           header.m = match[1];
           header.k = match[2];
           body_start_index = header_regex.lastIndex
        }   
    } 
    
    // BODY
    
    // Javascript port of Bob Sturm's original python script that was used to generate the training dataset.
    // Extended to return invalid ABC
    // Extended to handle wildcard token
    // Good for config5-wrepeats-20160112

    const ignoreSet = new Set([' ', '\n', '\r']);
    const noteset = new Set(['a','b','c','d','e','f','g','z','x','A','B','C','D','E','F','G']);
    const octset = new Set([',','\'']);
    const accset = new Set(['=','_','^']);
    const symbset = new Set(['|','[',']']);
    const numbset = new Set(['1','2','3','4','5','6','7','8','9']);
    const modset = new Set(['/']);
    const contset = new Set(['>','<']);
    const wildcardset = new Set(['*']);

    let result = [];
    let invalidIndexes = [];

    let w="";
    let flag_expectingnote=0;
    let flag_innote=0;
    let flag_indur=0;
    for (let i = body_start_index; i < abc.length; i++) {
        const c = abc[i];

        if (ignoreSet.has(c))
            continue;
        if (symbset.has(c)) {
            if (flag_innote || flag_indur) {
                if (w.length > 0) result.push(w);
                w=c;
            } else {
                w+=c;
            }
            flag_innote=0;
            flag_indur=0;
        } else if (c == ':') {
            if (flag_innote || flag_indur) {
                if (w.length > 0) result.push(w);
                w="";
                flag_innote=0;
                flag_indur=0;
            }
            w+=c;
        } else if (c == '(') {
            if (w.length > 0) result.push(w);
            w=c;
            flag_indur=1;
            flag_innote=0;
        } else if (numbset.has(c)) {
            if (flag_innote) {
                if (w.length > 0) result.push(w);
                w=c;
                flag_indur=1;
                flag_innote=0;
            } else if (flag_indur) {
                w+=c;
            } else {
                if (w.length > 0) result.push(w);
                w=c;
            }
            flag_indur=1;
        } else if (octset.has(c)) {
            w+=c;
        } else if (modset.has(c)) {
            if (flag_innote) {
                if (w.length > 0) result.push(w);
                w=c;
            } else {
                w+=c;
            }
            flag_indur=1;
            flag_innote=0;
        } else if (accset.has(c)) {
            if (flag_innote) { // terminate previous note
                if (w.length > 0) result.push(w);
                w=c;
            } else if (flag_expectingnote) { // double accidental
                w+=c;
            } else {
                if (w.length > 0) result.push(w);
                w=c;
            }
            flag_indur=0;
            flag_innote=0;
            flag_expectingnote=1;
        } else if (noteset.has(c)) {
            if (flag_expectingnote) {
                w+=c;
                flag_expectingnote=0;
            } else {
                if (w.length > 0) result.push(w);
                w=c;
            }
            flag_innote=1;
            flag_indur=0;
        } else if (contset.has(c)) {
            if (flag_indur) {
                w+=c;
            } else {
                if (w.length > 0) result.push(w);
                w=c;
            }
            flag_innote=0;
            flag_indur=1;
        } else if (wildcardset.has(c)) {
            if (w.length > 0) {
                result.push(w);
                w="";
            }
            flag_innote=0;
            flag_indur=0;
            flag_expectingnote=0;
            result.push(c);
        } else {
            invalidIndexes.push(i);
        }
    }

    // append final part
    result.push(w);
        
    // Post-process, for e.g. ':||:' needs to be ':|', '|:'.
    // From Bob –
    // sed 's/: |/:|/g' | sed 's/| :/|:/g' |
    // sed 's/|\[\([0-9]\)/|\1/g' | sed 's/| \[\([0-9]\)/|\1/g' |
    // sed 's/|\[ \([0-9]\)/|\1/g' | sed 's/| \([0-9]\)/|\1/g' |
    // sed 's/:|:/:| |:/g' | sed 's/:|\([0-9]\)/:| |\1/g' |
    // sed 's/::/:| |:/g' | sed 's/|\[/| \[/g' | sed 's/\]\[/\] \[/g' |
    // sed 's/\]|/\] |/g' | sed 's/|:\[/|: \[/g' | sed 's/\]:|/\] :|/g' |
    // sed 's/:||:/:| |:/g' | sed 's/\[ \([0-9]\)/|\1/g' | sed 's/-|/- |/g' |
    // sed 's/||/|/g' | sed 's/-:|/- :|/g'
    let tokensSpaced = result.join(' ');
    tokensSpaced = tokensSpaced.replace(/: \|/g, ':|'); // sed 's/: |/:|/g'
    tokensSpaced = tokensSpaced.replace(/\| :/g, '|:'); // sed 's/| :/|:/g'
    tokensSpaced = tokensSpaced.replace(/\|\[([0-9])/g, '|$1'); // sed 's/|\[\([0-9]\)/|\1/g'
    tokensSpaced = tokensSpaced.replace(/\| \[([0-9])/g, '|$1'); // sed 's/| \[\([0-9]\)/|\1/g'
    tokensSpaced = tokensSpaced.replace(/\|\[ ([0-9])/g, '|$1'); // sed 's/|\[ \([0-9]\)/|\1/g'
    tokensSpaced = tokensSpaced.replace(/\| ([0-9])/g, '|$1'); // sed 's/| \([0-9]\)/|\1/g'
    tokensSpaced = tokensSpaced.replace(/:\|:/g, ':| |:'); // sed 's/:|:/:| |:/g'
    tokensSpaced = tokensSpaced.replace(/:\|([0-9])/g, ':| |$1'); // sed 's/:|\([0-9]\)/:| |\1/g'
    tokensSpaced = tokensSpaced.replace(/::/g, ':| |:'); // sed 's/::/:| |:/g'
    tokensSpaced = tokensSpaced.replace(/\|\[/g, '| ['); // sed 's/|\[/| \[/g'
    tokensSpaced = tokensSpaced.replace(/\]\[/g, '] ['); // sed 's/\]\[/\] \[/g'
    tokensSpaced = tokensSpaced.replace(/\]\|/g, '] |'); // sed 's/\]|/\] |/g'
    tokensSpaced = tokensSpaced.replace(/\|:\[/g, '|: ['); // sed 's/|:\[/|: \[/g'
    tokensSpaced = tokensSpaced.replace(/\]:\|/g, '] :|'); // sed 's/\]:|/\] :|/g'
    tokensSpaced = tokensSpaced.replace(/:\|\|:/g, ':| |:'); // sed 's/:||:/:| |:/g'
    tokensSpaced = tokensSpaced.replace(/\[ ([0-9])/g, '|$1'); // sed 's/\[ \([0-9]\)/|\1/g'
    tokensSpaced = tokensSpaced.replace(/-\|/g, '- |'); // sed 's/-|/- |/g'
    tokensSpaced = tokensSpaced.replace(/\|\|/g, '|'); // sed 's/||/|/g'
    tokensSpaced = tokensSpaced.replace(/-:\|/g, '- :|'); //sed 's/-:|/- :|/g'    
    result = tokensSpaced.split(' ');

    return {'header': header, 'tokens': result, 'invalidIndexes': invalidIndexes};
};