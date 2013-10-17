var $ = function(selector) {
  return document.querySelector(selector);
};

var $$ = function(selector) {
  return document.querySelectorAll(selector);
};

function testXhrType(type) {
  if (typeof XMLHttpRequest == 'undefined') {
    return false;
  }

  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/', true);
  try {
    xhr.responseType = type;
  } catch(error) {
    return false;
  }
  return 'response' in xhr && xhr.responseType == type;
}

document.addEventListener('WebComponentsReady', function(e) {
  // // Add .resolved to all custom elements. This is a hack until :unknown is supported
  // // in browsers and Polymer registers elements using document.register().
  // for (var name in CustomElements.registry) {
  //   var els = document.querySelectorAll(name + ', [is="' + name + '"]');
  //   [].forEach.call(els, function(el, i) {
  //     el.classList.add('resolved');
  //   });
  // }

  //document.body.classList.add('ready');
});
