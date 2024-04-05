/**
 * Copyright 2024 Google LLC
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

import {css} from 'lit';

/**
 * Flexbox layout helper classes.
 *
 * This is a simplified version of the flexbox layout helper classes from
 * https://htmlpreview.github.io/?https://raw.githubusercontent.com/dlaliberte/standards-notes/master/flexbox-classes.html
 */
export const FLEX_BOX = css`
  .hbox,
  .vbox {
    display: flex;
    align-items: center;
  }

  .hbox {
    flex-direction: row;
  }
  .vbox {
    flex-direction: column;
  }

  .hbox > .spacer,
  .vbox > .spacer {
    flex-grow: 1;
    visibility: hidden;
  }
`;
