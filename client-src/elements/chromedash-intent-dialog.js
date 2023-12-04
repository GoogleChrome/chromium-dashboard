import {LitElement, html, css, nothing} from 'lit-element';
import {INTENT_STAGES} from './form-field-enums.js';
import {SHARED_STYLES} from '../css/shared-css.js';

/*
# -*- coding: utf-8 -*-
# Copyright 2021 Google Inc.
# intentpreview.py:
#
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# from google.appengine.api import users
from api.converters import feature_entry_to_json_verbose

from internals import core_enums
from internals import processes
from internals import stage_helpers
from framework import basehandlers
from framework import permissions
*/


// INTENT_PARAM = 'intent'
// LAUNCH_PARAM = 'launch'
// VIEW_FEATURE_URL = '/feature'

// const INTENT_PARAM = 'intent';
// const LAUNCH_PARAM = 'launch';
const VIEW_FEATURE_URL = '/feature';
// const INTENT_EMAIL_SECTIONS = {
//   INTENT_NONE: [],
//   INTENT_INCUBATE: [],
//   INTENT_IMPLEMENT: ['motivation'],
//   INTENT_EXPERIMENT: ['i2p_thread', 'experiment'],
//   INTENT_IMPLEMENT_SHIP: [
//     'need_api_owners_lgtms', 'motivation', 'tracking_bug', 'sample_links'],
//   INTENT_EXTEND_TRIAL: [
//     'i2p_thread', 'experiment', 'extension_reason'],
//   INTENT_SHIP: [
//     'need_api_owners_lgtms', 'i2p_thread', 'tracking_bug', 'sample_links',
//     'anticipated_spec_changes', 'ship'],
//   INTENT_REMOVED: [],
//   INTENT_SHIPPED: [],
//   INTENT_PARKED: [],
// };

let intentDialogEl = null;


export function templateAsString(data) {
  const {strings, values} = data;
  const valueList = [...values, '']; // + last empty part
  const resultList = [];
  for (let i = 0; i < strings.length; i++) {
    let v = valueList[i];
    if (v._$litType$ !== undefined) {
      v = templateAsString(v); // embedded Template
    } else if (v instanceof Array) {
      // array of strings or templates.
      let newValue = '';
      for (const innerValue of [...v]) {
        newValue += templateAsString(innerValue);
      }
      v = newValue;
    }
    resultList.push(strings[i] + v);
  }
  return resultList.join('');
}

export async function openIntentDialog(
  feature, progress, process, action, stage, feStage, featureGates) {
  if (!intentDialogEl) {
    intentDialogEl = document.createElement('chromedash-intent-dialog');
    document.body.appendChild(intentDialogEl);
    await intentDialogEl.updateComplete;
  }
  intentDialogEl.openWithContext(
    feature, progress, process, action, stage, feStage, featureGates);
}


class ChromeDashIntentDialog extends LitElement {
  static get properties() {
    return {
      // Define properties here
      // subject_prefix: {type: String},
      feature: {type: Object},
      stage_info: {type: Object},
      // should_render_mstone_table: {type: Boolean},
      // should_render_intents: {type: Boolean},
      sections_to_show: {type: Array},
      intent_stage: {type: String},
      default_url: {type: String},
    };
  } //

