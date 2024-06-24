/**
 * Copyright 2016 Google Inc. All rights reserved.
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

import {DefaultApi as Api, Configuration} from 'chromestatus-openapi';

/**
 * Creates a client.
 * @extends {import('chromestatus-openapi').DefaultApiInterface}
 */
export class ChromeStatusOpenApiClient extends Api {
  constructor() {
    super(
      new Configuration({
        credentials: 'same-origin',
        apiKey: 'placeholder-api-key',
        middleware: [
          {pre: ChromeStatusMiddlewares.xsrfMiddleware},
          {post: ChromeStatusMiddlewares.xssiMiddleware},
        ],
      })
    );
  }
}

export class ChromeStatusMiddlewares {
  /**
   * Refresh the XSRF Token, if needed. Add to headers.
   *
   * @param {import('chromestatus-openapi').RequestContext} req
   * @return {Promise<import('chromestatus-openapi').FetchParams>}
   */
  static async xsrfMiddleware(req) {
    const headers = req.init.headers || {};
    if ('X-Xsrf-Token' in headers) {
      await window.csClient.ensureTokenIsValid();
      headers['X-Xsrf-Token'] = window.csClient.token;
      req.init.headers = headers;
    }
    return req;
  }

  /**
   * Server sends XSSI prefix. Remove it and allow the client to parse.
   *
   * @param {import('chromestatus-openapi').ResponseContext} context
   * @return {Promise<Response>}
   */
  static async xssiMiddleware(context) {
    const response = context.response;
    return response.text().then(rawResponseText => {
      const XSSIPrefix = ")]}'\n";
      if (!rawResponseText.startsWith(XSSIPrefix)) {
        throw new Error(
          `Response does not start with XSSI prefix: ${XSSIPrefix}`
        );
      }
      return new Response(rawResponseText.substring(XSSIPrefix.length), {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
      });
    });
  }
}
