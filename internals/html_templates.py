# -*- coding: utf-8 -*-
# Copyright 2022 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License")
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


def estimated_milestone_tables_html(feature):
  def filtered_table_items(table_item_tuple):
    return tuple(item for item in table_item_tuple if item[1])

  def table_html(table_item_tuple):
    table_html = ''
    for item in table_item_tuple:
      title, value = item
      table_html += (
        f'<tr><td>{title}</td>\n'
        f'<td>{value}</td></tr>\n'
      )
    return f'<table>\n{table_html}</table>\n'
  
  desktop_table_items = filtered_table_items((
    ('Shipping on desktop', feature.shipped_milestone),
    ('OriginTrial desktop last', feature.ot_milestone_desktop_end),
    ('OriginTrial desktop first', feature.ot_milestone_desktop_start),
    ('DevTrial on desktop', feature.dt_milestone_desktop_start),
  ))
  andriod_table_items = filtered_table_items((
    ('Shipping on Android', feature.shipped_android_milestone),
    ('OriginTrial Android last', feature.ot_milestone_android_end),
    ('OriginTrial Android first', feature.ot_milestone_android_start),
    ('DevTrial on Android', feature.dt_milestone_android_start),
  ))
  webview_table_items = filtered_table_items((
    ('Shipping on WebView', feature.shipped_webview_milestone),
    ('OriginTrial webView last', feature.ot_milestone_webview_end),
    ('OriginTrial webView first', feature.ot_milestone_webview_start),
  ))
  ios_table_items = filtered_table_items((
    ('Shipping on iOS', feature.shipped_ios_milestone),
    ('DevTrial on iOS', feature.dt_milestone_ios_start),
  ))

  if not (desktop_table_items or andriod_table_items
          or webview_table_items or ios_table_items):
    return '<p>No milestones specified</p>\n'

  return table_html(desktop_table_items) + table_html(andriod_table_items) \
       + table_html(webview_table_items) + table_html(ios_table_items)
