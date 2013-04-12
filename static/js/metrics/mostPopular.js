(function() {

var parsedData;
var propertyOrder = 'greatestToLeast';

function getData() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/data/querystackrank');

  xhr.onloadend = function(e) {
    if (this.status == 200) {
      parsedData = JSON.parse(this.responseText);
      writeProperties();
    }
  }

  xhr.send();
}

function writeProperties() {
    
}

getData();

})();