  constructor() {
    super();

    // Initialize properties here.  Order is important.
    this.blinkDevEmail = 'blinkDevEmail';
    this.feature = {};
    this.stage_info = this.feature.stages;
    this.intent = true;
    this.intent_stage = '';
    this.subject_prefix = this.computeSubjectPrefix(this.intent_stage);
    // this.should_render_mstone_table = this.stage_info['should_render_mstone_table'];
    // this.should_render_intents = this.stage_info['should_render_intents'];
    this.sections_to_show = [];
    this.default_url = '';

    // const pageData = {
    //   'subject_prefix': this.computeSubjectPrefix(intent_stage),
    //   'feature': feature,
    //   'stage_info': stage_info,
    //   'should_render_mstone_table': stage_info['should_render_mstone_table'],
    //   'should_render_intents': stage_info['should_render_intents'],
    //   'sections_to_show': processes.INTENT_EMAIL_SECTIONS.get(
    //     intent_stage, []),
    //   'intent_stage': intent_stage,
    //   'default_url': '%s://%s%s/%s' % (
    //     this.request.scheme, this.request.host,
    //     VIEW_FEATURE_URL, feature.id),
    // };
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      :host {
        flex-direction: column;
        counter-reset: h3;
        height: auto;
      }
      :host section {
        max-width: 600px;
        flex: 1 0 auto;
        margin-bottom: 15px;
      }
      :host section > div {
        background: white;
        border: 1px solid #ddd;
        box-shadow: rgba(0, 0, 0, 0.067) 1px 1px 4px;
        padding: 12px;
        margin: 8px 0 16px 0;
      }
      :host section > p {
        color: #444;
      }
      :host h3 {
        margin-bottom: 10px;
      }
      :host h3:before {
        counter-increment: h3;
        content: counter(h3) ".";
        margin-right: 5px;
      }

      :host .subject {
        font-size: 16px;
        margin-bottom: 10px;
      }

      :host .email .help {
        font-style: italic;
        color: #aaa;
      }
      :host .email h4 {
        font-weight: 600;
      }

      :host .alertbox {
        margin: 2em;
        padding: 1em;
        background: var(--warning-background);
        color: var(--warning-color);
      }
      `];
  }


  openWithContext(
    feature, _progress, _process, _action, _stage, feStage, featureGates) {
    this.feature = feature;
    this.stage_info = this.feature.stages;
    this.intent = true;
    this.intent_stage = feStage.intent_stage;
    this.subject_prefix = this.computeSubjectPrefix(this.intent_stage);

    // Not necessarily valid:
    this.featureGates = featureGates;

    this.shadowRoot.querySelector('sl-dialog').show();
  }
  /*
  def getPageData(self, feature_id, f, intent_stage):
    """Return a dictionary of data used to render the page."""
    stage_info = stage_helpers.get_stage_info_for_templates(f)
    page_data = {
        'subject_prefix': self.computeSubjectPrefix(f, intent_stage),
        'feature': feature_entry_to_json_verbose(f),
        'stage_info': stage_info,
        'should_render_mstone_table': stage_info['should_render_mstone_table'],
        'should_render_intents': stage_info['should_render_intents'],
        'sections_to_show': processes.INTENT_EMAIL_SECTIONS.get(
            intent_stage, []),
        'intent_stage': intent_stage,
        'default_url': '%s://%s%s/%s' % (
            self.request.scheme, self.request.host,
            VIEW_FEATURE_URL, feature_id),
    }
*/
  getPageData(
    feature,
    intentStage,
  ) {
    this.feature = feature;
    // Return a dictionary of data used to render the page.
    const stageInfo = feature.stages;
    const pageData = {
      'subject_prefix': this.computeSubjectPrefix(intentStage),
      'feature': feature,
      'stage_info': stageInfo,
      'should_render_mstone_table': stageInfo['should_render_mstone_table'],
      'should_render_intents': stageInfo['should_render_intents'],
      'sections_to_show': processes.INTENT_EMAIL_SECTIONS.get(
        intentStage, []),
      'intent_stage': intentStage,
      'default_url': '%s://%s%s/%s' % (
        this.request.scheme, this.request.host,
        VIEW_FEATURE_URL, feature.id),
    };
    return pageData;
  }

  /*
  # class IntentEmailPreviewHandler(basehandlers.FlaskHandler):
  """Show a preview of an intent email, as appropriate to the feature stage."""

  TEMPLATE_PATH = 'admin/features/launch.html'

  def getTemplateData(self, **kwargs):
    # Validate the user has edit permissions and redirect if needed.
    feature_id = kwargs.get('feature_id', None)
    stage_id = kwargs.get('stage_id', None)

    redirect_resp = permissions.validate_feature_edit_permission(
        self, feature_id)
    if redirect_resp:
      return redirect_resp

    f = self.get_specified_feature(feature_id=feature_id)
    intent_stage = stage_id if stage_id is not None else f.intent_stage

    page_data = self.getPageData(feature_id, f, intent_stage)
    return page_data
    */

  getTemplateData(
    featureId,
    stageId,
  ) {
    // Validate the user has edit permissions and redirect if needed.
    const redirectResp = permissions.validate_feature_edit_permission(
      this, featureId,
    );
    if (redirectResp) {
      return redirectResp;
    }
    f = this.get_specified_feature(featureId);
    const intentStage = stageId || f.intent_stage;
    const pageData = this.getPageData(featureId, f, intentStage);
    return pageData;
  }

  /*

    if LAUNCH_PARAM in self.request.args:
      page_data[LAUNCH_PARAM] = True
    if INTENT_PARAM in self.request.args:
      page_data[INTENT_PARAM] = True

    return page_data

  def computeSubjectPrefix(self, feature, intent_stage):
    """Return part of the subject line for an intent email."""

    if intent_stage == core_enums.INTENT_INCUBATE:
      if feature.feature_type == core_enums.FEATURE_TYPE_DEPRECATION_ID:
        return 'Intent to Deprecate and Remove'
    elif intent_stage == core_enums.INTENT_IMPLEMENT:
      return 'Intent to Prototype'
    elif intent_stage == core_enums.INTENT_EXPERIMENT:
      return 'Ready for Developer Testing'
    elif intent_stage == core_enums.INTENT_EXTEND_TRIAL:
      if feature.feature_type == core_enums.FEATURE_TYPE_DEPRECATION_ID:
        return 'Request for Deprecation Trial'
      else:
        return 'Intent to Experiment'
    elif intent_stage == core_enums.INTENT_SHIP:
      if feature.feature_type == core_enums.FEATURE_TYPE_CODE_CHANGE_ID:
        return 'Web-Facing Change PSA'
      else:
        return 'Intent to Ship'
    elif intent_stage == core_enums.INTENT_REMOVED:
      return 'Intent to Extend Deprecation Trial'

    return 'Intent stage "%s"' % core_enums.INTENT_STAGES[intent_stage]
*/

  computeSubjectPrefix() {
    const intentStage = this.intent_stage;
    if (intentStage == INTENT_STAGES.INTENT_INCUBATE[0]) {
      if (this.feature.feature_type == INTENT_STAGES.FEATURE_TYPE_DEPRECATION_ID[0]) {
        return 'Intent to Deprecate and Remove';
      }
    } else if (intentStage == INTENT_STAGES.INTENT_IMPLEMENT[0]) {
      return 'Intent to Prototype';
    } else if (intentStage == INTENT_STAGES.INTENT_EXPERIMENT[0]) {
      return 'Ready for Developer Testing';
    } else if (intentStage == INTENT_STAGES.INTENT_EXTEND_TRIAL[0]) {
      if (this.feature.feature_type == INTENT_STAGES.FEATURE_TYPE_DEPRECATION_ID[0]) {
        return 'Request for Deprecation Trial';
      } else {
        return 'Intent to Experiment';
      }
    } else if (intentStage == INTENT_STAGES.INTENT_SHIP[0]) {
      if (this.feature.feature_type == INTENT_STAGES.FEATURE_TYPE_CODE_CHANGE_ID[0]) {
        return 'Web-Facing Change PSA';
      } else {
        return 'Intent to Ship';
      }
    } else if (intentStage == INTENT_STAGES.INTENT_REMOVED[0]) {
      return 'Intent to Extend Deprecation Trial';
    }
  }

  // Instead of vertical margins, <br> elements are used to create line breaks
  // that can be copied and pasted into a text editor.

  /*
  {% extends "_base.html" %}
  */

  /*
{% block page_title %}{{ feature.name }} - {% endblock %}

{% block css %}
<link rel="stylesheet" href="/static/css/forms.css?v={{app_version}}">
<link rel="stylesheet" href="/static/css/features/launch.css?v={{app_version}}">
{% endblock %}

*/

  /*
{% block subheader %}
<div id="subheader">
  <div>
    <h2>Next steps for the Blink launch process</h2>
  </div>
</div>
{% endblock %}

{% block content %}

{% if feature.unlisted %}
<div class="alertbox">
  Important: This feature is currently unlisted.  Please only share
  feature details with people who are collaborating with you on
  the feature.
</div>
{% endif %}

{% if launch %}
<section>
<h3>Click through this link to file a launch-tracking bug</h3>
  {% include "blink/launch_bug.html" %}
</section>
{% endif %}

{% if intent %}
<section>
<h3>Reach out to a spec mentor</h3>
<p style="margin-left: 1em">
  Consider showing your draft intent email to your spec mentor or
  sending it to spec-mentors@chromium.org.  They can help make sure
  that your intent email is ready for review.</p>
</section>
{% endif %}

{% if intent %}
<section>
<h3>Copy and send this text for your "Intent to ..." email</h3>

*/

  renderInstructions() {
    // const nextStepsHtml = html`
    // <section>
    // <h2>Next steps for the Blink launch process</h2>
    // <p style="margin-left: 1em">
    //   Click through this link to file a launch-tracking bug
    // </p>
    // </section>
    // `;

    const lauchHtml = this.launch ? html`
  <section>
  <h3>Click through this link to file a launch-tracking bug</h3>
    <!-- Description:
    { DESCRIPTION }

    Changes to API surface:
    Bulleted list here

    Links:
    Chromestatus.com entry: { generated_link }
    Public standards discussion: { SPEC }

    Support from other browsers:
    Firefox: { FF_SUPPORT }
    Edge: { IE_SUPPORT }
    Safari: { SAFARI_SUPPORT }

    *Make sure to fill in any labels with a -?, including all OSes this change
    affects.  Feel free to leave other labels at the defaults.
    -->

    <div>
    TODO
    </div>

  </section>
  ` : '';

    const intentHtml = this.intent ? html`
  <section>
  <h3>Reach out to a spec mentor</h3>
  <p style="margin-left: 1em">
    Consider showing your draft intent email to your spec mentor or
    sending it to spec-mentors@chromium.org.  They can help make sure
    that your intent email is ready for review.</p>
  </section>
  ` : '';

    return html`
  ${lauchHtml}
  ${intentHtml}
  `;
  }

  /*
{% include "blink/intent_to_implement.html" %}

{% endif %}


{% if 'need_api_owners_lgtms' in sections_to_show %}
<section>
<h3>Obtain LGTMs from 3 API Owners</h3>XS
<span class="help">
  You will need three LGTMs from API owners.
According to the
<a href="http://www.chromium.org/blink#launch-process">Blink Launch process</a>
after that, you're free to ship your feature.
</span>
</section>
{% endif %}

{% endblock %}
*/

  renderNeedApiOwnersApproval() {
    if (!this.sections_to_show.includes('need_api_owners_lgtms')) {
      return nothing;
    }
    return html`
    <section>
    <h3>Obtain LGTMs from 3 API Owners</h3>
    <span class="help">
      You will need three LGTMs from API owners.
      According to the
      <a href="http://www.chromium.org/blink#launch-process">Blink Launch process</a>
      after that, you're free to ship your feature.
    </span>
    </section>
    `;
  }


  /*
{% block js %}
<script nonce="{{nonce}}">
// Remove loading spinner at page load.
  document.body.classList.remove('loading');

  const copyEmailBodyEl = document.querySelector('#copy-email-body');
  const emailBodyEl = document.querySelector('.email');
  const toastEl = document.querySelector('chromedash-toast');
  if (copyEmailBodyEl && emailBodyEl) {
      copyEmailBodyEl.addEventListener('click', () => {
          window.getSelection().removeAllRanges();
          const range = document.createRange();
          range.selectNode(emailBodyEl);
          window.getSelection().addRange(range);
          document.execCommand('copy');
          toastEl.showMessage('Email body copied');
      });
  }
</script>
{% endblock %}
*/

