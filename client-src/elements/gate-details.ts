import {html, TemplateResult} from 'lit';
import * as enums from './form-field-enums';

const BLINK_GENERIC_QUESTIONNAIRE: TemplateResult = html` <p>
    To request a review, use the "Draft intent..." button above to generate an
    intent messsage, and then post that message to blink-dev@chromium.org.
  </p>
  <p>
    Be sure to update your feature entry in response to any suggestions on that
    email thread.
  </p>`;

const PRIVACY_GENERIC_QUESTIONNAIRE: TemplateResult = html` <p>
    <b
      >Please fill out the Security &amp; Privacy self-review questionnaire:
      <a
        href="https://www.w3.org/TR/security-privacy-questionnaire/"
        target="_blank"
        >https://www.w3.org/TR/security-privacy-questionnaire/</a
      ></b
    >
  </p>
  <p>
    Share it as a public document, as a file in your repository, or in any other
    public format of your choice.
  </p>
  <p>
    You can reuse the same filled-out questionnaire in the security review
    below, across all stages of this ChromeStatus entry, and across all entries
    related to the same API. If you updated an existing questionnaire to reflect
    new changes to the API, please highlight them for an easier review.
  </p>
  <p>
    <b>If you believe your feature has no privacy impact</b> and none of the
    questions in the questionnaire apply, you can provide a justification
    instead, e.g. "Removing a prefix from the API, no changes to functionality"
    or "New CSS property that doesn't depend on the user state, therefore
    doesn't reveal any user information". Note that if your reviewer disagrees
    with the justification, they may ask you to fill out the questionnaire
    nevertheless.
  </p>`;

const SECURITY_GENERIC_QUESTIONNAIRE: TemplateResult = html` <p>
    <b
      >Please fill out the Security &amp; Privacy self-review questionnaire:
      <a
        href="https://www.w3.org/TR/security-privacy-questionnaire/"
        target="_blank"
        >https://www.w3.org/TR/security-privacy-questionnaire/</a
      ></b
    >
  </p>
  <p>
    Share it as a public document, as a file in your repository, or in any other
    public format of your choice.
  </p>
  <p>
    You can reuse the same filled-out questionnaire in the privacy review above,
    across all stages of this ChromeStatus entry, and across all entries related
    to an API. If you updated an existing questionnaire to reflect new changes
    to the API, please highlight them for an easier review.
  </p>
  <p>
    <b>If you believe your feature has no security impact</b> and none of the
    questions in the questionnaire apply, you can provide a justification
    instead. Note that if your reviewer disagrees with the justification, they
    may ask you to fill out the questionnaire nevertheless.
  </p>`;

const ENTERPRISE_SHIP_QUESTIONNAIRE: TemplateResult = html` <p>
    <b>(1) Does this launch include a breaking change?</b> Does this launch
    remove or modify existing behavior or does it interrupt an existing user
    flow? (e.g. removing or restricting an API, or significant UI change).
    Answer with one of the following options, and/or describe anything you're
    unsure about:
  </p>
  <ul>
    <li>
      No. There's no change visible to users, developers, or IT admins (e.g.
      internal refactoring)
    </li>
    <li>No. This launch is strictly additive functionality</li>
    <li>
      Yes. Something that exists is changing or being removed (even if usage is
      very small)
    </li>
    <li>
      I don't know. Enterprise reviewers, please help me decide. The relevant
      information is: ______
    </li>
  </ul>
  <p>
    <b
      >(2) Is there any other reason you expect that enterprises will care about
      this launch?</b
    >
    (e.g. they may perceive a risk of data leaks if the browser is uploading new
    information, or it may be a surprise to employees resulting in them calling
    their help desk). Answer with one of the following options, and/or describe
    anything you're unsure about:
  </p>
  <ul>
    <li>No. Enterprises won't care about this</li>
    <li>Yes. They'll probably care because ______</li>
    <li>
      I don't know. Enterprise reviewers, please help me decide. The relevant
      information is: ______
    </li>
  </ul>
  <p>
    <b
      >(3) Does your launch have an enterprise policy to control it, and will it
      be available when this rolls out to stable (even to 1%)?</b
    >
    Only required if you answered Yes to either of the first 2 questions. Answer
    with one of the following options, and/or describe anything you're unsure
    about:
  </p>
  <ul>
    <li>
      Yes. It's called ______. It will be a permanent policy, and it will be
      available when stable rollout starts
    </li>
    <li>
      Yes. It's called ______. This is a temporary transition period, so the
      policy will stop working on milestone ___. It will be available when
      stable rollout starts
    </li>
    <li>
      No. A policy is infeasible because ______ (e.g. this launch is a change in
      how we compile Chrome)
    </li>
    <li>
      No. A policy isn't necessary because ______ (e.g. there's a better method
      of control available to admins)
    </li>
  </ul>
  <p>
    <b
      >(4) Provide a brief title and description of this launch, which can be
      shared with enterprises.</b
    >
    Only required if you answered Yes to either of the first 2 questions. This
    may be added to browser release notes. Where applicable, explain the benefit
    to users, and describe the policy to control it.
  </p>`;

