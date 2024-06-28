import {html, TemplateResult} from 'lit';
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
  DT_MILESTONE_FIELDS,
  OT_MILESTONE_START_FIELDS,
  SHIPPED_MILESTONE_FIELDS,
  STAGE_TYPES_DEV_TRIAL,
  STAGE_TYPES_ORIGIN_TRIAL,
  STAGE_TYPES_SHIPPING,
  ENTERPRISE_IMPACT,
} from './form-field-enums';
import {error} from 'console';

interface FieldAttrs {
  title?: string;
  type?: string;
  multiple?: boolean;
  placeholder?: string;
  pattern?: string;
  rows?: number;
  cols?: number;
  maxlength?: number;
  chromedash_single_pattern?: string;
  chromedash_split_pattern?: string;
  disabled?: boolean;
  min?: number;
}

interface MilestoneRange {
  earlier?: string;
  later?: string;
  allEarlier?: string;
  allLater?: string;
  warning?: string;
  error?: string;
}

type FeatureName = string;

interface Field {
  type?: string;
  name?: FeatureName;
  attrs?: FieldAttrs;
  required?: boolean;
  label?: string;
  help_text?: TemplateResult | string;
  enterprise_help_text?: TemplateResult;
  extra_help?: TemplateResult;
  enterprise_extra_help?: TemplateResult | string;
  check?: Function;
  initial?: number | boolean;
  enterprise_initial?: number;
  choices?:
    | Record<string, [number, string, string]>
    | Record<string, [number, string]>;
  displayLabel?: string;
  disabled?: boolean;
}

/* Patterns from https://www.oreilly.com/library/view/regular-expressions-cookbook/9781449327453/ch04s01.html
 * Removing single quote ('), backtick (`), and pipe (|) since they are risky unless properly escaped everywhere.
 * Also removing ! and % because they have special meaning for some older email routing systems. */
const USER_REGEX: string = String.raw`[A-Za-z0-9_#$&*+\/=?\{\}~^.\-]+`;
const DOMAIN_REGEX: string = String.raw`(([A-Za-z0-9\-]+\.)+[A-Za-z]{2,6})`;

const EMAIL_ADDRESS_REGEX: string = USER_REGEX + '@' + DOMAIN_REGEX;
const GOOGLE_EMAIL_ADDRESS_REGEX: string = `${USER_REGEX}@google.com`;
const EMAIL_ADDRESSES_REGEX: string =
  EMAIL_ADDRESS_REGEX + '([ ]*,[ ]*' + EMAIL_ADDRESS_REGEX + ')*';

// Simple http URLs
const PORTNUM_REGEX: string = '(:[0-9]+)?';
const URL_REGEX: string =
  '(https?)://' + DOMAIN_REGEX + PORTNUM_REGEX + String.raw`(/\S*)?`;
const URL_PADDED_REGEX: string = String.raw`\s*` + URL_REGEX + String.raw`\s*`;

const URL_FIELD_ATTRS: FieldAttrs = {
  title: 'Enter a full URL https://...',
  type: 'url',
  placeholder: 'https://...',
  pattern: URL_PADDED_REGEX,
};

const MULTI_STRING_FIELD_ATTRS: FieldAttrs = {
  title: 'Enter one or more comma-separated complete words.',
  type: 'text',
  multiple: true,
  placeholder: 'EnableFeature1, Feature1Policy',
};

const MULTI_EMAIL_FIELD_ATTRS: FieldAttrs = {
  title: 'Enter one or more comma-separated complete email addresses.',
  // Don't specify type="email" because browsers consider multiple emails
  // invalid, regardles of the multiple attribute.
  type: 'text',
  multiple: true,
  placeholder: 'user1@domain.com, user2@chromium.org',
  pattern: EMAIL_ADDRESSES_REGEX,
};

const TEXT_FIELD_ATTRS: FieldAttrs = {
  type: 'text',
};

const MILESTONE_NUMBER_FIELD_ATTRS: FieldAttrs = {
  type: 'number',
  placeholder: 'Milestone number',
};

const OT_MILESTONE_DESKTOP_RANGE: MilestoneRange = {
  earlier: 'ot_milestone_desktop_start',
  later: 'ot_milestone_desktop_end',
};

const OT_MILESTONE_ANDROID_RANGE: MilestoneRange = {
  earlier: 'ot_milestone_android_start',
  later: 'ot_milestone_android_end',
};

const OT_MILESTONE_WEBVIEW_RANGE: MilestoneRange = {
  earlier: 'ot_milestone_webview_start',
  later: 'ot_milestone_webview_end',
};

const OT_ALL_SHIPPED_MILESTONE_DESKTOP_RANGE: MilestoneRange = {
  earlier: 'ot_milestone_desktop_start',
  allLater: 'shipped_milestone',
  warning:
    'Origin trial starting milestone should be before all feature shipping milestones.',
};

const ALL_OT_SHIPPED_MILESTONE_DESKTOP_RANGE: MilestoneRange = {
  allEarlier: 'ot_milestone_desktop_start',
  later: 'shipped_milestone',
  warning:
    'All origin trials starting milestones should be before feature shipping milestone.',
};

const OT_ALL_SHIPPED_MILESTONE_WEBVIEW_RANGE: MilestoneRange = {
  earlier: 'ot_milestone_webview_start',
  allLater: 'shipped_webview_milestone',
  warning:
    'Origin trial starting milestone should be before all feature shipping milestones.',
};

const ALL_OT_SHIPPED_MILESTONE_WEBVIEW_RANGE: MilestoneRange = {
  allEarlier: 'ot_milestone_webview_start',
  later: 'shipped_webview_milestone',
  warning:
    'All origin trials starting milestones should be before feature shipping milestone.',
};

const OT_ALL_SHIPPED_MILESTONE_ANDROID_RANGE: MilestoneRange = {
  earlier: 'ot_milestone_android_start',
  allLater: 'shipped_android_milestone',
  warning:
    'Origin trial starting milestone should be before all feature shipping milestones.',
};

const ALL_OT_SHIPPED_MILESTONE_ANDROID_RANGE: MilestoneRange = {
  allEarlier: 'ot_milestone_android_start',
  later: 'shipped_android_milestone',
  warning:
    'All origin trials starting milestones should be before feature shipping milestone.',
};

const DT_ALL_SHIPPED_MILESTONE_DESKTOP_RANGE: MilestoneRange = {
  earlier: 'dt_milestone_desktop_start',
  allLater: 'shipped_milestone',
  warning: 'Shipped milestone should be later than dev trial.',
};

const ALL_DT_SHIPPED_MILESTONE_DESKTOP_RANGE: MilestoneRange = {
  allEarlier: 'dt_milestone_desktop_start',
  later: 'shipped_milestone',
  warning: 'Shipped milestone should be later than dev trial.',
};

const DT_ALL_SHIPPED_MILESTONE_ANDROID_RANGE: MilestoneRange = {
  earlier: 'dt_milestone_android_start',
  allLater: 'shipped_android_milestone',
  warning: 'Shipped milestone should be later than dev trial start milestone.',
};

const ALL_DT_SHIPPED_MILESTONE_ANDROID_RANGE: MilestoneRange = {
  allEarlier: 'dt_milestone_android_start',
  later: 'shipped_android_milestone',
  warning: 'Shipped milestone should be later than dev trial start milestone.',
};

const DT_ALL_SHIPPED_MILESTONE_IOS_RANGE: MilestoneRange = {
  earlier: 'dt_milestone_ios_start',
  allLater: 'shipped_ios_milestone',
  warning: 'Shipped milestone should be later than dev trial start milestone.',
};

const ALL_DT_SHIPPED_MILESTONE_IOS_RANGE: MilestoneRange = {
  allEarlier: 'dt_milestone_ios_start',
  later: 'shipped_ios_milestone',
  warning: 'Shipped milestone should be later than dev trial start milestone.',
};

const MULTI_URL_FIELD_ATTRS: FieldAttrs = {
  title: 'Enter one or more full URLs, one per line:\nhttps://...\nhttps://...',
  multiple: true,
  placeholder: 'https://...\nhttps://...',
  rows: 4,
  cols: 50,
  maxlength: 5000,
  chromedash_single_pattern: URL_REGEX,
  chromedash_split_pattern: String.raw`\s+`,
};

const SHIPPED_HELP_TXT = html` First milestone to ship with this status. Applies
to: Enabled by default, Browser Intervention, Deprecated, and Removed.`;

const SHIPPED_WEBVIEW_HELP_TXT = html` First milestone to ship with this status.
Applies to Enabled by default, Browser Intervention, Deprecated, and Removed.`;