  renderSubheader() {
    const header = html`
      <p>Email to
        <div class="subject">${this.blinkDevEmail}</div>
      </p>

      <p>Subject
        <div class="subject">${this.subject_prefix}: ${this.feature.name}</div>
      </p>

      <p>
        Body
        <span
          class="tooltip copy-text"
          style="float:right"
          title="Copy text to clipboard">
          <a href="#" data-tooltip>
            <iron-icon
              icon="chromestatus:content_copy"
              id="copy-email-body"
            ></iron-icon>
          </a>
        </span>
      </p>
    `;
    return header;
  }

  //   // Convert the following django template into a lit template render methods.
  //   /*
  //   <h4>Contact emails</h4>
  //   {% if not feature.browsers.chrome.owners %}None{% endif %}
  //   {% for owner in feature.browsers.chrome.owners %}
  //     <a href="mailto:{{owner}}">{% if loop.last %}{{owner}}</a>{% else %}{{owner}}</a>,{% endif %}
  //   {% endfor %}
  //   */


  renderContactEmails() {
    const owners = this.feature.browsers.chrome.owners;
    const ownersList = !owners ? html`None` : owners.map(
      (owner) => html` <a href="mailto:${owner}">${owner}</a> `,
    );
    return html`
        <h4>Contact emails</h4>
        ${ownersList}
        <br /><br />
      `;
  }

  //   /*
  //   {% if feature.explainer_links or feature.feature_type_int != 2 %}
  //     <br><br><h4>Explainer</h4>
  //     {% if not feature.explainer_links %}None{% endif %}
  //     {% for link in feature.explainer_links %}
  //       {% if loop.index0 %}<br>{% endif %}<a href="{{link}}">{{link}}</a>
  //     {% endfor %}
  //   {% endif %}
  //   */

  renderExplainerLinks() {
    const explainerLinks = this.feature.explainer_links;
    if (!explainerLinks && this.feature.feature_type_int === 2) {
      return nothing;
    }
    const explainerLinksList = explainerLinks.map(
      (link) => html`
        <a href="${link}">${link}</a>
      `,
    );
    return html`
      <h4>Explainer</h4>
      ${(explainerLinks && explainerLinks.length > 0) ?
        html`<br />${explainerLinksList.join(html`<br />`)}` :
        'None'}
      <br /><br />
    `;
  }

  //   /*
  //   <br><br><h4>Specification</h4>
  //   {{feature.standards.spec|urlize}}
  //   */

  renderSpec() {
    const spec = this.feature.standards.spec;
    return html`
      <h4>Specification</h4>
      <a href="${spec}">${spec}</a>
      <br /><br />
    `;
  }

  //   /*
  //   {% if feature.resources and feature.resources.docs %}
  //     <br><br><h4>Design docs</h4>
  //     {% for link in feature.resources.docs %}
  //       <br><a href="{{link}}">{{link}}</a>
  //     {% endfor %}
  //   {% endif %}
  //   */

  renderDesignDocs() {
    const docs = this.feature.resources.docs;
    if (!docs) {
      return nothing;
    }
    const docsList = docs.map(
      (link) => html` <br /><a href="${link}">${link}</a> `,
    );
    return html`
      <h4>Design docs</h4>
      ${docsList}
      <br /><br />
    `;
  }

  //   /*
  //   <br><br><h4>Summary</h4>
  //   <p class="preformatted">{{ feature.summary | urlize }}</p>
  //   */

  renderSummary() {
    const summary = this.feature.summary;
    return html`
      <h4>Summary</h4>
      <p class="preformatted">${summary}</p>
      <br /><br />
    `;
  }

  //   /*
  //   <br><br><h4>Blink component</h4>
  //   {% for c in feature.browsers.chrome.blink_components %}
  //     <a href="https://bugs.chromium.org/p/chromium/issues/list?q=component:{{c}}" target="_blank" rel="noopener">{{c}}</a>
  //   {% endfor %}
  //   */

  renderBlinkComponents() {
    const blinkComponents = this.feature.browsers.chrome.blink_components;
    const blinkComponentList = blinkComponents.map(
      (c) => html`
        <a
          href="https://bugs.chromium.org/p/chromium/issues/list?q=component:${c}"
          target="_blank"
          rel="noopener"
          >${c}</a
        >
      `,
    );
    return html`
      <h4>Blink component</h4>
      ${blinkComponentList}
      <br /><br />
    `;
  }

  //   /*
  //   {% if 'motivation' in sections_to_show %}
  //     <br><br><h4>Motivation</h4>
  //     <p class="preformatted">{{feature.motivation|urlize}}</p>

  //     <br><br><h4>Initial public proposal</h4>
  //     {{feature.initial_public_proposal_url|urlize}}
  //   {% endif %}
  //   */

  renderMotivation() {
    const motivation = this.feature.motivation;
    if (!motivation) {
      return nothing;
    }
    return html`
      <h4>Motivation</h4>
      <p class="preformatted">${motivation}</p>

      <br /><br />
      <h4>Initial public proposal</h4>

      <a href="${this.feature.initial_public_proposal_url}"
        >${this.feature.initial_public_proposal_url}</a
      >
      <br /><br />
    `;
  }

  //   //   html`
  //   //       <br><br><h4>Intent to implement</h4>
  //   //       <a href="${feature.intent_to_implement_url}">${feature.intent_to_implement_url}</a>
  //   //       <br><br><h4>Intent to Experiment</h4>

  //   //       <a href="${feature.intent_to_experiment_url}">${feature.intent_to_experiment_url}</a>

  //   //       <br><br><h4>Intent to Ship</h4>
  //   //       <a href="${feature.intent_to_ship_url}">${feature.intent_to_ship_url}</a>
  //   //       <br><br><h4>Intent to Deprecate</h4>
  //   //       <a href="${feature.intent_to_deprecate_url}">${feature.intent_to_deprecate_url}</a
  //   //     `;

  //   /*
  //   {% if feature.tags %}
  //     <br><br><h4>Search tags</h4>
  //     {% for tag in feature.tags %}
  //       <a href="/features#tags:{{tag}}">{{tag}}</a>{% if not loop.last %}, {% endif %}
  //     {% endfor %}

  //   {% endif %}
  //   */

  renderSearchTags() {
    const tags = this.feature.tags;
    if (!tags) {
      return nothing;
    }
    const tagsList = tags.map(
      (tag) => html` <a href="/features#tags:${tag}">${tag}</a> `,
    );
    return html`
      <h4>Search tags</h4>
      ${tagsList.join(', ')}
      <br /><br />
    `;
  }

  //   /*
  //   <br><br><h4>TAG review</h4>
  //   {{feature.tag_review|urlize}}
  //   */
  renderTagReview() {
    const tagReview = this.feature.tag_review;
    return html`
      <h4>TAG review</h4>
      <a href="${tagReview}">${tagReview}</a>
      <br /><br />
    `;
  }

  //   /*
  //   {% if feature.tag_review_status %}
  //     <br><br><h4>TAG review status</h4>
  //     {{feature.tag_review_status}}
  //   {% endif %}
  //   */

  //   renderTagReviewStatus() {
  //     const tagReviewStatus = this.feature.tag_review_status;
  //     if (!tagReviewStatus) {
  //       return nothing;
  //     }
  //     return html`
  //       <h4>TAG review status</h4>
  //       ${tagReviewStatus}
  //     `;
  //   }

  //   /*
  //   {% for stage in stage_info.ot_stages %}
  //     {% if stage.ot_chromium_trial_name %}
  //       <br><br><h4>Chromium Trial Name</h4>
  //       {{stage.ot_chromium_trial_name}}
  //     {% endif %}

