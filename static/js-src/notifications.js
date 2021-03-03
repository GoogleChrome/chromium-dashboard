(function(exports) {
'use strict';


class StarService {
  static getStars() {
    const url = location.hostname == 'localhost' ?
      'https://www.chromestatus.com/api/v0/currentuser/stars' :
      '/api/v0/currentuser/stars';
    return fetch(url, {
      method: 'GET',
      headers: {'Content-Type': 'application/json'},
    })
      .then((res) => res.json())
      .then((res) => res.featureIds);
    // TODO: catch((error) => { display message }
  }

  static setStar(featureId, starred) {
    const url = location.hostname == 'localhost' ?
      'https://www.chromestatus.com/api/v0/currentuser/stars' :
      '/api/v0/currentuser/stars';
    return fetch(url, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({featureId: featureId, starred: starred}),
    })
      .then((res) => res.json);
    // TODO: catch((error) => { display message }
  }
}


exports.StarService = StarService;
})(window);
