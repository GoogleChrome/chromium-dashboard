/**
 * Copyright 2021 Google Inc. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

export interface FeatureLink {
  url: string;
  type: string;
  information?: object;
  http_error_code?: number | null;
}

export interface SampleFeatureLink {
  url: string;
  http_error_code: number;
  feature_ids: number[];
}

export interface FeatureLinksSummary {
  total_count: number;
  covered_count: number;
  uncovered_count: number;
  error_count: number;
  http_error_count: number;
  link_types: Array<{key: string; count: number}>;
  uncovered_link_domains: Array<{key: string; count: number}>;
  error_link_domains: Array<{key: string; count: number}>;
}

export interface StageDict {
  id: number;
  created: string;
  feature_id: number;
  stage_type: number;
  display_name: string;
  intent_stage: number;
  intent_thread_url?: string;
  announcement_url?: string;
  origin_trial_id?: string;
  experiment_goals?: string;
  experiment_risks?: string;
  extensions: StageDict[];
  origin_trial_feedback_url?: string;
  ot_action_requested: boolean;
  ot_activation_date?: string;
  ot_approval_buganizer_component?: number;
  ot_approval_buganizer_custom_field_id?: number;
  ot_approval_criteria_url?: string;
  ot_approval_group_email?: string;
  ot_chromium_trial_name?: string;
  ot_description?: string;
  ot_display_name?: string;
  ot_documentation_url?: string;
  ot_emails: string[];
  ot_feedback_submission_url?: string;
  ot_has_third_party_support: boolean;
  ot_is_critical_trial: boolean;
  ot_is_deprecation_trial: boolean;
  ot_owner_email?: string;
  ot_requester_email?: string;
  ot_require_approvals: boolean;
  ot_setup_status?: number;
  ot_request_note?: string;
  ot_stage_id?: number;
  ot_use_counter_bucket_number?: number;
  experiment_extension_reason?: string;
  finch_url?: string;
  rollout_details?: string;
  rollout_milestone?: number;
  rollout_platforms: string[];
  rollout_stage_plan: number;
  enterprise_policies: string[];
  pm_emails: string[];
  tl_emails: string[];
  ux_emails: string[];
  te_emails: string[];
  desktop_first?: number;
  android_first?: number;
  ios_first?: number;
  webview_first?: number;
  desktop_last?: number;
  android_last?: number;
  ios_last?: number;
  webview_last?: number;
}

export interface FeatureDictInnerResourceInfo {
  samples: string[];
  docs: string[];
}

export interface FeatureDictInnerMaturityInfo {
  text?: string;
  short_text?: string;
  val: number;
}

export interface FeatureDictInnerStandardsInfo {
  spec?: string;
  maturity: FeatureDictInnerMaturityInfo;
}

export interface FeatureDictInnerBrowserStatus {
  text?: string;
  val?: number;
  milestone_str?: string;
}

export interface FeatureDictInnerViewInfo {
  text?: string;
  val?: number;
  url?: string;
  notes?: string;
}

export interface FeatureDictInnerChromeBrowserInfo {
  bug?: string;
  blink_components?: string[];
  devrel?: string[];
  owners?: string[];
  origintrial?: boolean;
  prefixed?: boolean;
  flag?: boolean;
  status: FeatureDictInnerBrowserStatus;
  desktop?: number;
  android?: number;
  webview?: number;
  ios?: number;
}

export interface FeatureDictInnerSingleBrowserInfo {
  view?: FeatureDictInnerViewInfo;
}

export interface FeatureBrowsersInfo {
  chrome: FeatureDictInnerChromeBrowserInfo;
  ff: FeatureDictInnerSingleBrowserInfo;
  safari: FeatureDictInnerSingleBrowserInfo;
  webdev: FeatureDictInnerSingleBrowserInfo;
  other: FeatureDictInnerSingleBrowserInfo;
}

export interface FeatureDictInnerUserEditInfo {
  by?: string;
  when?: string;
}

export interface Feature {
  id: number;
  // Metadata: Creation and updates
  created: FeatureDictInnerUserEditInfo;
  updated: FeatureDictInnerUserEditInfo;
  accurate_as_of?: string;
  creator_email?: string;
  updater_email?: string;
  // Metadata: Access controls
  owner_emails: string[];
  editor_emails: string[];
  cc_emails: string[];
  spec_mentor_emails: string[];
  unlisted: boolean;
  confidential: boolean;
  deleted: boolean;
  // Renamed metadata fields
  editors: string[];
  cc_recipients: string[];
  spec_mentors: string[];
  creator?: string;
  // Descriptive info.
  name: string;
  summary: string;
  markdown_fields: string[];
  category: string;
  category_int: number;
  web_feature?: string;
  blink_components: string[];
  star_count: number;
  search_tags: string[];
  feature_notes?: string;
  enterprise_feature_categories: string[];
  enterprise_product_category: number;
  is_releasenotes_content_reviewed?: boolean;
  is_releasenotes_publish_ready?: boolean;
  // Metadata: Process information
  feature_type: string;
  feature_type_int: number;
  intent_stage: string;
  intent_stage_int: number;
  active_stage_id?: number;
  bug_url?: string;
  launch_bug_url?: string;
  screenshot_links: string[];
  first_enterprise_notification_milestone?: number;
  breaking_change: boolean;
  enterprise_impact: number;
  // Implementation in Chrome
  flag_name?: string;
  finch_name?: string;
  non_finch_justification?: string;
  ongoing_constraints?: string;
  // Topic: Adoption
  motivation?: string;
  devtrial_instructions?: string;
  activation_risks?: string;
  measurement?: string;
  availability_expectation?: string;
  adoption_expectation?: string;
  adoption_plan?: string;
  // Gate: Standardization and Interop
  initial_public_proposal_url?: string;
  explainer_links: string[];
  requires_embedder_support: boolean;
  spec_link?: string;
  api_spec?: string;
  prefixed?: boolean;
  interop_compat_risks?: string;
  all_platforms?: boolean;
  all_platforms_descr?: string;
  tag_review?: string;
  non_oss_deps?: string;
  anticipated_spec_changes?: string;
  // Gate: Security & Privacy
  security_risks?: string;
  tags: string[];
  tag_review_status: string;
  tag_review_status_int?: number;
  security_review_status: string;
  security_review_status_int?: number;
  privacy_review_status: string;
  privacy_review_status_int?: number;
  security_continuity_id?: number;
  security_launch_issue_id?: number;
  // Gate: Testing / Regressions
  ergonomics_risks?: string;
  wpt?: boolean;
  wpt_descr?: string;
  webview_risks?: string;
  // Gate: Devrel & Docs
  devrel_emails: string[];
  debuggability?: string;
  doc_links: string[];
  sample_links: string[];
  stages: StageDict[];
  experiment_timeline?: string;
  resources: FeatureDictInnerResourceInfo;
  comments?: string;
  // AI WPT analysis fields
  ai_test_eval_report?: string;
  ai_test_eval_run_status?: number;
  ai_test_eval_status_timestamp?: string;
  // Repeated in 'browsers' section. TODO: delete these?
  ff_views: number;
  safari_views: number;
  web_dev_views: number;
  browsers: FeatureBrowsersInfo;
  standards: FeatureDictInnerStandardsInfo;
  is_released: boolean;
  is_enterprise_feature: boolean;
  updated_display?: string;
  new_crbug_url?: string;
}

export interface User {
  id: number;
  can_create_feature: boolean;
  can_edit_all: boolean;
  can_review_release_notes: boolean;
  can_comment: boolean;
  is_admin: boolean;
  email: string;
  is_site_editor: boolean;
  approvable_gate_types: number[];
  editable_features: number[];
}

export interface ReleaseInfo {
  version: number;
  earliest_beta?: string;
  mstone?: string;
  stable_date?: string | null;
  latest_beta?: string | null;
  final_beta?: string | null;
  early_stable?: string | null;
  features: {[key: string]: Feature[]};
}

export type Channels = {[key: string]: ReleaseInfo};

export interface Vote {
  feature_id: number;
  gate_id: number;
  gate_type?: number;
  state: number;
  set_on: string;
  set_by: string;
}

export interface GateDict {
  id: number;
  feature_id: number;
  stage_id: number;
  gate_type: number;
  team_name: string;
  gate_name: string;
  escalation_email?: string;
  state: number;
  requested_on?: string;
  responded_on?: string;
  assignee_emails: string[];
  next_action?: string;
  additional_review: boolean;
  slo_initial_response: number;
  slo_initial_response_took: number;
  slo_initial_response_remaining: number;
  slo_resolve: number;
  slo_resolve_took: number;
  slo_resolve_remaining: number;
  needs_work_started_on: string;
  possible_assignee_emails: string[];
  self_certify_possible: boolean;
  self_certify_eligible: boolean;
  survey_answers: {
    is_language_polyfill: boolean;
    is_api_polyfill: boolean;
    is_same_origin_css: boolean;
    launch_or_contact: string;
  };
}

/**
 * Generic Chrome Status Http Error.
 */
