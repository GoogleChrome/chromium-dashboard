(function() {

var fields = document.querySelectorAll('input, textarea');
for (var i = 0, input; input = fields[i]; ++i) {
  fields[i].addEventListener('blur', function(event) {
    event.target.classList.add('interacted');
  });
}

// TODO(ericbidelman): These values are brittle if changed in the db later on.
var MIN_MILESTONE_TO_BE_ACTIVE = 3;
var MIN_STD_TO_BE_ACTIVE = 5;
var NO_PUBLIC_SIGNALS = 5;
var NO_LONGER_PURSUING = 1000;

var form = document.querySelector('[name="feature_form"]');
form.addEventListener('change', function(event) {
  switch (event.target.tagName.toLowerCase()) {
    case 'select':
      if (event.target.name.match(/_views$/)) {
        toggleViewLink(event.target);
      } else if (event.target.id == 'id_impl_status_chrome') {
        toggleMilestones(event.target);
      } else if (event.target.id == 'id_standardization') {
        toggleSpecLink(event.target)
      }
      break;
    case 'input':
      if (event.target.name == 'shipped_milestone') {
        fillOperaFields(event.target);
      }
      break;
    default:
      break;
  }
});

var operaDesktop = window.id_shipped_opera_milestone;
var operaAndroid = window.id_shipped_opera_android_milestone;
function fillOperaFields(chromeField) {
  var chromeVersion = chromeField.valueAsNumber;
  if (chromeVersion < 28) {
    return;
  }
  var operaVersion = chromeVersion - 13; // e.g. Chrome 32 ~ Opera 19
  if (!operaDesktop.classList.contains('interacted')) {
    operaDesktop.value = operaVersion;
  }
  if (!operaAndroid.classList.contains('interacted')) {
    operaAndroid.value = operaVersion;
  }
}

var specLink = window.id_spec_link;
function toggleSpecLink(stdStage) {
  specLink.disabled = parseInt(stdStage.value) >= MIN_STD_TO_BE_ACTIVE;
  specLink.parentElement.parentElement.hidden = specLink.disabled;
}

function toggleMilestones(status) {
  var val = parseInt(status.value);
  var disabled = val <= MIN_MILESTONE_TO_BE_ACTIVE || val == NO_LONGER_PURSUING;

  var shippedInputs = document.querySelectorAll('[name^="shipped_"]');
  [].forEach.call(shippedInputs, function(input) {
    input.disabled = disabled;
    input.parentElement.parentElement.hidden = input.disabled;
  });

  // var milestone = window.id_shipped_milestone;
  // milestone.disabled = parseInt(status.value) <= MIN_MILESTONE_TO_BE_ACTIVE;
  // milestone.parentElement.parentElement.hidden = milestone.disabled;
}

function toggleViewLink(view) {
  var link = document.getElementById(view.id + '_link');
  if (link) {
    link.disabled = parseInt(view.value) == NO_PUBLIC_SIGNALS;
    //link.required = !link.disabled;
    link.parentElement.parentElement.hidden = link.disabled;
  }
}

document.addEventListener('DOMContentLoaded', function() {
  // Get around Django rendering input type="text" fields for URLs.
  var inputs = document.querySelectorAll('[name$="_url"], [name$="_link"]');
  [].forEach.call(inputs, function(input) {
    input.type = 'url';
    input.placeholder = 'http://';
  });

  var shippedInputs = document.querySelectorAll('[name^="shipped_"]');
  [].forEach.call(shippedInputs, function(input) {
    input.type = 'number';
    input.placeholder = 'Milestone #';
  });

  var owner = document.querySelector('[name="owner"]');
  owner.type = 'email';
  owner.multiple = true;

  toggleMilestones(window.id_impl_status_chrome);
  [].forEach.call(document.querySelectorAll('select[name$="_views"]'), toggleViewLink);
});

document.body.addEventListener('ajaxdeleted', function(event) {
  if (event.detail.xhr.status == 200) {
    location.href = '/features';
  }
});

})();
