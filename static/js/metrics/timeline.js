// var dashboardApp = angular.module('dashboardApp', []);

// var parsedData = null;
// var temp = {};
// var dataArray= [];



// dashboardApp.controller('TimeLineController', function($scope, $http) {
//   $scope.properties = [];

//   $scope.fetchData = function() {
//     $http.get('/data/querystableinstances').success(
//       function(resp, status, headers, config) {
//         $scope.properties = resp;
// parsedData = resp;
//         drawVisualization('color');
//       }
//     );
//   };

//   $scope.fetchData();
// });

// //TimeLineController.$inject = ['$scope', '$http'];


// function drawVisualization(name) {
//   var data = new google.visualization.DataTable();

//   /*Reformat the data

//   // TODO use bucket_ids instead of property_name in comparisons.

//   // Beginning structure
//   parsedData = [{
//     date: obj,
//     property_name: string,
//     day_percentage: float,
//     bucket_id: int
//   }...
//   ]

//   // Intermediate structure
//   temp = {
//     date1: {
//      property_name1: hits1
//      property_name2: hits2
//     }
//   }

//   // Final structure
//   [
//     [date1, hits1, hits2]
//     [date2, hits3, hits4]
//   ]*/

//   // Build structure of dates
//   for (var i = 0, item; item = parsedData[i]; ++i) {
//     var date = item.date;
//     if (!temp[date]) {
//       temp[date] = {};
//     }
//     temp[date][item.property_name] = item.day_percentage;
//   }

//   var dates = [];
//   for (var date in temp) {
//     dates.push(temp[date]);
//   }

// console.log(dates)

//   data.addColumn('date', 'Date');

//   var namesArray = getNamesArray(name);

//   for (var property_name in dates[0]) {
//     if (namesArray.indexOf(property_name) != -1) {
//       data.addColumn('number', property_name);
//     }
//   }

//   var rowArray = [];
//   for (var date in temp) {
//     var r = [];
//     var d = temp[date];
//     var fullDate = new Date((parseInt(date) * 1000));
//     r.push(new Date(fullDate.getYear(), fullDate.getMonth(), fullDate.getDay()));
    
//     for (var property_name in d) {
//       if (namesArray.indexOf(property_name) != -1) {
//         r.push(d[property_name]);
//       }
//     }
//     rowArray.push(r);
//   }

//   console.log(rowArray)

//   data.addRows(rowArray);

//   var options = {
//     vAxis: {title: 'Percentage'},
//     hAxis: {title: 'Time Range'},
//     width: 900,
//     height: 500,
//     chartArea: {width: '50%'},
//   };

//   var chart = new google.visualization.LineChart(document.querySelector('#chart'));
//   chart.draw(data, options);
// }

// function goToChart(id) {
//   var node = document.getElementById(id);

//   if (node && node.tagName == "SELECT") {
//     var selectedValue = node.options[node.selectedIndex].innerText;
//     drawVisualization(selectedValue);
//   }
// }

// function getNamesArray(name) {
//   var namesArray = [name];
  
//   if (name.substr(0, 7) === 'webkit-') {
//     var nameToCheck = name.substr(7);
//     var index = CSS_PROPERTIES_LIST.indexOf(nameToCheck);
//     if (index != -1) {
//       namesArray.push(CSS_PROPERTIES_LIST[index]);
//     }
//   } else {
//     var nameToCheck = 'webkit-' + name;
//     var index = CSS_PROPERTIES_LIST.indexOf(nameToCheck);
//     if (index != -1) {
//       namesArray.push(CSS_PROPERTIES_LIST[index]);
//     }
//   }

//   return namesArray;
// }


// var CSS_PROPERTIES_LIST = [];

// function init() {
//   var options = document.querySelector("#property-selector").options;
//   for (var i = 0, opt; opt = options[i]; ++i) {
//     CSS_PROPERTIES_LIST.push(options[i].textContent);
//   }
// }

// init();


// // (function(exports) {

// // var allProperties = [];
// // var temp = {};
// // var dataArray= [];

// // google.load('visualization', '1.0', {packages:['corechart']});
// // //google.setOnLoadCallback(visualizationReady);

// // function getData() {
// //   var xhr = new XMLHttpRequest();
// //   xhr.open('GET', '/data/querystableinstances');
  
// //   xhr.onloadend = function(e) {
// //     if (this.status == 200) {
// //       parsedData = JSON.parse(this.response);

// // console.log(parsedData);


// //       // Sort by date.
// //       parsedData.sort(function(obj1, obj2) {
// //         return obj1.date.epoch - obj2.date.epoch;
// //       });

// // console.log(parsedData)

// //       drawVisualization('color');
// //     }
// //   };

// //   xhr.send();
// // }



// // getData();

// // exports.goToChart = goToChart;

// // })(window);