const DEBUGGABILITY_ORIGIN_TRIAL_QUESTIONNAIRE: TemplateResult = html`
  <p>
    (1) Does the introduction of the new Web Platform feature break Chrome
    DevTools' existing developer experience?
  </p>

  <p>
    (2) Does Chrome DevTools' existing set of tooling features interact with the
    new Web Platform feature in an expected way?
  </p>

  <p>
    (3) Would the new Web Platform feature's acceptance and/or adoption benefit
    from adding a new developer workflow to Chrome DevTools?
  </p>

  <p>
    When in doubt, please check out https://goo.gle/devtools-checklist for
    details!
  </p>
`;

const DEBUGGABILITY_SHIP_QUESTIONNAIRE: TemplateResult =
  DEBUGGABILITY_ORIGIN_TRIAL_QUESTIONNAIRE;

const TESTING_SHIP_QUESTIONNAIRE: TemplateResult = html` <p>
    <b
      >(1) Does your feature have sufficient automated test coverage (Unit
      tests, WPT, browser tests and other integration tests)?</b
    >
    Chrome requires at least 70% automation code coverage (<a
      href="https://analysis.chromium.org/coverage/p/chromium"
      target="_blank"
      >dashboard</a
    >) running on the main/release branch and 70% Changelist
    <a
      href="https://chromium.googlesource.com/chromium/src/+/refs/heads/main/docs/testing/code_coverage_in_gerrit.md"
      target="_blank"
      >code coverage in Gerrit</a
    >? Do the automated tests have more than 93% green (flakiness < 7%) on CQ
    and CI builders?
  </p>
  <ul>
    <li>
      Yes. My feature met the minimum automated test coverage and health
      requirements.
    </li>
    <li>No. My feature does not meet the requirements since __________.</li>
  </ul>
  <p>
    <b>(2) How are performance tests conducted on Chromium builders?</b> List
    links to tests if any.
  </p>
  <p>
    <b
      >(3) Does this feature have non-automatable test cases that require manual
      testing? Do you have a plan to get them tested?</b
    >
  </p>
  <ul>
    <li>No. All feature related test cases are automated.</li>
    <li>
      Yes. There are non-automatable test cases and I have completed test
      execution or allocated resources to ensure the coverage of these test
      cases.
    </li>
    <li>
      Yes. There are non-automatable test cases and my feature impacts Google
      products.
    </li>
  </ul>
  <p>
    <b
      >(4) If your feature impacts Google products, please fill in
      <a href="http://go/chrome-wp-test-survey" target="_blank"
        >go/chrome-wp-test-survey</a
      >.</b
    >
    Make a copy, answer the survey questions, and provide a link to your
    document here.
  </p>`;

export const GATE_QUESTIONNAIRES: Record<number, TemplateResult> = {
  [enums.GATE_TYPES.API_PROTOTYPE]: BLINK_GENERIC_QUESTIONNAIRE,
  [enums.GATE_TYPES.API_ORIGIN_TRIAL]: BLINK_GENERIC_QUESTIONNAIRE,
  [enums.GATE_TYPES.API_EXTEND_ORIGIN_TRIAL]: BLINK_GENERIC_QUESTIONNAIRE,
  [enums.GATE_TYPES.API_SHIP]: BLINK_GENERIC_QUESTIONNAIRE,
  [enums.GATE_TYPES.API_PLAN]: BLINK_GENERIC_QUESTIONNAIRE,
  [enums.GATE_TYPES.PRIVACY_ORIGIN_TRIAL]: PRIVACY_GENERIC_QUESTIONNAIRE,
  [enums.GATE_TYPES.PRIVACY_SHIP]: PRIVACY_GENERIC_QUESTIONNAIRE,
  // Note: There is no privacy planning gate.
  [enums.GATE_TYPES.SECURITY_ORIGIN_TRIAL]: SECURITY_GENERIC_QUESTIONNAIRE,
  [enums.GATE_TYPES.SECURITY_SHIP]: SECURITY_GENERIC_QUESTIONNAIRE,
  // Note: There is no security planning gate.
  [enums.GATE_TYPES.ENTERPRISE_SHIP]: ENTERPRISE_SHIP_QUESTIONNAIRE,
  [enums.GATE_TYPES.ENTERPRISE_PLAN]: ENTERPRISE_SHIP_QUESTIONNAIRE,
  [enums.GATE_TYPES.DEBUGGABILITY_ORIGIN_TRIAL]:
    DEBUGGABILITY_ORIGIN_TRIAL_QUESTIONNAIRE,
  [enums.GATE_TYPES.DEBUGGABILITY_SHIP]: DEBUGGABILITY_SHIP_QUESTIONNAIRE,
  [enums.GATE_TYPES.DEBUGGABILITY_PLAN]: DEBUGGABILITY_SHIP_QUESTIONNAIRE,
  [enums.GATE_TYPES.TESTING_SHIP]: TESTING_SHIP_QUESTIONNAIRE,
  [enums.GATE_TYPES.TESTING_PLAN]: TESTING_SHIP_QUESTIONNAIRE,
};

