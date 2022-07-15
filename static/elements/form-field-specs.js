import {html} from 'lit';


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
    help_text: html`
        Capitalize only the first letter and the beginnings of proper nouns.
        <br/><br/>
        <a target="_blank"
            href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#feature-name">
          Learn more</a>.
        <a target="_blank"
            href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#feature-name-example">
          Example</a>.
      `,
  },

  'summary': {
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
    help_text: html`
        Comma separated list of full email addresses. Accounts
        from @chromium.org are preferred.`,
  },

  'editors': {
    help_text: html`
        Comma separated list of full email addresses. These users will be
        allowed to edit this feature, but will not be listed as feature owners.`,
  },

  'unlisted': {
    help_text: html`
        Check this box to hide draft emails in list views. Anyone with
        a link will be able to view the feature's detail page.`,
  },

  'blink_components': {
    help_text: html`
        Select the most specific component. If unsure, leave as "Blink".`,
  },

  'category': {
    help_text: html`
        Select the most specific category. If unsure, leave as "Miscellaneous".`,
  },

  'feature_type': {
    help_text: html`
        Select the feature type.`,
    possible_extra_help: html`
    <p>
    The first thing you will need to do is identify what type of feature you are building:
    </p>

    <h3>New feature incubation</h3>
    <p>
    This is the normal path when we are incubating and defining new features from scratch - e.g., most Fugu features follow this pattern, and any feature where we start without an already-defined standard for the feature. This also covers changes that are extending existing features (e.g., defining a new value and behavior for an existing standard feature). This type of feature has the most associated process steps, as it is charting new territory.
    </p>

    <h3>Implementation of existing standard</h3>
    <p>
    This type of feature has a lighter-weight “fast track” process, but this process can only be used when the feature has already been defined in a consensus standards document - e.g. a W3C Working Group has already agreed on the design, it has already been merged into a WHATWG standard, or the feature has already been implemented in another engine.
    </p>

    <h3>Web developer facing change to existing code</h3>
    <p>
    This is generally a public service announcement- “This is a web-developer-facing change to existing code without API changes, but you may see side effects.” This may be due to large-scale code refactoring or rewriting, where the goal is to cause no behavioral changes (but due to scope of change, side effects are likely), or this may encompass changes to current code that fix a bug or implement new changes to the spec without changes to the API shape itself.
    </p>

    <h3>Deprecation</h3>
    <p>
    Removal of already-shipped features.
    </p>
    `,
  },

  'intent_stage': {
    help_text: html`
        Select the appropriate spec process stage. If you select
        Dev trials, Origin Trial, or Shipped, be sure to set the
        equivalent Implementation status.`,
  },

  'search_tags': {
    help_text: html`
        Comma separated keywords used only in search.`,
  },

  'impl_status_chrome': {
    help_text: html`
        Select the appropriate Chromium development stage. If you
        select In developer trial, Origin trial, or Enabled by
        default, be sure to set the equivalent Process stage.`,
  },

  'bug_url': {
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
    help_text: html`
        Launch bug url (https://bugs.chromium.org/...) to track launch approvals.
        <br/><br/>
        <a target="_blank"
            href="https://bugs.chromium.org/p/chromium/issues/entry?template=Chrome+Launch+Feature">
          Create launch bug</a>.`,
  },

  'motivation': {
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
    help_text: html`
        Link to the first public proposal to create this feature, e.g.,
        a WICG discourse post.`,
  },

  'explainer_links': {
    help_text: html`
        Link to explainer(s) (one URL per line). You should have
        at least an explainer in hand and have shared it on a
        public forum before sending an Intent to Prototype in
        order to enable discussion with other browser vendors,
        standards bodies, or other interested parties.`,
  },

  'spec_link': {
    help_text: html`
        Link to the spec, if and when available. When implementing
        a spec update, please link to a heading in a published spec
        rather than a pull request when possible.`,
  },

  'comments': {
    help_text: html`
        Additional comments, caveats, info...`,
  },

  'standard_maturity': {
    help_text: html`
        How far along is the standard that this feature implements?`,
  },

  'api_spec': {
    help_text: html`
        The spec document has details in a specification language
        such as Web IDL, or there is an existing MDN page.`,
  },

  'spec_mentors': {
    help_text: html`
        Experienced 
        <a target="_blank"
            href="https://www.chromium.org/blink/spec-mentors">
          spec mentors</a> 
        are available to help you improve your feature spec.`,
  },

  'intent_to_implement_url': {
    help_text: html`
        After you have started the "Intent to Prototype"
        discussion thread, link to it here.`,
  },

  'doc_links': {
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
    help_text: html`
        It's important to measure the adoption and success of web-exposed
        features.  Note here what measurements you have added to track the
        success of this feature, such as a link to the UseCounter(s) you
        have set up.`,
  },

  'security_review_status': {
    help_text: html`
        Status of the security review.`,
  },

  'privacy_review_status': {
    help_text: html`Status of the privacy review.`,
  },

  'tag_review': {
    help_text: html`Link(s) to TAG review(s), or explanation why this is 
                not needed.`,
  },

  'tag_review_status': {
    help_text: html`Status of the tag review.`,
  },

  'intent_to_ship_url': {
    help_text: html`After you have started the "Intent to Ship" discussion 
                thread, link to it here.`,
  },

  'ready_for_trial_url': {
    help_text: html`After you have started the "Ready for Trial" discussion 
                thread, link to it here.`,
  },

  'intent_to_experiment_url': {
    help_text: html`After you have started the "Intent to Experiment" 
                 discussion thread, link to it here.`,
  },

  'intent_to_extend_experiment_url': {
    help_text: html`If this feature has an "Intent to Extend Experiment" 
                 discussion thread, link to it here.`,
  },

  'r4dt_url': {
    help_text: html`After you have started the "Request for Deprecation Trial" 
                discussion thread, link to it here.`,
  },

  'interop_compat_risks': {
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
    help_text: html`
      See <a target="_blank" href="https://bit.ly/blink-signals">
      https://bit.ly/blink-signals</a>`,
  },

  'safari_views_link': {
    help_text: html`Citation link.`,
  },

  'safari_views_notes': {},

  'ff_views': {
    help_text: html`
      See <a target="_blank" href="https://bit.ly/blink-signals">
      https://bit.ly/blink-signals</a>`,
  },

  'ff_views_link': {
    help_text: html`
    Citation link.`,
  },

  'ff_views_notes': {},

  'web_dev_views': {
    help_text: html`
      If unsure, default to "No signals". 
      See <a target="_blank" href="https://goo.gle/developer-signals">
      https://goo.gle/developer-signals</a>`,
  },

  'web_dev_views_link': {
    help_text: html`
      Citation link.`,
  },

  'web_dev_views_notes': {
    help_text: html`
      Reference known representative examples of opinions, 
      both positive and negative.`,
  },

  'other_views_notes': {
    help_text: html`
      For example, other browsers.`,
  },

  'ergonomics_risks': {
    help_text: html`
      Are there any other platform APIs this feature will frequently be 
      used in tandem with? Could the default usage of this API make it 
      hard for Chrome to maintain good performance (i.e. synchronous 
      return, must run on a certain thread, guaranteed return timing)?`,
  },

  'activation_risks': {
    help_text: html`
      Will it be challenging for developers to take advantage of this 
      feature immediately, as-is? Would this feature benefit from 
      having polyfills, significant documentation and outreach, and/or 
      libraries built on top of it to make it easier to use?`,
  },

  'security_risks': {
    help_text: html`
      List any security considerations that were taken into account 
      when designing this feature.`,
  },

  'webview_risks': {
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
    help_text: html`
      When does the experiment start and expire? 
      Deprecated: 
      Please use the numeric fields above instead.`,
  },

  'ot_milestone_desktop_start': {
    help_text: html`
      First desktop milestone that will support an origin 
      trial of this feature.`,
  },

  'ot_milestone_desktop_end': {
    help_text: html`
      Last desktop milestone that will support an origin 
      trial of this feature.`,
  },

  'ot_milestone_android_start': {
    help_text: html`
      First android milestone that will support an origin 
      trial of this feature.`,
  },

  'ot_milestone_android_end': {
    help_text: html`
      Last android milestone that will support an origin 
      trial of this feature.`,
  },

  'ot_milestone_webview_start': {
    help_text: html`
      First WebView milestone that will support an origin 
      trial of this feature.`,
  },

  'ot_milestone_webview_end': {
    help_text: html`
      Last WebView milestone that will support an origin 
      trial of this feature.`,
  },

  'experiment_risks': {
    help_text: html`
      When this experiment comes to an end are there any risks to the 
      sites that were using it, for example losing access to important 
      storage due to an experimental storage API?`,
  },

  'experiment_extension_reason': {
    help_text: html`
      If this is a repeated or extended experiment, explain why it's
      being repeated or extended.  Also, fill in discussion link fields below.`,
  },

  'ongoing_constraints': {
    help_text: html`
      Do you anticipate adding any ongoing technical constraints to 
      the codebase while implementing this feature? We prefer to avoid 
      features that require or assume a specific architecture. 
      For most features, the answer is "None."`,
  },

  'origin_trial_feedback_url': {
    help_text: html`
      If your feature was available as an origin trial, link to a summary 
      of usage and developer feedback. If not, leave this empty.`,
  },

  'anticipated_spec_changes': {
    help_text: html`
      Open questions about a feature may be a source of future web compat 
      or interop issues. Please list open issues (e.g. links to known 
      github issues in the repo for the feature specification) whose 
      resolution may introduce web compat/interop risk (e.g., changing 
      the naming or structure of the API in a 
      non-backward-compatible way).`,
  },

  'finch_url': {
    help_text: html`
      If your feature will roll out gradually via a 
      <a href="go/finch" targe="_blank">Finch experiment</a>, 
      link to it here.`,
  },

  'i2e_lgtms': {
    help_text: html`
      Full email address of API owner who LGTM\'d the 
      Intent to Experiment email thread.`,
  },

  'i2s_lgtms': {
    help_text: html`
      Comma separated list of 
      email addresses of API owners who LGTM'd 
      the Intent to Ship email thread.  `,
  },

  'r4dt_lgtms': {
    help_text: html`
      Full email addresses of API owners who LGTM\'d 
      the Request for Deprecation Trial email thread.`,
  },

  'debuggability': {
    help_text: html`
      Description of the DevTools debugging support for your feature. 
      Please follow 
      <a target="_blank" 
          href="https://goo.gle/devtools-checklist">
        DevTools support checklist</a> for guidance.`,
  },

  'all_platforms': {
    help_text: html`
      Will this feature be supported on all six Blink platforms 
      (Windows, Mac, Linux, Chrome OS, Android, and Android WebView)?`,
  },

  'all_platforms_descr': {
    help_text: html`
      Explain why this feature is, or is not, 
      supported on all platforms.`,
  },

  'wpt': {
    help_text: html`
      Is this feature fully tested in Web Platform Tests?`,
  },

  'wpt_descr': {
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
    help_text: html`
      Links to samples (one URL per line).`,
  },

  'non_oss_deps': {
    help_text: html`
      Does the feature depend on any code or APIs outside the Chromium 
      open source repository and its open-source dependencies to 
      function? (e.g. server-side APIs, operating system APIs 
      tailored to this feature or closed-source code bundles) 
      Yes or no. If yes, explain why this is necessary.`,
  },

  'devrel': {
    help_text: html`
      Comma separated list of full email addresses.`,
  },

  'shipped_milestone': {
    help_text: SHIPPED_HELP_TXT,
  },

  'shipped_android_milestone': {
    help_text: SHIPPED_HELP_TXT,
  },

  'shipped_ios_milestone': {
    help_text: SHIPPED_HELP_TXT,
  },

  'shipped_webview_milestone': {
    help_text: SHIPPED_WEBVIEW_HELP_TXT,
  },

  'requires_embedder_support': {
    help_text: html`
       Will this feature require support in //chrome?`,
    extra_help: html`
       That includes any code in //chrome, even if that is for 
       functionality on top of the spec.  Other //content embedders will need to be aware of that functionality. 
       Please add a row to this 
       <a target="_blank"
          href="https://docs.google.com/spreadsheets/d/1QV4SW4JBG3IyLzaonohUhim7nzncwK4ioop2cgUYevw/edit#gid=0">
        tracking spreadsheet</a>.`,
  },

  'devtrial_instructions': {
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
    help_text: html`
      First milestone that allows web developers to try 
      this feature on desktop platforms by setting a flag. 
      When flags are enabled by default in preparation for 
      shipping or removal, please use the fields in the ship stage.`,
  },

  'dt_milestone_android_start': {
    help_text: html`
      First milestone that allows web developers to try 
      this feature on desktop platforms by setting a flag. 
      When flags are enabled by default in preparation for 
      shipping or removal, please use the fields in the ship stage.`,
  },

  'dt_milestone_ios_start': {
    help_text: html`
      First milestone that allows web developers to try 
      this feature on desktop platforms by setting a flag. 
      When flags are enabled by default in preparation for 
      shipping or removal, please use the fields in the ship stage.`,
  },

  'flag_name': {
    help_text: html`
      Name of the flag on chrome://flags that enables this feature.`,
  },

};