class ChromeStatusHttpError extends Error {
  resource: string;
  method: string;
  status: number;

  constructor(
    message: string,
    resource: string,
    method: string,
    status: number
  ) {
    super(message);
    this.name = 'ChromeStatusHttpError';
    this.resource = resource;
    this.method = method;
    this.status = status;
  }
}

/**
 * FeatureNotFoundError represents an error for when a feature was not found
 * for the given ID.
 */
export class FeatureNotFoundError extends Error {
  featureID: number;

  constructor(featureID: number) {
    super('Feature not found');
    this.name = 'FeatureNotFoundError';
    this.featureID = featureID;
  }
}

export class ChromeStatusClient {
  token: string;
  tokenExpiresSec: number;
  baseUrl: string;

  constructor(token: string, tokenExpiresSec: number) {
    this.token = token;
    this.tokenExpiresSec = tokenExpiresSec;
    this.baseUrl = '/api/v0'; // Same scheme, host, and port.
  }

  /* Refresh the XSRF token if necessary. */
  async ensureTokenIsValid(): Promise<void> {
    if (ChromeStatusClient.isTokenExpired(this.tokenExpiresSec)) {
      const refreshResponse = (await this.doFetch(
        '/currentuser/token',
        'POST',
        null
      )) as {token: string; token_expires_sec: number};
      this.token = refreshResponse.token;
      this.tokenExpiresSec = refreshResponse.token_expires_sec;
    }
  }

