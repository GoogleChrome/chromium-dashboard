import {html} from 'lit';
import {
  FEATURE_CATEGORIES,
  FEATURE_TYPES,
  IMPLEMENTATION_STATUS,
  INTENT_STAGES,
  STANDARD_MATURITY_CHOICES,
  REVIEW_STATUS_CHOICES,
  VENDOR_VIEWS_COMMON,
  VENDOR_VIEWS_GECKO,
  WEB_DEV_VIEWS,
} from './form-field-enums';


/* Patterns from https://www.oreilly.com/library/view/regular-expressions-cookbook/9781449327453/ch04s01.html
 * Removing single quote ('), backtick (`), and pipe (|) since they are risky unless properly escaped everywhere.
 * Also removing ! and % because they have special meaning for some older email routing systems. */
const USER_REGEX = '[A-Za-z0-9_#$&*+/=?{}~^.-]+';
const DOMAIN_REGEX = String.raw`(([A-Za-z0-9-]+\.)+[A-Za-z]{2,6})`;

const EMAIL_ADDRESS_REGEX = USER_REGEX + '@' + DOMAIN_REGEX;
const EMAIL_ADDRESSES_REGEX = EMAIL_ADDRESS_REGEX + '([ ]*,[ ]*' + EMAIL_ADDRESS_REGEX + ')*';

// Simple http URLs
const PORTNUM_REGEX = '(:[0-9]+)?';
const URL_REGEX = '(https?)://' + DOMAIN_REGEX + PORTNUM_REGEX + String.raw`(/[^\s]*)?`;
const URL_PADDED_REGEX = String.raw`\s*` + URL_REGEX + String.raw`\s*`;

const URL_FIELD_ATTRS = {
  title: 'Enter a full URL https://...',
  type: 'url',
  placeholder: 'https://...',
  pattern: URL_PADDED_REGEX,
};

const MULTI_EMAIL_FIELD_ATTRS = {
  title: 'Enter one or more comma-separated complete email addresses.',
  // Don't specify type="email" because browsers consider multiple emails
  // invalid, regardles of the multiple attribute.
  type: 'text',
  multiple: true,
  placeholder: 'user1@domain.com, user2@chromium.org',
  pattern: EMAIL_ADDRESSES_REGEX,
};

const TEXT_FIELD_ATTRS = {
  type: 'text',
};

const MILESTONE_NUMBER_FILED_ATTRS = {
  type: 'number',
  placeholder: 'Milestone number',
};

const MULTI_URL_FIELD_ATTRS = {
  title: 'Enter one or more full URLs, one per line:\nhttps://...\nhttps://...',
  multiple: true,
  placeholder: 'https://...\nhttps://...',
  rows: 4, cols: 50, maxlength: 5000,
  chromedash_single_pattern: URL_REGEX,
  chromedash_split_pattern: String.raw`\s+`,
};

const SHIPPED_HELP_TXT = html`
  First milestone to ship with this status. Applies to: Enabled by
  default, Browser Intervention, Deprecated, and Removed.`;

const
  SHIPPED_WEBVIEW_HELP_TXT = html`
  First milestone to ship with this status.
  Applies to Enabled by default, Browser
  Intervention, Deprecated, and Removed.`;

