import {html} from 'lit';
import {
  ENTERPRISE_FEATURE_CATEGORIES,
  FEATURE_CATEGORIES,
  FEATURE_TYPES,
  FEATURE_TYPES_WITHOUT_ENTERPRISE,
  IMPLEMENTATION_STATUS,
  PLATFORM_CATEGORIES,
  ROLLOUT_IMPACT,
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

const MULTI_STRING_FIELD_ATTRS = {
  title: 'Enter one or more comma-separated complete words.',
  type: 'text',
  multiple: true,
  placeholder: 'EnableFeature1, Feature1Policy',
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

const MILESTONE_NUMBER_FIELD_ATTRS = {
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
    enterprise_help_text: html`
       <p>This text will be used in the
        <a href="https://support.google.com/chrome/a/answer/7679408?hl=en" target="_blank">
       enterprise release notes</a>,
        which are publicly visible and primarily written for IT admins.</p>
       <p>Explain what's changing from the point of view of an end-user,
        developer, or administrator. Indicate what the motivation is for
        this change, especially if there’s security or privacy benefits to
        the change. If an admin should do something (like test or set an enterprise policy),
        please explain. Finally, if the change has a user-visible benefit
        (eg. better security or privacy), explain that motivation.
        See <a href="go/releasenotes-examples" target="_blank">go/releasenotes-examples</a>
        for examples.</p>`,
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
    choices: FEATURE_TYPES_WITHOUT_ENTERPRISE,
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
        (under <a href="#id_explainer_links">Explainer link(s)</a>)
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
        Link to the first public proposal to create this feature.`,
    extra_help: html`
        If there isn't another obvious place to propose your feature, create a
        <a target="_blank"
           href="https://github.com/WICG/proposals#what-does-a-proposal-look-like">
        WICG proposal</a>.
        You can use your proposal document to help you socialize the problem with other vendors
        and developers.`,
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
    extra_help: html`
        <p>
        See the TAG guide to writing <a target="_blank"
           href="https://tag.w3.org/explainers/">Explainers</a>
        for several examples of good explainers and tips for effective explainers.
        </p>
        <p>
        If you've already made an initial public proposal (see above),
        post your explainer to that thread.
        Otherwise, make an initial proposal based on your explainer.
        </p>
        <p>
        Once a second organization is interested in the WICG proposal,
        you can move the explainer into the WICG.
        The <a href="https://wicg.github.io/admin/charter.html#chairs">WICG co-chairs</a>
        can help you.
        </p>
        <p>
        If you want help, ask for a <a target="_blank"
           href="https://sites.google.com/a/chromium.org/dev/blink/spec-mentors">specification mentor</a>.
        </p>`,
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
    label: 'Spec mentors',
    help_text: html`
        Experienced
        <a target="_blank"
            href="https://www.chromium.org/blink/spec-mentors">
          spec mentors</a>
        are available to help you improve your feature spec.`,
  },

  'intent_to_implement_url': {
    type: 'input',
    name: 'intent_thread_url',
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

  'availability_expectation': {
    type: 'textarea',
    attrs: {rows: 4},
    required: false,
    label: 'Availability expectation',
    help_text: html`
      What is your availability expectation for this feature?
      Examples:`,
    extra_help: html`
      <ul>
        <li>Feature is available on Web Platform mainline within 12 months
            of launch in Chrome.
        <li>Feature is available only in Chromium browsers for the
            foreseeable future.
      </ul>
    `,
  },

  'adoption_expectation': {
    type: 'textarea',
    attrs: {rows: 4},
    required: false,
    label: 'Adoption expectation',
    help_text: html`
      What is your adoption expectation for this feature?
      Examples:`,
    extra_help: html`
      <ul>
        <li>Feature is considered a best practice for some use case
            within 12 months of reaching Web Platform baseline.
        <li>Feature is used by specific partner(s) to provide functionality
            within 12 months of launch in Chrome.
        <li>At least 3 major abstractions replace their use of an existing
            feature with this feature within 24 months of reaching mainline.
      </ul>
    `,
  },

  'adoption_plan': {
    type: 'textarea',
    attrs: {rows: 4},
    required: false,
    label: 'Adoption plan',
    help_text: html`
      What is the plan to achieve the stated expectations?
      Please provide a plan that covers availability and adoption
      for the feature.`,
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
    name: 'intent_thread_url',
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Intent to Ship link',
    help_text: html`After you have started the "Intent to Ship" discussion
                thread, link to it here.`,
  },

  'announcement_url': {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Ready for Trial link',
    help_text: html`After you have started the "Ready for Trial" discussion
                thread, link to it here.`,
  },

  'intent_to_experiment_url': {
    name: 'intent_thread_url',
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Intent to Experiment link',
    help_text: html`After you have started the "Intent to Experiment"
                 discussion thread, link to it here.`,
  },

  'intent_to_extend_experiment_url': {
    name: 'intent_thread_url',
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Intent to Extend Experiment link',
    help_text: html`If this feature has an "Intent to Extend Experiment"
                 discussion thread, link to it here.`,
  },

  'r4dt_url': {
    // form field name matches underlying DB field (sets "intent_to_experiment_url" field in DB).
    name: 'intent_thread_url',
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
          href="https://www.chromium.org/blink/guidelines/web-platform-changes-guidelines#finding-balance">
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
    displayLabel: 'Safari views link',
    help_text: html`Citation link.`,
  },

  'safari_views_notes': {
    type: 'textarea',
    attrs: {rows: 2, placeholder: 'Notes'},
    required: false,
    label: '',
    displayLabel: 'Safari views notes',
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
    displayLabel: 'Firefox views link',
    help_text: html`
    Citation link.`,
  },

  'ff_views_notes': {
    type: 'textarea',
    attrs: {rows: 2, placeholder: 'Notes'},
    required: false,
    label: '',
    displayLabel: 'Firefox views notes',
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
    displayLabel: 'Web / Framework developer views link',
    help_text: html`
      Citation link.`,
  },

  'web_dev_views_notes': {
    type: 'textarea',
    attrs: {rows: 2, placeholder: 'Notes'},
    required: false,
    label: '',
    displayLabel: 'Web / Framework developer views notes',
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
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'OT desktop start',
    help_text: html`
      First desktop milestone that will support an origin
      trial of this feature.`,
  },

  'ot_milestone_desktop_end': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'OT desktop end',
    help_text: html`
      Last desktop milestone that will support an origin
      trial of this feature.`,
  },

  'ot_milestone_android_start': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'OT Android start',
    help_text: html`
      First android milestone that will support an origin
      trial of this feature.`,
  },

  'ot_milestone_android_end': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'OT Android end',
    help_text: html`
      Last android milestone that will support an origin
      trial of this feature.`,
  },

  'ot_milestone_webview_start': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'OT WebView start',
    help_text: html`
      First WebView milestone that will support an origin
      trial of this feature.`,
  },

  'ot_milestone_webview_end': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
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

  'extension_desktop_last': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'Trial extension desktop end',
    help_text: html`
      The new last desktop milestone for which the trial has been extended. `,
  },

  'extension_android_last': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'Trial extension Android end',
    help_text: html`
      The new last android milestone for which the trial has been extended. `,
  },

  'extension_webview_last': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'Trial extension WebView end',
    help_text: html`
      The new last WebView milestone for which the trial has been extended.`,
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
      <a target="_blank"
           href="http://go/finch">Finch experiment</a>,
      link to it here.`,
  },

  'i2e_lgtms': {
    type: 'input',
    attrs: {...MULTI_EMAIL_FIELD_ATTRS, placeholder: 'This field is deprecated', disabled: true},
    required: false,
    label: 'Intent to Experiment LGTM by',
    help_text: html`
      Full email address of API owner who LGTM\'d the
      Intent to Experiment email thread.`,
  },

  'i2s_lgtms': {
    type: 'input',
    attrs: {...MULTI_EMAIL_FIELD_ATTRS, placeholder: 'This field is deprecated', disabled: true},
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
    attrs: {...MULTI_EMAIL_FIELD_ATTRS, placeholder: 'This field is deprecated', disabled: true},
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
      Please link to the <a target="_blank"
           href="https://wpt.fyi/results">results on
      wpt.fyi</a>. If any part of the feature is not tested by
      web-platform-tests, please include links to issues, e.g. a
      web-platform-tests issue with the "infra" label explaining why a
      certain thing cannot be tested
      (<a target="_blank"
           href="https://github.com/w3c/web-platform-tests/issues/3867">example</a>),
      a spec issue for some change that would make it possible to test.
      (<a target="_blank"
           href="https://github.com/whatwg/fullscreen/issues/70">example</a>),
      or a Chromium issue to upstream some existing tests
      (<a target="_blank"
           href="https://bugs.chromium.org/p/chromium/issues/detail?id=695486">example</a>).`,
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
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'Chrome for desktop',
    help_text: SHIPPED_HELP_TXT,
  },

  'shipped_android_milestone': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'Chrome for Android',
    help_text: SHIPPED_HELP_TXT,
  },

  'shipped_ios_milestone': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'Chrome for iOS (RARE)',
    help_text: SHIPPED_HELP_TXT,
  },

  'shipped_webview_milestone': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
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
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
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
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
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
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
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

  'display_name': {
    type: 'input',
    attrs: TEXT_FIELD_ATTRS,
    required: false,
    label: 'Stage display name',
    help_text: html`
        <p>Optional. Stage name to display on the feature detail page.</p>`,
    extra_help: html`
    <p>
    This name is only used for displaying stages on this site. Use this to differentiate stages of the same type.
    </p>
    <h4>Examples</h4>
    <ul>
      <li>Extended deprecation trial</li>
      <li>Second origin trial run</li>
      <li>Delayed ship for Android</li>
    </ul>`,
  },

  'enterprise_policies': {
    type: 'input',
    attrs: MULTI_STRING_FIELD_ATTRS,
    required: false,
    label: 'Enterprise policies',
    help_text: html`
      List the policies that are being introduced, removed, or can be used to control the feature at this stage, if any.`,
  },

  'enterprise_feature_categories': {
    type: 'multiselect',
    choices: ENTERPRISE_FEATURE_CATEGORIES,
    required: false,
    label: 'Categories',
    help_text: html`
      Select all that apply.`,
  },

  'rollout_impact': {
    type: 'select',
    choices: ROLLOUT_IMPACT,
    initial: ROLLOUT_IMPACT.IMPACT_MEDIUM[0],
    label: 'Impact',
    help_text: html`
      A stage is probably high impact if it introduces a breaking change on the stable channel,
      or seriously changes the experience of using Chrome. Use your judgment; if you're unsure,
      most stages are Medium impact.`,
  },

  'rollout_milestone': {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'Rollout milestone',
    help_text: html`
      The milestone in which this stage rolls out to the stable channel (even a 1% rollout)`,
  },

  'rollout_platforms': {
    type: 'multiselect',
    choices: PLATFORM_CATEGORIES,
    required: false,
    label: 'Rollout platforms',
    help_text: html`
      The platform(s) affected by this stage`,
  },

  'rollout_details': {
    type: 'textarea',
    attrs: {rows: 4},
    required: false,
    label: 'Rollout details',
    help_text: html`
      Explain what specifically is changing in this milestone, for the given platforms.
      Many features are composed of multiple stages on different milestones. For example,
      you may have a stage that introduces a change and a temporary policy to control it,
      then another stage on a subsequent milestone that removes the policy. Alternatively,
      you may ship the feature to different platforms in different milestones.`,
  },

  'breaking_change': {
    type: 'checkbox',
    label: 'Breaking change',
    initial: false,
    help_text: html`
      This is a breaking change: customers or developers must take action
      to continue using some existing functionaity.`,
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
  const fieldProps = ALL_FIELDS[fieldName];
  const displayName = fieldProps.label || fieldProps.displayLabel ||
        makeHumanReadable(fieldName);
  const fieldType = categorizeFieldType(fieldProps);
  return [fieldName, displayName, fieldType];
};

export function makeDisplaySpecs(fieldNames) {
  return fieldNames.map(fieldName => makeDisplaySpec(fieldName));
}
