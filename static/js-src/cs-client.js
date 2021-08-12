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
      this.tokenExpiresSec = refreshResponse.tokenExpiresSec;
    }
  }

  /* Return true if the XSRF token has expired. */
  static isTokenExpired(tokenExpiresSec) {
    const tokenExpiresDate = new Date(tokenExpiresSec * 1000);
    return tokenExpiresDate < new Date();
  }

  /* Return all hidden form fields for XSRF tokens. */
  allTokenFields() {
    return document.querySelectorAll('input[name=token]');
  }

  /* Add updateFormToken() as a listener on all forms use XSRF. */
  addFormSubmitListner() {
    this.allTokenFields().forEach((field) => {
      field.form.addEventListener('submit', (event) => {
        this.updateFormToken(event);
      });
    });
  }

  /* If too much time has passed since the page loaded, get a new XSRF
   * token from the server and stuff it into the XSRF token form field
   * before submitting. */
  updateFormToken(event) {
    event.preventDefault();
    this.ensureTokenIsValid().then(() => {
      this.allTokenFields().forEach((field) => {
        field.value = this.token;
      });
      event.target.submit();
    });
  }

  /* Make a JSON API call to the server, including an XSRF header.
   * Then strip off the defensive prefix from the response. */
  async doFetch(resource, httpMethod, body, includeToken=true) {
    const url = this.baseUrl + resource;
    let headers = {
      'accept': 'application/json',
      'content-type': 'application/json',
    };
    if (includeToken) {
      headers['X-Xsrf-Token'] = this.token;
    }
    let options = {
      method: httpMethod,
      credentials: 'same-origin',
      headers: headers,
    };
    if (body !== null) {
      options['body'] = JSON.stringify(body);
    }

    const response = await fetch(url, options);

    if (response.status !== 200) {
      throw new Error(
          `Got error response from server ${resource}: ${response.status}`);
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

  signIn(googleUser) {
    // TODO(jrobbins): Consider using profile pic.
    // let profile = googleUser.getBasicProfile();
    let idToken = googleUser.getAuthResponse().id_token;
    // We don't use doPost because we don't already have a XSRF token.
    return this.doFetch('/login', 'POST', {'id_token': idToken}, false);
  }

  signOut(auth2) {
    return auth2.signOut().then(() => {
      return this.doPost('/logout');
    });
  }

  // Cues API

  dismissCue(cue) {
    return this.doPost('/currentuser/cues', {cue: cue})
      .then((res) => res);
    // TODO: catch((error) => { display message }
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

  createAccount(email, isAdmin) {
    return this.doPost('/accounts', {email, isAdmin});
    // TODO: catch((error) => { display message }
  }

  deleteAccount(accountId) {
    return this.doDelete('/accounts/' + accountId);
    // TODO: catch((error) => { display message }
  }

  // Review comments

  getComments(featureId, fieldId) {
    return this.doGet(`/features/${featureId}/approvals/${fieldId}/comments`);
  }

  postComment(featureId, fieldId, state, comment) {
    return this.doPost(
        `/features/${featureId}/approvals/${fieldId}/comments`,
        {state, comment});
  }

  // Features API
  getFeaturesInMilestone(milestone) {
    return this.doGet(`/features?milestone=${milestone}`);
  }

  // Channels API
  getChannels() {
    return this.doGet('/channels');
  }

  getSpecifiedChannels(start, end) {
    return this.doGet(`/channels?start=${start}&end=${end}`);
  }
};

exports.ChromeStatusClient = ChromeStatusClient;
})(window);