// Map of specifications for all form fields.
export const ALL_FIELDS = {

  'name': {
    type: 'input',
    attrs: TEXT_FIELD_ATTRS,
    required: true,
    label: 'Feature name',
    help_text: html`
        <p>Capitalize only the first letter and the beginnings of proper nouns.</p>`,
    extra_help: html`
    <p>
    Each feature should have a unique name that is written as a noun phrase.
    </p>
    <ul>
      <li>Capitalize only the first letter and the beginnings of proper nouns.</li>
      <li>Avoid using verbs such as "add", "enhance", "deprecate", or "delete". Instead, simply name the feature itself and use the feature type and stage fields to indicate the intent of change.</li>
      <li>Do not include markup or markdown because they will not be rendered..</li>
      <li>Write keywords and identifiers as they would appear to a web developer, not as they are in source code. For example, a method implemented as NewInterface#dostuff would be written as in JavaScript: NewInterface.doStuff().</li>
    </ul>

    <h4>Examples</h4>
    <ul>
      <li>Conversion Measurement API</li>
      <li>CSS Flexbox: intrinsic size algorithm</li>
      <li>Permissions-Policy header</li>
    </ul>`,
  },

  'summary': {
    type: 'textarea',
    required: true,
    label: 'Summary',
    help_text: html`
       <p>Text in the beta release post, the enterprise release notes,
        and other external sources will be based on this text.</p>
        <p>Write from a web developer's point of view. Begin with one line
        explaining what the feature does. Add one or two lines explaining
        how this feature helps developers. Write in a matter-of-fact
        manner and in the present tense. (This summary will be visible long after
        your project is finished.) Avoid language such as "a new feature" and
        "we propose".</p>
      `,
    extra_help: html`
    <p>
    Provide a one sentence description followed by one or two lines explaining how this feature works and how it helps web developers.
    </p>

    <p>
    Note: This text communicates with more than just the rest of Chromium development. It's the part most visible to external readers and is used in the beta release announcement, enterprise release notes, and other communications.
    </p>

    <ul>
      <li>Write from a web developer's point of view, not a browser developer's</li>
      <li>Do not use markup or markdown because they will not be rendered.</li>
      <li>Do not use hard or soft returns because they will not be rendered.</li>
      <li>Avoid phrases such as "a new feature". Every feature on the site was new when it was created. You don't need to repeat that information.</li>

      <li>The first line should be a sentence fragment beginning with a verb. (See below.) This is the rare exception to the requirement to always use complete sentences.</li>

      <li>"Conformance with spec" is not adequate. Most if not all features are in conformance to spec.</li>
    </ul>

    <h4>Example</h4>
    <blockquote>
    Splits the HTTP cache using the top frame origin (and possibly subframe origin) to prevent documents from one origin from knowing whether a resource from another origin was cached. The HTTP cache is currently one per profile, with a single namespace for all resources and subresources regardless of origin or renderer process. Splitting the cache on top frame origins helps the browser deflect side-channel attacks where one site can detect resources in another site's cache.
    </blockquote>
    `,
  },

  'owner': {
    type: 'input',
    attrs: MULTI_EMAIL_FIELD_ATTRS,
    required: true,
    label: 'Feature owners',
    help_text: html`
        Comma separated list of full email addresses.`,
  },

  'editors': {
    type: 'input',
    attrs: MULTI_EMAIL_FIELD_ATTRS,
    required: false,
    label: 'Feature editors',
    help_text: html`
        Comma separated list of full email addresses. These users will be
        allowed to edit this feature, but will not be listed as feature owners.
        User groups are not supported.`,
  },

  'cc_recipients': {
    type: 'input',
    attrs: MULTI_EMAIL_FIELD_ATTRS,
    required: false,
    label: 'CC',
    help_text: html`
        Comma separated list of full email addresses. These users will be
        notified of any changes to the feature, but do not gain permission to
        edit.  User groups must allow posting from
        admin@cr-status.appspotmail.com.`,
  },

  'unlisted': {
    type: 'checkbox',
    label: 'Unlisted',
    initial: false,
    help_text: html`
        Check this box to hide draft features in list views. Anyone with
        a link will be able to view the feature's detail page.`,
  },

  'accurate_as_of': {
    type: 'checkbox',
    label: 'Confirm accuracy',
    initial: true,
    help_text: html`
        Check this box to indicate that feature information is accurate
        as of today.
        (Selecting this avoids reminder emails for four weeks.)`,
  },

  'blink_components': {
    type: 'datalist',
    required: true,
    choices: undefined, // this gets replaced in chromedash-form-field via the blink component api
    label: 'Blink component',
    attrs: {placeholder: 'Please select a Blink component'},
    help_text: html`
        Select the most specific component. If unsure, leave as "Blink".`,
  },

  'category': {
    type: 'select',
    choices: FEATURE_CATEGORIES,
    initial: FEATURE_CATEGORIES.MISC[0],
    label: 'Category',
    help_text: html`
        Select the most specific category. If unsure, leave as "Miscellaneous".`,
  },

  'feature_type': {
    type: 'select',
    disabled: true,
    choices: FEATURE_TYPES,
    label: 'Feature type',
    help_text: html`
    Feature type chosen at time of creation.
        <br/>
        <p style="color: red"><strong>Note:</strong> The feature type field
        cannot be changed. If this field needs to be modified, a new feature
        would need to be created.</p>`,
  },

  'feature_type_radio_group': {
    // form field name matches underlying DB field (sets "feature_type" in DB).
    name: 'feature_type',
    type: 'radios',
    choices: FEATURE_TYPES,
    label: 'Feature type',
    help_text: html`
        Select the feature type.
        <br/>
        <p style="color: red"><strong>Note:</strong> The feature type field
        cannot be changed. If this field needs to be modified, a new feature
        would need to be created.</p>`,
  },

  'set_stage': {
    type: 'checkbox',
    label: 'Set to this stage',
    help_text: html`
      Check this box to move this feature to this
      stage in the process. Leave it unchecked if you are adding
      draft information or revising a previous stage.`,
  },

  'intent_stage': {
    type: 'select',
    choices: INTENT_STAGES,
    initial: INTENT_STAGES.INTENT_IMPLEMENT[0],
    label: 'Process stage',
    help_text: html`
        Select the appropriate spec process stage. If you select
        Dev trials, Origin Trial, or Shipped, be sure to set the
        equivalent Implementation status.`,
  },

  'search_tags': {
    type: 'input',
    attrs: TEXT_FIELD_ATTRS,
    required: false,
    label: 'Search tags',
    help_text: html`
        Comma separated keywords used only in search.`,
  },

  'impl_status_chrome': {
    type: 'select',
    choices: IMPLEMENTATION_STATUS,
    label: 'Implementation status',
    help_text: html`
        Select the appropriate Chromium development stage. If you
        select In developer trial, Origin trial, or Enabled by
        default, be sure to set the equivalent Process stage.`,
  },

  'bug_url': {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Tracking bug URL',
    help_text: html`
        Tracking bug url (https://bugs.chromium.org/...).
        This bug should have "Type=Feature" set
        and be world readable.
        Note: This field only accepts one URL.
        <br/><br/>
        <a target="_blank"
            href="https://bugs.chromium.org/p/chromium/issues/entry">
          Create tracking bug</a>`,
  },

  'launch_bug_url': {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Launch URL',
    help_text: html`
        Launch URL (https://launch.corp.google.com/...) to track internal
        approvals, if any.
        <br/><br/>
        <a target="_blank"
            href="https://launch.corp.google.com/">
          Create a launch</a>.`,
  },

  'motivation': {
    type: 'textarea',
    required: false,
    label: 'Motivation',
    help_text: html`
        Explain why the web needs this change. It may be useful
        to describe what web developers are forced to do without
        it. When possible, add links to your explainer
        backing up your claims.
        <br/><br/>
        This text is sometimes included with the summary in the
        beta post, enterprise release notes and other external
        documents. Write in a matter-of-fact manner and in the
        present tense.
        <br/><br/>
        <a target="_blank"
            href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#motivation-example">
          Example</a>`,
  },

  'deprecation_motivation': {
    // form field name matches underlying DB field (sets "motivation" field in DB).
    name: 'motivation',
    type: 'textarea',
    required: false,
    label: 'Motivation',
    help_text: html`
        Deprecations and removals must have strong reasons, backed up
        by measurements. There must be clear and actionable paths forward
        for developers.
        <br/><br/>
        This text is sometimes included with the summary in the
        beta post, enterprise release notes and other external
        documents. Write in a matter-of-fact manner and in the
        present tense.
        <br/><br/>
        Please see
        <a target="_blank"
            href="https://docs.google.com/a/chromium.org/document/d/1LdqUfUILyzM5WEcOgeAWGupQILKrZHidEXrUxevyi_Y/edit?usp=sharing">
          Removal guidelines</a>.`,
  },

  'initial_public_proposal_url': {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Initial public proposal URL',
    help_text: html`
        Link to the first public proposal to create this feature, e.g.,
        a WICG discourse post.`,
  },

  'explainer_links': {
    type: 'textarea',
    attrs: MULTI_URL_FIELD_ATTRS,
    required: false,
    label: 'Explainer link(s)',
    help_text: html`
        Link to explainer(s) (one URL per line). You should have
        at least an explainer in hand and have shared it on a
        public forum before sending an Intent to Prototype in
        order to enable discussion with other browser vendors,
        standards bodies, or other interested parties.`,
  },

  'spec_link': {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Spec link',
    help_text: html`
        Link to the spec, if and when available. When implementing
        a spec update, please link to a heading in a published spec
        rather than a pull request when possible.`,
  },

  'comments': {
    type: 'textarea',
    attrs: {rows: 4},
    required: false,
    label: 'Comments',
    help_text: html`
        Additional comments, caveats, info...`,
  },

  'standard_maturity': {
    type: 'select',
    choices: STANDARD_MATURITY_CHOICES,
    initial: STANDARD_MATURITY_CHOICES.PROPOSAL_STD[0],
    label: 'Standard maturity',
    help_text: html`
        How far along is the standard that this feature implements?`,
  },

  'api_spec': {
    type: 'checkbox',
    initial: false,
    label: 'API spec',
    help_text: html`
        The spec document has details in a specification language
        such as Web IDL, or there is an existing MDN page.`,
  },

  'spec_mentors': {
    type: 'input',
    attrs: MULTI_EMAIL_FIELD_ATTRS,
    required: false,
    label: 'Spec mentor',
    help_text: html`
        Experienced
        <a target="_blank"
            href="https://www.chromium.org/blink/spec-mentors">
          spec mentors</a>
        are available to help you improve your feature spec.`,
  },

  'intent_to_implement_url': {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Intent to Prototype link',
    help_text: html`
        After you have started the "Intent to Prototype"
        discussion thread, link to it here.`,
  },

  'doc_links': {
    type: 'textarea',
    attrs: MULTI_URL_FIELD_ATTRS,
    required: false,
    label: 'Doc link(s)',
    help_text: html`
        Links to design doc(s) (one URL per line), if and when
        available. [This is not required to send out an Intent
        to Prototype. Please update the intent thread with the
        design doc when ready]. An explainer and/or design doc
        is sufficient to start this process. [Note: Please
        include links and data, where possible, to support any
        claims.`,
  },

  'measurement': {
    type: 'textarea',
    attrs: {rows: 4},
    required: false,
    label: 'Measurement',
    help_text: html`
        It's important to measure the adoption and success of web-exposed
        features.  Note here what measurements you have added to track the
        success of this feature, such as a link to the UseCounter(s) you
        have set up.`,
  },

  'security_review_status': {
    type: 'select',
    choices: REVIEW_STATUS_CHOICES,
    initial: REVIEW_STATUS_CHOICES.REVIEW_PENDING[0],
    label: 'Security review status',
    help_text: html`
        Status of the security review.`,
  },

  'privacy_review_status': {
    type: 'select',
    choices: REVIEW_STATUS_CHOICES,
    initial: REVIEW_STATUS_CHOICES.REVIEW_PENDING[0],
    label: 'Privacy review status',
    help_text: html`Status of the privacy review.`,
  },

  'tag_review': {
    type: 'textarea',
    attrs: {rows: 2},
    required: false,
    label: 'TAG Specification Review',
    help_text: html`
      Link(s) to TAG specification review(s), or explanation why this is not needed.`,
    extra_help: html`
    <p>
      The <a target="_blank" href="https://www.w3.org/2001/tag/">W3C Technical Architecture Group</a> (TAG)
      is a special working group of the W3C that consists of a few appointed and elected members,
      all of whom are experienced members of the web standards community.
      The Blink launch process has a formal requirement for requesting a
      <a target="_blank" href="https://github.com/w3ctag/design-reviews">TAG specification review</a>
      for all features. The review happens publicly on a GitHub issue.
    </p>
    <p>
      You will likely have asked for an "<a target="_blank" href=
        "https://github.com/w3ctag/design-reviews/issues/new?template=005-early-design-review.md"
      >Early Design Review</a>" earlier in the process to get the TAG familiar with your feature.
      This isn't that.
    </p>
    <p>
      It's recommended that you file a TAG <a target="_blank" href=
        "https://github.com/w3ctag/design-reviews/issues/new?template=010-specification-review.md"
      >Specification Review</a> as soon as your specification is written, and at least a month ahead of sending an Intent to Ship.
      There may be some work involved in preparing your feature for review (see the
      <a target="_blank" href=
        "https://github.com/w3ctag/design-reviews/blob/main/.github/ISSUE_TEMPLATE/010-specification-review.md"
      >submission template fields</a>).
    </p>
    <p>
      A large number of Intents to Ship are delayed because a TAG specification review was only
      recently filed and engagement from the TAG can take multiple weeks to multiple months.
      Note that the API owners can approve shipping even if the TAG hasn't replied to your review request,
      as long as you've made a reasonable effort
      to obtain their review with enough time for them to give feedback.
    </p>`,
  },

  'tag_review_status': {
    type: 'select',
    choices: REVIEW_STATUS_CHOICES,
    initial: REVIEW_STATUS_CHOICES.REVIEW_PENDING[0],
    label: 'TAG Specification Review Status',
    help_text: html`Status of the TAG specification review.`,
  },

  'intent_to_ship_url': {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Intent to Ship link',
    help_text: html`After you have started the "Intent to Ship" discussion
                thread, link to it here.`,
  },

  'ready_for_trial_url': {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Ready for Trial link',
    help_text: html`After you have started the "Ready for Trial" discussion
                thread, link to it here.`,
  },

  'intent_to_experiment_url': {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Intent to Experiment link',
    help_text: html`After you have started the "Intent to Experiment"
                 discussion thread, link to it here.`,
  },

  'intent_to_extend_experiment_url': {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Intent to Extend Experiment link',
    help_text: html`If this feature has an "Intent to Extend Experiment"
                 discussion thread, link to it here.`,
  },

  'r4dt_url': {
    // form field name matches underlying DB field (sets "intent_to_experiment_url" field in DB).
    name: 'intent_to_experiment_url',
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Request for Deprecation Trial link',
    help_text: html`After you have started the "Request for Deprecation Trial"
                discussion thread, link to it here.`,
  },

  'interop_compat_risks': {
    type: 'textarea',
    required: false,
    label: 'Interoperability and Compatibility Risks',
    help_text: html`
      Describe the degree of
      <a target="_blank"
          href="https://www.chromium.org/blink/guidelines/web-platform-changes-guidelines#TOC-Finding-balance">
        interoperability risk</a>.
      For a new feature, the main risk is
      that it fails to become an interoperable part of the web platform
      if other browsers do not implement it. For a removal, please review our
      <a target="_blank"
          href="https://docs.google.com/document/d/1RC-pBBvsazYfCNNUSkPqAVpSpNJ96U8trhNkfV0v9fk/edit">
      principles of web compatibility</a>.<br>
      <br>
      Please include citation links below where possible. Examples include
      resolutions from relevant standards bodies (e.g. W3C working group),
      tracking bugs, or links to online conversations.
      <a target="_blank"
          href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#interoperability-and-compatibility-risks-example">
        Example</a>.`,
  },

  'safari_views': {
    type: 'select',
    choices: VENDOR_VIEWS_COMMON,
    initial: VENDOR_VIEWS_COMMON.NO_PUBLIC_SIGNALS[0],
    label: 'Safari views',
    help_text: html`
      See <a target="_blank" href="https://bit.ly/blink-signals">
      https://bit.ly/blink-signals</a>`,
  },

  'safari_views_link': {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: '',
    help_text: html`Citation link.`,
  },

  'safari_views_notes': {
    type: 'textarea',
    attrs: {rows: 2, placeholder: 'Notes'},
    required: false,
    label: '',
    help_text: '',
  },

  'ff_views': {
    type: 'select',
    choices: VENDOR_VIEWS_GECKO,
    initial: VENDOR_VIEWS_GECKO.NO_PUBLIC_SIGNALS[0],
    label: 'Firefox views',
    help_text: html`
      See <a target="_blank" href="https://bit.ly/blink-signals">
      https://bit.ly/blink-signals</a>`,
  },

  'ff_views_link': {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: '',
    help_text: html`
    Citation link.`,
  },

  'ff_views_notes': {
    type: 'textarea',
    attrs: {rows: 2, placeholder: 'Notes'},
    required: false,
    label: '',
    help_text: '',
  },

  'web_dev_views': {
    type: 'select',
    choices: WEB_DEV_VIEWS,
    initial: WEB_DEV_VIEWS.DEV_NO_SIGNALS[0],
    label: 'Web / Framework developer views',
    help_text: html`
      If unsure, default to "No signals".
      See <a target="_blank" href="https://goo.gle/developer-signals">
      https://goo.gle/developer-signals</a>`,
  },

  'web_dev_views_link': {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: '',
    help_text: html`
      Citation link.`,
  },

  'web_dev_views_notes': {
    type: 'textarea',
    attrs: {rows: 2, placeholder: 'Notes'},
    required: false,
    label: '',
    help_text: html`
      Reference known representative examples of opinions,
      both positive and negative.`,
  },

  'other_views_notes': {
    type: 'textarea',
    attrs: {rows: 4, placeholder: 'Notes'},
    required: false,
    label: 'Other views',
    help_text: html`
      For example, other browsers.`,
  },

  'ergonomics_risks': {
    type: 'textarea',
    required: false,
    label: 'Ergonomics Risks',
    help_text: html`
      Are there any other platform APIs this feature will frequently be
      used in tandem with? Could the default usage of this API make it
      hard for Chrome to maintain good performance (i.e. synchronous
      return, must run on a certain thread, guaranteed return timing)?`,
  },

  'activation_risks': {
    type: 'textarea',
    required: false,
    label: 'Activation Risks',
    help_text: html`
      Will it be challenging for developers to take advantage of this
      feature immediately, as-is? Would this feature benefit from
      having polyfills, significant documentation and outreach, and/or
      libraries built on top of it to make it easier to use?`,
  },

  'security_risks': {
    type: 'textarea',
    required: false,
    label: 'Security Risks',
    help_text: html`
      List any security considerations that were taken into account
      when designing this feature.`,
  },

  'webview_risks': {
    type: 'textarea',
    required: false,
    label: 'WebView application risks',
    help_text: html`
      Does this feature deprecate or change behavior of existing APIs,
      such that it has potentially high risk for Android WebView-based
      applications?
      (See <a target="_blank"
          href="https://new.chromium.org/developers/webview-changes/">
        here</a>
      for a definition of "potentially high risk",
      information on why changes to this platform carry higher
      risk, and general rules of thumb for which changes have higher or
      lower risk) If so:
      <ul>
        <li>Please use a base::Feature killswitch
          (<a target="_blank"
              href="https://source.chromium.org/chromium/chromium/src/+/main:third_party/blink/public/common/features.h"
              >examples here</a>)
          that can be flipped off in case of compat issues</li>
        <li>Consider contacting android-webview-dev@chromium.org for advice</li>
        <li>If you are not sure, just put "not sure" as the answer and
          the API owners can help during the review of your Intent to Ship</li>
      </ul>`,
  },

  'experiment_goals': {
    type: 'textarea',
    required: false,
    label: 'Experiment Goals',
    help_text: html`
      Which pieces of the API surface are you looking to gain insight on?
      What metrics/measurement/feedback will you be using to validate
      designs? Double check that your experiment makes sense given that
      a large developer (e.g. a Google product or Facebook) likely
      can't use it in production due to the limits enforced by origin
      trials.
      <br/><br/>
      If you send an Intent to Extend Origin Trial, highlight
      areas for experimentation. They should not be an exact copy of the goals
      from the first Intent to Experiment.`,
  },

  'experiment_timeline': {
    type: 'textarea',
    attrs: {rows: 2, placeholder: 'This field is deprecated', disabled: true},
    required: false,
    label: 'Experiment Timeline',
    help_text: html`
      When does the experiment start and expire?
      Deprecated:
      Please use the numeric fields above instead.`,
  },

  'ot_milestone_desktop_start': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FILED_ATTRS,
    required: false,
    label: 'OT desktop start',
    help_text: html`
      First desktop milestone that will support an origin
      trial of this feature.`,
  },

  'ot_milestone_desktop_end': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FILED_ATTRS,
    required: false,
    label: 'OT desktop end',
    help_text: html`
      Last desktop milestone that will support an origin
      trial of this feature.`,
  },

  'ot_milestone_android_start': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FILED_ATTRS,
    required: false,
    label: 'OT Android start',
    help_text: html`
      First android milestone that will support an origin
      trial of this feature.`,
  },

  'ot_milestone_android_end': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FILED_ATTRS,
    required: false,
    label: 'OT Android end',
    help_text: html`
      Last android milestone that will support an origin
      trial of this feature.`,
  },

  'ot_milestone_webview_start': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FILED_ATTRS,
    required: false,
    label: 'OT WebView start',
    help_text: html`
      First WebView milestone that will support an origin
      trial of this feature.`,
  },

  'ot_milestone_webview_end': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FILED_ATTRS,
    required: false,
    label: 'OT WebView end',
    help_text: html`
      Last WebView milestone that will support an origin
      trial of this feature.`,
  },

  'experiment_risks': {
    type: 'textarea',
    required: false,
    label: 'Experiment Risks',
    help_text: html`
      When this experiment comes to an end are there any risks to the
      sites that were using it, for example losing access to important
      storage due to an experimental storage API?`,
  },

  'experiment_extension_reason': {
    type: 'textarea',
    required: false,
    label: 'Experiment Extension Reason',
    help_text: html`
      If this is a repeated or extended experiment, explain why it's
      being repeated or extended.  Also, fill in discussion link fields below.`,
  },

  'ongoing_constraints': {
    type: 'textarea',
    required: false,
    label: 'Ongoing Constraints',
    help_text: html`
      Do you anticipate adding any ongoing technical constraints to
      the codebase while implementing this feature? We prefer to avoid
      features that require or assume a specific architecture.
      For most features, the answer is "None."`,
  },

  'origin_trial_feedback_url': {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Origin trial feedback summary',
    help_text: html`
      If your feature was available as an origin trial, link to a summary
      of usage and developer feedback. If not, leave this empty.`,
  },

  'anticipated_spec_changes': {
    type: 'textarea',
    attrs: {rows: 4},
    required: false,
    label: 'Anticipated spec changes',
    help_text: html`
      Open questions about a feature may be a source of future web compat
      or interop issues. Please list open issues (e.g. links to known
      github issues in the repo for the feature specification) whose
      resolution may introduce web compat/interop risk (e.g., changing
      the naming or structure of the API in a
      non-backward-compatible way).`,
  },

  'finch_url': {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Finch experiment',
    help_text: html`
      If your feature will roll out gradually via a
      <a href="http://go/finch" targe="_blank">Finch experiment</a>,
      link to it here.`,
  },

  'i2e_lgtms': {
    type: 'input',
    attrs: MULTI_EMAIL_FIELD_ATTRS,
    required: false,
    label: 'Intent to Experiment LGTM by',
    help_text: html`
      Full email address of API owner who LGTM\'d the
      Intent to Experiment email thread.`,
  },

  'i2s_lgtms': {
    type: 'input',
    attrs: MULTI_EMAIL_FIELD_ATTRS,
    required: false,
    label: 'Intent to Ship LGTMs by',
    help_text: html`
      Comma separated list of
      email addresses of API owners who LGTM'd
      the Intent to Ship email thread.  `,
  },

  'r4dt_lgtms': {
    // form field name matches underlying DB field (sets "i2e_lgtms" field in DB).
    name: 'i2e_lgtms',
    type: 'input',
    attrs: MULTI_EMAIL_FIELD_ATTRS,
    required: false,
    label: 'Request for Deprecation Trial LGTM by',
    help_text: html`
      Full email addresses of API owners who LGTM\'d
      the Request for Deprecation Trial email thread.`,
  },

  'debuggability': {
    type: 'textarea',
    required: false,
    label: 'Debuggability',
    help_text: html`
      Description of the DevTools debugging support for your feature.
      Please follow the
      <a target="_blank"
          href="https://goo.gle/devtools-checklist">
        DevTools support checklist</a> for guidance.`,
  },

  'all_platforms': {
    type: 'checkbox',
    inital: false,
    label: 'Supported on all platforms?',
    help_text: html`
      Will this feature be supported on all six Blink platforms
      (Windows, Mac, Linux, Chrome OS, Android, and Android WebView)?`,
  },

  'all_platforms_descr': {
    type: 'textarea',
    attrs: {rows: 2},
    required: false,
    label: 'Platform Support Explanation',
    help_text: html`
      Explain why this feature is, or is not,
      supported on all platforms.`,
  },

  'wpt': {
    type: 'checkbox',
    initial: false,
    label: 'Web Platform Tests',
    help_text: html`
      Is this feature fully tested in Web Platform Tests?`,
  },

  'wpt_descr': {
    type: 'textarea',
    required: false,
    label: 'Web Platform Tests Description',
    help_text: html`
      Please link to the <a href="https://wpt.fyi/results">results on
      wpt.fyi</a>. If any part of the feature is not tested by
      web-platform-tests, please include links to issues, e.g. a
      web-platform-tests issue with the "infra" label explaining why a
      certain thing cannot be tested
      (<a href="https://github.com/w3c/web-platform-tests/issues/3867">example</a>),
      a spec issue for some change that would make it possible to test.
      (<a href="https://github.com/whatwg/fullscreen/issues/70">example</a>),
      or a Chromium issue to upstream some existing tests
      (<a href="https://bugs.chromium.org/p/chromium/issues/detail?id=695486">example</a>).`,
  },

  'sample_links': {
    type: 'textarea',
    attrs: MULTI_URL_FIELD_ATTRS,
    required: false,
    label: 'Demo and sample links',
    help_text: html`
      Links to demos and samples (one URL per line).`,
  },

  'non_oss_deps': {
    type: 'textarea',
    required: false,
    label: 'Non-OSS dependencies',
    help_text: html`
      Does the feature depend on any code or APIs outside the Chromium
      open source repository and its open-source dependencies to
      function? (e.g. server-side APIs, operating system APIs
      tailored to this feature or closed-source code bundles)
      Yes or no. If yes, explain why this is necessary.`,
  },

  'devrel': {
    type: 'input',
    attrs: MULTI_EMAIL_FIELD_ATTRS,
    required: false,
    label: 'Developer relations emails',
    help_text: html`
      Comma separated list of full email addresses.`,
  },

  'shipped_milestone': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FILED_ATTRS,
    required: false,
    label: 'Chrome for desktop',
    help_text: SHIPPED_HELP_TXT,
  },

  'shipped_android_milestone': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FILED_ATTRS,
    required: false,
    label: 'Chrome for Android',
    help_text: SHIPPED_HELP_TXT,
  },

  'shipped_ios_milestone': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FILED_ATTRS,
    required: false,
    label: 'Chrome for iOS (RARE)',
    help_text: SHIPPED_HELP_TXT,
  },

  'shipped_webview_milestone': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FILED_ATTRS,
    required: false,
    label: 'Android Webview',
    help_text: SHIPPED_WEBVIEW_HELP_TXT,
  },

  'requires_embedder_support': {
    type: 'checkbox',
    initial: false,
    label: 'Requires Embedder Support',
    help_text: html`
       Will this feature require support in //chrome?
       That includes any code in //chrome, even if that is for
       functionality on top of the spec.  Other //content embedders
       will need to be aware of that functionality.
       Please add a row to this
       <a target="_blank"
          href="https://docs.google.com/spreadsheets/d/1QV4SW4JBG3IyLzaonohUhim7nzncwK4ioop2cgUYevw/edit#gid=0">
        tracking spreadsheet</a>.`,
  },

  'devtrial_instructions': {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'DevTrial instructions',
    help_text: html`
        Link to a HOWTO or FAQ describing how developers can get started
        using this feature in a DevTrial.
        <br/><br/>
        <a target="_blank"
            href="https://github.com/samuelgoto/WebID/blob/master/HOWTO.md">
          Example 1</a>.
        <a target="_blank"
            href="https://github.com/WICG/idle-detection/blob/main/HOWTO.md">
          Example 2</a>.`,
  },

  'dt_milestone_desktop_start': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FILED_ATTRS,
    required: false,
    label: 'DevTrial on desktop',
    help_text: html`
      First milestone that allows web developers to try
      this feature on desktop platforms by setting a flag.
      When flags are enabled by default in preparation for
      shipping or removal, please use the fields in the ship stage.`,
  },

  'dt_milestone_android_start': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FILED_ATTRS,
    required: false,
    label: 'DevTrial on Android',
    help_text: html`
      First milestone that allows web developers to try
      this feature on Android by setting a flag.
      When flags are enabled by default in preparation for
      shipping or removal, please use the fields in the ship stage.`,
  },

  'dt_milestone_ios_start': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FILED_ATTRS,
    required: false,
    label: 'DevTrial on iOS (RARE)',
    help_text: html`
      First milestone that allows web developers to try
      this feature on iOS by setting a flag.
      When flags are enabled by default in preparation for
      shipping or removal, please use the fields in the ship stage.`,
  },

  'flag_name': {
    type: 'input',
    attrs: TEXT_FIELD_ATTRS,
    required: false,
    label: 'Flag name',
    help_text: html`
      Name of the flag on chrome://flags that enables this feature.`,
  },

  'prefixed': {
    type: 'checkbox',
    label: 'Prefixed?',
    initial: false,
    help_text: '',
  },

};