// Map of specifications for all form fields.
export const ALL_FIELDS: Record<string, Field> = {
  name: {
    type: 'input',
    attrs: TEXT_FIELD_ATTRS,
    required: true,
    label: 'Feature name',
    help_text: html` <p>
      Capitalize only the first letter and the beginnings of proper nouns.
    </p>`,
    extra_help: html` <p>
        Each feature should have a unique name that is written as a noun phrase.
      </p>
      <ul>
        <li>
          Capitalize only the first letter and the beginnings of proper nouns.
        </li>
        <li>
          Avoid using verbs such as "add", "enhance", "deprecate", or "delete".
          Instead, simply name the feature itself and use the feature type and
          stage fields to indicate the intent of change.
        </li>
        <li>
          Do not include markup or markdown because they will not be rendered..
        </li>
        <li>
          Write keywords and identifiers as they would appear to a web
          developer, not as they are in source code. For example, a method
          implemented as NewInterface#dostuff would be written as in JavaScript:
          NewInterface.doStuff().
        </li>
      </ul>

      <h4>Examples</h4>
      <ul>
        <li>Conversion Measurement API</li>
        <li>CSS Flexbox: intrinsic size algorithm</li>
        <li>Permissions-Policy header</li>
      </ul>`,
    check: (_value, getFieldValue) => checkFeatureNameAndType(getFieldValue),
  },

  summary: {
    type: 'textarea',
    required: true,
    label: 'Summary',
    enterprise_help_text: html` <p>
        This text will be used in the
        <a
          href="https://support.google.com/chrome/a/answer/7679408"
          target="_blank"
          >enterprise release notes</a
        >, which are publicly visible and primarily written for IT admins.
      </p>
      <p>
        Explain what's changing from the point of view of an end-user,
        developer, or administrator. Indicate what the motivation is for this
        change, especially if there’s security or privacy benefits to the
        change. If an admin should do something (like test or set a flag or an
        enterprise policy), please explain. Finally, if the change has a
        user-visible benefit (eg. better security or privacy), explain that
        motivation. If there are already publicly visible comms (e.g. blog
        posts), you should link to them here as well.
      </p>
      <p>
        See
        <a
          href="https://docs.google.com/document/d/1SdQ-DKeA5O7I8ju5Cb8zSM5S4NPwUACNJ9qbEhz-AYU"
          target="_blank"
          >go/releasenotes-examples</a
        >
        for examples.
      </p>`,
    help_text: html`
      <p>
        Text in the beta release post, the enterprise release notes, and other
        external sources will be based on this text.
      </p>
      <p>
        Write from a web developer's point of view. Begin with one line
        explaining what the feature does. Add one or two lines explaining how
        this feature helps developers. Write in a matter-of-fact manner and in
        the present tense. (This summary will be visible long after your project
        is finished.) Avoid language such as "a new feature" and "we propose".
      </p>
    `,
    extra_help: html`
      <p>
        Provide a one sentence description followed by one or two lines
        explaining how this feature works and how it helps web developers.
      </p>

      <p>
        Note: This text communicates with more than just the rest of Chromium
        development. It's the part most visible to external readers and is used
        in the beta release announcement, enterprise release notes, and other
        communications.
      </p>

      <ul>
        <li>
          Write from a web developer's point of view, not a browser developer's
        </li>
        <li>
          Do not use markup or markdown because they will not be rendered.
        </li>
        <li>
          Do not use hard or soft returns because they will not be rendered.
        </li>
        <li>
          Avoid phrases such as "a new feature". Every feature on the site was
          new when it was created. You don't need to repeat that information.
        </li>

        <li>
          The first line should be a sentence fragment beginning with a verb.
          (See below.) This is the rare exception to the requirement to always
          use complete sentences.
        </li>

        <li>
          "Conformance with spec" is not adequate. Most if not all features are
          in conformance to spec.
        </li>
      </ul>

      <h4>Example</h4>
      <blockquote>
        Splits the HTTP cache using the top frame origin (and possibly subframe
        origin) to prevent documents from one origin from knowing whether a
        resource from another origin was cached. The HTTP cache is currently one
        per profile, with a single namespace for all resources and subresources
        regardless of origin or renderer process. Splitting the cache on top
        frame origins helps the browser deflect side-channel attacks where one
        site can detect resources in another site's cache.
      </blockquote>
    `,
    enterprise_extra_help: '',
    check: value => {
      if (value && typeof value === 'string' && value.length > 0) {
        if (value.length < 100 || value.length > 5000) {
          return {
            warning:
              'Feature summary should be between 100 and 5000 characters long.',
          };
        }
      }
      return undefined;
    },
  },

  owner: {
    type: 'input',
    name: 'owner_emails', // Field name in database.
    attrs: MULTI_EMAIL_FIELD_ATTRS,
    required: true,
    label: 'Feature owners',
    help_text: html` Comma separated list of full email addresses.`,
  },

  editors: {
    type: 'input',
    name: 'editor_emails', // Field name in database.
    attrs: MULTI_EMAIL_FIELD_ATTRS,
    required: false,
    label: 'Feature editors',
    help_text: html` Comma separated list of full email addresses. These users
    will be allowed to edit this feature, but will not be listed as feature
    owners. User groups are not supported.`,
  },

  cc_recipients: {
    type: 'input',
    name: 'cc_emails', // Field name in database.
    attrs: MULTI_EMAIL_FIELD_ATTRS,
    required: false,
    label: 'CC',
    help_text: html` Comma separated list of full email addresses. These users
    will be notified of any changes to the feature, but do not gain permission
    to edit. User groups must allow posting from
    admin@cr-status.appspotmail.com.`,
  },

  unlisted: {
    type: 'checkbox',
    label: 'Unlisted',
    initial: false,
    help_text: html` Check this box to hide draft features in list views. Anyone
    with a link will be able to view the feature's detail page.`,
  },

  accurate_as_of: {
    type: 'checkbox',
    label: 'Confirm accuracy',
    initial: true,
    help_text: html` Check this box to indicate that feature information is
    accurate as of today. (Selecting this avoids reminder emails for four
    weeks.)`,
  },

  blink_components: {
    type: 'datalist',
    required: true,
    choices: undefined, // this gets replaced in chromedash-form-field via the blink component api
    label: 'Blink component',
    attrs: {placeholder: 'Please select a Blink component'},
    help_text: html` Select the most specific component. If unsure, leave as
    "Blink".`,
  },

  category: {
    type: 'select',
    choices: FEATURE_CATEGORIES,
    initial: FEATURE_CATEGORIES.MISC[0],
    label: 'Category',
    help_text: html` Select the most specific category. If unsure, leave as
    "Miscellaneous".`,
  },

  feature_type: {
    type: 'select',
    disabled: true,
    choices: FEATURE_TYPES,
    label: 'Feature type',
    help_text: html` Feature type chosen at time of creation.
      <br />
      <p style="color: red">
        <strong>Note:</strong> The feature type field cannot be changed. If this
        field needs to be modified, a new feature would need to be created.
      </p>`,
    check: (_value, getFieldValue) => checkFeatureNameAndType(getFieldValue),
  },

  feature_type_radio_group: {
    // form field name matches underlying DB field (sets "feature_type" in DB).
    name: 'feature_type',
    type: 'radios',
    choices: FEATURE_TYPES_WITHOUT_ENTERPRISE,
    label: 'Feature type',
    help_text: html` Select the feature type.
      <br />
      <p style="color: red">
        <strong>Note:</strong> The feature type field cannot be changed. If this
        field needs to be modified, a new feature would need to be created.
      </p>`,
    check: (_value, getFieldValue) => checkFeatureNameAndType(getFieldValue),
  },

  set_stage: {
    name: 'active_stage_id',
    type: 'checkbox',
    label: 'Set to this stage',
    help_text: html` Check this box to move this feature to this stage in the
    process. Leave it unchecked if you are adding draft information or revising
    a previous stage.`,
  },

  search_tags: {
    type: 'input',
    attrs: TEXT_FIELD_ATTRS,
    required: false,
    label: 'Search tags',
    help_text: html` Comma separated keywords used only in search.`,
  },

  impl_status_chrome: {
    type: 'select',
    choices: IMPLEMENTATION_STATUS,
    label: 'Implementation status',
    help_text: html` Select the appropriate Chromium development stage. If you
    select In developer trial, Origin trial, or Enabled by default, be sure to
    set the equivalent Process stage.`,
  },

  set_impl_status: {
    type: 'checkbox',
    name: 'impl_status_chrome',
    label: 'Implementation status',
    help_text: html` Check this box to update the implementation status of this
    feature in Chromium.`,
  },

  bug_url: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Tracking bug URL',
    help_text: html` Tracking bug url (https://bugs.chromium.org/...). This bug
      should have "Type=Feature" set and be world readable. Note: This field
      only accepts one URL.
      <br /><br />
      <a
        target="_blank"
        href="https://bugs.chromium.org/p/chromium/issues/entry"
      >
        Create tracking bug</a
      >`,
  },

  launch_bug_url: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Launch URL',
    help_text: html` Launch URL (https://launch.corp.google.com/...) to track
      internal approvals, if any.
      <br /><br />
      <a target="_blank" href="https://launch.corp.google.com/">
        Create a launch</a
      >.`,
  },
  screenshot_links: {
    type: 'textarea',
    attrs: MULTI_URL_FIELD_ATTRS,
    required: false,
    label: 'Screenshots link(s)',
    help_text: html` Optional: Link to screenshots showcasing this feature (one
    URL per line). These will be shared publicly.`,
    check: async value => {
      const urls = value.split('\n').filter(x => !!x);
      if (!urls.length) {
        return undefined;
      }
      const urlTypes = await Promise.all(
        urls.map(url =>
          fetch(url, {method: 'HEAD'})
            .then(response => response.blob())
            .then(blob => blob.type)
            .catch(() => 'error')
        )
      );
      // All urls must link to an image.
      if (urlTypes.some(type => !type.startsWith('image'))) {
        return {
          error:
            'One or more urls are not actual images. Use a valid link to an actual image.',
        };
      }
      return undefined;
    },
  },

  first_enterprise_notification_milestone: {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'First notification milestone',
    help_text: html` Optional: Unless you're sure you need to use this, leave it
      blank.
      <br /><br />
      If you leave this blank, we will automatically find the right milestone.
      <br /><br />
      If you're not ready to communicate this feature to enterprises yet, what
      is the earliest milestone that you expect to be ready to communicate it?
      You can change this later. In general, you should provide enterprises
      notice at least 3 milestones before making an impactful change.`,
    check: (value, _, initialValue) =>
      checkFirstEnterpriseNotice(value, initialValue),
  },

  motivation: {
    type: 'textarea',
    required: false,
    label: 'Motivation',
    help_text: html` Explain why the web needs this change. It may be useful to
      describe what web developers are forced to do without it. When possible,
      add links to your explainer (under
      <a href="#id_explainer_links">Explainer link(s)</a>) backing up your
      claims. <br /><br />
      This text is sometimes included with the summary in the beta post,
      enterprise release notes and other external documents. Write in a
      matter-of-fact manner and in the present tense.
      <br /><br />
      <a
        target="_blank"
        href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#motivation-example"
      >
        Example</a
      >`,
  },

  deprecation_motivation: {
    // form field name matches underlying DB field (sets "motivation" field in DB).
    name: 'motivation',
    type: 'textarea',
    required: false,
    label: 'Motivation',
    help_text: html` Deprecations and removals must have strong reasons, backed
      up by measurements. There must be clear and actionable paths forward for
      developers.
      <br /><br />
      This text is sometimes included with the summary in the beta post,
      enterprise release notes and other external documents. Write in a
      matter-of-fact manner and in the present tense.
      <br /><br />
      Please see
      <a
        target="_blank"
        href="https://docs.google.com/a/chromium.org/document/d/1LdqUfUILyzM5WEcOgeAWGupQILKrZHidEXrUxevyi_Y/edit?usp=sharing"
      >
        Removal guidelines</a
      >.`,
  },

  initial_public_proposal_url: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Initial public proposal URL',
    help_text: html` Link to the first public proposal to create this feature.`,
    extra_help: html` If there isn't another obvious place to propose your
      feature, create a
      <a
        target="_blank"
        href="https://github.com/WICG/proposals#what-does-a-proposal-look-like"
      >
        WICG proposal</a
      >. You can use your proposal document to help you socialize the problem
      with other vendors and developers.`,
  },

  explainer_links: {
    type: 'textarea',
    attrs: MULTI_URL_FIELD_ATTRS,
    required: false,
    label: 'Explainer link(s)',
    help_text: html` Link to explainer(s) (one URL per line). You should have at
    least an explainer in hand and have shared it on a public forum before
    sending an Intent to Prototype in order to enable discussion with other
    browser vendors, standards bodies, or other interested parties.`,
    extra_help: html` <p>
        See the TAG guide to writing
        <a target="_blank" href="https://tag.w3.org/explainers/">Explainers</a>
        for several examples of good explainers and tips for effective
        explainers.
      </p>
      <p>
        If you've already made an initial public proposal (see above), post your
        explainer to that thread. Otherwise, make an initial proposal based on
        your explainer.
      </p>
      <p>
        Once a second organization is interested in the WICG proposal, you can
        move the explainer into the WICG. The
        <a href="https://wicg.github.io/admin/charter.html#chairs"
          >WICG co-chairs</a
        >
        can help you.
      </p>
      <p>
        If you want help, ask for a
        <a
          target="_blank"
          href="https://sites.google.com/a/chromium.org/dev/blink/spec-mentors"
          >specification mentor</a
        >.
      </p>`,
  },

  spec_link: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Spec link',
    help_text: html` Link to the spec, if and when available. When implementing
    a spec update, please link to a heading in a published spec rather than a
    pull request when possible.`,
  },

  comments: {
    type: 'textarea',
    name: 'feature_notes', // Field name in database.
    attrs: {rows: 4},
    required: false,
    label: 'Comments',
    help_text: html` Additional comments, caveats, info...`,
  },

  standard_maturity: {
    type: 'select',
    choices: STANDARD_MATURITY_CHOICES,
    initial: STANDARD_MATURITY_CHOICES.PROPOSAL_STD[0],
    label: 'Standard maturity',
    help_text: html` How far along is the standard that this feature implements?`,
  },

  api_spec: {
    type: 'checkbox',
    initial: false,
    label: 'API spec',
    help_text: html` The spec document has details in a specification language
    such as Web IDL, or there is an existing MDN page.`,
  },

  spec_mentors: {
    type: 'input',
    name: 'spec_mentor_emails',
    attrs: MULTI_EMAIL_FIELD_ATTRS,
    required: false,
    label: 'Spec mentors',
    help_text: html` Experienced
      <a target="_blank" href="https://www.chromium.org/blink/spec-mentors">
        spec mentors</a
      >
      are available to help you improve your feature spec.`,
  },

  intent_to_implement_url: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Intent to Prototype link',
    help_text: html` After you have started the "Intent to Prototype" discussion
    thread, link to it here.`,
  },

  doc_links: {
    type: 'textarea',
    attrs: MULTI_URL_FIELD_ATTRS,
    required: false,
    label: 'Doc link(s)',
    help_text: html` Links to design doc(s) (one URL per line), if and when
    available. [This is not required to send out an Intent to Prototype. Please
    update the intent thread with the design doc when ready]. An explainer
    and/or design doc is sufficient to start this process. [Note: Please include
    links and data, where possible, to support any claims.`,
  },

  measurement: {
    type: 'textarea',
    attrs: {rows: 4},
    required: false,
    label: 'Measurement',
    help_text: html` It's important to measure the adoption and success of
    web-exposed features. Note here what measurements you have added to track
    the success of this feature, such as a link to the UseCounter(s) you have
    set up.`,
  },

  availability_expectation: {
    type: 'textarea',
    attrs: {rows: 4},
    required: false,
    label: 'Availability expectation',
    help_text: html` What is your availability expectation for this feature?
    Examples:`,
    extra_help: html`
      <ul>
        <li>
          Feature is available on Web Platform mainline within 12 months of
          launch in Chrome.
        </li>

        <li>
          Feature is available only in Chromium browsers for the foreseeable
          future.
        </li>
      </ul>
    `,
  },

  adoption_expectation: {
    type: 'textarea',
    attrs: {rows: 4},
    required: false,
    label: 'Adoption expectation',
    help_text: html` What is your adoption expectation for this feature?
    Examples:`,
    extra_help: html`
      <ul>
        <li>
          Feature is considered a best practice for some use case within 12
          months of reaching Web Platform baseline.
        </li>

        <li>
          Feature is used by specific partner(s) to provide functionality within
          12 months of launch in Chrome.
        </li>

        <li>
          At least 3 major abstractions replace their use of an existing feature
          with this feature within 24 months of reaching mainline.
        </li>
      </ul>
    `,
  },

  adoption_plan: {
    type: 'textarea',
    attrs: {rows: 4},
    required: false,
    label: 'Adoption plan',
    help_text: html` What is the plan to achieve the stated expectations? Please
    provide a plan that covers availability and adoption for the feature.`,
  },

  security_review_status: {
    type: 'select',
    choices: REVIEW_STATUS_CHOICES,
    initial: REVIEW_STATUS_CHOICES.REVIEW_PENDING[0],
    label: 'Security review status',
    help_text: html` Status of the security review.`,
  },

  privacy_review_status: {
    type: 'select',
    choices: REVIEW_STATUS_CHOICES,
    initial: REVIEW_STATUS_CHOICES.REVIEW_PENDING[0],
    label: 'Privacy review status',
    help_text: html`Status of the privacy review.`,
  },

  tag_review: {
    type: 'textarea',
    attrs: {rows: 2},
    required: false,
    label: 'TAG Specification Review',
    help_text: html` Link(s) to TAG specification review(s), or explanation why
    this is not needed.`,
    extra_help: html` <p>
        The
        <a target="_blank" href="https://www.w3.org/2001/tag/"
          >W3C Technical Architecture Group</a
        >
        (TAG) is a special working group of the W3C that consists of a few
        appointed and elected members, all of whom are experienced members of
        the web standards community. The Blink launch process has a formal
        requirement for requesting a
        <a target="_blank" href="https://github.com/w3ctag/design-reviews"
          >TAG specification review</a
        >
        for all features. The review happens publicly on a GitHub issue.
      </p>
      <p>
        You will likely have asked for an "<a
          target="_blank"
          href="https://github.com/w3ctag/design-reviews/issues/new?template=005-early-design-review.md"
          >Early Design Review</a
        >" earlier in the process to get the TAG familiar with your feature.
        This isn't that.
      </p>
      <p>
        It's recommended that you file a TAG
        <a
          target="_blank"
          href="https://github.com/w3ctag/design-reviews/issues/new?template=010-specification-review.md"
          >Specification Review</a
        >
        as soon as your specification is written, and at least a month ahead of
        sending an Intent to Ship. There may be some work involved in preparing
        your feature for review (see the
        <a
          target="_blank"
          href="https://github.com/w3ctag/design-reviews/blob/main/.github/ISSUE_TEMPLATE/010-specification-review.md"
          >submission template fields</a
        >).
      </p>
      <p>
        A large number of Intents to Ship are delayed because a TAG
        specification review was only recently filed and engagement from the TAG
        can take multiple weeks to multiple months. Note that the API owners can
        approve shipping even if the TAG hasn't replied to your review request,
        as long as you've made a reasonable effort to obtain their review with
        enough time for them to give feedback.
      </p>`,
  },

  tag_review_status: {
    type: 'select',
    choices: REVIEW_STATUS_CHOICES,
    initial: REVIEW_STATUS_CHOICES.REVIEW_PENDING[0],
    label: 'TAG Specification Review Status',
    help_text: html`Status of the TAG specification review.`,
  },

  intent_to_ship_url: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Intent to Ship link',
    help_text: html`After you have started the "Intent to Ship" discussion
    thread, link to it here.`,
  },

  announcement_url: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Ready for Developer Testing link',
    help_text: html`After you have started the "Ready for Developer Testing"
    discussion thread, link to it here.`,
  },

  intent_to_experiment_url: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Intent to Experiment link',
    help_text: html`After you have started the "Intent to Experiment" discussion
    thread, link to it here.`,
  },

  intent_to_extend_experiment_url: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Intent to Extend Experiment link',
    help_text: html`If this feature has an "Intent to Extend Experiment"
    discussion thread, link to it here.`,
  },

  ot_extension__intent_to_extend_experiment_url: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: true,
    label: 'Intent to Extend Experiment link',
    help_text: html` Link to the approved Intent to Extend Experiment, as per
      <a
        target="_blank"
        href="https://www.chromium.org/blink/origin-trials/running-an-origin-trial/#what-is-the-process-to-extend-an-origin-trial"
      >
        the trial extension process </a
      >.`,
  },

  r4dt_url: {
    // form field name matches underlying DB field (sets "intent_to_experiment_url" field in DB).
    name: 'intent_to_experiment_url',
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Request for Deprecation Trial link',
    help_text: html`After you have started the "Request for Deprecation Trial"
    discussion thread, link to it here.`,
  },

  interop_compat_risks: {
    type: 'textarea',
    required: false,
    label: 'Interoperability and Compatibility Risks',
    help_text: html` Describe the degree of
      <a
        target="_blank"
        href="https://www.chromium.org/blink/guidelines/web-platform-changes-guidelines#finding-balance"
      >
        interoperability risk</a
      >. For a new feature, the main risk is that it fails to become an
      interoperable part of the web platform if other browsers do not implement
      it. For a removal, please review our
      <a
        target="_blank"
        href="https://docs.google.com/document/d/1RC-pBBvsazYfCNNUSkPqAVpSpNJ96U8trhNkfV0v9fk/edit"
      >
        principles of web compatibility</a
      >.<br />
      <br />
      Please include citation links below where possible. Examples include
      resolutions from relevant standards bodies (e.g. W3C working group),
      tracking bugs, or links to online conversations.
      <a
        target="_blank"
        href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#interoperability-and-compatibility-risks-example"
      >
        Example</a
      >.`,
  },

  safari_views: {
    type: 'select',
    choices: VENDOR_VIEWS_COMMON,
    initial: VENDOR_VIEWS_COMMON.NO_PUBLIC_SIGNALS[0],
    label: 'Safari views',
    help_text: html` See
      <a target="_blank" href="https://bit.ly/blink-signals">
        https://bit.ly/blink-signals</a
      >`,
  },

  safari_views_link: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: '',
    displayLabel: 'Safari views link',
    help_text: html`Citation link.`,
  },

  safari_views_notes: {
    type: 'textarea',
    attrs: {rows: 2, placeholder: 'Notes'},
    required: false,
    label: '',
    displayLabel: 'Safari views notes',
    help_text: '',
  },

  ff_views: {
    type: 'select',
    choices: VENDOR_VIEWS_GECKO,
    initial: VENDOR_VIEWS_GECKO.NO_PUBLIC_SIGNALS[0],
    label: 'Firefox views',
    help_text: html` See
      <a target="_blank" href="https://bit.ly/blink-signals">
        https://bit.ly/blink-signals</a
      >`,
  },

  ff_views_link: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: '',
    displayLabel: 'Firefox views link',
    help_text: html` Citation link.`,
  },

  ff_views_notes: {
    type: 'textarea',
    attrs: {rows: 2, placeholder: 'Notes'},
    required: false,
    label: '',
    displayLabel: 'Firefox views notes',
    help_text: '',
  },

  web_dev_views: {
    type: 'select',
    choices: WEB_DEV_VIEWS,
    initial: WEB_DEV_VIEWS.DEV_NO_SIGNALS[0],
    label: 'Web / Framework developer views',
    help_text: html` If unsure, default to "No signals". See
      <a target="_blank" href="https://goo.gle/developer-signals">
        https://goo.gle/developer-signals</a
      >`,
  },

  web_dev_views_link: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: '',
    displayLabel: 'Web / Framework developer views link',
    help_text: html` Citation link.`,
  },

  web_dev_views_notes: {
    type: 'textarea',
    attrs: {rows: 2, placeholder: 'Notes'},
    required: false,
    label: '',
    displayLabel: 'Web / Framework developer views notes',
    help_text: html` Reference known representative examples of opinions, both
    positive and negative.`,
  },

  other_views_notes: {
    type: 'textarea',
    attrs: {rows: 4, placeholder: 'Notes'},
    required: false,
    label: 'Other views',
    help_text: html` For example, other browsers.`,
  },

  ergonomics_risks: {
    type: 'textarea',
    required: false,
    label: 'Ergonomics Risks',
    help_text: html` Are there any other platform APIs this feature will
    frequently be used in tandem with? Could the default usage of this API make
    it hard for Chrome to maintain good performance (i.e. synchronous return,
    must run on a certain thread, guaranteed return timing)?`,
  },

  activation_risks: {
    type: 'textarea',
    required: false,
    label: 'Activation Risks',
    help_text: html` Will it be challenging for developers to take advantage of
    this feature immediately, as-is? Would this feature benefit from having
    polyfills, significant documentation and outreach, and/or libraries built on
    top of it to make it easier to use?`,
  },

  security_risks: {
    type: 'textarea',
    required: false,
    label: 'Security Risks',
    help_text: html` List any security considerations that were taken into
    account when designing this feature.`,
  },

  webview_risks: {
    type: 'textarea',
    required: false,
    label: 'WebView application risks',
    help_text: html` Does this feature deprecate or change behavior of existing
      APIs, such that it has potentially high risk for Android WebView-based
      applications? (See
      <a
        target="_blank"
        href="https://new.chromium.org/developers/webview-changes/"
      >
        here</a
      >
      for a definition of "potentially high risk", information on why changes to
      this platform carry higher risk, and general rules of thumb for which
      changes have higher or lower risk) If so:
      <ul>
        <li>
          Please use a base::Feature killswitch (<a
            target="_blank"
            href="https://source.chromium.org/chromium/chromium/src/+/main:third_party/blink/public/common/features.h"
            >examples here</a
          >) that can be flipped off in case of compat issues
        </li>
        <li>Consider contacting android-webview-dev@chromium.org for advice</li>
        <li>
          If you are not sure, just put "not sure" as the answer and the API
          owners can help during the review of your Intent to Ship
        </li>
      </ul>`,
  },

  experiment_goals: {
    type: 'textarea',
    required: false,
    label: 'Experiment Goals',
    help_text: html` Which pieces of the API surface are you looking to gain
      insight on? What metrics/measurement/feedback will you be using to
      validate designs? Double check that your experiment makes sense given that
      a large developer (e.g. a Google product or Facebook) likely can't use it
      in production due to the limits enforced by origin trials.
      <br /><br />
      If you send an Intent to Extend Origin Trial, highlight areas for
      experimentation. They should not be an exact copy of the goals from the
      first Intent to Experiment.`,
  },

  experiment_timeline: {
    type: 'textarea',
    attrs: {rows: 2, placeholder: 'This field is deprecated', disabled: true},
    required: false,
    label: 'Experiment Timeline',
    help_text: html` When does the experiment start and expire? Deprecated:
    Please use the numeric fields above instead.`,
  },

  ot_milestone_desktop_start: {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'OT desktop start',
    help_text: html` First desktop milestone that will support an origin trial
    of this feature.`,
    check: (_value, getFieldValue) =>
      checkMilestoneRanges(
        [OT_MILESTONE_DESKTOP_RANGE, OT_ALL_SHIPPED_MILESTONE_DESKTOP_RANGE],
        getFieldValue
      ),
  },

  ot_milestone_desktop_end: {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'OT desktop end',
    help_text: html` Last desktop milestone that will support an origin trial of
    this feature.`,
    check: (_value, getFieldValue) =>
      checkMilestoneRanges([OT_MILESTONE_DESKTOP_RANGE], getFieldValue),
  },

  ot_milestone_android_start: {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'OT Android start',
    help_text: html` First android milestone that will support an origin trial
    of this feature.`,
    check: (_value, getFieldValue) =>
      checkMilestoneRanges(
        [OT_MILESTONE_ANDROID_RANGE, OT_ALL_SHIPPED_MILESTONE_ANDROID_RANGE],
        getFieldValue
      ),
  },

  ot_milestone_android_end: {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'OT Android end',
    help_text: html` Last android milestone that will support an origin trial of
    this feature.`,
    check: (_value, getFieldValue) =>
      checkMilestoneRanges([OT_MILESTONE_ANDROID_RANGE], getFieldValue),
  },

  ot_milestone_webview_start: {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'OT WebView start',
    help_text: html` First WebView milestone that will support an origin trial
    of this feature.`,
    check: (_value, getFieldValue) =>
      checkMilestoneRanges(
        [OT_MILESTONE_WEBVIEW_RANGE, OT_ALL_SHIPPED_MILESTONE_WEBVIEW_RANGE],
        getFieldValue
      ),
  },

  ot_milestone_webview_end: {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'OT WebView end',
    help_text: html` Last WebView milestone that will support an origin trial of
    this feature.`,
    check: (_value, getFieldValue) =>
      checkMilestoneRanges([OT_MILESTONE_WEBVIEW_RANGE], getFieldValue),
  },

  experiment_risks: {
    type: 'textarea',
    required: false,
    label: 'Experiment Risks',
    help_text: html` When this experiment comes to an end are there any risks to
    the sites that were using it, for example losing access to important storage
    due to an experimental storage API?`,
  },

  experiment_extension_reason: {
    type: 'textarea',
    required: false,
    label: 'Experiment Extension Reason',
    help_text: html` If this is a repeated or extended experiment, explain why
    it's being repeated or extended. Also, fill in discussion link fields below.`,
  },

  extension_desktop_last: {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: true,
    label: 'Trial extension end milestone',
    help_text: html` The last desktop milestone in which the trial will be
    available after extension.`,
  },

  extension_android_last: {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'Trial extension Android end',
    help_text: html` The last android milestone in which the trial will be
    available after extension.`,
  },

  extension_webview_last: {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'Trial extension WebView end',
    help_text: html` The last WebView milestone in which the trial will be
    available after extension.`,
  },

  ot_extension__milestone_desktop_last: {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: true,
    label: 'Trial extension end milestone',
    help_text: html` The last milestone in which the trial will be available
    after extension.`,
    check: _value => checkExtensionMilestoneIsValid(_value),
  },

  ongoing_constraints: {
    type: 'textarea',
    required: false,
    label: 'Ongoing Constraints',
    help_text: html` Do you anticipate adding any ongoing technical constraints
    to the codebase while implementing this feature? We prefer to avoid features
    that require or assume a specific architecture. For most features, the
    answer is "None."`,
  },

  origin_trial_feedback_url: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Origin trial feedback summary',
    help_text: html` If your feature was available as an origin trial, link to a
    summary of usage and developer feedback. If not, leave this empty. DO NOT
    USE FEEDBACK VERBATIM without prior consultation with the Origin Trials
    team.`,
  },

  ot_chromium_trial_name: {
    type: 'input',
    attrs: TEXT_FIELD_ATTRS,
    required: true,
    label: 'Chromium trial name',
    help_text: html` Name for the trial, given as the value of the property
      "origin_trial_feature_name" as specified in
      <a
        target="_blank"
        href="https://chromium.googlesource.com/chromium/src/+/main/third_party/blink/renderer/platform/runtime_enabled_features.json5"
        >runtime_enabled_features.json5</a
      >.
      <br />
      <p style="color: red">
        <strong>Note:</strong> This name should be unique and should not be used
        by any previous origin trials!
      </p>`,
  },

  ot_documentation_url: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: true,
    label: 'Documentation link',
    help_text: html` Link to more information to help developers use the trial's
    feature (e.g. blog post, Github explainer, etc.).`,
  },

  ot_emails: {
    type: 'input',
    attrs: MULTI_EMAIL_FIELD_ATTRS,
    required: false,
    label: 'Origin trial contacts',
    help_text: html` List any other individuals or groups to include on the
      contact list (e.g. for reminders on trial milestones).
      <p>
        <strong>
          Please prefer using "@google.com" domain email addresses for any
          contacts that have one.
        </strong>
      </p>`,
  },

  ot_has_third_party_support: {
    type: 'checkbox',
    initial: false,
    label: 'Origin trial supports third party origins',
    help_text: html` Whether this trial supports third party origins. See
      <a href="https://web.dev/third-party-origin-trials/">this article</a>
      for more information. The feature should have
      "origin_trial_allows_third_party" set to "true" in
      <a
        target="_blank"
        href="https://chromium.googlesource.com/chromium/src/+/main/third_party/blink/renderer/platform/runtime_enabled_features.json5"
        >runtime_enabled_features.json5</a
      >`,
  },

  ot_is_critical_trial: {
    type: 'checkbox',
    initial: false,
    label: 'Critical origin trial',
    help_text: html` See
      <a href="https://goto.google.com/running-an-origin-trial"
        >go/running-an-origin-trial</a
      >
      for criteria and additional process requirements. The feature name must be
      added to the "kHasExpiryGracePeriod" array in
      <a
        target="_blank"
        href="https://source.chromium.org/chromium/chromium/src/+/main:third_party/blink/common/origin_trials/manual_completion_origin_trial_features.cc"
        >manual_completion_origin_trial_features.cc</a
      >`,
  },

  ot_is_deprecation_trial: {
    type: 'checkbox',
    initial: false,
    label: 'Deprecation trial',
    help_text: html` Is this a deprecation trial? See the
      <a
        href="https://www.chromium.org/blink/launching-features/#deprecation-trial"
        >deprecation trial section</a
      >
      for more information.`,
  },

  ot_request_note: {
    type: 'textarea',
    required: false,
    label: 'Anything else?',
    help_text: html`<p>
      Let us know if you have any further questions or comments.
    </p>`,
  },

  ot_webfeature_use_counter: {
    type: 'input',
    attrs: {
      ...TEXT_FIELD_ATTRS,
      placeholder: 'e.g. "kWebFeature"',
      pattern: String.raw`k\S*`,
    },
    label: 'WebFeature UseCounter name',
    help_text: html` For measuring usage, this must be a single named value from
      the WebFeature enum, e.g. kWorkerStart. The use counter must be landed in
      <a
        target="_blank"
        href="https://source.chromium.org/chromium/chromium/src/+/main:third_party/blink/public/mojom/use_counter/metrics/web_feature.mojom"
        >web_feature.mojom</a
      >. Not required for deprecation trials.`,
  },

  ot_require_approvals: {
    type: 'checkbox',
    initial: false,
    label: 'Trial participation requires approval',
    help_text: html` <p>
      Will this trial require registrants to receive approval before
      participating? Please reach out to origin-trials-support@google.com
      beforehand to discuss options here.
    </p>`,
  },

  ot_approval_buganizer_component: {
    type: 'input',
    attrs: {type: 'number'},
    required: true,
    label: 'Approvals Buganizer component ID',
    help_text: html` Buganizer component ID used for approvals requests.`,
  },

  ot_approval_group_email: {
    type: 'input',
    required: true,
    attrs: {
      ...TEXT_FIELD_ATTRS,
      pattern: GOOGLE_EMAIL_ADDRESS_REGEX,
      placeholder: 'ex. "approval-requests@google.com"',
    },
    label: 'Registration request notifications group',
    help_text: html` <p>
      Google group email to be used for new registration request notifications.
      Please supply a '@google.com' domain email address only.
    </p>`,
  },

  ot_approval_criteria_url: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: true,
    label: 'Approval criteria link',
    help_text: html` <p>
      Link to public documentation describing the requirements to be approved
      for trial participation.
    </p>`,
  },

  ot_creation__intent_to_experiment_url: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: true,
    label: 'Intent to Experiment link',
    help_text: html`Your "Intent to Experiment" discussion thread. The necessary
    LGTMs should already have been received.`,
  },

  ot_creation__milestone_desktop_first: {
    name: 'ot_milestone_desktop_start',
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: true,
    label: 'Trial milestone start',
    help_text: html` First milestone that will support an origin trial of this
    feature.`,
    check: (_value, getFieldValue) =>
      checkMilestoneRanges(
        [OT_MILESTONE_DESKTOP_RANGE, OT_ALL_SHIPPED_MILESTONE_DESKTOP_RANGE],
        getFieldValue
      ),
  },

  ot_creation__milestone_desktop_last: {
    name: 'ot_milestone_desktop_end',
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: true,
    label: 'Trial milestone end',
    help_text: html` Last milestone that will support an origin trial of this
    feature.`,
    check: (_value, getFieldValue) =>
      checkMilestoneRanges([OT_MILESTONE_DESKTOP_RANGE], getFieldValue),
  },

  anticipated_spec_changes: {
    type: 'textarea',
    attrs: {rows: 4},
    required: false,
    label: 'Anticipated spec changes',
    help_text: html` Open questions about a feature may be a source of future
    web compat or interop issues. Please list open issues (e.g. links to known
    github issues in the repo for the feature specification) whose resolution
    may introduce web compat/interop risk (e.g., changing the naming or
    structure of the API in a non-backward-compatible way).`,
  },

  finch_url: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'Finch experiment',
    help_text: html` If your feature will roll out gradually via a
      <a target="_blank" href="http://go/finch">Finch experiment</a>, link to it
      here.`,
  },

  i2e_lgtms: {
    type: 'input',
    attrs: {
      ...MULTI_EMAIL_FIELD_ATTRS,
      placeholder: 'This field is deprecated',
      disabled: true,
    },
    required: false,
    label: 'Intent to Experiment LGTM by',
    help_text: html` Full email address of API owner who LGTM'd the Intent to
    Experiment email thread.`,
  },

  i2s_lgtms: {
    type: 'input',
    attrs: {
      ...MULTI_EMAIL_FIELD_ATTRS,
      placeholder: 'This field is deprecated',
      disabled: true,
    },
    required: false,
    label: 'Intent to Ship LGTMs by',
    help_text: html`
      Comma separated list of email addresses of API owners who LGTM'd the
      Intent to Ship email thread.
    `,
  },

  r4dt_lgtms: {
    // form field name matches underlying DB field (sets "i2e_lgtms" field in DB).
    name: 'i2e_lgtms',
    type: 'input',
    attrs: {
      ...MULTI_EMAIL_FIELD_ATTRS,
      placeholder: 'This field is deprecated',
      disabled: true,
    },
    required: false,
    label: 'Request for Deprecation Trial LGTM by',
    help_text: html` Full email addresses of API owners who LGTM'd the Request
    for Deprecation Trial email thread.`,
  },

  debuggability: {
    type: 'textarea',
    required: false,
    label: 'Debuggability',
    help_text: html` Description of the DevTools debugging support for your
      feature. Please follow the
      <a target="_blank" href="https://goo.gle/devtools-checklist">
        DevTools support checklist</a
      >
      for guidance.`,
  },

  all_platforms: {
    type: 'checkbox',
    initial: false,
    label: 'Supported on all platforms?',
    help_text: html` Will this feature be supported on all six Blink platforms
    (Windows, Mac, Linux, ChromeOS, Android, and Android WebView)?`,
  },

  all_platforms_descr: {
    type: 'textarea',
    attrs: {rows: 2},
    required: false,
    label: 'Platform Support Explanation',
    help_text: html` Explain why this feature is, or is not, supported on all
    platforms.`,
  },

  wpt: {
    type: 'checkbox',
    initial: false,
    label: 'Web Platform Tests',
    help_text: html` Is this feature fully tested in Web Platform Tests?`,
  },

  wpt_descr: {
    type: 'textarea',
    required: false,
    label: 'Web Platform Tests Description',
    help_text: html` Please link to the
      <a target="_blank" href="https://wpt.fyi/results">results on wpt.fyi</a>.
      If any part of the feature is not tested by web-platform-tests, please
      include links to issues, e.g. a web-platform-tests issue with the "infra"
      label explaining why a certain thing cannot be tested (<a
        target="_blank"
        href="https://github.com/w3c/web-platform-tests/issues/3867"
        >example</a
      >), a spec issue for some change that would make it possible to test. (<a
        target="_blank"
        href="https://github.com/whatwg/fullscreen/issues/70"
        >example</a
      >), or a Chromium issue to upstream some existing tests (<a
        target="_blank"
        href="https://bugs.chromium.org/p/chromium/issues/detail?id=695486"
        >example</a
      >).`,
  },

  sample_links: {
    type: 'textarea',
    attrs: MULTI_URL_FIELD_ATTRS,
    required: false,
    label: 'Demo and sample links',
    help_text: html` Links to demos and samples (one URL per line).`,
  },

  non_oss_deps: {
    type: 'textarea',
    required: false,
    label: 'Non-OSS dependencies',
    help_text: html` Does the feature depend on any code or APIs outside the
    Chromium open source repository and its open-source dependencies to
    function? (e.g. server-side APIs, operating system APIs tailored to this
    feature or closed-source code bundles) Yes or no. If yes, explain why this
    is necessary.`,
  },

  devrel: {
    type: 'input',
    name: 'devrel_emails', // Field name in database.
    attrs: MULTI_EMAIL_FIELD_ATTRS,
    required: false,
    label: 'Developer relations emails',
    help_text: html` Comma separated list of full email addresses.`,
  },

  shipped_milestone: {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'Chrome for desktop',
    help_text: SHIPPED_HELP_TXT,
    check: (_value, getFieldValue) =>
      checkMilestoneRanges(
        [
          ALL_OT_SHIPPED_MILESTONE_DESKTOP_RANGE,
          ALL_DT_SHIPPED_MILESTONE_DESKTOP_RANGE,
        ],
        getFieldValue
      ),
  },

  shipped_android_milestone: {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'Chrome for Android',
    help_text: SHIPPED_HELP_TXT,
    check: (_value, getFieldValue) =>
      checkMilestoneRanges(
        [
          ALL_OT_SHIPPED_MILESTONE_ANDROID_RANGE,
          ALL_DT_SHIPPED_MILESTONE_ANDROID_RANGE,
        ],
        getFieldValue
      ),
  },

  shipped_ios_milestone: {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'Chrome for iOS (RARE)',
    help_text: SHIPPED_HELP_TXT,
    check: (_value, getFieldValue) =>
      checkMilestoneRanges([ALL_DT_SHIPPED_MILESTONE_IOS_RANGE], getFieldValue),
  },

  shipped_webview_milestone: {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'Android Webview',
    help_text: SHIPPED_WEBVIEW_HELP_TXT,
    check: (_value, getFieldValue) =>
      checkMilestoneRanges(
        [ALL_OT_SHIPPED_MILESTONE_WEBVIEW_RANGE],
        getFieldValue
      ),
  },

  requires_embedder_support: {
    type: 'checkbox',
    initial: false,
    label: 'Requires Embedder Support',
    help_text: html` Will this feature require support in //chrome? That
      includes any code in //chrome, even if that is for functionality on top of
      the spec. Other //content embedders will need to be aware of that
      functionality. Please add a row to this
      <a
        target="_blank"
        href="https://docs.google.com/spreadsheets/d/1QV4SW4JBG3IyLzaonohUhim7nzncwK4ioop2cgUYevw/edit#gid=0"
      >
        tracking spreadsheet</a
      >.`,
  },

  devtrial_instructions: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: false,
    label: 'DevTrial instructions',
    help_text: html` Link to a HOWTO or FAQ describing how developers can get
      started using this feature in a DevTrial.
      <br /><br />
      <a
        target="_blank"
        href="https://github.com/samuelgoto/WebID/blob/master/HOWTO.md"
      >
        Example 1</a
      >.
      <a
        target="_blank"
        href="https://github.com/WICG/idle-detection/blob/main/HOWTO.md"
      >
        Example 2</a
      >.`,
  },

  dt_milestone_desktop_start: {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'DevTrial on desktop',
    help_text: html` First milestone that allows web developers to try this
    feature on desktop platforms by setting a flag. When flags are enabled by
    default in preparation for shipping or removal, please use the fields in the
    ship stage.`,
    check: (_value, getFieldValue) =>
      checkMilestoneRanges(
        [DT_ALL_SHIPPED_MILESTONE_DESKTOP_RANGE],
        getFieldValue
      ),
  },

  dt_milestone_android_start: {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'DevTrial on Android',
    help_text: html` First milestone that allows web developers to try this
    feature on Android by setting a flag. When flags are enabled by default in
    preparation for shipping or removal, please use the fields in the ship
    stage.`,
    check: (_value, getFieldValue) =>
      checkMilestoneRanges(
        [DT_ALL_SHIPPED_MILESTONE_ANDROID_RANGE],
        getFieldValue
      ),
  },

  dt_milestone_ios_start: {
    type: 'input',
    attrs: MILESTONE_NUMBER_FIELD_ATTRS,
    required: false,
    label: 'DevTrial on iOS (RARE)',
    help_text: html` First milestone that allows web developers to try this
    feature on iOS by setting a flag. When flags are enabled by default in
    preparation for shipping or removal, please use the fields in the ship
    stage.`,
    check: (_value, getFieldValue) =>
      checkMilestoneRanges([DT_ALL_SHIPPED_MILESTONE_IOS_RANGE], getFieldValue),
  },

  flag_name: {
    type: 'input',
    attrs: TEXT_FIELD_ATTRS,
    required: false,
    label: 'Flag name',
    help_text: html` Name of the flag on chrome://flags that allows a web
      developer to enable this feature in their own browser to try it out. E.g.,
      "storage-buckets". These are defined in
      <a
        target="_blank"
        href="https://source.chromium.org/chromium/chromium/src/+/main:chrome/browser/about_flags.cc"
        >about_flags.cc</a
      >.`,
  },

  finch_name: {
    type: 'input',
    attrs: TEXT_FIELD_ATTRS,
    required: false,
    label: 'Finch feature name',
    help_text: html` String name of the <code>base::Feature</code> defined via
      the <code>BASE_FEATURE</code> macro in your feature implementation code.
      E.g., "StorageBuckets". These names are used in
      <a
        target="_blank"
        href="https://chromium.googlesource.com/chromium/src/+/main/third_party/blink/renderer/platform/runtime_enabled_features.json5"
        >runtime_enabled_features.json5</a
      >
      and finch GCL files`,
  },

  non_finch_justification: {
    type: 'textarea',
    required: false,
    label: 'Non-finch justification',
    help_text: html` The
      <a
        target="_blank"
        href="https://chromium.googlesource.com/chromium/src/+/main/docs/flag_guarding_guidelines.md"
        >Flag Guarding Guidelines</a
      >
      require new features to have a finch flag. If your feature does not have a
      finch flag, explain why.`,
  },

  prefixed: {
    type: 'checkbox',
    label: 'Prefixed?',
    initial: false,
    help_text: '',
  },

  display_name: {
    type: 'input',
    attrs: TEXT_FIELD_ATTRS,
    required: false,
    label: 'Stage display name',
    help_text: html` <p>
      Optional. Stage name to display on the feature detail page.
    </p>`,
    extra_help: html` <p>
        This name is only used for displaying stages on this site. Use this to
        differentiate stages of the same type.
      </p>
      <h4>Examples</h4>
      <ul>
        <li>Extended deprecation trial</li>
        <li>Second origin trial run</li>
        <li>Delayed ship for Android</li>
      </ul>`,
  },

  ot_display_name: {
    type: 'input',
    attrs: TEXT_FIELD_ATTRS,
    required: true,
    label: 'Origin trial display name',
    help_text: html` <p>
      Name shown in the
      <a href="https://developer.chrome.com/origintrials/" target="_blank">
        Origin Trials Console
      </a>
      and included in reminder emails.
    </p>`,
  },

  ot_description: {
    type: 'textarea',
    required: true,
    label: 'Trial description',
    help_text: html` <p>
      A brief description of the feature to interest web developers in joining
      the trial (1-2 sentences). Shown as the trial description in the
      <a href="https://developer.chrome.com/origintrials/" target="_blank">
        Origin Trials Console </a
      >.
    </p>`,
  },

  ot_owner_email: {
    type: 'input',
    required: true,
    attrs: {...TEXT_FIELD_ATTRS, pattern: GOOGLE_EMAIL_ADDRESS_REGEX},
    label: 'Trial owner email',
    help_text: html` <p>
      The primary contact for this origin trial. Please supply a '@google.com'
      domain email address only.
    </p>`,
  },

  ot_feedback_submission_url: {
    type: 'input',
    attrs: URL_FIELD_ATTRS,
    required: true,
    label: 'Feature feedback link',
    help_text: html` Link for developers to file feedback on the feature (e.g.
    GitHub issues, or WICG page).`,
  },

  enterprise_policies: {
    type: 'input',
    attrs: MULTI_STRING_FIELD_ATTRS,
    required: false,
    label: 'Enterprise policies',
    help_text: html` List the policies that are being introduced, removed, or
    can be used to control the feature at this stage, if any.`,
  },

  enterprise_feature_categories: {
    type: 'multiselect',
    choices: ENTERPRISE_FEATURE_CATEGORIES,
    required: false,
    label: 'Categories',
    help_text: html` Select all that apply.`,
  },

  enterprise_impact: {
    type: 'select',
    choices: ENTERPRISE_IMPACT,
    initial: ENTERPRISE_IMPACT.IMPACT_NONE[0],
    enterprise_initial: ENTERPRISE_IMPACT.IMPACT_MEDIUM[0],
    label: 'Enterprise impact / risk',
    help_text: html` Most web platform changes have no enterprise impact or risk
    unless they introduce a breaking change that could cause breakage without
    remediation from the web developer. Enterprise reviewers can help judge risk
    if you're unsure.`,
    enterprise_help_text: html` A feature is probably high impact if it
    introduces a breaking change on the stable channel, or seriously changes the
    experience of using Chrome. Use your judgment; Enterprise reviewers can help
    judge risk if you're unsure.`,
  },

  rollout_impact: {
    type: 'select',
    choices: ROLLOUT_IMPACT,
    initial: ROLLOUT_IMPACT.IMPACT_MEDIUM[0],
    label: 'Impact',
    help_text: html` A stage is probably high impact if it introduces a breaking
    change on the stable channel, or seriously changes the experience of using
    Chrome. Use your judgment; if you're unsure, most stages are Medium impact.`,
  },

  rollout_milestone: {
    type: 'input',
    attrs: {...MILESTONE_NUMBER_FIELD_ATTRS, min: 100},
    required: true,
    label: 'Chrome milestone',
    help_text: html` The milestone in which this stage rolls out to the stable
    channel (even a 1% rollout). If you don't yet know which milestone it will
    be, put in your best estimate. You can always change this later.`,
  },

  rollout_platforms: {
    type: 'multiselect',
    choices: PLATFORM_CATEGORIES,
    required: true,
    label: 'Rollout platforms',
    help_text: html` The platform(s) affected by this stage`,
  },

  rollout_details: {
    type: 'textarea',
    attrs: {rows: 4},
    required: false,
    label: 'Rollout details (optional)',
    help_text: html` Explain what specifically is changing in this milestone,
    for the given platforms. Many features are composed of multiple stages on
    different milestones. For example, you may have a stage that introduces a
    change and a temporary policy to control it, then another stage on a
    subsequent milestone that removes the policy. Alternatively, you may ship
    the feature to different platforms in different milestones.`,
  },

  breaking_change: {
    type: 'checkbox',
    label: 'Breaking change',
    initial: false,
    help_text: html` This is a breaking change: customers or developers must
    take action to continue using some existing functionaity.`,
  },
};

