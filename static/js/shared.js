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

(function(exports) {
let addToHomescreenEvent;

const a2hsButton = document.querySelector('#a2hs-button');

exports.addEventListener('beforeinstallprompt', e => {
  e.preventDefault();
  addToHomescreenEvent = e;
  a2hsButton.classList.add('available');
});

if (a2hsButton) {
  a2hsButton.addEventListener('click', e => {
    e.preventDefault();
    if (addToHomescreenEvent && !a2hsButton.classList.contains('disabled')) {
      addToHomescreenEvent.prompt().then(() => {
        // TODO: handle user pressing "cancel" button on prompt.
        // https://bugs.chromium.org/p/chromium/issues/detail?id=805744
        addToHomescreenEvent.userChoice.then(choice => {
          console.log(choice);
          if (choice.outcome === 'accepted') {
            a2hsButton.classList.add('disabled');
            a2hsButton.setAttribute('title', 'App already installed.');
            addToHomescreenEvent = null;
          } else {
            a2hsButton.setAttribute(
                'title', 'Refresh the page and click again to install app.');
          }
          a2hsButton.classList.add('disabled'); // Can't re-prompt, so disable button
        });
      });
    }
  });
}
})(window);

// Google Analytics
/*eslint-disable */
(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','//www.google-analytics.com/analytics.js','ga');
/*eslint-enable */

ga('create', 'UA-39048143-1', 'auto');
ga('send', 'pageview');
// End Google Analytics