  //     {% if stage.origin_trial_feedback_url %}
  //       <br><br><h4>Link to origin trial feedback summary</h4>
  //       {{stage.origin_trial_feedback_url}}
  //     {% endif %}

  //     {% if stage.ot_documentation_url %}
  //       <br><br><h4>Origin Trial documentation link</h4>
  //       {{stage.ot_documentation_url}}
  //     {% endif %}

  //     {% if stage.ot_webfeature_use_counter %}
  //       <br><br><h4>WebFeature UseCounter name</h4>
  //       {{stage.ot_webfeature_use_counter}}
  //     {% endif %}
  //   {% endfor %}
  //   */

  //   renderOTInfo() {
  //     const otStages = stage_info.ot_stages;
  //     if (!otStages) {
  //       return nothing;
  //     }

  //     const otInfoList = otStages.map(
  //       (stage) => html`
  //         ${stage.ot_chromium_trial_name ?
  //           html`
  //               <br /><br />
  //               <h4>Chromium Trial Name</h4>
  //               ${stage.ot_chromium_trial_name}
  //             ` :
  //           nothing}
  //         ${stage.origin_trial_feedback_url ?
  //           html`
  //               <br /><br />
  //               <h4>Link to origin trial feedback summary</h4>
  //               ${stage.origin_trial_feedback_url}
  //             ` :
  //           nothing}
  //         ${stage.ot_documentation_url ?
  //           html`
  //               <br /><br />
  //               <h4>Origin Trial documentation link</h4>
  //               ${stage.ot_documentation_url}
  //             ` :
  //           nothing}
  //         ${stage.ot_webfeature_use_counter ?
  //           html`
  //               <br /><br />
  //               <h4>WebFeature UseCounter name</h4>
  //               ${stage.ot_webfeature_use_counter}
  //             ` :
  //           nothing}
  //       `,
  //     );

  //     return html` ${otInfoList} `;
  //   }

  //   /*
  //     <br><br><h4>Interoperability and Compatibility</h4>
  //     <p class="preformatted">{{feature.interop_compat_risks|urlize}}</p>
  //     */

  //   renderInteropCompatRisks() {
  //     const interopCompatRisks = this.feature.interop_compat_risks;
  //     return html`
  //       <br /><br />
  //       <h4>Interoperability and Compatibility</h4>
  //       <p class="preformatted">${interopCompatRisks}</p>
  //     `;
  //   }

  //   /*
  //     <br><br><i>Gecko</i>: {{feature.browsers.ff.view.text}}
  //     {% if feature.browsers.ff.view.url %}
  //       (<a href="{{feature.browsers.ff.view.url}}">{{feature.browsers.ff.view.url}}</a>)
  //     {% endif %}
  //     {% if feature.browsers.ff.view.notes %}
  //      {{feature.browsers.ff.view.notes|urlize}}
  //     {% endif %}
  //     */

  //   renderGeckoRisks() {
  //     const geckoInfo = this.feature.browsers.ff;
  //     return html`
  //       <br /><br />
  //       <i>Gecko</i>:
  //       ${geckoInfo.view.text}
  //       ${geckoInfo.view.url ?
  //         html` (<a href="${geckoInfo.view.url}">${geckoInfo.view.url}</a>) ` :
  //         nothing}
  //       ${geckoInfo.view.notes ? html` ${geckoInfo.view.notes} ` : nothing}
  //     `;
  //   }

  //   /*
  //     <br><br><i>WebKit</i>: {{feature.browsers.safari.view.text}}
  //     {% if feature.browsers.safari.view.url %}
  //       (<a href="{{feature.browsers.safari.view.url}}">{{feature.browsers.safari.view.url}}</a>)
  //     {% endif %}
  //     {% if feature.browsers.safari.view.notes %}
  //      {{feature.browsers.safari.view.notes|urlize}}
  //     {% endif %}
  //     */

  //   renderWebKitRisks() {
  //     const webkitInfo = this.feature.browsers.safari;
  //     return html`
  //       <br /><br />
  //       <i>WebKit</i>:
  //       ${webkitInfo.view.text}
  //       ${webkitInfo.view.url ?
  //         html` (<a href="${webkitInfo.view.url}">${webkitInfo.view.url}</a>) ` :
  //         nothing}
  //       ${webkitInfo.view.notes ? html` ${webkitInfo.view.notes} ` : nothing}
  //     `;
  //   }

  //   /*
  //     <br><br><i>Web developers</i>: {{feature.browsers.webdev.view.text}}
  //     {% if feature.browsers.webdev.view.url %}
  //       (<a href="{{feature.browsers.webdev.view.url}}">{{feature.browsers.webdev.view.url}}</a>)
  //     {% endif %}
  //     {% if feature.browsers.webdev.view.notes %}
  //       {{feature.browsers.webdev.view.notes|urlize}}
  //     {% endif %}
  //     */
  //   renderWebDevRisks() {
  //     const webDevInfo = this.feature.browsers.webdev;
  //     return html`
  //       <br /><br />
  //       <i>Web developers</i>:
  //       ${webDevInfo.view.text}
  //       ${webDevInfo.view.url ?
  //         html` (<a href="${webDevInfo.view.url}">${webDevInfo.view.url}</a>) ` :
  //         nothing}
  //       ${webDevInfo.view.notes ? html` ${webDevInfo.view.notes} ` : nothing}
  //     `;
  //   }

  //   /*
  //     <br><br><i>Other signals</i>:
  //     {% if feature.browsers.other.view.notes %}
  //       {{feature.browsers.other.view.notes|urlize}}
  //     {% endif %}
  //     */
  //   renderOtherNotes() {
  //     const notes = this.feature.browsers.other.view.notes;
  //     return html`
  //       <br /><br />
  //       <i>Other signals</i>:
  //       : ${notes ? html` ${notes} ` : nothing}
  //     `;
  //   }

  //   /*
  //     {% if feature.ergonomics_risks %}
  //       <br><br><h4>Ergonomics</h4>
  //       <p class="preformatted">{{feature.ergonomics_risks|urlize}}</p>
  //     {% endif %}
  //     */
  //   renderErgonomicsRisks() {
  //     const ergonomicsRisks = this.feature.ergonomics_risks;
  //     if (!ergonomicsRisks) {
  //       return nothing;
  //     }
  //     return html`
  //       <br /><br />
  //       <h4>Ergonomics</h4>
  //       <p class="preformatted">${ergonomicsRisks}</p>
  //     `;
  //   }

  //   /*
  //     {% if feature.activation_risks %}
  //       <br><br><h4>Activation</h4>
  //       <p class="preformatted">{{feature.activation_risks|urlize}}</p>
  //     {% endif %}
  //     */
  //   renderActivationRisks() {
  //     const activationRisks = this.feature.activation_risks;
  //     if (!activationRisks) {
  //       return nothing;
  //     }
  //     return html`
  //       <br /><br />
  //       <h4>Activation</h4>
  //       <p class="preformatted">${activationRisks}</p>
  //     `;
  //   }

  //   /*
  //     {% if feature.security_risks %}
  //       <br><br><h4>Security</h4>
  //       <p class="preformatted">{{feature.security_risks|urlize}}</p>
  //     {% endif %}
  //     */

  //   renderSecurityRisks() {
  //     const securityRisks = this.feature.security_risks;
  //     if (!securityRisks) {
  //       return nothing;
  //     }
  //     return html`
  //       <br /><br />
  //       <h4>Security</h4>
  //       <p class="preformatted">${securityRisks}</p>
  //     `;
  //   }

  //   /*
  //     <br><br><h4>WebView application risks</h4>
  //     <p style="font-style: italic">
  //       Does this intent deprecate or change behavior of existing APIs,
  //       such that it has potentially high risk for Android WebView-based
  //       applications?</p>
  //     <p class="preformatted">{{feature.webview_risks|urlize}}</p>
  //     */

