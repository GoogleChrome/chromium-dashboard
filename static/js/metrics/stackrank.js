var dashboardApp = angular.module('dashboardApp', []);

dashboardApp.controller('StackRankController', function($scope, $http) {
  $scope.properties = [];
  $scope.sortBy = '-day_percentage';

  var desc = true;

  $scope.fetchData = function() {
    $http.get('/data/querystackrank').success(
      function(resp, status, headers, config) {
        // Filter out bad results.
        $scope.properties = resp.filter(function(el, i) {
          return el.property_name != 'ERROR' && el.bucket_id != 1;
        });
      }
    );
  };

  $scope.sortList = function() {
    desc = !desc;
    $scope.sortBy = (desc ? '-' : '') + 'day_percentage';
  };

  $scope.fetchData();
});

//StackRankController.$inject = ['$scope', '$http'];


