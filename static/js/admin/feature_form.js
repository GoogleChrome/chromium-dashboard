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

// TODO(ericbidelman): These values are brittle if changed in the db later on.
var MIN_MILESTONE_TO_BE_ACTIVE = 3;
var MIN_STD_TO_BE_ACTIVE = 5;
var NO_PUBLIC_SIGNALS = 5;

var form = document.querySelector('[name="feature_form"]');
form.addEventListener('change', function(e) {
  switch(e.target.tagName.toLowerCase()) {
    case 'select':
      if (e.target.name.match(/_views$/)) {
        toggleViewLink(e.target);
      } else if (e.target.id == 'id_impl_status_chrome') {
        toggleMilestone(e.target);
      } else if (e.target.id == 'id_standardization') {
        toggleSpecLink(e.target)
      }
      break;
    default:
      break;
  }
});

function toggleSpecLink(stdStage) {
  var specLink = document.querySelector('#id_spec_link')
  specLink.disabled = parseInt(stdStage.value) >= MIN_STD_TO_BE_ACTIVE;
  specLink.parentElement.parentElement.hidden = specLink.disabled;
}

function toggleMilestone(status) {
   var milestone = document.querySelector('#id_shipped_milestone')
   milestone.disabled = parseInt(status.value) <= MIN_MILESTONE_TO_BE_ACTIVE;
   milestone.hidden = milestone.disabled;
}

function toggleViewLink(view) {
  var link = document.getElementById(view.id + '_link');
  if (link) {
    link.disabled = parseInt(view.value) == NO_PUBLIC_SIGNALS;
    //link.required = !link.disabled;
    link.parentElement.parentElement.hidden = link.disabled;
  }
}

document.addEventListener('DOMContentLoaded', function(e) {
  // Get around Django rendering input type="text" fields for URLs.
  var inputs = document.querySelectorAll('[name$="_url"], [name$="_link"]');
  [].forEach.call(inputs, function(input) {
    input.type = 'url';
    input.placeholder = 'http://';
  });

  var owner = document.querySelector('[name="owner"]');
  owner.type = 'email';
  owner.multiple = true;

  toggleMilestone(document.querySelector('#id_impl_status_chrome'));
  [].forEach.call(document.querySelectorAll('select[name$="_views"]'), toggleViewLink);
});

document.body.addEventListener('ajaxdeleted', function(e) {
  if (e.detail.xhr.status == 200) {
    location.href = '/features';
  }
});

})();