  //   renderWebViewRisks() {
  //     const webviewRisks = this.feature.webview_risks;
  //     return html`
  //       <br /><br />
  //       <h4>WebView application risks</h4>
  //       <p style="font-style: italic">
  //         Does this intent deprecate or change behavior of existing APIs, such
  //         that it has potentially high risk for Android WebView-based
  //         applications?
  //       </p>
  //       <p class="preformatted">${webviewRisks}</p>
  //     `;
  //   }

  //   /*
  //   <br><br><h4>Risks</h4>
  //   <div style="margin-left: 4em;">

  //   </div> <!-- end risks -->
  //   */
  //   renderRisks() {
  //     return html`
  //       <br /><br />
  //       <h4>Risks</h4>
  //       <div style="margin-left: 4em;">
  //         ${renderInteropCompatRisks()} ${renderGeckoRisks()}
  //         ${renderWebKitRisks()} ${renderWebDevRisks()} ${renderOtherRisks()}
  //         ${renderErgonomicsRisks()} ${renderActivationRisks()}
  //         ${renderSecurityRisks()} ${renderWebViewRisks()}
  //       </div>
  //       <!-- end risks -->
  //     `;
  //   }

  //   /*
  // {% if 'experiment' in sections_to_show %}

  //   <br><br><h4>Goals for experimentation</h4>
  //   <p class="preformatted">{{feature.experiment_goals|urlize}}</p>

  //   {% if feature.experiment_timeline %}
  //     <br><br><h4>Experimental timeline</h4>
  //     <p class="preformatted">{{feature.experiment_timeline|urlize}}</p>
  //   {% endif %}

  //   {% if 'extension_reason' in sections_to_show %}
  //     {% for stage in stage_info.extension_stages %}
  //       {% if stage.experiment_extension_reason %}
  //         <br><br><h4>Reason this experiment is being extended</h4>
  //         <p class="preformatted">{{stage.experiment_extension_reason|urlize}}</p>
  //       {% endif %}
  //     {% endfor %}
  //   {% endif %}

  //   <br><br><h4>Ongoing technical constraints</h4>
  //   <p class="preformatted">{{feature.ongoing_constraints|urlize}}</p>

  // {% endif %}
  // */

  //   renderExperiment() {
  //     if (!sectionsToShow.includes('experiment')) return nothing;

  //     let extensionStagesHTML = '';
  //     if (sectionsToShow.includes('extension_reason')) {
  //       const stages = this.feature.stage_info.extension_stages;
  //       const extensionsHtml = [];
  //       for (stage in stages) {
  //         if (stage.experiment_extension_reason) {
  //           extensionsHtml.push(html`
  //             <br /><br />
  //             <h4>Reason this experiment is being extended</h4>
  //             <p class="preformatted">${stage.experiment_extension_reason}</p>
  //           `);
  //         }
  //       }
  //       extensionStagesHTML = html` ${extensionsHtml.join('')} `;
  //     }

  //     const experimentInfo = this.feature.experiment_goals;

  //     return html`
  //       <br /><br />
  //       <h4>Goals for experimentation</h4>
  //       <p class="preformatted">${experimentInfo}</p>

  //       ${this.feature.experiment_timeline ?
  //         html`
  //             <br /><br />
  //             <h4>Experimental timeline</h4>
  //             <p class="preformatted">${this.feature.experiment_timeline}</p>
  //           ` :
  //         nothing}

  //       ${extensionStagesHTML}

  //       ${this.feature.ongoing_constraints ?
  //         html`
  //             <br /><br />
  //             <h4>Ongoing technical constraints</h4>
  //             <p class="preformatted">${this.feature.ongoing_constraints}</p>
  //           ` :
  //         nothing}
  //     `;
  //   }

  //   /*
  // <br><br><h4>Debuggability</h4>
  // <p class="preformatted">{{feature.debuggability|urlize}}</p>
  // */

  //   renderDebuggability() {
  //     const debuggability = this.feature.debuggability;
  //     return html`
  //       <br /><br />
  //       <h4>Debuggability</h4>
  //       <p class="preformatted">${debuggability}</p>
  //     `;
  //   }

  //   /*
  // {% if 'experiment' in sections_to_show or 'ship' in sections_to_show %}
  //   <br><br><h4>Will this feature be supported on all six Blink platforms
  //       (Windows, Mac, Linux, Chrome OS, Android, and Android WebView)?</h4>
  //   {% if feature.all_platforms %}Yes{% else %}No{% endif %}
  //   {% if feature.all_platforms_descr %}
  //     <p class="preformatted">{{feature.all_platforms_descr|urlize}}</p>
  //   {% endif %}
  // {% endif %}
  // */

  //   renderAllPlatforms() {
  //     if (!sectionsToShow.includes('experiment') && !sectionsToShow.includes('ship')) {
  //       return nothing;
  //     }

  //     const allPlatforms = this.feature.all_platforms;
  //     return html`
  //       <br /><br />
  //       <h4>
  //         Will this feature be supported on all six Blink platforms (Windows, Mac,
  //         Linux, Chrome OS, Android, and Android WebView)?
  //       </h4>
  //       ${allPlatforms ? 'Yes' : 'No'}
  //       ${this.feature.all_platforms_descr ?
  //         html` <p class="preformatted">${this.feature.all_platforms_descr}</p> ` :
  //         nothing}
  //     `;
  //   }

  //   /*
  // <br><br><h4>Is this feature fully tested by <a href="https://chromium.googlesource.com/chromium/src/+/main/docs/testing/web_platform_tests.md">web-platform-tests</a>?</h4>
  // {% if feature.wpt %}Yes{% else %}No{% endif %}
  // {% if feature.wpt_descr %}
  //   <p class="preformatted">{{feature.wpt_descr|urlize}}</p>
  // {% endif %}
  // */

  //   renderWPT() {
  //     const wpt = this.feature.wpt;
  //     return html`
  //       <br /><br />
  //       <h4>
  //         Is this feature fully tested by
  //         <a
  //           href="https://chromium.googlesource.com/chromium/src/+/main/docs/testing/web_platform_tests.md"
  //           >web-platform-tests</a
  //         >?
  //       </h4>
  //       ${wpt ? 'Yes' : 'No'}
  //       ${this.feature.wpt_descr ?
  //         html` <p class="preformatted">${this.feature.wpt_descr}</p> ` :
  //         nothing}
  //     `;
  //   }

  //   /*
  // {% if feature.devtrial_instructions %}
  //   <br><br><h4>DevTrial instructions</h4>
  //   <a href="{{feature.devtrial_instructions}}"
  //      >{{feature.devtrial_instructions}}</a>
  // {% endif %}
  // */

  //   renderDevTrialInstructions() {
  //     const devTrialInstructions = this.feature.devtrial_instructions;
  //     if (!devTrialInstructions) {
  //       return nothing;
  //     }
  //     return html`
  //       <br /><br />
  //       <h4>DevTrial instructions</h4>
  //       <a href="${devTrialInstructions}">${devTrialInstructions}</a>
  //     `;
  //   }

  //   /*
  // <br><br><h4>Flag name on chrome://flags</h4>
  // {{feature.flag_name}}
  // */

  //   renderFlagName() {
  //     const flagName = this.feature.flag_name;
  //     return html`
  //       <br /><br />
  //       <h4>Flag name on chrome://flags</h4>
  //       ${flagName}
  //     `;
  //   }

  //   /*
  // <br><br><h4>Finch feature name</h4>
  // {{feature.finch_name}}

  // {% if feature.non_finch_justification %}
  //   <br><br><h4>Non-finch justification</h4>
  //   <p class="preformatted">{{feature.non_finch_justification|urlize}}</p>
  // {% else %}
  //   {% if not feature.finch_name %}
  //     <br><br><h4>Non-finch justification</h4>
  //     None
  //   {% endif %}
  // {% endif %}
  // */

