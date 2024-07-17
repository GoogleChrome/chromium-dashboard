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

/**
 * @typedef {object} FeatureLink
 * @property {string} url
 * @property {string} type
 * @property {object} information - fields depend on type; see link_helpers.py
 * @property {number} http_error_code
 */

/**
 * @typedef {object} SampleFeatureLink
 * @property {string} url
 * @property {number} http_error_code
 * @property {number[]} feature_ids
 */

/**
 * @typedef {object} FeatureLinksSummary
 * @property {number} total_count
 * @property {number} covered_count
 * @property {number} uncovered_count
 * @property {number} error_count
 * @property {number} http_error_count
 * @property {Array<{key: string; count: number}>} link_types
 * @property {Array<{key: string; count: number}>} uncovered_link_domains
 * @property {Array<{key: string; count: number}>} error_link_domains
 */

/**
 * @typedef {Object} StageDict
 * @property {number} id
 * @property {string} created
 * @property {number} feature_id
 * @property {number} stage_type
 * @property {string} display_name
 * @property {number} intent_stage
 * @property {string} [intent_thread_url]
 * @property {string} [announcement_url]
 * @property {string} [origin_trial_id]
 * @property {string} [experiment_goals]
 * @property {string} [experiment_risks]
 * @property {StageDict[]} extensions
 * @property {string} [origin_trial_feedback_url]
 * @property {boolean} ot_action_requested
 * @property {string} [ot_activation_date]
 * @property {number} [ot_approval_buganizer_component]
 * @property {number} [ot_approval_buganizer_custom_field_id]
 * @property {string} [ot_approval_criteria_url]
 * @property {string} [ot_approval_group_email]
 * @property {string} [ot_chromium_trial_name]
 * @property {string} [ot_description]
 * @property {string} [ot_display_name]
 * @property {string} [ot_documentation_url]
 * @property {string[]} ot_emails
 * @property {string} [ot_feedback_submission_url]
 * @property {boolean} ot_has_third_party_support
 * @property {boolean} ot_is_critical_trial
 * @property {boolean} ot_is_deprecation_trial
 * @property {string} [ot_owner_email]
 * @property {boolean} ot_require_approvals
 * @property {number} [ot_setup_status]
 * @property {string} [ot_request_note]
 * @property {number} [ot_stage_id]
 * @property {string} [experiment_extension_reason]
 * @property {string} [finch_url]
 * @property {string} [rollout_details]
 * @property {number} [rollout_impact]
 * @property {number} [rollout_milestone]
 * @property {string[]} rollout_platforms
 * @property {string[]} enterprise_policies
 * @property {string[]} pm_emails
 * @property {string[]} tl_emails
 * @property {string[]} ux_emails
 * @property {string[]} te_emails
 * @property {number} [desktop_first]
 * @property {number} [android_first]
 * @property {number} [ios_first]
 * @property {number} [webview_first]
 * @property {number} [desktop_last]
 * @property {number} [android_last]
 * @property {number} [ios_last]
 * @property {number} [webview_last]
 */

/**
 * @typedef {Object} FeatureDictInnerResourceInfo
 * @property {string[]} samples
 * @property {string[]} docs
 */

/**
 * @typedef {Object} FeatureDictInnerMaturityInfo
 * @property {string} [text]
 * @property {string} [short_text]
 * @property {number} val
 */

/**
 * @typedef {Object} FeatureDictInnerStandardsInfo
 * @property {string} [spec]
 * @property {FeatureDictInnerMaturityInfo} maturity
 */

/**
 * @typedef {Object} FeatureDictInnerBrowserStatus
 * @property {string} [text]
 * @property {string} [val]
 * @property {string} [milestone_str]
 */

/**
 * @typedef {Object} FeatureDictInnerViewInfo
 * @property {string} [text]
 * @property {number} [val]
 * @property {string} [url]
 * @property {string} [notes]
 */

/**
 * @typedef {Object} FeatureDictInnerChromeBrowserInfo
 * @property {string} [bug]
 * @property {string[]} [blink_components]
 * @property {string[]} [devrel]
 * @property {string[]} [owners]
 * @property {boolean} [origintrial]
 * @property {boolean} [intervention]
 * @property {boolean} [prefixed]
 * @property {boolean} [flag]
 * @property {FeatureDictInnerBrowserStatus} status
 * @property {number} [desktop]
 * @property {number} [android]
 * @property {number} [webview]
 * @property {number} [ios]
 */

/**
 * @typedef {Object} FeatureDictInnerSingleBrowserInfo
 * @property {FeatureDictInnerViewInfo} [view]
 */

