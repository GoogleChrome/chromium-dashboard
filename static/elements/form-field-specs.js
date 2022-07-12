import {html} from 'lit';

// Map of specifications for all form fields.
// TODO:
//   * Finish migrating remaining fields.
//   * Migrate other properties.
export const ALL_FIELDS = {

  'name': {
    help_text: html`
        Capitalize only the first letter and the beginnings of proper nouns.
        <a target="_blank"
            href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#feature-name">
          Learn more</a>
        <a target="_blank"
            href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#feature-name-example">
          Example</a>
    `},

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
          Learn more</a>
        <a target="_blank"
            href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#example-1">
          Example</a>
      `},

  'owner': {
    help_text: html`
        Comma separated list of all owners' email addresses. Accounts 
        from @chromium.org are preferred.`,
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
        Tracking bug url (https://bugs.chromium.org/...). This bug
        should have "Type=Feature" set and be world readable.
        Note: This field only accepts one URL.\n\n
        <a target="_blank"
            href="https://bugs.chromium.org/p/chromium/issues/entry">
          Create tracking bug</a>`,
  },

  'launch_bug_url': {
    help_text: html`
        Launch bug url (https://bugs.chromium.org/...) to track launch approvals.
        <a target="_blank"
            href="https://bugs.chromium.org/p/chromium/issues/entry?template=Chrome+Launch+Feature">
          Create launch bug</a>.`,
  },

  'motivation': {
    help_text: html`
        Explain why the web needs this change. It may be useful 
        to describe what web developers are forced to do without 
        it. When possible, add links to your explainer 
        backing up your claims.\n\n
        This text is sometimes included with the summary in the
        beta post, enterprise release notes and other external
        documents. Write in a matter-of-fact manner and in the
        present tense.\n\n
        <a target="_blank" 
            href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#motivation-example">
          Example</a>.`,
  },

  'deprecation_motivation': {
    help_text: html`
        Deprecations and removals must have strong reasons, backed up
        by measurements. There must be clear and actionable paths forward
        for developers.\n\n
        This text is sometimes included with the summary in the
        beta post, enterprise release notes and other external
        documents. Write in a matter-of-fact manner and in the
        present tense.\n\n
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
        public forum before sending an intent to prototype in
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
        After you have started the intent to prototype
        discussion thread, link to it here.`,
  },

  'doc_links': {
    help_text: html`
        Links to design doc(s) (one URL per line), if and when
        available. [This is not required to send out an intent
        to prototype. Please update the intent thread with the
        design doc when ready]. An explainer and/or design doc
        is sufficient to start this process. [Note: Please
        include links and data, where possible, to support any
        claims.`,
  },

  'neasurement': {
    help_text: html`
        It's important to measure the adoption and success of web-exposed
        features.  Note here what measurements you have added to track the
        success of this feature, such as a link to the UseCounter(s) you
        have set up.`,
  },
};
