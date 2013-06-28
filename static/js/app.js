document.addEventListener('WebComponentsReady', function(e) {
  // Add .resolved to all custom elements. This is a hack until :unknown is supported
  // in browsers and Polymer registers elements using document.register().
  for (var name in CustomElements.registry) {
    [].forEach.call(document.querySelectorAll(name), function(el, i) {
      el.classList.add('resolved');
    });
  }
});