  /* Return true if the XSRF token has expired. */
  static isTokenExpired(tokenExpiresSec: number): boolean {
    const tokenExpiresDate = new Date(tokenExpiresSec * 1000);
    return tokenExpiresDate < new Date();
  }

  /* Make a JSON API call to the server, including an XSRF header.
   * Then strip off the defensive prefix from the response. */
  async doFetch(
    resource: string,
    httpMethod: string,
    body: unknown,
    includeToken = true,
    postingJson = true
  ): Promise<unknown> {
    const url = this.baseUrl + resource;
    const headers: {[key: string]: string} = {
      accept: 'application/json',
    };
    if (postingJson) {
      headers['content-type'] = 'application/json';
    }
    if (includeToken) {
      headers['X-Xsrf-Token'] = this.token;
    }
    const options: RequestInit = {
      method: httpMethod,
      credentials: 'same-origin',
      headers: headers,
    };
    if (body !== null && body !== undefined) {
      if (postingJson) {
        options['body'] = JSON.stringify(body);
      } else {
        options['body'] = body as BodyInit;
      }
    }

    const response = await fetch(url, options);

    if (response.status !== 200) {
      throw new ChromeStatusHttpError(
        `Got error response from server ${resource}: ${response.status}`,
        resource,
        httpMethod,
        response.status
      );
    }
    const rawResponseText = await response.text();
    const XSSIPrefix = ")]}'\n";
    if (!rawResponseText.startsWith(XSSIPrefix)) {
      throw new Error(
        `Response does not start with XSSI prefix: ${XSSIPrefix}`
      );
    }
    return JSON.parse(rawResponseText.substring(XSSIPrefix.length));
  }

  async doGet(resource: string, body?: unknown): Promise<unknown> {
    // GET's do not use token.
    return this.doFetch(resource, 'GET', body, false);
  }

  async doPost(resource: string, body?: unknown): Promise<unknown> {
    return this.ensureTokenIsValid().then(() => {
      return this.doFetch(resource, 'POST', body);
    });
  }

  async doFilePost(resource: string, file: File): Promise<unknown> {
    const formData = new FormData();
    formData.append('uploaded-file', file, file.name);
    return this.ensureTokenIsValid().then(() => {
      return this.doFetch(resource, 'POST', formData, true, false);
    });
  }