const LAUNCHING_FEATURES_URL =
  'https://www.chromium.org/blink/launching-features/';

const BLINK_GENERIC_RATIONALE = html`
  The API Owners review provides a final check on all aspects of your feature
  and how you have followed the
  <a href=${LAUNCHING_FEATURES_URL} target="_blank">Blink launch process</a>.
`;

const PRIVACY_GENERIC_RATIONALE = html`
  The Web Platform privacy review puts you in touch with the privacy team so
  that they can consult further with you when needed.
`;

const SECURITY_GENERIC_RATIONALE = html`
  The Web Platform Security review helps ensure that new or changed web APIs
  uphold the security principles of the web - the same origin policy, no
  cross-site leaks, compliance with CSP, CORS, permission norms, etc. It aims to
  show that the API can be implemented safely. It doesn’t necessarily try to
  prove that it has been implemented safely within Chromium - for Chrome team
  features, that’s done by the Chrome launch review process.
`;

const ENTERPRISE_GENERIC_RATIONALE = html`
  The enterprise review helps identify the impact of your feature on
  enterprises. Features need to be enterprise-friendly. That is:

  <ul>
    <li>Breaking changes need to have sufficient notice</li>
    <li>
      Breaking changes need to have a soft deadline and transition period where
      feasible
    </li>
    <li>Admins need to have central controls where appropriate</li>
  </ul>
`;

const DEBUGGABILITY_GENERIC_RATIONALE = html`
  The debuggability review helps identify opportunities to make your feature
  more successful by integrating with Chrome Dev Tools.
`;

const TESTING_GENERIC_RATIONALE = html`
  The test review helps identify gaps in test coverage and ensures that all
  crucial functionalities are thoroughly tested. This can lead to a more
  polished final product and reduce the odds of missed defects and issues.
`;

export const GATE_RATIONALE: Record<number, TemplateResult> = {
  [enums.GATE_TYPES.API_PROTOTYPE]: BLINK_GENERIC_RATIONALE,
  [enums.GATE_TYPES.API_ORIGIN_TRIAL]: BLINK_GENERIC_RATIONALE,
  [enums.GATE_TYPES.API_EXTEND_ORIGIN_TRIAL]: BLINK_GENERIC_RATIONALE,
  [enums.GATE_TYPES.API_SHIP]: BLINK_GENERIC_RATIONALE,
  [enums.GATE_TYPES.API_PLAN]: BLINK_GENERIC_RATIONALE,
  [enums.GATE_TYPES.PRIVACY_ORIGIN_TRIAL]: PRIVACY_GENERIC_RATIONALE,
  [enums.GATE_TYPES.PRIVACY_SHIP]: PRIVACY_GENERIC_RATIONALE,
  // Note: There is no privacy planning gate.
  [enums.GATE_TYPES.SECURITY_ORIGIN_TRIAL]: SECURITY_GENERIC_RATIONALE,
  [enums.GATE_TYPES.SECURITY_SHIP]: SECURITY_GENERIC_RATIONALE,
  // Note: There is no security planning gate.
  [enums.GATE_TYPES.ENTERPRISE_SHIP]: ENTERPRISE_GENERIC_RATIONALE,
  [enums.GATE_TYPES.ENTERPRISE_PLAN]: ENTERPRISE_GENERIC_RATIONALE,
  [enums.GATE_TYPES.DEBUGGABILITY_ORIGIN_TRIAL]:
    DEBUGGABILITY_GENERIC_RATIONALE,
  [enums.GATE_TYPES.DEBUGGABILITY_SHIP]: DEBUGGABILITY_GENERIC_RATIONALE,
  [enums.GATE_TYPES.DEBUGGABILITY_PLAN]: DEBUGGABILITY_GENERIC_RATIONALE,
  [enums.GATE_TYPES.TESTING_SHIP]: TESTING_GENERIC_RATIONALE,
  [enums.GATE_TYPES.TESTING_PLAN]: TESTING_GENERIC_RATIONALE,
};
