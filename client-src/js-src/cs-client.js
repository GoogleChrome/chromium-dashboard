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
