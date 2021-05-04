(function(exports) {
'use strict';


class CuesService {
  static dismissCue(cue) {
    return window.csClient.doPost('/currentuser/cues', {cue: cue})
      .then((res) => res);
    // TODO: catch((error) => { display message }
  }
}


exports.CuesService = CuesService;
})(window);
