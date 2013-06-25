(function() {

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

var MIN_MILESTONE_FOR_ACTIVE = 3;

var implStatus = document.querySelector('#id_impl_status_chrome');
var milestone = document.querySelector('#id_shipped_milestone');

implStatus.addEventListener('change', function(e) {
  milestone.disabled = e.target.value <= MIN_MILESTONE_FOR_ACTIVE;
});

function init() {
  milestone.disabled = implStatus.value <= MIN_MILESTONE_FOR_ACTIVE;
}

init();

})();
