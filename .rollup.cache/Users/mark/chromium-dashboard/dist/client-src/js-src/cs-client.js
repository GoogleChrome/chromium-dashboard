"use strict";
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
// prettier-ignore
(function (exports) {
    'use strict';
    /**
     * Generic Chrome Status Http Error.
     */
    var ChromeStatusHttpError = /** @class */ (function (_super) {
        __extends(ChromeStatusHttpError, _super);
        function ChromeStatusHttpError(message, resource, method, status) {
            var _this = _super.call(this, message) || this;
            _this.name = 'ChromeStatusHttpError';
            _this.resource = resource;
            _this.method = method;
            _this.status = status;
            return _this;
        }
        return ChromeStatusHttpError;
    }(Error));
    /**
     * FeatureNotFoundError represents an error for when a feature was not found
     * for the given ID.
     */
    var FeatureNotFoundError = /** @class */ (function (_super) {
        __extends(FeatureNotFoundError, _super);
        function FeatureNotFoundError(featureID) {
            var _this = _super.call(this, 'Feature not found') || this;
            _this.name = 'FeatureNotFoundError';
            _this.featureID = featureID;
            return _this;
        }
        return FeatureNotFoundError;
    }(Error));
    var ChromeStatusClient = /** @class */ (function () {
        function ChromeStatusClient(token, tokenExpiresSec) {
            this.token = token;
            this.tokenExpiresSec = tokenExpiresSec;
            this.baseUrl = '/api/v0'; // Same scheme, host, and port.
        }
        /* Refresh the XSRF token if necessary. */
        ChromeStatusClient.prototype.ensureTokenIsValid = function () {
            return __awaiter(this, void 0, void 0, function () {
                var refreshResponse;
                return __generator(this, function (_a) {
                    switch (_a.label) {
                        case 0:
                            if (!ChromeStatusClient.isTokenExpired(this.tokenExpiresSec)) return [3 /*break*/, 2];
                            return [4 /*yield*/, this.doFetch('/currentuser/token', 'POST', null)];
                        case 1:
                            refreshResponse = _a.sent();
                            this.token = refreshResponse.token;
                            this.tokenExpiresSec = refreshResponse.token_expires_sec;
                            _a.label = 2;
                        case 2: return [2 /*return*/];
                    }
                });
            });
        };
        /* Return true if the XSRF token has expired. */
        ChromeStatusClient.isTokenExpired = function (tokenExpiresSec) {
            var tokenExpiresDate = new Date(tokenExpiresSec * 1000);
            return tokenExpiresDate < new Date();
        };
        /* Make a JSON API call to the server, including an XSRF header.
         * Then strip off the defensive prefix from the response. */
        ChromeStatusClient.prototype.doFetch = function (resource_1, httpMethod_1, body_1) {
            return __awaiter(this, arguments, void 0, function (resource, httpMethod, body, includeToken) {
                var url, headers, options, response, rawResponseText, XSSIPrefix;
                if (includeToken === void 0) { includeToken = true; }
                return __generator(this, function (_a) {
                    switch (_a.label) {
                        case 0:
                            url = this.baseUrl + resource;
                            headers = {
                                'accept': 'application/json',
                                'content-type': 'application/json',
                            };
                            if (includeToken) {
                                headers['X-Xsrf-Token'] = this.token;
                            }
                            options = {
                                method: httpMethod,
                                credentials: 'same-origin',
                                headers: headers,
                            };
                            if (body !== null) {
                                options['body'] = JSON.stringify(body);
                            }
                            return [4 /*yield*/, fetch(url, options)];
                        case 1:
                            response = _a.sent();
                            if (response.status !== 200) {
                                throw new ChromeStatusHttpError("Got error response from server ".concat(resource, ": ").concat(response.status), resource, httpMethod, response.status);
                            }
                            return [4 /*yield*/, response.text()];
                        case 2:
                            rawResponseText = _a.sent();
                            XSSIPrefix = ')]}\'\n';
                            if (!rawResponseText.startsWith(XSSIPrefix)) {
                                throw new Error("Response does not start with XSSI prefix: ".concat(XSSIPrefix));
                            }
                            return [2 /*return*/, JSON.parse(rawResponseText.substr(XSSIPrefix.length))];
                    }
                });
            });
        };
        ChromeStatusClient.prototype.doGet = function (resource, body) {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    // GET's do not use token.
                    return [2 /*return*/, this.doFetch(resource, 'GET', body, false)];
                });
            });
        };
        ChromeStatusClient.prototype.doPost = function (resource, body) {
            return __awaiter(this, void 0, void 0, function () {
                var _this = this;
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.ensureTokenIsValid().then(function () {
                            return _this.doFetch(resource, 'POST', body);
                        })];
                });
            });
        };
        ChromeStatusClient.prototype.doPatch = function (resource, body) {
            return __awaiter(this, void 0, void 0, function () {
                var _this = this;
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.ensureTokenIsValid().then(function () {
                            return _this.doFetch(resource, 'PATCH', body);
                        })];
                });
            });
        };
        ChromeStatusClient.prototype.doDelete = function (resource) {
            return __awaiter(this, void 0, void 0, function () {
                var _this = this;
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.ensureTokenIsValid().then(function () {
                            return _this.doFetch(resource, 'DELETE', null);
                        })];
                });
            });
        };
        // //////////////////////////////////////////////////////////////
        // Specific API calls
        // Signing in and out
        ChromeStatusClient.prototype.signIn = function (credentialResponse) {
            var credential = credentialResponse.credential;
            // We don't use doPost because we don't already have a XSRF token.
            return this.doFetch('/login', 'POST', { 'credential': credential }, false);
        };
        ChromeStatusClient.prototype.signOut = function () {
            return this.doPost('/logout');
        };
        // Cues API
        ChromeStatusClient.prototype.getDismissedCues = function () {
            return this.doGet('/currentuser/cues');
        };
        ChromeStatusClient.prototype.dismissCue = function (cue) {
            return this.doPost('/currentuser/cues', { cue: cue })
                .then(function (res) { return res; });
            // TODO: catch((error) => { display message }
        };
        // Permissions API
        ChromeStatusClient.prototype.getPermissions = function (returnPairedUser) {
            if (returnPairedUser === void 0) { returnPairedUser = false; }
            var url = '/currentuser/permissions';
            if (returnPairedUser) {
                url += '?returnPairedUser';
            }
            return this.doGet(url)
                .then(function (res) { return res.user; });
        };
        // Settings API
        ChromeStatusClient.prototype.getSettings = function () {
            return this.doGet('/currentuser/settings');
        };
        ChromeStatusClient.prototype.setSettings = function (notify) {
            return this.doPost('/currentuser/settings', { notify: notify });
        };
        // Star API
        ChromeStatusClient.prototype.getStars = function () {
            return this.doGet('/currentuser/stars')
                .then(function (res) { return res.featureIds; });
            // TODO: catch((error) => { display message }
        };
        ChromeStatusClient.prototype.setStar = function (featureId, starred) {
            return this.doPost('/currentuser/stars', { featureId: featureId, starred: starred })
                .then(function (res) { return res; });
            // TODO: catch((error) => { display message }
        };
        // Accounts API
        ChromeStatusClient.prototype.createAccount = function (email, isAdmin, isSiteEditor) {
            return this.doPost('/accounts', { email: email, isAdmin: isAdmin, isSiteEditor: isSiteEditor });
            // TODO: catch((error) => { display message }
        };
        ChromeStatusClient.prototype.deleteAccount = function (accountId) {
            return this.doDelete('/accounts/' + accountId);
            // TODO: catch((error) => { display message }
        };
        ChromeStatusClient.prototype.getVotes = function (featureId, gateId) {
            if (gateId) {
                return this.doGet("/features/".concat(featureId, "/votes/").concat(gateId));
            }
            return this.doGet("/features/".concat(featureId, "/votes"));
        };
        ChromeStatusClient.prototype.setVote = function (featureId, gateId, state) {
            return this.doPost("/features/".concat(featureId, "/votes/").concat(gateId), { state: Number(state) });
        };
        ChromeStatusClient.prototype.getGates = function (featureId) {
            return this.doGet("/features/".concat(featureId, "/gates"));
        };
        ChromeStatusClient.prototype.getPendingGates = function () {
            return this.doGet('/gates/pending');
        };
        ChromeStatusClient.prototype.updateGate = function (featureId, gateId, assignees) {
            return this.doPost("/features/".concat(featureId, "/gates/").concat(gateId), { assignees: assignees,
            });
        };
        ChromeStatusClient.prototype.getComments = function (featureId, gateId) {
            var url = "/features/".concat(featureId, "/approvals/comments");
            if (gateId) {
                url = "/features/".concat(featureId, "/approvals/").concat(gateId, "/comments");
            }
            return this.doGet(url);
        };
        ChromeStatusClient.prototype.postComment = function (featureId, gateId, comment, postToThreadType) {
            if (gateId) {
                return this.doPost("/features/".concat(featureId, "/approvals/").concat(gateId, "/comments"), { comment: comment, postToThreadType: postToThreadType });
            }
            else {
                return this.doPost("/features/".concat(featureId, "/approvals/comments"), { comment: comment, postToThreadType: postToThreadType });
            }
        };
        ChromeStatusClient.prototype.deleteComment = function (featureId, commentId) {
            return this.doPatch("/features/".concat(featureId, "/approvals/comments"), { commentId: commentId, isUndelete: false });
        };
        ChromeStatusClient.prototype.undeleteComment = function (featureId, commentId) {
            return this.doPatch("/features/".concat(featureId, "/approvals/comments"), { commentId: commentId, isUndelete: true });
        };
        // Features API
        ChromeStatusClient.prototype.getFeature = function (featureId) {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.doGet("/features/".concat(featureId))
                            .catch(function (error) {
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
                        })];
                });
            });
        };
        ChromeStatusClient.prototype.getFeaturesInMilestone = function (milestone) {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.doGet("/features?milestone=".concat(milestone)).then(function (resp) { return resp['features_by_type']; })];
                });
            });
        };
        ChromeStatusClient.prototype.getFeaturesForEnterpriseReleaseNotes = function (milestone) {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.doGet("/features?releaseNotesMilestone=".concat(milestone))];
                });
            });
        };
        ChromeStatusClient.prototype.searchFeatures = function (userQuery, showEnterprise, sortSpec, start, num) {
            return __awaiter(this, void 0, void 0, function () {
                var url;
                return __generator(this, function (_a) {
                    url = "/features?q=".concat(userQuery);
                    if (showEnterprise) {
                        url += '&showEnterprise';
                    }
                    if (sortSpec) {
                        url += '&sort=' + sortSpec;
                    }
                    if (start) {
                        url += '&start=' + start;
                    }
                    if (num) {
                        url += '&num=' + num;
                    }
                    return [2 /*return*/, this.doGet(url)];
                });
            });
        };
        ChromeStatusClient.prototype.updateFeature = function (featureChanges) {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.doPatch('/features', featureChanges)];
                });
            });
        };
        // FeatureLinks API
        /**
         * @param {number} featureId
         * @returns {Promise<{data: FeatureLink[], has_stale_links: boolean}>}
         */
        ChromeStatusClient.prototype.getFeatureLinks = function (featureId_1) {
            return __awaiter(this, arguments, void 0, function (featureId, updateStaleLinks) {
                if (updateStaleLinks === void 0) { updateStaleLinks = true; }
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.doGet("/feature_links?feature_id=".concat(featureId, "&update_stale_links=").concat(updateStaleLinks))];
                });
            });
        };
        ChromeStatusClient.prototype.getFeatureLinksSummary = function () {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.doGet('/feature_links_summary')];
                });
            });
        };
        ChromeStatusClient.prototype.getFeatureLinksSamples = function (domain, type, isError) {
            return __awaiter(this, void 0, void 0, function () {
                var optionalParams;
                return __generator(this, function (_a) {
                    optionalParams = '';
                    if (type) {
                        optionalParams += "&type=".concat(type);
                    }
                    if (isError !== undefined && isError !== null) {
                        optionalParams += "&is_error=".concat(isError);
                    }
                    return [2 /*return*/, this.doGet("/feature_links_samples?domain=".concat(domain).concat(optionalParams))];
                });
            });
        };
        // Stages API
        ChromeStatusClient.prototype.getStage = function (featureId, stageId) {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.doGet("/features/".concat(featureId, "/stages/").concat(stageId))];
                });
            });
        };
        ChromeStatusClient.prototype.deleteStage = function (featureId, stageId) {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.doDelete("/features/".concat(featureId, "/stages/").concat(stageId))];
                });
            });
        };
        ChromeStatusClient.prototype.createStage = function (featureId, body) {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.doPost("/features/".concat(featureId, "/stages"), body)];
                });
            });
        };
        ChromeStatusClient.prototype.updateStage = function (featureId, stageId, body) {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.doPatch("/features/".concat(featureId, "/stages/").concat(stageId), body)];
                });
            });
        };
        ChromeStatusClient.prototype.addXfnGates = function (featureId, stageId) {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.doPost("/features/".concat(featureId, "/stages/").concat(stageId, "/addXfnGates"))];
                });
            });
        };
        // Origin trials API
        ChromeStatusClient.prototype.getOriginTrials = function () {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.doGet('/origintrials')];
                });
            });
        };
        ChromeStatusClient.prototype.createOriginTrial = function (featureId, stageId, body) {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.doPost("/origintrials/".concat(featureId, "/").concat(stageId, "/create"), body)];
                });
            });
        };
        ChromeStatusClient.prototype.extendOriginTrial = function (featureId, stageId, body) {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.doPatch("/origintrials/".concat(featureId, "/").concat(stageId, "/extend"), body)];
                });
            });
        };
        // Processes API
        ChromeStatusClient.prototype.getFeatureProcess = function (featureId) {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.doGet("/features/".concat(featureId, "/process"))];
                });
            });
        };
        // Progress API
        ChromeStatusClient.prototype.getFeatureProgress = function (featureId) {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.doGet("/features/".concat(featureId, "/progress"))];
                });
            });
        };
        // Blinkcomponents API
        ChromeStatusClient.prototype.getBlinkComponents = function () {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.doGet('/blinkcomponents')];
                });
            });
        };
        // Channels API
        ChromeStatusClient.prototype.getChannels = function () {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.doGet('/channels')];
                });
            });
        };
        ChromeStatusClient.prototype.getSpecifiedChannels = function (start, end) {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    return [2 /*return*/, this.doGet("/channels?start=".concat(start, "&end=").concat(end))];
                });
            });
        };
        return ChromeStatusClient;
    }());
    ;
    exports.ChromeStatusClient = ChromeStatusClient;
    exports.FeatureNotFoundError = FeatureNotFoundError;
})(window);
//# sourceMappingURL=cs-client.js.map