  //   renderFinch() {
  //     const finchName = this.feature.finch_name;

  //     return html`
  //       <br /><br />
  //       <h4>Finch feature name</h4>
  //       ${finchName}
  //       ${this.feature.non_finch_justification ?
  //         html` <br /><br />
  //             <h4>Non-finch justification</h4>
  //             <p class="preformatted">${this.feature.non_finch_justification}</p>` :
  //         !finchName ?
  //           html` <br /><br />
  //             <h4>Non-finch justification</h4>
  //             None` :
  //           nothing}
  //     `;
  //   }

  //   /*
  // <br><br><h4>Requires code in //chrome?</h4>
  // {{feature.requires_embedder_support}}
  // */

  //   renderRequiresEmbedderSupport() {
  //     const requiresEmbedderSupport = this.feature.requires_embedder_support;
  //     return html`
  //       <br /><br />
  //       <h4>Requires code in //chrome?</h4>
  //       ${requiresEmbedderSupport}
  //     `;
  //   }

  //   /*
  // {% if feature.browsers.chrome.bug %}
  //   <br><br><h4>Tracking bug</h4>
  //   <a href="{{feature.browsers.chrome.bug}}">{{feature.browsers.chrome.bug}}</a>
  // {% endif %}
  // */

  //   renderTrackingBug() {
  //     const trackingBug = this.feature.browsers.chrome.bug;
  //     if (!trackingBug) {
  //       return nothing;
  //     }
  //     return html`
  //       <br /><br />
  //       <h4>Tracking bug</h4>
  //       <a href="${trackingBug}">${trackingBug}</a>
  //     `;
  //   }

  //   /*
  // {% if feature.launch_bug_url %}
  //   <br><br><h4>Launch bug</h4>
  //   <a href="{{feature.launch_bug_url}}">{{feature.launch_bug_url}}</a>
  // {% endif %}
  // */

  //   renderLaunchBug() {
  //     const launchBug = this.feature.launch_bug_url;
  //     if (!launchBug) {
  //       return nothing;
  //     }
  //     return html`
  //       <br /><br />
  //       <h4>Launch bug</h4>
  //       <a href="${launchBug}">${launchBug}</a>
  //     `;
  //   }

  //   /*
  // {% if feature.measurement %}
  //   <br><br><h4>Measurement</h4>
  //   {{feature.measurement|urlize}}
  // {% endif %}
  // */

  //   renderMeasurement() {
  //     const measurement = this.feature.measurement;
  //     if (!measurement) {
  //       return nothing;
  //     }
  //     return html`
  //       <br /><br />
  //       <h4>Measurement</h4>
  //       ${measurement}
  //     `;
  //   }

  //   /*
  // {% if feature.availability_expectation %}
  //   <br><br><h4>Availability expectation</h4>
  //   {{feature.availability_expectation|urlize}}
  // {% endif %}
  // */

  //   renderAvailabilityExpectation() {
  //     const availabilityExpectation = this.feature.availability_expectation;
  //     if (!availabilityExpectation) {
  //       return nothing;
  //     }
  //     return html`
  //       <br /><br />
  //       <h4>Availability expectation</h4>
  //       ${availabilityExpectation}
  //     `;
  //   }

  //   /*
  // {% if feature.adoption_expectation %}
  //   <br><br><h4>Adoption expectation</h4>
  //   {{feature.adoption_expectation|urlize}}
  // {% endif %}
  // */

  //   renderAdoptionExpectation() {
  //     const adoptionExpectation = this.feature.adoption_expectation;
  //     if (!adoptionExpectation) {
  //       return nothing;
  //     }
  //     return html`
  //       <br /><br />
  //       <h4>Adoption expectation</h4>
  //       ${adoptionExpectation}
  //     `;
  //   }

  //   /*
  // {% if feature.adoption_plan %}
  //   <br><br><h4>Adoption plan</h4>
  //   {{feature.adoption_plan|urlize}}
  // {% endif %}
  // */

  //   renderAdoptionPlan() {
  //     const adoptionPlan = this.feature.adoption_plan;
  //     if (!adoptionPlan) {
  //       return nothing;
  //     }
  //     return html`
  //       <br /><br />
  //       <h4>Adoption plan</h4>
  //       ${adoptionPlan}
  //     `;
  //   }

  //   /*
  // {% if feature.non_oss_deps %}
  //   <br><br><h4>Non-OSS dependencies</h4>
  //   <p style="font-style: italic">
  //     Does the feature depend on any code or APIs outside the Chromium
  //     open source repository and its open-source dependencies to
  //     function?</p>

  //   {{feature.non_oss_deps|urlize}}
  // {% endif %}
  // */

  //   renderNonOSSDeps() {
  //     const nonOSSDeps = this.feature.non_oss_deps;
  //     if (!nonOSSDeps) {
  //       return nothing;
  //     }
  //     return html`
  //       <br /><br />
  //       <h4>Non-OSS dependencies</h4>
  //       <p style="font-style: italic">
  //         Does the feature depend on any code or APIs outside the Chromium open
  //         source repository and its open-source dependencies to function?
  //       </p>
  //       ${nonOSSDeps}
  //     `;
  //   }

  //   /*
  // {% if 'sample_links' in sections_to_show %}
  //    {% if feature.resources and feature.resources.samples %}
  //      <br><br><h4>Sample links</h4>
  //      {% for link in feature.resources.samples %}
  //        <br><a href="{{link}}">{{link}}</a>
  //      {% endfor %}
  //    {% endif %}
  // {% endif %}
  // */

  //   renderSampleLinks() {
  //     if (!sectionsToShow.includes('sample_links')) return nothing;

  //     const sampleLinks = this.feature.resources.samples;
  //     if (!sampleLinks) {
  //       return nothing;
  //     }
  //     const sampleLinksList = sampleLinks.map(
  //       (link) => html` <br /><a href="${link}">${link}</a> `,
  //     );
  //     return html`
  //       <br /><br />
  //       <h4>Sample links</h4>
  //       ${sampleLinksList}
  //     `;
  //   }

  //   /*
  //   <table>

  //     {% for stage in stage_info.ship_stages %}
  //     {% if stage.milestones.desktop_first %}
  //       <tr><td>Shipping on desktop</td>
  //       <td>{{stage.milestones.desktop_first}}</td></tr>
  //     {% endif %}
  //     {% endfor %}

  //     {% for stage in stage_info.ot_stages %}
  //     {% if stage.milestones.desktop_last %}
  //       <tr><td>OriginTrial desktop last</td>
  //       <td>{{stage.milestones.desktop_last}}</td></tr>
  //     {% endif %}

  //     {% if stage.milestones.desktop_first %}
  //       <tr><td>OriginTrial desktop first</td>
  //       <td>{{stage.milestones.desktop_first}}</td></tr>
  //     {% endif %}
  //     {% endfor %}

  //     {% for stage in stage_info.dt_stages %}
  //     {% if stage.milestones.desktop_first %}
  //       <tr><td>DevTrial on desktop</td>
  //       <td>{{stage.milestones.desktop_first}}</td></tr>
  //     {% endif %}
  //     {% endfor %}

  //   </table>
  //   */

  //   renderDesktopMilestoneTable() {
  //     const shipStages = stage_info.ship_stages;
  //     const otStages = stage_info.ot_stages;
  //     const dtStages = stage_info.dt_stages;

  //     const shipStagesHTML = [];
  //     for (stage in shipStages) {
  //       if (!shipStages.hasOwnProperty(stage)) continue;
  //       if (stage.milestones.desktop_first) {
  //         shipStagesHTML.push(html`
  //           <tr>
  //             <td>Shipping on desktop</td>
  //             <td>${stage.milestones.desktop_first}</td>
  //           </tr>
  //         `);
  //       }
  //     }

