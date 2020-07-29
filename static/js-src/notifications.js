(function(exports) {
'use strict';


class StarService {
  static getStars() {
    const url = location.hostname == 'localhost' ?
      'https://www.chromestatus.com/features/star/list' :
      '/features/star/list';
    return fetch(url, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({}),
    })
      .then((res) => res.json())
      .then((res) => res.featureIds);
    // TODO: catch((error) => { display message }
  }

  static setStar(featureId, starred) {
    const url = location.hostname == 'localhost' ?
      'https://www.chromestatus.com/features/star/set' :
      '/features/star/set';
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
