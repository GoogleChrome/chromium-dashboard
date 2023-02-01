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

(function(exports) {
'use strict';

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
class FeatureNotFoundError extends Error {
  constructor(featureID) {
    super('Feature not found');
    this.name = 'FeatureNotFoundError';
    this.featureID = featureID;
  }
}

class ChromeStatusClient {
  constructor(token, tokenExpiresSec) {
    this.token = token;
    this.tokenExpiresSec = tokenExpiresSec;
    this.baseUrl = '/api/v0'; // Same scheme, host, and port.
  }

  /* Refresh the XSRF token if necessary. */
  async ensureTokenIsValid() {
    if (ChromeStatusClient.isTokenExpired(this.tokenExpiresSec)) {
      const refreshResponse = await this.doFetch(
        '/currentuser/token', 'POST', null);
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
  async doFetch(resource, httpMethod, body, includeToken=true) {
    const url = this.baseUrl + resource;
    const headers = {
      'accept': 'application/json',
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
        response.status);
    }
    const rawResponseText = await response.text();
    const XSSIPrefix = ')]}\'\n';
    if (!rawResponseText.startsWith(XSSIPrefix)) {
      console.log(rawResponseText);
      throw new Error(
          `Response does not start with XSSI prefix: ${XSSIPrefix}`);
    }
    return JSON.parse(rawResponseText.substr(XSSIPrefix.length));
  }

  doGet(resource, body) {
    // GET's do not use token.
    return this.doFetch(resource, 'GET', body, false);
  }

  doPost(resource, body) {
    return this.ensureTokenIsValid().then(() => {
      return this.doFetch(resource, 'POST', body);
    });
  }

  doPatch(resource, body) {
    return this.ensureTokenIsValid().then(() => {
      return this.doFetch(resource, 'PATCH', body);
    });
  }

  doDelete(resource) {
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
    return this.doFetch('/login', 'POST', {'credential': credential}, false);
  }

  signOut() {
    return this.doPost('/logout');
  }

  // Cues API

  getDismissedCues() {
    return this.doGet(`/currentuser/cues`);
  }

  dismissCue(cue) {
    return this.doPost('/currentuser/cues', {cue: cue})
      .then((res) => res);
    // TODO: catch((error) => { display message }
  }

  // Permissions API
  getPermissions() {
    return this.doGet('/currentuser/permissions')
      .then((res) => res.user);
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
    return this.doGet('/currentuser/stars')
      .then((res) => res.featureIds);
    // TODO: catch((error) => { display message }
  }

  setStar(featureId, starred) {
    return this.doPost(
      '/currentuser/stars',
      {featureId: featureId, starred: starred})
      .then((res) => res);
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
    return this.doPost(
        `/features/${featureId}/votes/${gateId}`,
        {state: Number(state)});
  }

  getApprovalConfigs(featureId) {
    return this.doGet(`/features/${featureId}/configs`);
  }

  setApprovalConfig(featureId, fieldId, owners, nextAction, additionalReview) {
    return this.doPost(
        `/features/${featureId}/configs`,
        {fieldId: Number(fieldId),
          owners: owners || '',
          nextAction: nextAction || '',
          additionalReview: additionalReview || false,
        });
  }

  getGates(featureId) {
    return this.doGet(`/features/${featureId}/gates`);
  }

  getComments(featureId, gateId, commentsOnly=true) {
    let url = `/features/${featureId}/approvals/comments`;
    if (gateId) {
      url = `/features/${featureId}/approvals/${gateId}/comments`;
    }
    if (commentsOnly) {
      url += '?comments_only';
    }
    return this.doGet(url);
  }

  postComment(featureId, gateId, comment, postToThreadType) {
    if (gateId) {
      return this.doPost(
          `/features/${featureId}/approvals/${gateId}/comments`,
          {comment, postToThreadType});
    } else {
      return this.doPost(
          `/features/${featureId}/approvals/comments`,
          {comment, postToThreadType});
    }
  }

  deleteComment(featureId, commentId) {
    return this.doPatch(
      `/features/${featureId}/approvals/comments`,
      {commentId, isUndelete: false},
    );
  }

  undeleteComment(featureId, commentId) {
    return this.doPatch(
      `/features/${featureId}/approvals/comments`,
      {commentId, isUndelete: true},
    );
  }

  // Features API
  getFeature(featureId) {
    return this.doGet(`/features/${featureId}`)
      .catch((error) => {
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

  getFeaturesInMilestone(milestone) {
    return this.doGet(`/features?milestone=${milestone}`).then(
      (resp) => resp['features_by_type']);
  }

  searchFeatures(userQuery, sortSpec, start, num) {
    let url = `/features?q=${userQuery}`;
    if (sortSpec) {
      url += '&sort=' + sortSpec;
    }
    if (start) {
      url += '&start=' + start;
    }
    if (num) {
      url += '&num=' + num;
    }
    return this.doGet(url);
  }

  // Stages API
  getStage(featureId, stageId) {
    return this.doGet(`/features/${featureId}/stages/${stageId}`);
  }

  createStage(featureId, body) {
    return this.doPost(`/features/${featureId}/stages`, body);
  }

  // Processes API
  getFeatureProcess(featureId) {
    return this.doGet(`/features/${featureId}/process`);
  }

  // Progress API
  getFeatureProgress(featureId) {
    return this.doGet(`/features/${featureId}/progress`);
  }

  // Blinkcomponents API
  getBlinkComponents() {
    return this.doGet(`/blinkcomponents`);
  }

  // Channels API
  getChannels() {
    return this.doGet('/channels');
  }

  getSpecifiedChannels(start, end) {
    return this.doGet(`/channels?start=${start}&end=${end}`);
  }

  /**
   * Parses URL query strings into a dict.
   * @param {string} rawQuery a raw URL query string, e.g. q=abc&num=1;
   * @return {Object} A key-value pair dictionary for the query string.
   */
  parseRawQuery(rawQuery) {
    const params = new URLSearchParams(rawQuery);
    const result = {};
    for (const param of params.keys()) {
      const values = params.getAll(param);
      if (!values.length) {
        continue;
      }
      // Assume there is only one value.
      result[param] = values[0];
    }
    return result;
  }
};

exports.ChromeStatusClient = ChromeStatusClient;
exports.FeatureNotFoundError = FeatureNotFoundError;
})(window);
