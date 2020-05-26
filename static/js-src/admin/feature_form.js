(function() {
'use strict';

const fields = document.querySelectorAll('input, textarea');
for (let i = 0; i < fields.length; ++i) {
  fields[i].addEventListener('blur', (e) => {
    e.target.classList.add('interacted');
  });
}

// TODO(ericbidelman): These values are brittle if changed in the db later on.
const MIN_MILESTONE_TO_BE_ACTIVE = 3;
const NO_LONGER_PURSUING = 1000;

document.querySelector('[name=feature_form]').addEventListener('change', (e) => {
  switch (e.target.tagName.toLowerCase()) {
    case 'select':
      if (e.target.id === 'id_impl_status_chrome') {
        toggleMilestones(e.target);
      } else if (e.target.id === 'id_intent_stage' ||
                 e.target.id === 'id_category') {
        intentStageChanged();
      }
      break;
    default:
      break;
  }
});

// Only admins see this button
if (document.querySelector('.delete-button')) {
  document.querySelector('.delete-button').addEventListener('click', (e) => {
    if (!confirm('Delete feature?')) {
      return;
    }

    fetch(`/admin/features/delete/${e.currentTarget.dataset.id}`, {
      method: 'POST',
      credentials: 'include',
    }).then((resp) => {
      if (resp.status === 200) {
        location.href = '/features';
      }
    });
  });
}


if (document.querySelector('#cancel-button')) {
  document.querySelector('#cancel-button').addEventListener('click', (e) => {
    location.href = `/guide/edit/${e.currentTarget.dataset.id}`;
  });
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

const INTENT_NONE = 0;
const INTENT_IMPLEMENT = 1;
const INTENT_EXPERIMENT = 2;
const INTENT_EXTEND_TRIAL = 3;
const INTENT_IMPLEMENT_SHIP = 4;
const INTENT_SHIP = 5;
const INTENT_REMOVE = 6;

let INTENT_IDENTIFIER_NAMES = {};

INTENT_IDENTIFIER_NAMES[INTENT_NONE] = 'INTENT_NONE';
INTENT_IDENTIFIER_NAMES[INTENT_IMPLEMENT] = 'INTENT_IMPLEMENT';
INTENT_IDENTIFIER_NAMES[INTENT_EXPERIMENT] = 'INTENT_EXPERIMENT';
INTENT_IDENTIFIER_NAMES[INTENT_EXTEND_TRIAL] = 'INTENT_EXTEND_TRIAL';
INTENT_IDENTIFIER_NAMES[INTENT_IMPLEMENT_SHIP] = 'INTENT_IMPLEMENT_SHIP';
INTENT_IDENTIFIER_NAMES[INTENT_SHIP] = 'INTENT_SHIP';
INTENT_IDENTIFIER_NAMES[INTENT_REMOVE] = 'INTENT_REMOVE';

// An object graph mapping form fields to implementation status and whether or
// not the form field is shown or hidden (first 1/0) and required or optional
// (second 1/0).

const FORM_FIELD_SHOW_POS = 0;
const FORM_FIELD_REQUIRED_POS = 1;

const HIDDEN = [0, 0];
const VISIBLE_OPTIONAL = [1, 0];
const VISIBLE_REQUIRED = [1, 1];

const FORM_FIELD_GRAPH = {
  'intent_to_implement_url': {
    INTENT_NONE: HIDDEN,
    INTENT_IMPLEMENT: HIDDEN,
    INTENT_EXPERIMENT: VISIBLE_OPTIONAL,
    INTENT_EXTEND_TRIAL: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT_SHIP: HIDDEN,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'explainer_links': {
    INTENT_NONE: HIDDEN,
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: HIDDEN,
  },
  'doc_links': {
    INTENT_NONE: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: VISIBLE_REQUIRED,
    INTENT_EXTEND_TRIAL: VISIBLE_REQUIRED,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'spec_link': {
    INTENT_NONE: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: VISIBLE_OPTIONAL,
    INTENT_EXTEND_TRIAL: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'standardization': {
    INTENT_NONE: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'tag_review': {
    INTENT_NONE: HIDDEN,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: HIDDEN,
  },
  'wpt': {
    INTENT_NONE: HIDDEN,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'wpt_descr': {
    INTENT_NONE: HIDDEN,
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'sample_links': {
    INTENT_NONE: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: HIDDEN,
  },
  'bug_url': {
    INTENT_NONE: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'blink_components': {
    INTENT_NONE: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'impl_status_chrome': {
    INTENT_NONE: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'prefixed': {
    INTENT_NONE: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'footprint': {
    INTENT_NONE: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'interop_compat_risks': {
    INTENT_NONE: HIDDEN,
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'motivation': {
    INTENT_NONE: HIDDEN,
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: HIDDEN,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'ff_views': {
    INTENT_NONE: VISIBLE_REQUIRED,
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'ie_views': {
    INTENT_NONE: VISIBLE_REQUIRED,
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'safari_views': {
    INTENT_NONE: VISIBLE_REQUIRED,
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'web_dev_views': {
    INTENT_NONE: VISIBLE_REQUIRED,
    INTENT_IMPLEMENT: VISIBLE_REQUIRED,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_REQUIRED,
    INTENT_SHIP: VISIBLE_REQUIRED,
    INTENT_REMOVE: VISIBLE_REQUIRED,
  },
  'ff_views_link': {
    INTENT_NONE: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'ie_views_link': {
    INTENT_NONE: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'safari_views_link': {
    INTENT_NONE: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'web_dev_views_link': {
    INTENT_NONE: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'ff_views_notes': {
    INTENT_NONE: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'ie_views_notes': {
    INTENT_NONE: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'safari_views_notes': {
    INTENT_NONE: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'web_dev_views_notes': {
    INTENT_NONE: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'experiment_goals': {
    INTENT_NONE: HIDDEN,
    INTENT_IMPLEMENT: HIDDEN,
    INTENT_EXPERIMENT: VISIBLE_REQUIRED,
    INTENT_EXTEND_TRIAL: VISIBLE_REQUIRED,
    INTENT_IMPLEMENT_SHIP: HIDDEN,
    INTENT_SHIP: HIDDEN,
    INTENT_REMOVE: HIDDEN,
  },
  'experiment_timeline': {
    INTENT_NONE: HIDDEN,
    INTENT_IMPLEMENT: HIDDEN,
    INTENT_EXPERIMENT: VISIBLE_REQUIRED,
    INTENT_EXTEND_TRIAL: VISIBLE_REQUIRED,
    INTENT_IMPLEMENT_SHIP: HIDDEN,
    INTENT_SHIP: HIDDEN,
    INTENT_REMOVE: HIDDEN,
  },
  'experiment_risks': {
    INTENT_NONE: HIDDEN,
    INTENT_IMPLEMENT: HIDDEN,
    INTENT_EXPERIMENT: VISIBLE_REQUIRED,
    INTENT_EXTEND_TRIAL: VISIBLE_REQUIRED,
    INTENT_IMPLEMENT_SHIP: HIDDEN,
    INTENT_SHIP: HIDDEN,
    INTENT_REMOVE: HIDDEN,
  },
  'experiment_extension_reason': {
    INTENT_NONE: HIDDEN,
    INTENT_IMPLEMENT: HIDDEN,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: VISIBLE_REQUIRED,
    INTENT_IMPLEMENT_SHIP: HIDDEN,
    INTENT_SHIP: HIDDEN,
    INTENT_REMOVE: HIDDEN,
  },
  'ongoing_constraints': {
    INTENT_NONE: HIDDEN,
    INTENT_IMPLEMENT: HIDDEN,
    INTENT_EXPERIMENT: VISIBLE_OPTIONAL,
    INTENT_EXTEND_TRIAL: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT_SHIP: HIDDEN,
    INTENT_SHIP: HIDDEN,
    INTENT_REMOVE: HIDDEN,
  },
  'all_platforms': {
    INTENT_NONE: HIDDEN,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'all_platforms_descr': {
    INTENT_NONE: HIDDEN,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'ergonomics_risks': {
    INTENT_NONE: HIDDEN,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'activation_risks': {
    INTENT_NONE: HIDDEN,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'security_risks': {
    INTENT_NONE: HIDDEN,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'origin_trial_feedback_url': {
    INTENT_NONE: HIDDEN,
    INTENT_IMPLEMENT: HIDDEN,
    INTENT_EXPERIMENT: HIDDEN,
    INTENT_EXTEND_TRIAL: HIDDEN,
    INTENT_IMPLEMENT_SHIP: HIDDEN,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
  'debuggability': {
    INTENT_NONE: HIDDEN,
    INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
    INTENT_EXPERIMENT: VISIBLE_OPTIONAL,
    INTENT_EXTEND_TRIAL: VISIBLE_OPTIONAL,
    INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_SHIP: VISIBLE_OPTIONAL,
    INTENT_REMOVE: VISIBLE_OPTIONAL,
  },
};

// Exceptions by category to the above set of values
const FORM_FIELD_CATEGORY_EXCEPTIONS =
{
  'JavaScript': {
    'tag_review': {
      INTENT_NONE: VISIBLE_OPTIONAL,
      INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
      INTENT_EXPERIMENT: VISIBLE_OPTIONAL,
      INTENT_EXTEND_TRIAL: VISIBLE_OPTIONAL,
      INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
      INTENT_SHIP: VISIBLE_OPTIONAL,
      INTENT_REMOVE: VISIBLE_OPTIONAL,
    },
    'wpt': {
      INTENT_NONE: VISIBLE_OPTIONAL,
      INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
      INTENT_EXPERIMENT: VISIBLE_OPTIONAL,
      INTENT_EXTEND_TRIAL: VISIBLE_OPTIONAL,
      INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
      INTENT_SHIP: VISIBLE_OPTIONAL,
      INTENT_REMOVE: VISIBLE_OPTIONAL,
    },
    'wpt_descr': {
      INTENT_NONE: VISIBLE_OPTIONAL,
      INTENT_IMPLEMENT: VISIBLE_OPTIONAL,
      INTENT_EXPERIMENT: VISIBLE_OPTIONAL,
      INTENT_EXTEND_TRIAL: VISIBLE_OPTIONAL,
      INTENT_IMPLEMENT_SHIP: VISIBLE_OPTIONAL,
      INTENT_SHIP: VISIBLE_OPTIONAL,
      INTENT_REMOVE: VISIBLE_OPTIONAL,
    },
  },
};

function intentStageChanged() {
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

  const stageEl = document.querySelector('#id_intent_stage');
  const stageIndex = Number(stageEl.value);
  const stageIdentifier = INTENT_IDENTIFIER_NAMES[stageIndex];

  const category = document.querySelector('#id_category').selectedOptions[0].textContent;

  for (let id in FORM_FIELD_GRAPH) {
    if (!FORM_FIELD_GRAPH.hasOwnProperty(id)) {
      continue;
    }

    let formFieldValues = FORM_FIELD_GRAPH[id][stageIdentifier];

    if (category in FORM_FIELD_CATEGORY_EXCEPTIONS &&
        id in FORM_FIELD_CATEGORY_EXCEPTIONS[category] &&
        stageIdentifier in FORM_FIELD_CATEGORY_EXCEPTIONS[category][id]) {
      formFieldValues = FORM_FIELD_CATEGORY_EXCEPTIONS[category][id][stageIdentifier];
    }

    if (formFieldValues[FORM_FIELD_SHOW_POS]) {
      show(id);
    } else {
      hide(id);
    }

    if (formFieldValues[FORM_FIELD_REQUIRED_POS]) {
      setRequired(id, true);
    } else {
      setRequired(id, false);
    }
  }

  // Update the "Intent to <X>" wording in the form to match the intent stage.
  let intentStageNameEl = document.querySelector('#id_intent_stage_name');

  if (intentStageNameEl) {
    if (stageIndex != INTENT_NONE) {
      intentStageNameEl.textContent =
        stageEl.options[stageEl.options.selectedIndex].textContent;
    } else {
      intentStageNameEl.textContent = '...';
    }
  }

  // Disable the "Generate Intent to..." checkbox when the intent stage is
  // "None" (i.e. for entries created before the notion of an intent stage was
  // known to Features).
  let intentToImplementEl = document.querySelector('#id_intent_to_implement');

  if (intentToImplementEl) {
    if (stageIndex == INTENT_NONE) {
      intentToImplementEl.disabled = true;
      intentToImplementEl.checked = false;
    } else {
      intentToImplementEl.disabled = false;
    }
  }
}

document.addEventListener('DOMContentLoaded', function() {
  document.body.classList.remove('loading');

  // Get around Django rendering input type="text" fields for URLs.
  const inputsEls = document.querySelectorAll('[name$="_url"], [name$="_link"]');
  [].forEach.call(inputsEls, function(inputEl) {
    inputEl.type = 'url';
    inputEl.placeholder = 'http://';
  });

  const shippedInputEls = document.querySelectorAll('[name^="shipped_"]');
  [].forEach.call(shippedInputEls, function(inputEl) {
    inputEl.type = 'number';
    inputEl.placeholder = 'Milestone #';
  });

  const ownerEl = document.querySelector('[name="owner"]');
  ownerEl.type = 'email';
  ownerEl.multiple = true;

  toggleMilestones(document.querySelector('#id_impl_status_chrome'));

  intentStageChanged();
});
})();
