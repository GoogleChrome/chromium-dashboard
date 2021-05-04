(function(exports) {
'use strict';


class StarService {
  static getStars() {
    return window.csClient.doGet('/currentuser/stars')
      .then((res) => res.featureIds);
    // TODO: catch((error) => { display message }
  }

  static setStar(featureId, starred) {
    return window.csClient.doPost(
      '/currentuser/stars',
      {featureId: featureId, starred: starred})
      .then((res) => res);
    // TODO: catch((error) => { display message }
  }
}


exports.StarService = StarService;
})(window);