  async doPatch(resource: string, body?: unknown): Promise<unknown> {
    return this.ensureTokenIsValid().then(() => {
      return this.doFetch(resource, 'PATCH', body);
    });
  }

  async doDelete(resource: string): Promise<unknown> {
    return this.ensureTokenIsValid().then(() => {
      return this.doFetch(resource, 'DELETE', null);
    });
  }

  // //////////////////////////////////////////////////////////////
  // Specific API calls

  // Signing in and out

  signIn(credentialResponse: unknown): Promise<unknown> {
    const credential = (credentialResponse as {credential: string}).credential;
    // We don't use doPost because we don't already have a XSRF token.
    return this.doFetch('/login', 'POST', {credential: credential}, false);
  }

  signOut(): Promise<unknown> {
    return this.doPost('/logout');
  }

  // Cues API

  getDismissedCues(): Promise<string[]> {
    return this.doGet('/currentuser/cues') as Promise<string[]>;
  }

  dismissCue(cue: string): Promise<unknown> {
    return this.doPost('/currentuser/cues', {cue: cue}).then(res => res);
    // TODO: catch((error) => { display message }
  }

  // Permissions API
  getPermissions(returnPairedUser = false): Promise<User> {
    let url = '/currentuser/permissions';
    if (returnPairedUser) {
      url += '?returnPairedUser';
    }
    return this.doGet(url).then(res => (res as {user: User}).user);
  }

  // Settings API

  getSettings(): Promise<unknown> {
    return this.doGet('/currentuser/settings');
  }

  setSettings(notify: boolean): Promise<unknown> {
    return this.doPost('/currentuser/settings', {notify: notify});
  }

  // Star API

  getStars(): Promise<number[]> {
    // TODO(markxiong0122): delete this backward compatibility code after 30 days
    return (
      this.doGet('/currentuser/stars') as Promise<{
        featureIds?: number[];
        feature_ids?: number[];
      }>
    ).then(res => res.featureIds || res.feature_ids || []);
    // TODO: catch((error) => { display message }
  }

  setStar(featureId: number, starred: boolean): Promise<unknown> {
    return this.doPost('/currentuser/stars', {
      featureId: featureId,
      starred: starred,
    }).then(res => res);
    // TODO: catch((error) => { display message }
  }

  // Accounts API

  createAccount(
    email: string,
    isAdmin: boolean,
    isSiteEditor: boolean
  ): Promise<User | {error_message: string}> {
    return this.doPost('/accounts', {email, isAdmin, isSiteEditor}) as Promise<
      User | {error_message: string}
    >;
    // TODO: catch((error) => { display message }
  }

  deleteAccount(accountId: number): Promise<unknown> {
    return this.doDelete('/accounts/' + accountId);
    // TODO: catch((error) => { display message }
  }

  // Attachments API
  addAttachment(
    featureId: number,
    fieldName: string,
    file: File
  ): Promise<{attachment_url: string}> {
    return this.doFilePost(
      `/features/${featureId}/attachments`,
      file
    ) as Promise<{attachment_url: string}>;
  }

  // Reviews API

  getVotes(featureId: number, gateId?: number): Promise<{votes: Vote[]}> {
    if (gateId) {
      return this.doGet(`/features/${featureId}/votes/${gateId}`) as Promise<{
        votes: Vote[];
      }>;
    }
    return this.doGet(`/features/${featureId}/votes`) as Promise<{
      votes: Vote[];
    }>;
  }

  setVote(featureId: number, gateId: number, state: number): Promise<unknown> {
    return this.doPost(`/features/${featureId}/votes/${gateId}`, {
      state: Number(state),
    });
  }

  getGates(featureId: number): Promise<{gates: GateDict[]}> {
    return this.doGet(
      `/features/${featureId}/gates?include_deleted=1`
    ) as Promise<{gates: GateDict[]}>;
  }

  getPendingGates(): Promise<{gates: GateDict[]}> {
    return this.doGet('/gates/pending') as Promise<{gates: GateDict[]}>;
  }

  updateGate(
    featureId: number,
    gateId: number,
    assignees: string[],
    survey_answers: unknown
  ): Promise<unknown> {
    return this.doPatch(`/features/${featureId}/gates/${gateId}`, {
      assignees,
      survey_answers,
    });
  }