  //     const otStagesHTML = [];
  //     for (stage in otStages) {
  //       if (!otStages.hasOwnProperty(stage)) continue;
  //       if (stage.milestones.desktop_last) {
  //         otStagesHTML.push(html`
  //           <tr>
  //             <td>OriginTrial desktop last</td>
  //             <td>${stage.milestones.desktop_last}</td>
  //           </tr>
  //         `);
  //       }
  //       if (stage.milestones.desktop_first) {
  //         otStagesHTML.push(html`
  //           <tr>
  //             <td>OriginTrial desktop first</td>
  //             <td>${stage.milestones.desktop_first}</td>
  //           </tr>
  //         `);
  //       }
  //     }

  //     const dtStagesHTML = [];
  //     for (stage in dtStages) {
  //       if (stage.milestones.desktop_first) {
  //         dtStagesHTML.push(html`
  //           <tr>
  //             <td>DevTrial on desktop</td>
  //             <td>${stage.milestones.desktop_first}</td>
  //           </tr>
  //         `);
  //       }
  //     }

  //     return html`
  //       <table>
  //         ${shipStagesHTML.join('')} ${otStagesHTML.join('')}
  //         ${dtStagesHTML.join('')}
  //       </table>
  //     `;
  //   }

  //   /*
  //   <table>

  //     {% for stage in stage_info.ship_stages %}{% if stage.milestones.android_first %}
  //         <tr><td>Shipping on Android</td>
  //         <td>{{stage.milestones.android_first}}</td></tr>

  //     {% endif %}{% endfor %}
  //     {% for stage in stage_info.ot_stages %}{% if stage.milestones.android_last %}
  //         <tr><td>OriginTrial Android last</td>
  //         <td>{{stage.milestones.android_last}}</td></tr>

  //       {% endif %}{% if stage.milestones.android_first %}
  //         <tr><td>OriginTrial Android first</td>
  //         <td>{{stage.milestones.android_first}}</td></tr>

  //     {% endif %}{% endfor %}
  //     {% for stage in stage_info.dt_stages %}{% if stage.milestones.android_first %}
  //         <tr><td>DevTrial on Android</td>
  //         <td>{{stage.milestones.android_first}}</td></tr>

  //     {% endif %}{% endfor %}
  //   </table>
  //   */

  //   renderAndroidMilestoneTable() {
  //     const shipStages = stage_info.ship_stages;
  //     const otStages = stage_info.ot_stages;
  //     const dtStages = stage_info.dt_stages;

  //     const shipStagesHTML = [];
  //     for (stage in shipStages) {
  //       if (stage.milestones.android_first) {
  //         shipStagesHTML.push(html`
  //           <tr>
  //             <td>Shipping on Android</td>
  //             <td>${stage.milestones.android_first}</td>
  //           </tr>
  //         `);
  //       }
  //     }

  //     const otStagesHTML = [];
  //     for (stage in otStages) {
  //       if (!otStages.hasOwnProperty(stage)) continue;
  //       if (stage.milestones.android_last) {
  //         otStagesHTML.push(html`
  //           <tr>
  //             <td>OriginTrial Android last</td>
  //             <td>${stage.milestones.android_last}</td>
  //           </tr>
  //         `);
  //       }
  //       if (stage.milestones.android_first) {
  //         otStagesHTML.push(html`
  //           <tr>
  //             <td>OriginTrial Android first</td>
  //             <td>${stage.milestones.android_first}</td>
  //           </tr>
  //         `);
  //       }
  //     }

  //     const dtStagesHTML = [];
  //     for (stage in dtStages) {
  //       if (stage.milestones.android_first) {
  //         dtStagesHTML.push(html`
  //           <tr>
  //             <td>DevTrial on Android</td>
  //             <td>${stage.milestones.android_first}</td>
  //           </tr>
  //         `);
  //       }
  //     }

  //     return html`
  //       <table>
  //         ${shipStagesHTML.join('')} ${otStagesHTML.join('')}
  //         ${dtStagesHTML.join('')}
  //       </table>
  //     `;
  //   }

  //   /*
  //   <table>

  //     {% for stage in stage_info.ship_stages %}
  //     {% if stage.milestones.webview_first %}
  //       <tr><td>Shipping on WebView</td>
  //       <td>{{stage.milestones.webview_first}}</td></tr>
  //     {% endif %}
  //     {% endfor %}

  //     {% for stage in stage_info.ot_stages %}
  //       {% if stage.milestones.webview_last %}
  //         <tr><td>OriginTrial webView last</td>
  //         <td>{{stage.milestones.webview_last}}</td></tr>
  //       {% endif %}

  //       {% if stage.milestones.webview_first %}
  //         <tr><td>OriginTrial webView first</td>
  //         <td>{{stage.milestones.webview_first}}</td></tr>
  //       {% endif %}
  //     {% endfor %}

  //   </table>
  //   */

  //   renderWebViewMilestoneTable() {
  //     const shipStages = stage_info.ship_stages;
  //     const otStages = stage_info.ot_stages;

  //     const shipStagesHTML = [];
  //     for (stage in shipStages) {
  //       if (stage.milestones.webview_first) {
  //         shipStagesHTML.push(html`
  //           <tr>
  //             <td>Shipping on WebView</td>
  //             <td>${stage.milestones.webview_first}</td>
  //           </tr>
  //         `);
  //       }
  //     }

  //     const otStagesHTML = [];
  //     for (stage in otStages) {
  //       if (!otStages.hasOwnProperty(stage)) continue;
  //       if (stage.milestones.webview_last) {
  //         otStagesHTML.push(html`
  //           <tr>
  //             <td>OriginTrial webView last</td>
  //             <td>${stage.milestones.webview_last}</td>
  //           </tr>
  //         `);
  //       }
  //       if (stage.milestones.webview_first) {
  //         otStagesHTML.push(html`
  //           <tr>
  //             <td>OriginTrial webView first</td>
  //             <td>${stage.milestones.webview_first}</td>
  //           </tr>
  //         `);
  //       }
  //     }

  //     return html`
  //       <table>
  //         ${shipStagesHTML.join('')} ${otStagesHTML.join('')}
  //       </table>
  //     `;
  //   }

  //   /*
  //   <table>

  //     {% for stage in stage_info.ship_stages %}
  //       {% if stage.milestones.ios_first %}
  //         <tr><td>Shipping on WebView</td>
  //         <td>{{stage.milestones.ios_first}}</td></tr>
  //       {% endif %}
  //     {% endfor %}

  //     {% for stage in stage_info.dt_stages %}
  //       {% if stage.milestones.ios_first %}
  //         <tr><td>DevTrial on iOS</td>
  //         <td>{{stage.milestones.ios_first}}</td></tr>
  //       {% endif %}
  //     {% endfor %}

  //   </table>
  // */

  //   renderIOSMilestoneTable() {
  //     const shipStages = stage_info.ship_stages;
  //     const dtStages = stage_info.dt_stages;

  //     const shipStagesHTML = [];
  //     for (stage in shipStages) {
  //       if (stage.milestones.ios_first) {
  //         shipStagesHTML.push(html`
  //           <tr>
  //             <td>Shipping on WebView</td>
  //             <td>${stage.milestones.ios_first}</td>
  //           </tr>
  //         `);
  //       }
  //     }

  //     const dtStagesHTML = [];
  //     for (stage in dtStages) {
  //       if (stage.milestones.ios_first) {
  //         dtStagesHTML.push(html`
  //           <tr>
  //             <td>DevTrial on iOS</td>
  //             <td>${stage.milestones.ios_first}</td>
  //           </tr>
  //         `);
  //       }
  //     }

  //     return html`
  //       <table>
  //         ${shipStagesHTML.join('')} ${dtStagesHTML.join('')}
  //       </table>
  //     `;
  //   }

  //   /*
  // {% if should_render_mstone_table %}

  // {% else %}

  //   <p>No milestones specified</p>

  // {% endif %}
  // */

