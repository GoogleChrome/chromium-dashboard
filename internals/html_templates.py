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

import urllib
from django.utils.html import conditional_escape as escape

from internals import core_enums


def estimated_milestone_tables_html(feature):
  """Return an HTML string for the milestone tables."""
  
  def filtered_table_items(table_item_tuple):
    """Given a table tuple consists of milestone titles and values,
    filter out entries with a None value."""
    return tuple(item for item in table_item_tuple if item[1])

  def table_html(table_item_tuple):
    """Given a table tuple consists of milestone titles and values,
    return an HTML string for a milestone table."""
    table_html = ''
    for item in table_item_tuple:
      title, value = item
      table_html += (
        f'  <tr><td>{title}</td>\n'
        f'  <td>{value}</td></tr>\n'
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

def email_header_html(feature):
  """Return an HTML string for the email header."""
  blink_components = ', '.join(feature.blink_components)
  status = core_enums.IMPLEMENTATION_STATUS[feature.impl_status_chrome]
  estimated_milestone_tables = estimated_milestone_tables_html(feature)

  return (
    f'<p><b><a href="https://chromestatus.com/feature/{feature.key.integer_id()}">'
    f'{feature.name}</a></b></p>\n'
    f'<p><b>Components</b>: {blink_components}</p>\n'
    f'<p><b>Implementation status</b>: {status}</p>\n'
    f'<p><b>Estimated milestones</b>:{estimated_milestone_tables}</p>\n'
  )

def new_feature_email_html(feature):
  """Return an HTML string for new feature emails."""

  return (
    f'<p>{feature.created_by.email()} added a new feature:</p>\n'
    f'{email_header_html(feature)}\n'
    '<hr>\n'
    '<p>Next steps:</p>\n'
    '<ul>\n'
    '  <li>Try the API, write a sample, provide early feedback to eng.</li>\n'
    '  <li>Consider authoring a new article/update for /web.</li>\n'
    '  <li>Write a\n'
    '    <a href="https://github.com/GoogleChrome/lighthouse/tree/master/docs/recipes/custom-audit">\n'
    '    new Lighthouse audit</a>. This can help drive adoption of an API over time.\n'
    '  </li>\n'
    '  <li>Add a sample to https://github.com/GoogleChrome/samples (see\n'
    '    <a href="https://github.com/GoogleChrome/samples#contributing-samples">\n'
    '    contributing</a>).\n'
    '  </li>\n'
    '  <li>Add demo links and other details to the\n'
    f'    <a href="https://chromestatus.com/guide/edit/{feature.key.integer_id()}">\n'
    '    ChromeStatus feature entry</a>.\n'
    '  </li>\n'
    '</ul>\n'
  )

def update_feature_email_html(feature, changes):
  """Return an HTML string for update feature emails."""

  def formatted_changes_html(changes):
    """Return an HTML string showing the feature changes."""
    formatted_changes = ''
    for prop in changes:
      prop_name = prop['prop_name']
      new_val = prop['new_val']
      old_val = prop['old_val']

      formatted_changes += (
        f'<li><b>{prop_name}:</b> <br/>'
        f'<b>old:</b> {escape(old_val)} <br/>'
        f'<b>new:</b> {escape(new_val)} <br/></li><br/>'
      )
    return formatted_changes if formatted_changes else '<li>None</li>'

  def moz_links_html():
    """Return an HTML string for the Mozilla links."""
    moz_link_urls = [link for link in feature.doc_links
      if urllib.parse.urlparse(link).hostname == 'developer.mozilla.org']
    if moz_link_urls:
      links = ''
      for url in moz_link_urls:
        links += f'<li>{url}</li>\n'
      return (
        '<li>Review the following MDN pages and\n'
        '<a href="https://docs.google.com/document/d/10jDTZeW914ahqWfxwm9_WXJWvyAKT6EcDIlbI3w0BKY'
        '/edit#heading=h.frumfipthu7">subscribe to updates</a> for them.\n'
        '  <ul>\n'
        f'    {links}\n'
        '  </ul>\n'
        '</li>\n'
      )
    return ''

  return (
    f'<p>{feature.updated_by.email()} updated this feature:</p>\n'
    f'{email_header_html(feature)}\n'
    '<p><b>Changes:</b></p>\n'
    f'<ul>{formatted_changes_html(changes)}</ul>\n'
    '<hr>\n'
    '<p>Next steps:</p>\n'
    '<ul>\n'
    '  <li>Check existing\n'
    '    <a href="https://github.com/GoogleChrome/lighthouse/tree/master/lighthouse-core/audits">'
    '    Lighthouse audits</a> for correctness.</li>\n'
    f'{moz_links_html()}\n'
    '</ul>\n'
  )