  getComments(
    featureId: number,
    gateId?: number
  ): Promise<{comments: string[]}> {
    let url = `/features/${featureId}/approvals/comments`;
    if (gateId) {
      url = `/features/${featureId}/approvals/${gateId}/comments`;
    }
    return this.doGet(url) as Promise<{comments: string[]}>;
  }

  postComment(
    featureId: number,
    gateId: number,
    comment: string,
    postToThreadType: number
  ): Promise<unknown> {
    if (gateId) {
      return this.doPost(
        `/features/${featureId}/approvals/${gateId}/comments`,
        {comment, postToThreadType}
      );
    } else {
      return this.doPost(`/features/${featureId}/approvals/comments`, {
        comment,
        postToThreadType,
      });
    }
  }

  deleteComment(featureId: number, commentId: number): Promise<unknown> {
    return this.doPatch(`/features/${featureId}/approvals/comments`, {
      commentId,
      isUndelete: false,
    });
  }

  undeleteComment(featureId: number, commentId: number): Promise<unknown> {
    return this.doPatch(`/features/${featureId}/approvals/comments`, {
      commentId,
      isUndelete: true,
    });
  }

  // Features API
  async getFeature(featureId: number): Promise<Feature> {
    return (this.doGet(`/features/${featureId}`) as Promise<Feature>).catch(
      error => {
        // If not the ChromeStatusHttpError, continue throwing.
        if (!(error instanceof ChromeStatusHttpError)) {
          throw error;
        }
        // Else, do further validations
        if (error.status === 404) {
          throw new FeatureNotFoundError(featureId);
        }
        // No other special cases means, we can re throw the error.
        throw error;
      }
    );
  }

  async getFeaturesInMilestone(
    milestone: number
  ): Promise<{[key: string]: Feature[]}> {
    return (
      this.doGet(`/features?milestone=${milestone}`) as Promise<{
        features_by_type: {[key: string]: Feature[]};
      }>
    ).then(resp => resp.features_by_type);
  }

  async getFeaturesForEnterpriseReleaseNotes(
    milestone: number
  ): Promise<unknown> {
    return this.doGet(`/features?releaseNotesMilestone=${milestone}`);
  }

  async searchFeatures(
    userQuery: string,
    showEnterprise?: boolean,
    sortSpec?: string,
    start?: number,
    num?: number,
    nameOnly?: boolean
  ): Promise<{features: Feature[]; total_count: number}> {
    const query = new URLSearchParams();
    query.set('q', userQuery);
    if (showEnterprise) {
      query.set('showEnterprise', '');
    }
    if (sortSpec) {
      query.set('sort', sortSpec);
    }
    if (start) {
      query.set('start', start.toString());
    }
    if (num) {
      query.set('num', num.toString());
    }
    if (nameOnly) {
      query.set('name_only', nameOnly.toString());
    }
    return this.doGet(`/features?${query.toString()}`) as Promise<{
      features: Feature[];
      total_count: number;
    }>;
  }

  async createFeature(
    featureChanges: Partial<Feature>
  ): Promise<{feature_id: number}> {
    return this.doPost('/features', featureChanges) as Promise<{
      feature_id: number;
    }>;
  }

  async updateFeature(featureChanges: Partial<Feature>): Promise<unknown> {
    return this.doPatch('/features', featureChanges);
  }

  // FeatureLinks API

  /**
   * @param {number} featureId
   * @returns {Promise<{data: FeatureLink[], has_stale_links: boolean}>}
   */
  async getFeatureLinks(
    featureId: number,
    updateStaleLinks = true
  ): Promise<{data: FeatureLink[]; has_stale_links: boolean}> {
    return this.doGet(
      `/feature_links?feature_id=${featureId}&update_stale_links=${updateStaleLinks}`
    ) as Promise<{data: FeatureLink[]; has_stale_links: boolean}>;
  }

  async getFeatureLinksSummary(): Promise<FeatureLinksSummary> {
    return this.doGet('/feature_links_summary') as Promise<FeatureLinksSummary>;
  }

