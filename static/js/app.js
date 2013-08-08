document.addEventListener('WebComponentsReady', function(e) {
  // // Add .resolved to all custom elements. This is a hack until :unknown is supported
  // // in browsers and Polymer registers elements using document.register().
  // for (var name in CustomElements.registry) {
  //   var els = document.querySelectorAll(name + ', [is="' + name + '"]');
  //   [].forEach.call(els, function(el, i) {
  //     el.classList.add('resolved');
  //   });
  // }
  document.body.classList.add('ready');
});