/**
 * @typedef {Object} FeatureBrowsersInfo
 * @property {FeatureDictInnerChromeBrowserInfo} chrome
 * @property {FeatureDictInnerSingleBrowserInfo} ff
 * @property {FeatureDictInnerSingleBrowserInfo} safari
 * @property {FeatureDictInnerSingleBrowserInfo} webdev
 * @property {FeatureDictInnerSingleBrowserInfo} other
 */

/**
 * @typedef {Object} FeatureDictInnerUserEditInfo
 * @property {string} [by]
 * @property {string} [when]
 */

/**
 * @typedef {Object} Feature
 * Metadata: Creation and updates
 * @property {number} id
 * @property {FeatureDictInnerUserEditInfo} created
 * @property {FeatureDictInnerUserEditInfo} updated
 * @property {string} [accurate_as_of]
 * @property {string} [creator_email]
 * @property {string} [updater_email]
 * Metadata: Access controls
 * @property {string[]} owner_emails
 * @property {string[]} editor_emails
 * @property {string[]} cc_emails
 * @property {string[]} spec_mentor_emails
 * @property {boolean} unlisted
 * @property {boolean} deleted
 * Renamed metadata fields
 * @property {string[]} editors
 * @property {string[]} cc_recipients
 * @property {string[]} spec_mentors
 * @property {string} [creator]
 * Descriptive info.
 * @property {string} name
 * @property {string} summary
 * @property {string} category
 * @property {number} category_int
 * @property {string[]} blink_components
 * @property {number} star_count
 * @property {string[]} search_tags
 * @property {string} [feature_notes]
 * @property {string[]} enterprise_feature_categories
 * Metadata: Process information
 * @property {string} feature_type
 * @property {number} feature_type_int
 * @property {string} intent_stage
 * @property {number} intent_stage_int
 * @property {number} [active_stage_id]
 * @property {string} [bug_url]
 * @property {string} [launch_bug_url]
 * @property {string[]} screenshot_links
 * @property {number} [first_enterprise_notification_milestone]
 * @property {boolean} breaking_change
 * @property {number} enterprise_impact
 * Implementation in Chrome
 * @property {string} [flag_name]
 * @property {string} [finch_name]
 * @property {string} [non_finch_justification]
 * @property {string} [ongoing_constraints]
 * Topic: Adoption
 * @property {string} [motivation]
 * @property {string} [devtrial_instructions]
 * @property {string} [activation_risks]
 * @property {string} [measurement]
 * @property {string} [availability_expectation]
 * @property {string} [adoption_expectation]
 * @property {string} [adoption_plan]
 * Gate: Standardization and Interop
 * @property {string} [initial_public_proposal_url]
 * @property {string[]} explainer_links
 * @property {boolean} requires_embedder_support
 * @property {string} [spec_link]
 * @property {string} [api_spec]
 * @property {boolean} [prefixed]
 * @property {string} [interop_compat_risks]
 * @property {boolean} [all_platforms]
 * @property {boolean} [all_platforms_descr]
 * @property {string} [tag_review]
 * @property {string} [non_oss_deps]
 * @property {string} [anticipated_spec_changes]
 * Gate: Security & Privacy
 * @property {string} [security_risks]
 * @property {string[]} tags
 * @property {string} tag_review_status
 * @property {number} [tag_review_status_int]
 * @property {string} security_review_status
 * @property {number} [security_review_status_int]
 * @property {string} privacy_review_status
 * @property {number} [privacy_review_status_int]
 * Gate: Testing / Regressions
 * @property {string} [ergonomics_risks]
 * @property {boolean} [wpt]
 * @property {string} [wpt_descr]
 * @property {string} [webview_risks]
 * Gate: Devrel & Docs
 * @property {string[]} devrel_emails
 * @property {string} [debuggability]
 * @property {string[]} doc_links
 * @property {string[]} sample_links
 * @property {StageDict[]} stages
 * @property {string} [experiment_timeline]
 * @property {FeatureDictInnerResourceInfo} resources
 * @property {string} [comments]
 * Repeated in 'browsers' section. TODO: delete these?
 * @property {number} ff_views
 * @property {number} safari_views
 * @property {number} web_dev_views
 * @property {FeatureBrowsersInfo} browsers
 * @property {FeatureDictInnerStandardsInfo} standards
 * @property {boolean} is_released
 * @property {boolean} is_enterprise_feature
 * @property {string} [updated_display]
 * @property {string} [new_crbug_url]
 */

/**
 * @typedef {object} User
 * @property {boolean} can_create_feature
 * @property {boolean} can_edit_all
 * @property {boolean} can_comment
 * @property {boolean} is_admin
 * @property {string} email
 * @property {number[]} approvable_gate_types
 * @property {number[]} editable_features
 */

