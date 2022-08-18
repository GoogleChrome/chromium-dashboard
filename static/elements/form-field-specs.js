import {html} from 'lit';
import {
  FEATURE_CATEGORIES,
  FEATURE_TYPES,
  INTENT_STAGES,
  STANDARD_MATURITY_CHOICES,
  REVIEW_STATUS_CHOICES,
  VENDOR_VIEWS_COMMON,
  VENDOR_VIEWS_GECKO,
  WEB_DEV_VIEWS,
} from './form-field-enums';


const SHIPPED_HELP_TXT = html`
  First milestone to ship with this status. Applies to: Enabled by
  default, Browser Intervention, Deprecated, and Removed.`;

const
  SHIPPED_WEBVIEW_HELP_TXT = html`
  First milestone to ship with this status.
  Applies to Enabled by default, Browser
  Intervention, Deprecated, and Removed.`;

// Map of specifications for all form fields.
// TODO: Migrate other properties.
export const ALL_FIELDS = {

  'name': {
    label: 'Feature name',
    help_text: html`
        <p>Capitalize only the first letter and the beginnings of proper nouns.</p>
        <a target="_blank"
            href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#feature-name">
          Learn more</a>.
        <a target="_blank"
            href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#feature-name-example">
          Example</a>.
      `,
  },

  'summary': {
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

        <a target="_blank"
            href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#summary">
          Learn more</a>.
        <a target="_blank"
            href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#example-1">
          Example</a>.
      `,
  },

  'owner': {
    label: 'Feature owners',
    help_text: html`
        Comma separated list of full email addresses. Accounts
        from @chromium.org are preferred.`,
  },

  'editors': {
    label: 'Feature editors',
    help_text: html`
        Comma separated list of full email addresses. These users will be allowed to edit this feature, but will not be listed as feature owners.`,
  },

  'unlisted': {
    type: 'checkbox',
    label: 'Unlisted',
    help_text: html`
        Check this box to hide draft emails in list views. Anyone with
        a link will be able to view the feature's detail page.`,
  },

  'accurate_as_of': {
    type: 'checkbox',
    label: 'Confirm accuracy',
    help_text: html`
        Check this box to indicate that feature information is accurate
        as of today.
        (Selecting this avoids reminder emails for four weeks.)`,
  },

  'blink_components': {
    label: 'Blink component',
    help_text: html`
        Select the most specific component. If unsure, leave as "Blink".`,
  },

  'category': {
    type: 'select',
    choices: FEATURE_CATEGORIES,
    label: 'Category',
    help_text: html`
        Select the most specific category. If unsure, leave as "Miscellaneous".`,
  },

  'feature_type': {
    type: 'select',
    choices: FEATURE_TYPES,
    label: 'Feature type',
    help_text: html`
        Select the feature type.`,
  },

  'feature_type_radio_group': {
    type: 'radios',
    choices: FEATURE_TYPES,
    label: 'Feature type',
    help_text: html`
        Select the feature type.`,
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
    label: 'Process stage',
    help_text: html`
        Select the appropriate spec process stage. If you select
        Dev trials, Origin Trial, or Shipped, be sure to set the
        equivalent Implementation status.`,
  },

  'search_tags': {
    label: 'Search tags',
    help_text: html`
        Comma separated keywords used only in search.`,
  },

  'impl_status_chrome': {
    label: 'Implementation status',
    help_text: html`
        Select the appropriate Chromium development stage. If you
        select In developer trial, Origin trial, or Enabled by
        default, be sure to set the equivalent Process stage.`,
  },

  'bug_url': {
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
    label: 'Launch bug URL',
    help_text: html`
        Launch bug url (https://bugs.chromium.org/...) to track launch approvals.
        <br/><br/>
        <a target="_blank"
            href="https://bugs.chromium.org/p/chromium/issues/entry?template=Chrome+Launch+Feature">
          Create launch bug</a>.`,
  },

  'motivation': {
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
    label: 'Initial public proposal URL',
    help_text: html`
        Link to the first public proposal to create this feature, e.g.,
        a WICG discourse post.`,
  },

  'explainer_links': {
    label: 'Explainer link(s)',
    help_text: html`
        Link to explainer(s) (one URL per line). You should have
        at least an explainer in hand and have shared it on a
        public forum before sending an Intent to Prototype in
        order to enable discussion with other browser vendors,
        standards bodies, or other interested parties.`,
  },

  'spec_link': {
    label: 'Spec link',
    help_text: html`
        Link to the spec, if and when available. When implementing
        a spec update, please link to a heading in a published spec
        rather than a pull request when possible.`,
  },

  'comments': {
    label: 'Comments',
    help_text: html`
        Additional comments, caveats, info...`,
  },

  'standard_maturity': {
    type: 'select',
    choices: STANDARD_MATURITY_CHOICES,
    label: 'Standard maturity',
    help_text: html`
        How far along is the standard that this feature implements?`,
  },

  'api_spec': {
    type: 'checkbox',
    label: 'API spec',
    help_text: html`
        The spec document has details in a specification language
        such as Web IDL, or there is an existing MDN page.`,
  },

  'spec_mentors': {
    label: 'Spec mentor',
    help_text: html`
        Experienced
        <a target="_blank"
            href="https://www.chromium.org/blink/spec-mentors">
          spec mentors</a>
        are available to help you improve your feature spec.`,
  },

  'intent_to_implement_url': {
    label: 'Intent to Prototype link',
    help_text: html`
        After you have started the "Intent to Prototype"
        discussion thread, link to it here.`,
  },

  'doc_links': {
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
    label: 'Security review status',
    help_text: html`
        Status of the security review.`,
  },

  'privacy_review_status': {
    type: 'select',
    choices: REVIEW_STATUS_CHOICES,
    label: 'Privacy review status',
    help_text: html`Status of the privacy review.`,
  },

  'tag_review': {
    label: 'TAG Review',
    help_text: html`Link(s) to TAG review(s), or explanation why this is
                not needed.`,
  },

  'tag_review_status': {
    type: 'select',
    choices: REVIEW_STATUS_CHOICES,
    label: 'TAG review status',
    help_text: html`Status of the tag review.`,
  },

  'intent_to_ship_url': {
    label: 'Intent to Ship link',
    help_text: html`After you have started the "Intent to Ship" discussion
                thread, link to it here.`,
  },

  'ready_for_trial_url': {
    label: 'Ready for Trial link',
    help_text: html`After you have started the "Ready for Trial" discussion
                thread, link to it here.`,
  },

  'intent_to_experiment_url': {
    label: 'Intent to Experiment link',
    help_text: html`After you have started the "Intent to Experiment"
                 discussion thread, link to it here.`,
  },

  'intent_to_extend_experiment_url': {
    label: 'Intent to Extend Experiment link',
    help_text: html`If this feature has an "Intent to Extend Experiment"
                 discussion thread, link to it here.`,
  },

  'r4dt_url': {
    // Sets intent_to_experiment_url in DB
    label: 'Request for Deprecation Trial link',
    help_text: html`After you have started the "Request for Deprecation Trial"
                discussion thread, link to it here.`,
  },

  'interop_compat_risks': {
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
    choices: VENDOR_VIEWS_GECKO,
    label: 'Safari views',
    help_text: html`
      See <a target="_blank" href="https://bit.ly/blink-signals">
      https://bit.ly/blink-signals</a>`,
  },

  'safari_views_link': {
    label: '',
    help_text: html`Citation link.`,
  },

  'safari_views_notes': {
    label: '',
    help_text: '',
  },

  'ff_views': {
    type: 'select',
    choices: VENDOR_VIEWS_COMMON,
    label: 'Firefox views',
    help_text: html`
      See <a target="_blank" href="https://bit.ly/blink-signals">
      https://bit.ly/blink-signals</a>`,
  },

  'ff_views_link': {
    label: '',
    help_text: html`
    Citation link.`,
  },

  'ff_views_notes': {
    label: '',
    help_text: '',
  },

  'web_dev_views': {
    type: 'select',
    choices: WEB_DEV_VIEWS,
    label: 'Web / Framework developer views',
    help_text: html`
      If unsure, default to "No signals".
      See <a target="_blank" href="https://goo.gle/developer-signals">
      https://goo.gle/developer-signals</a>`,
  },

  'web_dev_views_link': {
    label: '',
    help_text: html`
      Citation link.`,
  },

  'web_dev_views_notes': {
    label: '',
    help_text: html`
      Reference known representative examples of opinions,
      both positive and negative.`,
  },

  'other_views_notes': {
    label: 'Other views',
    help_text: html`
      For example, other browsers.`,
  },

  'ergonomics_risks': {
    label: 'Ergonomics Risks',
    help_text: html`
      Are there any other platform APIs this feature will frequently be
      used in tandem with? Could the default usage of this API make it
      hard for Chrome to maintain good performance (i.e. synchronous
      return, must run on a certain thread, guaranteed return timing)?`,
  },

  'activation_risks': {
    label: 'Activation Risks',
    help_text: html`
      Will it be challenging for developers to take advantage of this
      feature immediately, as-is? Would this feature benefit from
      having polyfills, significant documentation and outreach, and/or
      libraries built on top of it to make it easier to use?`,
  },

  'security_risks': {
    label: 'Security Risks',
    help_text: html`
      List any security considerations that were taken into account
      when designing this feature.`,
  },

  'webview_risks': {
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
    label: 'Experiment Timeline',
    help_text: html`
      When does the experiment start and expire?
      Deprecated:
      Please use the numeric fields above instead.`,
  },

  'ot_milestone_desktop_start': {
    label: 'OT desktop start',
    help_text: html`
      First desktop milestone that will support an origin
      trial of this feature.`,
  },

  'ot_milestone_desktop_end': {
    label: 'OT desktop end',
    help_text: html`
      Last desktop milestone that will support an origin
      trial of this feature.`,
  },

  'ot_milestone_android_start': {
    label: 'OT Android start',
    help_text: html`
      First android milestone that will support an origin
      trial of this feature.`,
  },

  'ot_milestone_android_end': {
    label: 'OT Android end',
    help_text: html`
      Last android milestone that will support an origin
      trial of this feature.`,
  },

  'ot_milestone_webview_start': {
    label: 'OT WebView start',
    help_text: html`
      First WebView milestone that will support an origin
      trial of this feature.`,
  },

  'ot_milestone_webview_end': {
    label: 'OT WebView end',
    help_text: html`
      Last WebView milestone that will support an origin
      trial of this feature.`,
  },

  'experiment_risks': {
    label: 'Experiment Risks',
    help_text: html`
      When this experiment comes to an end are there any risks to the
      sites that were using it, for example losing access to important
      storage due to an experimental storage API?`,
  },

  'experiment_extension_reason': {
    label: 'Experiment Extension Reason',
    help_text: html`
      If this is a repeated or extended experiment, explain why it's
      being repeated or extended.  Also, fill in discussion link fields below.`,
  },

  'ongoing_constraints': {
    label: 'Ongoing Constraints',
    help_text: html`
      Do you anticipate adding any ongoing technical constraints to
      the codebase while implementing this feature? We prefer to avoid
      features that require or assume a specific architecture.
      For most features, the answer is "None."`,
  },

  'origin_trial_feedback_url': {
    label: 'Origin trial feedback summary',
    help_text: html`
      If your feature was available as an origin trial, link to a summary
      of usage and developer feedback. If not, leave this empty.`,
  },

  'anticipated_spec_changes': {
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
    label: 'Finch experiment',
    help_text: html`
      If your feature will roll out gradually via a
      <a href="go/finch" targe="_blank">Finch experiment</a>,
      link to it here.`,
  },

  'i2e_lgtms': {
    label: 'Intent to Experiment LGTM by',
    help_text: html`
      Full email address of API owner who LGTM\'d the
      Intent to Experiment email thread.`,
  },

  'i2s_lgtms': {
    label: 'Intent to Ship LGTMs by',
    help_text: html`
      Comma separated list of
      email addresses of API owners who LGTM'd
      the Intent to Ship email thread.  `,
  },

  'r4dt_lgtms': {
    // Sets i2e_lgtms field.
    label: 'Request for Deprecation Trial LGTM by',
    help_text: html`
      Full email addresses of API owners who LGTM\'d
      the Request for Deprecation Trial email thread.`,
  },

  'debuggability': {
    label: 'Debuggability',
    help_text: html`
      Description of the DevTools debugging support for your feature.
      Please follow
      <a target="_blank"
          href="https://goo.gle/devtools-checklist">
        DevTools support checklist</a> for guidance.`,
  },

  'all_platforms': {
    type: 'checkbox',
    label: 'Supported on all platforms?',
    help_text: html`
      Will this feature be supported on all six Blink platforms
      (Windows, Mac, Linux, Chrome OS, Android, and Android WebView)?`,
  },

  'all_platforms_descr': {
    label: 'Platform Support Explanation',
    help_text: html`
      Explain why this feature is, or is not,
      supported on all platforms.`,
  },

  'wpt': {
    label: 'Web Platform Tests',
    help_text: html`
      Is this feature fully tested in Web Platform Tests?`,
  },

  'wpt_descr': {
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
    label: 'Demo and sample links',
    help_text: html`
      Links to demos and samples (one URL per line).`,
  },

  'non_oss_deps': {
    label: 'Non-OSS dependencies',
    help_text: html`
      Does the feature depend on any code or APIs outside the Chromium
      open source repository and its open-source dependencies to
      function? (e.g. server-side APIs, operating system APIs
      tailored to this feature or closed-source code bundles)
      Yes or no. If yes, explain why this is necessary.`,
  },

  'devrel': {
    label: 'Developer relations emails',
    help_text: html`
      Comma separated list of full email addresses.`,
  },

  'shipped_milestone': {
    label: 'Chrome for desktop',
    help_text: SHIPPED_HELP_TXT,
  },

  'shipped_android_milestone': {
    label: 'Chrome for Android',
    help_text: SHIPPED_HELP_TXT,
  },

  'shipped_ios_milestone': {
    label: 'Chrome for iOS (RARE)',
    help_text: SHIPPED_HELP_TXT,
  },

  'shipped_webview_milestone': {
    label: 'Android Webview',
    help_text: SHIPPED_WEBVIEW_HELP_TXT,
  },

  'requires_embedder_support': {
    type: 'checkbox',
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
    label: 'DevTrial on desktop',
    help_text: html`
      First milestone that allows web developers to try
      this feature on desktop platforms by setting a flag.
      When flags are enabled by default in preparation for
      shipping or removal, please use the fields in the ship stage.`,
  },

  'dt_milestone_android_start': {
    label: 'DevTrial on Android',
    help_text: html`
      First milestone that allows web developers to try
      this feature on desktop platforms by setting a flag.
      When flags are enabled by default in preparation for
      shipping or removal, please use the fields in the ship stage.`,
  },

  'dt_milestone_ios_start': {
    label: 'DevTrial on iOS (RARE)',
    help_text: html`
      First milestone that allows web developers to try
      this feature on desktop platforms by setting a flag.
      When flags are enabled by default in preparation for
      shipping or removal, please use the fields in the ship stage.`,
  },

  'flag_name': {
    label: 'Flag name',
    help_text: html`
      Name of the flag on chrome://flags that enables this feature.`,
  },

  'prefixed': {
    type: 'checkbox',
    label: 'Prefixed?',
    help_text: '',
  },

};
