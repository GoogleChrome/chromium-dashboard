#!/usr/bin/env python3
# Copyright 2026 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Seeds demo features for Chrome 151 release notes in the local Datastore emulator."""

import os
import sys

# Ensure repository root is in sys.path and required development env vars are set
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('SERVER_SOFTWARE', 'Development/2.0')
os.environ.setdefault('DATASTORE_EMULATOR_HOST', 'localhost:15606')

from google.cloud import ndb
from internals.core_models import FeatureEntry, Stage, MilestoneSet
from internals import core_enums
from framework import rediscache

client = ndb.Client(project='cr-status-staging')
with client.context():
    for f in FeatureEntry.query():
        f.key.delete()
    for s in Stage.query():
        s.key.delete()

    css_features = [
        (
            'CSS Container Style Queries',
            'Enables querying computed styles of container elements using CSS @container style(...) queries, allowing modular styling based on ancestor custom properties and computed values without modifying markup.',
            ['https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_containment/Container_style_queries', 'https://drafts.csswg.org/css-contain-3/#style-container']
        ),
        (
            'CSS Anchor Positioning API',
            'Enables positioning tethered elements (such as tooltips, popovers, context menus, and floating badges) relative to one or more anchor elements declaratively in CSS using anchor() and position-area properties.',
            ['https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_anchor_positioning', 'https://drafts.csswg.org/css-anchor-position-1/']
        ),
        (
            'CSS @starting-style for Entry Transitions',
            'Enables defining starting styles for elements transitioning from display: none into the DOM, unlocking smooth top-layer entry animations for dialogs and popovers without JavaScript timers.',
            ['https://developer.mozilla.org/en-US/docs/Web/CSS/@starting-style', 'https://drafts.csswg.org/css-transitions-2/#defining-before-change-style']
        ),
        (
            'CSS text-wrap: pretty Typography',
            'Optimizes paragraph and heading line breaking by preventing typographic orphans (single trailing words on the last line) and minimizing hyphenation rivers across wrapped multiline text blocks.',
            ['https://developer.mozilla.org/en-US/docs/Web/CSS/text-wrap', 'https://drafts.csswg.org/css-text-4/#text-wrap']
        ),
        (
            'CSS Subgrid Interpolation & Alignment',
            'Enables nested grid items to participate directly in the sizing and alignment tracks of their parent grid container across both row and column axes simultaneously.',
            ['https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout/Subgrid', 'https://drafts.csswg.org/css-grid-2/#subgrids']
        ),
        (
            'CSS color-mix() Gamut Mapping',
            'Allows mixing two color values in any specified color space (including Oklab, Oklch, Display P3, and sRGB) with customizable percentage weightings and perceptually uniform gamut clipping.',
            ['https://developer.mozilla.org/en-US/docs/Web/CSS/color_value/color-mix', 'https://drafts.csswg.org/css-color-5/#color-mix']
        ),
        (
            'CSS @scope Rule Isolation',
            'Enables scoping CSS selectors to specific DOM subtrees with optional scope limits (donut scoping), preventing style leakage without requiring shadow DOM boundaries or BEM class naming conventions.',
            ['https://developer.mozilla.org/en-US/docs/Web/CSS/@scope', 'https://drafts.csswg.org/css-cascade-6/#scoped-styles']
        ),
    ]

    for name, summary, doc_links in css_features:
        fe = FeatureEntry(
            name=name,
            summary=summary,
            category=core_enums.CSS,
            feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
            impl_status_chrome=core_enums.ENABLED_BY_DEFAULT,
            unlisted=False,
            confidential=False,
            doc_links=doc_links
        )
        fe.put()
        st = Stage(
            feature_id=fe.key.integer_id(),
            stage_type=core_enums.STAGE_BLINK_SHIPPING,
            milestones=MilestoneSet(desktop_first=151),
            archived=False
        )
        st.put()

    js_features = [
        (
            'Temporal API',
            'Provides modern date and time handling with full timezone support, precise calendar arithmetic, nanosecond precision, and immutable data structures replacing the legacy Date object.',
            ['https://tc39.es/proposal-temporal/', 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Temporal']
        ),
        (
            'Array & Object Grouping (Object.groupBy)',
            'Introduces static methods Object.groupBy and Map.groupBy to group iterable elements according to return values from a provided callback function without manual reducer loops.',
            ['https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/groupBy']
        ),
    ]

    for name, summary, doc_links in js_features:
        fe = FeatureEntry(
            name=name,
            summary=summary,
            category=core_enums.JAVASCRIPT,
            feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
            impl_status_chrome=core_enums.ENABLED_BY_DEFAULT,
            unlisted=False,
            confidential=False,
            doc_links=doc_links
        )
        fe.put()
        st = Stage(
            feature_id=fe.key.integer_id(),
            stage_type=core_enums.STAGE_BLINK_SHIPPING,
            milestones=MilestoneSet(desktop_first=151),
            archived=False
        )
        st.put()

    webrtc_features = [
        (
            'WebRTC Encoded Transform',
            'Allows insertable streams processing for raw audio and video frames directly in worker threads before encoding or after decoding, enabling end-to-end encryption and custom packet transforms.',
            ['https://w3c.github.io/webrtc-encoded-transform/']
        ),
        (
            'WebCodecs VideoFrame Metadata Extensions',
            'Adds detailed metadata inspection including color space, display aspect ratio, and capture timestamp directly to WebCodecs VideoFrame instances.',
            ['https://w3c.github.io/webcodecs/']
        ),
    ]

    for name, summary, doc_links in webrtc_features:
        fe = FeatureEntry(
            name=name,
            summary=summary,
            category=core_enums.WEBRTC,
            feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
            impl_status_chrome=core_enums.ENABLED_BY_DEFAULT,
            unlisted=False,
            confidential=False,
            doc_links=doc_links
        )
        fe.put()
        st = Stage(
            feature_id=fe.key.integer_id(),
            stage_type=core_enums.STAGE_BLINK_SHIPPING,
            milestones=MilestoneSet(desktop_first=151),
            archived=False
        )
        st.put()

rediscache.flushall()
print('Successfully seeded 11 demo features for Chrome 151 and flushed Redis!')