// Return a simplified field type to help differentiate the
// render behavior of each field in chromedash-feature-detail
function categorizeFieldType(field: Field) {
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
function makeHumanReadable(fieldName: string) {
  fieldName = fieldName.replace('_', ' ');
  return fieldName.charAt(0).toUpperCase() + fieldName.slice(1);
}

// Return an array of field info
function makeDisplaySpec(fieldName: string) {
  const fieldProps = ALL_FIELDS[fieldName];
  const displayName =
    fieldProps.label || fieldProps.displayLabel || makeHumanReadable(fieldName);
  const fieldType = categorizeFieldType(fieldProps);
  return [fieldName, displayName, fieldType];
}

export function makeDisplaySpecs(fieldNames: string[]) {
  return fieldNames.map(fieldName => makeDisplaySpec(fieldName));
}

// Find the minimum milestone, used for shipped milestones.
function findMinMilestone(
  fieldName: string,
  stageTypes: Set<number>,
  getFieldValue: any
) {
  let minMilestone = Infinity;
  // Iterate through all stages that are in stageTypes.
  const feature = getFieldValue.feature;
  for (const stage of feature.stages) {
    if (stageTypes.has(stage.stage_type)) {
      const milestone = getFieldValue(fieldName, stage);
      if (milestone != null && milestone !== '') {
        minMilestone = Math.min(minMilestone, milestone);
      }
    }
  }
  if (minMilestone === Infinity) return undefined;
  return minMilestone;
}

// Find the maximum milestone, used for OT start milestones.
function findMaxMilestone(
  fieldName: string,
  stageTypes: Set<number>,
  getFieldValue: any
) {
  let maxMilestone = -Infinity;
  // Iterate through all stages that are in stageTypes.
  const feature = getFieldValue.feature;
  for (const stage of feature.stages) {
    if (stageTypes.has(stage.stage_type)) {
      const milestone = getFieldValue(fieldName, stage);
      if (milestone != null && milestone !== '') {
        maxMilestone = Math.max(maxMilestone, milestone);
      }
    }
  }
  if (maxMilestone === -Infinity) return undefined;
  return maxMilestone;
}

// Check that the earlier milestone is before all later milestones.
// Used with OT start milestone and all shipped milestones.
function checkEarlierBeforeAllLaterMilestones(
  fieldPair: MilestoneRange,
  getFieldValue: any
) {
  const {earlier, allLater, warning} = fieldPair;
  const stageTypes =
    // Only shipping, for now.
    allLater && SHIPPED_MILESTONE_FIELDS.has(allLater)
      ? STAGE_TYPES_SHIPPING
      : null;
  const earlierValue = getNumericValue(earlier, getFieldValue);
  if (stageTypes && allLater) {
    const laterValue = findMinMilestone(allLater, stageTypes, getFieldValue);
    if (
      earlierValue != null &&
      laterValue != null &&
      Number(earlierValue) >= laterValue
    ) {
      return warning
        ? {
            warning,
          }
        : {
            error: `Earlier milestone #${earlierValue} should be before shipped milestone #${laterValue}.`,
          };
    }
  }
}

// Check that all earlier milestones before a later milestone.
// Used with all OT start milestones and a shipped milestone.
function checkAllEarlierBeforeLaterMilestone(
  fieldPair: MilestoneRange,
  getFieldValue: any
) {
  const {allEarlier, later, warning, error} = fieldPair;
  const stageTypes =
    allEarlier &&
    // Only origin trials or dev trials, for now.
    OT_MILESTONE_START_FIELDS.has(allEarlier)
      ? STAGE_TYPES_ORIGIN_TRIAL
      : allEarlier && DT_MILESTONE_FIELDS.has(allEarlier)
        ? STAGE_TYPES_DEV_TRIAL
        : null;
  // console.info(`stageTypes: ${stageTypes}`);
  if (stageTypes && allEarlier) {
    const earlierValue = findMaxMilestone(
      allEarlier,
      stageTypes,
      getFieldValue
    );
    const laterValue = getNumericValue(later, getFieldValue);
    if (
      earlierValue != null &&
      laterValue != null &&
      earlierValue >= Number(laterValue)
    ) {
      return warning
        ? {
            warning,
          }
        : {
            error:
              error ||
              `Earlier milestone #${earlierValue} should be before shipped milestone #${laterValue}.`,
          };
    }
  }
}

function getNumericValue(name, getFieldValue) {
  const value = getFieldValue(name, 'current stage');
  if (typeof value === 'string') {
    if (value === '') return undefined;
    return Number(value);
  }
  return value;
}

function checkMilestoneRanges(ranges, getFieldValue) {
  let result;
  for (const range of ranges) {
    const {earlier, allEarlier, later, allLater, warning, error} = range;
    // There can be an allLater or allEarlier, but not both.
    if (allLater) {
      result = checkEarlierBeforeAllLaterMilestones(range, getFieldValue);
    } else if (allEarlier) {
      result = checkAllEarlierBeforeLaterMilestone(range, getFieldValue);
    } else {
      const earlierMilestone = getNumericValue(earlier, getFieldValue);
      const laterMilestone = getNumericValue(later, getFieldValue);
      if (earlierMilestone != null && laterMilestone != null) {
        if (laterMilestone <= earlierMilestone) {
          // It's either a warning or an error.
          result = warning
            ? {
                warning,
              }
            : {
                error: error || 'Start milestone must be before end milestone',
              };
        }
      }
    }
    if (result) return result;
  }
}

function checkFeatureNameAndType(getFieldValue) {
  const name = (getFieldValue('name') || '').toLowerCase();
  const featureType = Number(getFieldValue('feature_type') || '0');
  const isdeprecationName = name.includes('deprecat') || name.includes('remov');
  const isdeprecationType =
    featureType === FEATURE_TYPES.FEATURE_TYPE_DEPRECATION_ID[0];
  if (isdeprecationName !== isdeprecationType) {
    if (isdeprecationName) {
      return {
        warning: `If the feature name contains "deprecate" or "remove",
        the feature type should be "Feature deprecation"`,
      };
    } else {
      return {
        warning: `If the feature type is "Feature deprecation",
        the feature name should contain "deprecate" or "remove"`,
      };
    }
  }
}

async function checkFirstEnterpriseNotice(value, initialValue) {
  if (!value) {
    return undefined;
  }
  const newChannelStableDate = await window.csClient
    .getSpecifiedChannels(value, value)
    .then(channels => channels[value]?.stable_date);
  const previousChannelStableDate = initialValue
    ? await window.csClient
        .getSpecifiedChannels(initialValue, initialValue)
        .then(channels => channels[value]?.stable_date)
    : undefined;

  if (!newChannelStableDate) {
    return {error: `Unknown milestone ${value}`};
  }
  if (
    previousChannelStableDate &&
    Date.parse(previousChannelStableDate) < Date.now()
  ) {
    return {
      warning: `Feature was already shown in milestone ${initialValue}, this cannot be changed`,
    };
  }
  if (Date.parse(newChannelStableDate) <= Date.now()) {
    return {
      warning: `Milestone ${value}  was already released, choose a future milestone`,
    };
  }
  return undefined;
}

async function checkExtensionMilestoneIsValid(value) {
  if (isNaN(value)) {
    return {error: 'Invalid milestone format.'};
  }
  for (let i = 0; i < value.length; i++) {
    // Milestone should only have digits.
    if (value[i] < '0' || value[i] > '9') {
      return {error: 'Invalid milestone format.'};
    }
  }
  const intValue = parseInt(value);
  if (intValue >= 1000) {
    return {error: 'Milestone is too distant.'};
  }
  const resp = await fetch(
    'https://chromiumdash.appspot.com/fetch_milestone_schedule'
  );
  const json = await resp.json();
  if (parseInt(json.mstones[0].mstone) > intValue) {
    return {error: 'End milestone cannot be in the past.'};
  }
  // TODO(DanielRyanSmith): Check that the extension milestone comes after
  // OT end milestone and all previous extension end milestones.
  return undefined;
}