  async getFeatureLinksSamples(
    domain: string,
    type?: string,
    isError?: boolean
  ): Promise<SampleFeatureLink[]> {
    let optionalParams = '';
    if (type) {
      optionalParams += `&type=${type}`;
    }
    if (isError !== undefined && isError !== null) {
      optionalParams += `&is_error=${isError}`;
    }
    return this.doGet(
      `/feature_links_samples?domain=${domain}${optionalParams}`
    ) as Promise<SampleFeatureLink[]>;
  }

  // Stages API
  async getStage(featureId: number, stageId: number): Promise<StageDict> {
    return this.doGet(
      `/features/${featureId}/stages/${stageId}`
    ) as Promise<StageDict>;
  }

  async deleteStage(featureId: number, stageId: number): Promise<unknown> {
    return this.doDelete(`/features/${featureId}/stages/${stageId}`);
  }

  async createStage(featureId: number, body: unknown): Promise<unknown> {
    return this.doPost(`/features/${featureId}/stages`, body);
  }

  async updateStage(
    featureId: number,
    stageId: number,
    body: unknown
  ): Promise<unknown> {
    return this.doPatch(`/features/${featureId}/stages/${stageId}`, body);
  }

  async addXfnGates(featureId: number, stageId: number): Promise<unknown> {
    return this.doPost(`/features/${featureId}/stages/${stageId}/addXfnGates`);
  }

  // Origin trials API
  async getOriginTrials(): Promise<unknown> {
    return this.doGet('/origintrials');
  }

  async createOriginTrial(
    featureId: number,
    stageId: number,
    body: unknown
  ): Promise<unknown> {
    return this.doPost(`/origintrials/${featureId}/${stageId}/create`, body);
  }

  async extendOriginTrial(
    featureId: number,
    stageId: number,
    body: unknown
  ): Promise<unknown> {
    return this.doPatch(`/origintrials/${featureId}/${stageId}/extend`, body);
  }

  // Security Reviews API
  async createSecurityLaunchIssue(
    featureId: number,
    gateId: number,
    continuityId?: number
  ): Promise<unknown> {
    const body: Record<string, unknown> = {
      feature_id: featureId,
      gate_id: gateId,
    };
    if (continuityId) {
      body.continuity_id = continuityId;
    }
    return this.doPost('/security-reviews/create-launch-issue', body);
  }

  // Processes API
  async getFeatureProcess(featureId: number): Promise<unknown> {
    return this.doGet(`/features/${featureId}/process`);
  }

  // Intents API
  async getIntentBody(
    featureId: number,
    stageId: number,
    gateId: number
  ): Promise<unknown> {
    return this.doGet(`/features/${featureId}/${stageId}/${gateId}/intent`);
  }
  async postIntentToBlinkDev(
    featureId: number,
    stageId: number,
    body: unknown
  ): Promise<unknown> {
    return this.doPost(`/features/${featureId}/${stageId}/intent`, body);
  }

  // Progress API
  async getFeatureProgress(featureId: number): Promise<unknown> {
    return this.doGet(`/features/${featureId}/progress`);
  }

  // Blinkcomponents API
  async getBlinkComponents(): Promise<unknown> {
    return this.doGet('/blinkcomponents');
  }

  // Web Features API
  async getWebFeatureIDs(): Promise<unknown> {
    return this.doGet('/web_feature_ids');
  }

  // Webdx Feature UseCounter enums
  async getWebdxFeatures(): Promise<unknown> {
    return this.doGet('/webdxfeatures');
  }

  // Channels API
  async getChannels(): Promise<Channels> {
    return this.doGet('/channels') as Promise<Channels>;
  }

  // Stale Features API
  async getStaleFeatures(): Promise<unknown> {
    return this.doGet('/features/stale');
  }

  // WPT Coverage API
  async generateWPTCoverageEvaluation(
    featureId: number,
    includeExplainer = false
  ): Promise<unknown> {
    return this.doPost(`/features/${featureId}/wpt-coverage-analysis`, {
      include_explainer: includeExplainer,
    });
  }

  // Delete WPT Coverage Report
  async deleteWPTCoverageEvaluation(featureId: number): Promise<unknown> {
    return this.doDelete(`/features/${featureId}/wpt-coverage-analysis`);
  }

  async getSpecifiedChannels(start: number, end: number): Promise<unknown> {
    return this.doGet(`/channels?start=${start}&end=${end}`);
  }
}