/**
 * @typedef {Object} ReleaseInfo
 * @property {number} version
 * @property {string} [earliest_beta] (optional).
 * @property {string} [mstone] (optional).
 * @property {string | null} [stable_date] (optional).
 * @property {string | null} [latest_beta] - The latest beta release date (optional).
 */

/**
 * @typedef {Object.<string, ReleaseInfo>} Channels
 */

/**
 * Generic Chrome Status Http Error.
 */
class ChromeStatusHttpError extends Error {
  constructor(message, resource, method, status) {
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
  constructor(featureID) {
    super('Feature not found');
    this.name = 'FeatureNotFoundError';
    this.featureID = featureID;
  }
}

export class ChromeStatusClient {
  constructor(token, tokenExpiresSec) {
    this.token = token;
    this.tokenExpiresSec = tokenExpiresSec;
    this.baseUrl = '/api/v0'; // Same scheme, host, and port.
  }

  /* Refresh the XSRF token if necessary. */
  async ensureTokenIsValid() {
    if (ChromeStatusClient.isTokenExpired(this.tokenExpiresSec)) {
      const refreshResponse = await this.doFetch(
        '/currentuser/token',
        'POST',
        null
      );
      this.token = refreshResponse.token;
      this.tokenExpiresSec = refreshResponse.token_expires_sec;
    }
  }

  /* Return true if the XSRF token has expired. */
  static isTokenExpired(tokenExpiresSec) {
    const tokenExpiresDate = new Date(tokenExpiresSec * 1000);
    return tokenExpiresDate < new Date();
  }

