(function(exports) {
'use strict';


class CuesService {
  static dismissCue(cue) {
    const url = location.hostname == 'localhost' ?
      'https://www.chromestatus.com/api/v0/currentuser/cues' :
      '/api/v0/currentuser/cues';
    return fetch(url, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({cue: cue}),
    })
      .then((res) => res.json);
    // TODO: catch((error) => { display message }
  }
}


exports.CuesService = CuesService;
})(window);
