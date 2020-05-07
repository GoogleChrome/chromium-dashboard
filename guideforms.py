from __future__ import division
from __future__ import print_function

# -*- coding: utf-8 -*-
# Copyright 2020 Google Inc.
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

from django import forms

from google.appengine.api import users

import models


# We define all form fields here so that they can be include in one or more
# stage-specific fields without repeating the details and help text.
ALL_FIELDS = {
    'name': forms.CharField(
        required=True, label='Feature',
        help_text=('Capitalize only the first letter and the beginnings of '
                   'proper nouns.')),

    'summary': forms.CharField(
        label='', required=True,
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 500}),
        help_text=('Provide a one sentence description followed by one or '
                   'two lines explaining how this feature helps web '
                   'developers.')),

    'category': forms.ChoiceField(
        required=True,
        help_text=('Select the most specific category. If unsure, '
                   'leave as "%s".' % models.FEATURE_CATEGORIES[models.MISC]),
        initial=models.MISC,
        choices=sorted(models.FEATURE_CATEGORIES.items(), key=lambda x: x[1])),

    'motivation': forms.CharField(
        label='Motivation', required=True,
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
        help_text=('Explain why the web needs this change.  It may be useful '
                   'to describe what web developers are forced to do without '
                   'it. When possible, include links to back up your claims '
                   'in the explainer.')),

    'doc_links': forms.CharField(
        label='Doc link(s)', required=False,
        widget=forms.Textarea(
            attrs={'rows': 4, 'cols': 50, 'maxlength': 500}),
        help_text=('Links to design doc(s) (one URL per line), if and when '
                   'available. [This is not required to send out an Intent '
                   'to Prototype. Please update the intent thread with the '
                   'design doc when ready]. An explainer and/or design doc '
                   'is sufficient to start this process. [Note: Please '
                   'include links and data, where possible, to support any '
                   'claims.]')),

    'standardization': forms.ChoiceField(
        label='Standardization', choices=models.STANDARDIZATION.items(),
        initial=models.EDITORS_DRAFT,
        help_text=("The standardization status of the API. In bodies that don't "
                   "use this nomenclature, use the closest equivalent.")),

    'spec_link': forms.URLField(
        required=False, label='Spec link',
        help_text=('Link to spec, if and when available.  Please update the '
                   'chromestatus.com entry and the intent thread(s) with the '
                   'spec link when available.')),

    'explainer_links': forms.CharField(
        label='Explainer link(s)', required=False,
        widget=forms.Textarea(attrs={'rows': 4, 'cols': 50, 'maxlength': 500}),
        help_text=('Link to explainer(s) (one URL per line). You should have '
                   'at least an explainer in hand and have shared it on a '
                   'public forum before sending an Intent to Prototype in '
                   'order to enable discussion with other browser vendors, '
                   'standards bodies, or other interested parties.')),

    'tag_review': forms.CharField(
        label='TAG Review', required=True,
        widget=forms.Textarea(attrs={'rows': 2, 'cols': 50, 'maxlength': 1480}),
        help_text=('Link(s) to TAG review(s), or explanation why this is '
                   'not needed.')),

    'intent_to_implement_url': forms.URLField(
        required=False, label='Intent to Prototype link',
        help_text='Link to the "Intent to Prototype" discussion thread.'),

    'interop_compat_risks': forms.CharField(
        label='Interoperability and Compatibility Risks', required=True,
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
        help_text=
        ('Describe the degree of <a target="_blank" '
         'href="https://sites.google.com/a/chromium.org/dev/blink?'
         'pli=1#TOC-Policy-for-shipping-and-removing-web-platform-API-features'
         '">interoperability risk</a>. For a new feature, the main risk is '
         'that it fails to become an interoperable part of the web platform '
         'if other browsers do not implement it. For a removal, please review '
         'our <a target="_blank" href="'
         'https://docs.google.com/document/d/'
         '1RC-pBBvsazYfCNNUSkPqAVpSpNJ96U8trhNkfV0v9fk/edit">'
         'principles of web compatibility</a>.')),

    'safari_views': forms.ChoiceField(
        label='Safari views',
        choices=models.VENDOR_VIEWS.items(),
        initial=models.NO_PUBLIC_SIGNALS),

    'safari_views_link': forms.URLField(
        required=False, label='',
        help_text='Citation link.'),

    'safari_views_notes': forms.CharField(
        required=False, label='',
        widget=forms.Textarea(
            attrs={'rows': 2, 'cols': 50, 'placeholder': 'Notes',
                   'maxlength': 1480})),

    'ff_views': forms.ChoiceField(
        label='Firefox views',
        choices=models.VENDOR_VIEWS.items(),
        initial=models.NO_PUBLIC_SIGNALS),

    'ff_views_link': forms.URLField(
        required=False, label='',
        help_text='Citation link.'),

    'ff_views_notes': forms.CharField(
        required=False, label='',
        widget=forms.Textarea(
            attrs={'rows': 2, 'cols': 50, 'placeholder': 'Notes',
                   'maxlength': 1480})),

    'ie_views': forms.ChoiceField(
        label='Edge',
        choices=models.VENDOR_VIEWS.items(),
        initial=models.NO_PUBLIC_SIGNALS),

    'ie_views_link': forms.URLField(
        required=False, label='',
        help_text='Citation link.'),

    'ie_views_notes': forms.CharField(
        required=False, label='',
        widget=forms.Textarea(
            attrs={'rows': 2, 'cols': 50, 'placeholder': 'Notes',
                   'maxlength': 1480})),

    'web_dev_views': forms.ChoiceField(
        label='Web / Framework developer views',
        choices=models.WEB_DEV_VIEWS.items(),
        initial=models.DEV_NO_SIGNALS,
        help_text='If unsure, default to "No signals".'),

    'web_dev_views_link': forms.URLField(
        required=False, label='',
        help_text='Citation link.'),

    'web_dev_views_notes': forms.CharField(
        required=False, label='',
        widget=forms.Textarea(
            attrs={'rows': 2, 'cols': 50, 'placeholder': 'Notes',
                   'maxlength': 1480}),
        help_text=('Reference known representative examples of opinion, '
                   'both positive and negative.')),

    'ergonomics_risks': forms.CharField(
        label='Ergonomics Risks', required=False,
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
        help_text=
        ('Are there any other platform APIs this feature will frequently be '
         'used in tandem with? Could the default usage of this API make it '
         'hard for Chrome to maintain good performance (i.e. synchronous '
         'return, must run on a certain thread, guaranteed return timing)?')),

    'activation_risks': forms.CharField(
        label='Activation Risks', required=False,
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
        help_text=
        ('Will it be challenging for developers to take advantage of this '
         'feature immediately, as-is? Would this feature benefit from '
         'having polyfills, significant documentation and outreach, and/or '
         'libraries built on top of it to make it easier to use?')),

    'security_risks': forms.CharField(
        label='Security Risks', required=False,
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
        help_text=
        ('List any security considerations that were taken into account '
         'when deigning this feature.')),

    'experiment_goals': forms.CharField(
        label='Experiment Goals', required=False,
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
        help_text=
        ('Which pieces of the API surface are you looking to gain insight on? '
         'What metrics/measurement/feedback will you be using to validate '
         'designs? Double check that your experiment makes sense given that '
         'a large developer (e.g. a Google product or Facebook) likely '
         'can\'t use it in production due to the limits enforced by origin '
         'trials.\n\nIf Intent to Extend Origin Trial, highlight new/different '
         'areas for experimentation. Should not be an exact copy of goals '
         'from the first Intent to Experiment.')),

    'experiment_timeline': forms.CharField(
        label='Experiment Timeline', required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'cols': 50, 'maxlength': 1480}),
        help_text='When does the experiment start and expire?'),

    'experiment_risks': forms.CharField(
        label='Experiment Risks', required=False,
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
        help_text=
        ('When this experiment comes to an end are there any risks to the '
         'sites that were using it, for example losing access to important '
         'storage due to an experimental storage API?')),

    'experiment_extension_reason': forms.CharField(
        label='Experiment Extension Reason', required=False,
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
        help_text=
        ('If this is a repeat experiment, link to the previous Intent to '
         'Experiment thread and explain why you want to extend this '
         'experiment.')),

    'ongoing_constraints': forms.CharField(
        label='Ongoing Constraints', required=False,
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
        help_text=
        ('Do you anticipate adding any ongoing technical constraints to '
         'the codebase while implementing this feature? We prefer to avoid '
         'features which require or assume a specific architecture. '
         'For most features, the answer here is "None."')),

    }