  /* Make a JSON API call to the server, including an XSRF header.
   * Then strip off the defensive prefix from the response. */
  async doFetch(resource, httpMethod, body, includeToken = true) {
    const url = this.baseUrl + resource;
    const headers = {
      accept: 'application/json',
      'content-type': 'application/json',
    };
    if (includeToken) {
      headers['X-Xsrf-Token'] = this.token;
    }
    const options = {
      method: httpMethod,
      credentials: 'same-origin',
      headers: headers,
    };
    if (body !== null) {
      options['body'] = JSON.stringify(body);
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
    return JSON.parse(rawResponseText.substr(XSSIPrefix.length));
  }

  async doGet(resource, body) {
    // GET's do not use token.
    return this.doFetch(resource, 'GET', body, false);
  }

  async doPost(resource, body) {
    return this.ensureTokenIsValid().then(() => {
      return this.doFetch(resource, 'POST', body);
    });
  }

  async doPatch(resource, body) {
    return this.ensureTokenIsValid().then(() => {
      return this.doFetch(resource, 'PATCH', body);
    });
  }

  async doDelete(resource) {
    return this.ensureTokenIsValid().then(() => {
      return this.doFetch(resource, 'DELETE', null);
    });
  }

  // //////////////////////////////////////////////////////////////
  // Specific API calls

  // Signing in and out

  signIn(credentialResponse) {
    const credential = credentialResponse.credential;
    // We don't use doPost because we don't already have a XSRF token.
    return this.doFetch('/login', 'POST', {credential: credential}, false);
  }

  signOut() {
    return this.doPost('/logout');
  }

  // Cues API

  getDismissedCues() {
    return this.doGet('/currentuser/cues');
  }

  dismissCue(cue) {
    return this.doPost('/currentuser/cues', {cue: cue}).then(res => res);
    // TODO: catch((error) => { display message }
  }

  // Permissions API
  getPermissions(returnPairedUser = false) {
    let url = '/currentuser/permissions';
    if (returnPairedUser) {
      url += '?returnPairedUser';
    }
    return this.doGet(url).then(res => res.user);
  }

  // Settings API

  getSettings() {
    return this.doGet('/currentuser/settings');
  }

  setSettings(notify) {
    return this.doPost('/currentuser/settings', {notify: notify});
  }

  // Star API

  getStars() {
    return this.doGet('/currentuser/stars').then(res => res.featureIds);
    // TODO: catch((error) => { display message }
  }

  setStar(featureId, starred) {
    return this.doPost('/currentuser/stars', {
      featureId: featureId,
      starred: starred,
    }).then(res => res);
    // TODO: catch((error) => { display message }
  }

  // Accounts API

  createAccount(email, isAdmin, isSiteEditor) {
    return this.doPost('/accounts', {email, isAdmin, isSiteEditor});
    // TODO: catch((error) => { display message }
  }

  deleteAccount(accountId) {
    return this.doDelete('/accounts/' + accountId);
    // TODO: catch((error) => { display message }
  }

  getVotes(featureId, gateId) {
    if (gateId) {
      return this.doGet(`/features/${featureId}/votes/${gateId}`);
    }
    return this.doGet(`/features/${featureId}/votes`);
  }

  setVote(featureId, gateId, state) {
    return this.doPost(`/features/${featureId}/votes/${gateId}`, {
      state: Number(state),
    });
  }

  getGates(featureId) {
    return this.doGet(`/features/${featureId}/gates`);
  }

  getPendingGates() {
    return this.doGet('/gates/pending');
  }

  updateGate(featureId, gateId, assignees) {
    return this.doPost(`/features/${featureId}/gates/${gateId}`, {assignees});
  }

  getComments(featureId, gateId) {
    let url = `/features/${featureId}/approvals/comments`;
    if (gateId) {
      url = `/features/${featureId}/approvals/${gateId}/comments`;
    }
    return this.doGet(url);
  }

  postComment(featureId, gateId, comment, postToThreadType) {
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

  deleteComment(featureId, commentId) {
    return this.doPatch(`/features/${featureId}/approvals/comments`, {
      commentId,
      isUndelete: false,
    });
  }

  undeleteComment(featureId, commentId) {
    return this.doPatch(`/features/${featureId}/approvals/comments`, {
      commentId,
      isUndelete: true,
    });
  }

  // Features API
  async getFeature(featureId) {
    return this.doGet(`/features/${featureId}`).catch(error => {
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
    });
  }

  async getFeaturesInMilestone(milestone) {
    return this.doGet(`/features?milestone=${milestone}`).then(
      resp => resp['features_by_type']
    );
  }

  async getFeaturesForEnterpriseReleaseNotes(milestone) {
    return this.doGet(`/features?releaseNotesMilestone=${milestone}`);
  }

  async searchFeatures(userQuery, showEnterprise, sortSpec, start, num) {
    const query = new URLSearchParams();
    query.set('q', userQuery);
    if (showEnterprise) {
      query.set('showEnterprise', '');
    }
    if (sortSpec) {
      query.set('sort', sortSpec);
    }
    if (start) {
      query.set('start', start);
    }
    if (num) {
      query.set('num', num);
    }
    return this.doGet(`/features?${query.toString()}`);
  }

  async updateFeature(featureChanges) {
    return this.doPatch('/features', featureChanges);
  }

  // FeatureLinks API

  /**
   * @param {number} featureId
   * @returns {Promise<{data: FeatureLink[], has_stale_links: boolean}>}
   */
  async getFeatureLinks(featureId, updateStaleLinks = true) {
    return this.doGet(
      `/feature_links?feature_id=${featureId}&update_stale_links=${updateStaleLinks}`
    );
  }

  async getFeatureLinksSummary() {
    return this.doGet('/feature_links_summary');
  }

  async getFeatureLinksSamples(domain, type, isError) {
    let optionalParams = '';
    if (type) {
      optionalParams += `&type=${type}`;
    }
    if (isError !== undefined && isError !== null) {
      optionalParams += `&is_error=${isError}`;
    }
    return this.doGet(
      `/feature_links_samples?domain=${domain}${optionalParams}`
    );
  }

  // Stages API
  async getStage(featureId, stageId) {
    return this.doGet(`/features/${featureId}/stages/${stageId}`);
  }

  async deleteStage(featureId, stageId) {
    return this.doDelete(`/features/${featureId}/stages/${stageId}`);
  }

  async createStage(featureId, body) {
    return this.doPost(`/features/${featureId}/stages`, body);
  }

  async updateStage(featureId, stageId, body) {
    return this.doPatch(`/features/${featureId}/stages/${stageId}`, body);
  }

  async addXfnGates(featureId, stageId) {
    return this.doPost(`/features/${featureId}/stages/${stageId}/addXfnGates`);
  }

  // Origin trials API
  async getOriginTrials() {
    return this.doGet('/origintrials');
  }

  async createOriginTrial(featureId, stageId, body) {
    return this.doPost(`/origintrials/${featureId}/${stageId}/create`, body);
  }

  async extendOriginTrial(featureId, stageId, body) {
    return this.doPatch(`/origintrials/${featureId}/${stageId}/extend`, body);
  }

  // Processes API
  async getFeatureProcess(featureId) {
    return this.doGet(`/features/${featureId}/process`);
  }

  // Progress API
  async getFeatureProgress(featureId) {
    return this.doGet(`/features/${featureId}/progress`);
  }

  // Blinkcomponents API
  async getBlinkComponents() {
    return this.doGet('/blinkcomponents');
  }

  // Channels API
  async getChannels() {
    return this.doGet('/channels');
  }

  async getSpecifiedChannels(start, end) {
    return this.doGet(`/channels?start=${start}&end=${end}`);
  }
}
