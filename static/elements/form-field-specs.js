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
        NOTE: Text in the beta release post, the enterprise release notes, 
        and other external sources will be based on this text.
  
        Begin with one line explaining what the feature does. Add one or two 
        lines explaining how this feature helps developers. Avoid language such 
        as "a new feature". They all are or have been new features.
  
        Write it from a web developer's point of view.
        Follow the example link below for more guidance.<br>
        <a target="_blank" 
            href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#summary-example">
          Guidelines and example</a>.`,
  },

  'owner': {
    help_text: html`
        Comma separated list of full email addresses. Prefer @chromium.org.`,
  },

  'unlisted': {
    help_text: html`
        Check this box for draft features that should not appear
        in the feature list. Anyone with the link will be able to
        view the feature on the detail page.`,
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
        Select the appropriate process stage.`,
  },

  'search_tags': {
    help_text: html`
        Comma separated keywords used only in search.`,
  },

  'impl_status_chrome': {
    help_text: html`
        Implementation status in Chromium.`,
  },

  'bug_url': {
    help_text: html`
        Tracking bug url (https://bugs.chromium.org/...). This bug
        should have "Type=Feature" set and be world readable.
        Note: This field only accepts one URL.`,
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
        backing up your claims. 
        <a target="_blank" 
            href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#motivation-example">
          Example</a>.`,
  },

  'deprecation_motivation': {
    help_text: html`
        Deprecations and removals must have strong reasons, backed up
        by measurements.  There must be clear and actionable paths forward
        for developers.  Please see
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
        Link to spec, if and when available.  Please update the
        chromestatus.com entry and the intent thread(s) with the
        spec link when available.`,
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

  'neasurement': {
    help_text: html`
        It's important to measure the adoption and success of web-exposed
        features.  Note here what measurements you have added to track the
        success of this feature, such as a link to the UseCounter(s) you
        have set up.`,
  },
};