// Return a simplified field type to help differentiate the
// render behavior of each field in chromedash-feature-detail
function categorizeFieldType(field) {
  if (field.attrs === MULTI_URL_FIELD_ATTRS) {
    return 'multi-url';
  } else if (field.attrs === URL_FIELD_ATTRS) {
    return 'url';
  } else if (field.type === 'checkbox') {
    return 'checkbox';
  }
  return 'text'; // select, input, textarea can all render as plain text.
}

// Return a field name with underscored replaced and first character capitalized
function makeHumanReadable(fieldName) {
  fieldName = fieldName.replace('_', ' ');
  return fieldName.charAt(0).toUpperCase() + fieldName.slice(1);
}

// Return an array of field info
function makeDisplaySpec(fieldName) {
  const field = ALL_FIELDS[fieldName];
  const displayName = field.label || makeHumanReadable(fieldName);
  const fieldType = categorizeFieldType(field);
  return [fieldName, displayName, fieldType];
};

// Return a list of field specs for each of the fields named in the args.
function makeDisplaySpecs(fields) {
  return fields.map(field => makeDisplaySpec(field));
};

export const DISPLAY_FIELDS_IN_STAGES = {
  'Metadata': makeDisplaySpecs([
    'category', 'feature_type', 'intent_stage', 'accurate_as_of',
  ]),
  [INTENT_STAGES.INTENT_INCUBATE[0]]: makeDisplaySpecs([
    'initial_public_proposal_url', 'explainer_links',
    'requires_embedder_support',
  ]),
  [INTENT_STAGES.INTENT_IMPLEMENT[0]]: makeDisplaySpecs([
    'spec_link', 'standard_maturity', 'api_spec', 'spec_mentors',
    'intent_to_implement_url',
  ]),
  [INTENT_STAGES.INTENT_EXPERIMENT[0]]: makeDisplaySpecs([
    'devtrial_instructions', 'doc_links',
    'interop_compat_risks',
    'safari_views', 'safari_views_link', 'safari_views_notes',
    'ff_views', 'ff_views_link', 'ff_views_notes',
    'web_dev_views', 'web_dev_views_link', 'web_dev_views_notes',
    'other_views_notes',
    'security_review_status', 'privacy_review_status',
    'ergonomics_risks', 'activation_risks', 'security_risks',
    'debuggability',
    'all_platforms', 'all_platforms_descr', 'wpt', 'wpt_descr',
    'sample_links', 'devrel', 'ready_for_trial_url',
    'dt_milestone_desktop_start', 'dt_milestone_android_start',
    'dt_milestone_ios_start',
    'flag_name',
  ]),
  [INTENT_STAGES.INTENT_IMPLEMENT_SHIP[0]]: makeDisplaySpecs([
    'launch_bug_url',
    'tag_review', 'tag_review_status',
    'webview_risks',
    'measurement', 'prefixed', 'non_oss_deps',
  ]),
  [INTENT_STAGES.INTENT_EXTEND_TRIAL[0]]: makeDisplaySpecs([
    'experiment_goals', 'experiment_risks',
    'experiment_extension_reason', 'ongoing_constraints',
    'origin_trial_feedback_url', 'intent_to_experiment_url',
    'r4dt_url',
    'intent_to_extend_experiment_url',
    'i2e_lgtms', 'r4dt_lgtms',
    'ot_milestone_desktop_start', 'ot_milestone_desktop_end',
    'ot_milestone_android_start', 'ot_milestone_android_end',
    'ot_milestone_webview_start', 'ot_milestone_webview_end',
    'experiment_timeline', // Deprecated
  ]),
  [INTENT_STAGES.INTENT_SHIP[0]]: makeDisplaySpecs([
    'finch_url', 'anticipated_spec_changes',
    'shipped_milestone', 'shipped_android_milestone',
    'shipped_ios_milestone', 'shipped_webview_milestone',
    'intent_to_ship_url', 'i2s_lgtms',
  ]),
  [INTENT_STAGES.INTENT_SHIPPED[0]]: makeDisplaySpecs([]),
};
