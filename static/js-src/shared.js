/**
 * Copyright 2018 Google Inc. All rights reserved.
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

'use strict';

// Google Analytics
/* eslint-disable */
// Global site tag (gtag.js) - Google Analytics
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());

gtag('config', 'UA-179341418-1');
// End Google Analytics


// Make sure that our form handler for XSRF token updates gets
// registered after all the Shoelace form listeners are registered
// so that failed form validation cancels the submit event before
// our listener tries to programatically submit the form.
// Ten seconds should be enough time, and there is no rush since
// XSRF tokens don't expire until much more time has passsed.
window.setTimeout(window.csClient.addFormSubmitListner, 10 * 1000);