  //   renderEstimatedMilestoneTable() {
  //     if (this.shouldRenderMstoneTable) {
  //       return html`
  //         ${renderDesktopMilestoneTable()} ${renderAndroidMilestoneTable()}
  //         ${renderWebViewMilestoneTable()} ${renderIOSMilestoneTable()}
  //       `;
  //     } else {
  //       return html` <p>No milestones specified</p> `;
  //     }
  //   }

  //   /*
  // <br><br><h4>Estimated milestones</h4>
  // {% include "estimated-milestones-table.html" %}
  // */

  //   renderEstimatedMilestones() {
  //     return html`
  //       <br /><br />
  //       <h4>Estimated milestones</h4>
  //       ${renderEstimatedMilestonesTable()}
  //     `;
  //   }

  //   /*
  // {% if 'anticipated_spec_changes' in sections_to_show or feature.anticipated_spec_changes %}
  //   <br><br><h4>Anticipated spec changes</h4>
  //   <p style="font-style: italic">
  //     Open questions about a feature may be a source of future web compat or
  //     interop issues. Please list open issues (e.g. links to known github
  //     issues in the project for the feature specification) whose resolution
  //     may introduce web compat/interop risk (e.g., changing to naming or
  //     structure of the API in a non-backward-compatible way).</p>

  //   {{feature.anticipated_spec_changes|urlize}}
  // {% endif %}
  // */

  //   renderAnticipatedSpecChanges() {
  //     const sectionsToShow = this.sectionsToShow;
  //     const anticipatedSpecChanges = this.feature.anticipated_spec_changes;
  //     if (!sectionsToShow.includes('anticipated_spec_changes') ||
  //       !anticipatedSpecChanges) {
  //       return nothing;
  //     }

  //     return html`
  //       <br /><br />
  //       <h4>Anticipated spec changes</h4>
  //       <p style="font-style: italic">
  //         Open questions about a feature may be a source of future web compat or
  //         interop issues. Please list open issues (e.g. links to known github
  //         issues in the project for the feature specification) whose resolution
  //         may introduce web compat/interop risk (e.g., changing to naming or
  //         structure of the API in a non-backward-compatible way).
  //       </p>
  //       ${anticipatedSpecChanges}
  //     `;
  //   }

  //   /*
  // <br><br><h4>Link to entry on the {{APP_TITLE}}</h4>
  // <a href="{{default_url}}">{{default_url}}</a>
  // */

  //   renderDefaultURL() {
  //     const defaultURL = this.feature.default_url;
  //     return html`
  //       <br /><br />
  //       <h4>Link to entry on the ${APP_TITLE}</h4>
  //       <a href="${defaultURL}">${defaultURL}</a>
  //     `;
  //   }

  //   /*
  // {% if should_render_intents %}
  //   <br><br><h4>Links to previous Intent discussions</h4>

  //   {% for stage in stage_info.proto_stages %}{% if stage.intent_thread_url %}
  //       Intent to prototype: {{stage.intent_thread_url|urlize}}

  //   {% endif %}{% endfor %}
  //   {% for stage in stage_info.dt_stages %}{% if stage.announcement_url %}
  //       Ready for Trial: {{stage.announcement_url|urlize}}
  //       <br>

  //   {% endif %}{% endfor %}
  //   {% for stage in stage_info.ot_stages %}{% if stage.intent_thread_url %}
  //       Intent to Experiment: {{stage.intent_thread_url|urlize}}
  //       <br>

  //   {% endif %}{% endfor %}
  //   {% for stage in stage_info.extension_stages %}
  //     {% if stage.intent_thread_url %}
  //       Intent to Extend Experiment: {{stage.intent_thread_url|urlize}}
  //       <br>

  //   {% endif %}{% endfor %}
  //   {% for stage in stage_info.extension_stages %}{% if stage.intent_thread_url %}
  //       Intent to Ship: {{stage.intent_thread_url|urlize}}
  //       <br>

  //   {% endif %}{% endfor %}
  // {% endif %}
  // */

  //   renderIntentLinks() {
  //     if (this.shouldRenderIntents) {
  //       const protoStages = stage_info.proto_stages;
  //       const dtStages = stage_info.dt_stages;
  //       const otStages = stage_info.ot_stages;
  //       const extensionStages = stage_info.extension_stages;

  //       const protoStagesHTML = [];
  //       for (stage in protoStages) {
  //         if (stage.intent_thread_url) {
  //           protoStagesHTML.push(html`
  //             Intent to prototype: ${stage.intent_thread_url}
  //           `);
  //         }
  //       }

  //       const dtStagesHTML = [];
  //       for (stage in dtStages) {
  //         if (stage.announcement_url) {
  //           dtStagesHTML.push(html`
  //             Ready for Trial: ${stage.announcement_url}
  //             <br />
  //           `);
  //         }
  //       }

  //       const otStagesHTML = [];
  //       for (stage in otStages) {
  //         if (stage.intent_thread_url) {
  //           otStagesHTML.push(html`
  //             Intent to Experiment: ${stage.intent_thread_url}
  //             <br />
  //           `);
  //         }
  //       }

  //       const extensionStagesHTML = [];
  //       for (stage in extensionStages) {
  //         if (stage.intent_thread_url) {
  //           extensionStagesHTML.push(html`
  //             Intent to Extend Experiment: ${stage.intent_thread_url}
  //             <br />
  //           `);
  //         }
  //       }

  //       return html`
  //         <br /><br />
  //         <h4>Links to previous Intent discussions</h4>
  //         ${protoStagesHTML.join('')}
  //         ${dtStagesHTML.join('')}
  //         ${otStagesHTML.join('')}
  //         ${extensionStagesHTML.join('')}
  //       `;
  //     }
  //   }

  //   <!--
  //   ${this.renderTagReviewStatus()} ${this.renderOTInfo()}
  //   ${this.renderRisks()} ${this.renderExperiment()}
  //   ${this.renderDebuggability()} ${this.renderAllPlatforms()}
  //   ${this.renderWPT()} ${this.renderDevTrialInstructions()}
  //   ${this.renderFlagName()} ${this.renderFinch()}
  //   ${this.renderRequiresEmbedderSupport()} ${this.renderTrackingBug()}
  //   ${this.renderLaunchBug()} ${this.renderMeasurement()}
  //   ${this.renderAvailabilityExpectation()}
  //   ${this.renderAdoptionExpectation()} ${this.renderAdoptionPlan()}
  //   ${this.renderNonOSSDeps()} ${this.renderSampleLinks()}
  //   ${this.renderEstimatedMilestones()}
  //   ${this.renderAnticipatedSpecChanges()} ${this.renderDefaultURL()}
  //   ${this.renderIntentLinks()}
  // -->

  renderDialogContent() {
    if (!this.feature || !this.feature.browsers) return '';
    return html`
      ${this.renderInstructions()}
      ${this.renderNeedApiOwnersApproval()}

      <section>
       <h3>Copy and send this text for your "Intent to ..." email</h3>
        ${this.renderSubheader()}

        <div class="email">
          ${this.renderContactEmails()}
          ${this.renderExplainerLinks()}
          ${this.renderSpec()}
          ${this.renderDesignDocs()}
          ${this.renderSummary()}
          ${this.renderBlinkComponents()}
          ${this.renderMotivation()}
          ${this.renderSearchTags()}
          ${this.renderTagReview()}


          <br /><br />
          <div>
            <small>
              This intent message was generated by
              <a href="https://chromestatus.com">Chrome Platform Status</a>.
            </small>
          </div>
        </div>
      </section>
      <!-- end email body div -->
    `;
  }

  render() {
    return html`
    <sl-dialog class="intent-email"
      label="Intent email"
      style="--width:fit-content">
      ${this.renderDialogContent()}
    </sl-dialog>
  `;
  }
}
customElements.define('chromedash-intent-dialog', ChromeDashIntentDialog);
