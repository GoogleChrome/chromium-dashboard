(function() {
'use strict';

const fields = document.querySelectorAll('input, textarea');
for (let i = 0; i < fields.length; ++i) {
  fields[i].addEventListener('blur', function(e) {
    e.target.classList.add('interacted');
  });
}

// TODO(ericbidelman): These values are brittle if changed in the db later on.
const MIN_MILESTONE_TO_BE_ACTIVE = 3;
const MIN_STD_TO_BE_ACTIVE = 5;
const NO_LONGER_PURSUING = 1000;

const form = document.querySelector('[name="feature_form"]');
form.addEventListener('change', function(e) {
  switch (e.target.tagName.toLowerCase()) {
    case 'select':
      if (e.target.id === 'id_impl_status_chrome') {
        toggleMilestones(e.target);
      } else if (e.target.id === 'id_intent_stage') {
        intentStageChanged(e.target);
      }
      break;
    case 'input':
      if (e.target.name === 'shipped_milestone') {
        fillOperaFields(e.target);
      }
      break;
    default:
      break;
  }
});

const operaDesktop = document.querySelector('#id_shipped_opera_milestone');
const operaAndroid = document.querySelector(
  '#id_shipped_opera_android_milestone');

/**
 * Populates Opera version inputs with Chrome 32 -> Opera 19 version mapping.
 * @param {HTMLInputElement} chromeField Chrome version input.
 */
function fillOperaFields(chromeField) {
  const chromeVersion = chromeField.valueAsNumber;
  if (chromeVersion < 28) {
    return;
  }
  const operaVersion = chromeVersion - 13; // e.g. Chrome 32 ~ Opera 19
  if (!operaDesktop.classList.contains('interacted')) {
    operaDesktop.value = operaVersion;
  }
  if (!operaAndroid.classList.contains('interacted')) {
    operaAndroid.value = operaVersion;
  }
}

/**
 * Toggles the chrome milestone inputs.
 * @param {HTMLInputElement} status Input element.
 */
function toggleMilestones(status) {
  const val = parseInt(status.value, 10);
  const disabled = (val <= MIN_MILESTONE_TO_BE_ACTIVE ||
                    val === NO_LONGER_PURSUING);

  const shippedInputs = document.querySelectorAll('[name^="shipped_"]');
  [].forEach.call(shippedInputs, function(input) {
    input.disabled = disabled;
    input.parentElement.parentElement.hidden = input.disabled;
  });

  // var milestone = document.querySelector('#id_shipped_milestone');
  // milestone.disabled = parseInt(status.value) <= MIN_MILESTONE_TO_BE_ACTIVE;
  // milestone.parentElement.parentElement.hidden = milestone.disabled;
}

const INTENT_IMPLEMENT = 1;
const INTENT_EXPERIMENT = 2;
const INTENT_EXTEND_TRIAL = 3;
const INTENT_IMPLEMENT_SHIP = 4;
const INTENT_SHIP = 5;
const INTENT_REMOVE = 6;

let INTENT_IDENTIFIER_NAMES = {};

INTENT_IDENTIFIER_NAMES[INTENT_IMPLEMENT] = "INTENT_IMPLEMENT";
INTENT_IDENTIFIER_NAMES[INTENT_EXPERIMENT] = "INTENT_EXPERIMENT";
INTENT_IDENTIFIER_NAMES[INTENT_EXTEND_TRIAL] = "INTENT_EXTEND_TRIAL";
INTENT_IDENTIFIER_NAMES[INTENT_IMPLEMENT_SHIP] = "INTENT_IMPLEMENT_SHIP";
INTENT_IDENTIFIER_NAMES[INTENT_SHIP] = "INTENT_SHIP";
INTENT_IDENTIFIER_NAMES[INTENT_REMOVE] = "INTENT_REMOVE";

// An object graph mapping form fields to implementation status and whether or
// not the form field is shown or hidden (first 1/0) and required or optional
// (second 1/0).

const FORM_FIELD_SHOW_POS = 0
const FORM_FIELD_REQUIRED_POS = 1

const HIDDEN = [0, 0];
const VISIBLE_OPTIONAL = [1, 0];
const VISIBLE_REQUIRED = [1, 1];

const FORM_FIELD_GRAPH = {
  'intent_to_implement_url': {
    INTENT_IMPLEMENT: HIDDEN,
    INTENT_EXPERIMENT: VISIBLE_REQUIRED,
    INTENT_EXTEND_TRIAL: VISIBLE_REQUIRED,
    INTENT_IMPLEMENT_SHIP: HIDDEN,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'explainer_links': {
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'doc_links': {
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: HIDDEN,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'spec_link': {
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: VISIBLE_OPTIONAL,
    INTENT_EXTEND_TRIAL: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'standardization': {
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'tag_review': {
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: HIDDEN,
  },
  'wpt': {
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'wpt_descr': {
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'sample_links': {
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: HIDDEN,
  },
  'bug_url': {
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'blink_components': {
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'impl_status_chrome': {
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'prefixed': {
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'footprint': {
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'interop_compat_risks': {
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'motivation': {
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: HIDDEN,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'ff_views': {
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'ie_views': {
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'safari_views': {
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'web_dev_views': {
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'ff_views_link': {
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'ie_views_link': {
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'safari_views_link': {
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'web_dev_views_link': {
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'ff_views_notes': {
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'ie_views_notes': {
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'safari_views_notes': {
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'web_dev_views_notes': {
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'experiment_goals': {
    INTENT_IMPLEMENT: HIDDEN,
    INTENT_EXPERIMENT: VISIBLE_REQUIRED,
    INTENT_EXTEND_TRIAL: VISIBLE_REQUIRED,
    INTENT_IMPLEMENT_SHIP: HIDDEN,
    INTENT_SHIP: HIDDEN,
    INTENT_REMOVE: HIDDEN,
  },
  'experiment_timeline': {
    INTENT_IMPLEMENT: HIDDEN,
    INTENT_EXPERIMENT: VISIBLE_REQUIRED,
    INTENT_EXTEND_TRIAL: VISIBLE_REQUIRED,
    INTENT_IMPLEMENT_SHIP: HIDDEN,
    INTENT_SHIP: HIDDEN,
    INTENT_REMOVE: HIDDEN,
  },
  'experiment_risks': {
    INTENT_IMPLEMENT: HIDDEN,
    INTENT_EXPERIMENT: VISIBLE_REQUIRED,
    INTENT_EXTEND_TRIAL: VISIBLE_REQUIRED,
    INTENT_IMPLEMENT_SHIP: HIDDEN,
    INTENT_SHIP: HIDDEN,
    INTENT_REMOVE: HIDDEN,
  },
  'experiment_extension_reason': {
    INTENT_IMPLEMENT: HIDDEN,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: VISIBLE_REQUIRED,
    INTENT_IMPLEMENT_SHIP: HIDDEN,
    INTENT_SHIP: HIDDEN,
    INTENT_REMOVE: HIDDEN,
  },
  'ongoing_constraints': {
    INTENT_IMPLEMENT: HIDDEN,
    INTENT_EXPERIMENT: VISIBLE_OPTIONAL,
    INTENT_EXTEND_TRIAL: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT_SHIP: HIDDEN,
    INTENT_SHIP: HIDDEN,
    INTENT_REMOVE: HIDDEN,
  },
  'all_platforms_descr': {
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'ergonomics_risks': {
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'activation_risks': {
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'security_risks': {
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'origin_trial_feedback_url': {
    INTENT_IMPLEMENT: HIDDEN,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: HIDDEN,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
};

function intentStageChanged(stage) {
  function setRequired(id, required) {
    if (required) {
      document.querySelector('#id_' + id).setAttribute('required', 'required');
    } else {
      document.querySelector('#id_' + id).removeAttribute('required');
    }
  }

  function show(id) {
    // Clear the inline style for the control's table row.
    document.querySelector('#id_' + id).parentNode.parentNode.style = '';
  }

  function hide(id) {
    // Set the control's table row style to display: none.
    document.querySelector('#id_' + id).parentNode.parentNode.style.display = 'none';
  }

  let stageIndex = INTENT_IDENTIFIER_NAMES[Number(stage.value)];

  for (let id in FORM_FIELD_GRAPH) {
    if (!FORM_FIELD_GRAPH.hasOwnProperty(id))
      continue

    if (FORM_FIELD_GRAPH[id][stageIndex][FORM_FIELD_SHOW_POS]) {
      show(id);
    } else {
      hide(id);
    }

    if (FORM_FIELD_GRAPH[id][stageIndex][FORM_FIELD_REQUIRED_POS]) {
      setRequired(id, true);
    } else {
      setRequired(id, false);
    }
  }

  let intentStageName = document.querySelector('#id_intent_stage_name')

  if (intentStageName) {
    intentStageName.textContent =
      stage.options[stage.options.selectedIndex].textContent;
  }
}

document.addEventListener('DOMContentLoaded', function() {
  document.body.classList.remove('loading');

  // Get around Django rendering input type="text" fields for URLs.
  const inputs = document.querySelectorAll('[name$="_url"], [name$="_link"]');
  [].forEach.call(inputs, function(input) {
    input.type = 'url';
    input.placeholder = 'http://';
  });

  const shippedInputs = document.querySelectorAll('[name^="shipped_"]');
  [].forEach.call(shippedInputs, function(input) {
    input.type = 'number';
    input.placeholder = 'Milestone #';
  });

  const owner = document.querySelector('[name="owner"]');
  owner.type = 'email';
  owner.multiple = true;

  toggleMilestones(document.querySelector('#id_impl_status_chrome'));

  intentStageChanged(document.querySelector('#id_intent_stage'));
});

document.body.addEventListener('ajax-delete', function(e) {
  if (e.detail.status === 200) {
    location.href = '/features';
  }
});
})();