class OverviewForm(forms.Form):

  name = ALL_FIELDS['name']
  summary = ALL_FIELDS['summary']
  category = ALL_FIELDS['category']


class Incubate(forms.Form):

  current_user_email = users.get_current_user().email if users.get_current_user() else None
  owner = forms.CharField(
      initial=current_user_email, required=True, label='Contact emails',
      help_text=('Comma separated list of full email addresses. '
                 'Prefer @chromium.org.'))

  motivation = ALL_FIELDS['motivation']
  doc_links = ALL_FIELDS['doc_links']
  standardization = ALL_FIELDS['standardization']
  spec_link = ALL_FIELDS['spec_link']


class Prototype(forms.Form):

  doc_links = ALL_FIELDS['doc_links']
  standardization = ALL_FIELDS['standardization']
  spec_link = ALL_FIELDS['spec_link']
  tag_review = ALL_FIELDS['tag_review']
  intent_to_implement_url = ALL_FIELDS['intent_to_implement_url']


class DevTrial(forms.Form):

  interop_compat_risks = ALL_FIELDS['interop_compat_risks']

  safari_views = ALL_FIELDS['safari_views']
  safari_views_link = ALL_FIELDS['safari_views_link']
  safari_views_notes = ALL_FIELDS['safari_views_notes']

  ff_views = ALL_FIELDS['ff_views']
  ff_views_link = ALL_FIELDS['ff_views_link']
  ff_views_notes = ALL_FIELDS['ff_views_notes']

  ie_views = ALL_FIELDS['ie_views']
  ie_views_link = ALL_FIELDS['ie_views_link']
  ie_views_notes = ALL_FIELDS['ie_views_notes']

  web_dev_views = ALL_FIELDS['web_dev_views']
  web_dev_views_link = ALL_FIELDS['web_dev_views_link']

  ergonomics_risks = ALL_FIELDS['ergonomics_risks']
  activation_risks = ALL_FIELDS['activation_risks']
  security_risks = ALL_FIELDS['security_risks']


class OriginTrial(forms.Form):

  experiment_goals = ALL_FIELDS['experiment_goals']
  experiment_timeline = ALL_FIELDS['experiment_timeline']
  experiment_risks = ALL_FIELDS['experiment_risks']
  experiment_extension_reason = ALL_FIELDS['experiment_extension_reason']
  ongoing_constraints = ALL_FIELDS['ongoing_constraints']
