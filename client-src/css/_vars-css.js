/**
 * Copyright 2026 Google LLC
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

export const VARS = css`
:host {
  --default-font-color: #222;

  --light-grey: #eee;

  --gray-1: #e6e6e6;
  --gray-2: #a9a9a9;
  --gray-3: #797979;
  --gray-4: #515151;

  --nav-link-color: #444;

  --bar-shadow-color: rgba(0, 0, 0, .065);
  --bar-border-color: #D4D4D4;
  --error-border-color: #FF0000;

  --chromium-color-dark: #366597;
  --chromium-color-medium: #85b4df;
  --chromium-color-light: #bdd6ed;
  --chromium-color-center: #4580c0;

  --material-primary-button: #58f;

  --card-background: white;
  --card-border: 1px solid #ddd;
  --card-box-shadow: rgba(0, 0, 0, 0.067) 1px 1px 4px;

  /* App specific */
  --invalid-color: rgba(255,0,0,0.75);
  --content-padding: 16px;
  --content-padding-half: 8px;
  --content-padding-negative: -16px;
  --content-padding-huge: 80px;
  --default-border-radius: 3px;

  --max-content-width: 860px;
}`;
