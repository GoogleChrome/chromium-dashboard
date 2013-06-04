var inputs = document.querySelectorAll('input');
for (var i = 0, input; input = inputs[i]; ++i) {
  inputs[i].addEventListener('blur', function(e) {
    e.target.classList.add('interacted');
  });
}

var textareas = document.querySelectorAll('textarea');
for (var i = 0, textarea; textarea = textareas[i]; ++i) {
  textareas[i].addEventListener('blur', function(e) {
    e.target.classList.add('interacted');
  });
}
