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
import processes


SHIPPED_HELP_TXT = (
    'First milestone to ship with this status. Applies to: Enabled by '
    'default, Behind a flag, Origin trial, Browser Intervention, and '
    'Deprecated. If the flag is \'test\' rather than \'experimental\' set '
    'status to In development. If the flag is for an origin trial set status '
    'to Origin trial.')

# We define all form fields here so that they can be include in one or more
# stage-specific fields without repeating the details and help text.
ALL_FIELDS = {
    'name': forms.CharField(
        required=True, label='Feature',
        widget=forms.TextInput(attrs={'autocomplete': 'off'}),
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

    'feature_type': forms.ChoiceField(
        required=True,
        help_text=('Select the feature type.'),
        initial=models.FEATURE_TYPE_INCUBATE_ID,
        choices=sorted(models.FEATURE_TYPES.items())),

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

    'unlisted': forms.BooleanField(
      required=False, initial=False,
      help_text=('Check this box for draft features that should not appear '
                 'in the feature list. Anyone with the link will be able to '
                 'view the feature on the detail page.')),

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
         'principles of web compatibility</a>.<br>'
         '<br>'
         'Please include citation links below where possible. Examples include '
         'resolutions from relevant standards bodies (e.g. W3C working group), '
         'tracking bugs, or links to online conversations.')),

    'safari_views': forms.ChoiceField(
        label='Safari views',
        choices=models.VENDOR_VIEWS_WEBKIT.items(),
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
        choices=models.VENDOR_VIEWS_GECKO.items(),
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
        choices=models.VENDOR_VIEWS_EDGE.items(),
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

    # TODO(jrobbins): consider splitting this into start and end fields.
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

    'origin_trial_feedback_url': forms.URLField(
        required=False, label='Origin Trial feedback summary',
        help_text=
        ('If your feature was available as an Origin Trial, link to a summary '
         'of usage and developer feedback. If not, leave this empty.')),

    'debuggability': forms.CharField(
        label='Debuggability', required=False,
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
        help_text=
        ('Description of the desired DevTools debugging support for your '
         'feature. Consider emailing the '
         '<a href="https://groups.google.com/forum/?'
         'fromgroups#!forum/google-chrome-developer-tools">'
         'google-chrome-developer-tools</a> list for additional help. '
         'For new language features in V8 specifically, refer to the '
         'debugger support checklist. If your feature doesn\'t require '
         'changes to DevTools to provide a good debugging '
         'experience, feel free to leave this section empty.')),

    'all_platforms': forms.BooleanField(
        required=False, initial=False, label='Supported on all platforms?',
        help_text=
        ('Will this feature be supported on all six Blink platforms '
         '(Windows, Mac, Linux, Chrome OS, Android, and Android WebView)?')),

    'all_platforms_descr': forms.CharField(
        label='Platform Support Explanation', required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'cols': 50, 'maxlength': 2000}),
        help_text=
        ('Explain why this feature is, or is not, '
         'supported on all platforms.')),

    'wpt': forms.BooleanField(
        required=False, initial=False, label='Web Platform Tests',
        help_text='Is this feature fully tested in Web Platform Tests?'),

    'wpt_descr': forms.CharField(
        label='Web Platform Tests Description', required=True,
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
        help_text=
        ('Please link to the <a href="https://wpt.fyi/results">results on '
         'wpt.fyi</a>. If any part of the feature is not tested by '
         'web-platform-tests. Please include links to issues, e.g. a '
         'web-platform-tests issue with the "infra" label explaining why a '
         'certain thing cannot be tested (<a '
         'href="https://github.com/w3c/web-platform-tests/issues/3867">'
         'example</a>), a spec issue for some change that would make it '
         'possible to test. (<a href="'
         'https://github.com/whatwg/fullscreen/issues/70">example</a>), or '
         'a Chromium issue to upstream some existing tests (<a href="'
         'https://bugs.chromium.org/p/chromium/issues/detail?id=695486">'
         'example</a>).')),

    'sample_links': forms.CharField(
        label='Samples links', required=False,
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 500}),
        help_text='Links to samples (one URL per line).'),

    'bug_url': forms.URLField(
        required=False, label='Tracking bug URL',
        help_text=
        ('Tracking bug url (https://bugs.chromium.org/...). This bug '
         'should have "Type=Feature" set and be world readable. '
         'Note: This field only accepts one URL.')),

    # TODO(jrobbins): Consider a button to file the launch bug automatically,
    # or a deep link that has some feature details filled in.
    'launch_bug_url': forms.URLField(
        required=False, label='Launch bug URL',
        help_text=(
            'Launch bug url (https://bugs.chromium.org/...) to track launch '
            'aprpovals. '
          '<a href="https://bugs.chromium.org/p/chromium/issues/entry?template=Chrome+Launch+Feature" '
          'target="_blank" '
          '>Create launch bug<a>')),

    'initial_public_proposal_url': forms.URLField(
      required=False, label='Initial public proposal URL',
      help_text=(
          'Link to the first public proposal to create this feature, e.g., '
          'a WICG discourse post.')),

    'blink_components': forms.ChoiceField(
      required=True,
      label='Blink component',
      help_text=
      ('Select the most specific component. If unsure, leave as "%s".' %
       models.BlinkComponent.DEFAULT_COMPONENT),
      choices=[(x, x) for x in models.BlinkComponent.fetch_all_components()],
      initial=[models.BlinkComponent.DEFAULT_COMPONENT]),

    'devrel': forms.CharField(
        required=False, label='Developer relations emails',
        help_text='Comma separated list of full email addresses.'),

    'impl_status_chrome': forms.ChoiceField(
        required=True, label='Status in Chromium',
        choices=models.IMPLEMENTATION_STATUS.items()),

    'shipped_milestone': forms.IntegerField(
        required=False, label='',
        help_text='Desktop:<br/>' + SHIPPED_HELP_TXT),

    'shipped_android_milestone': forms.IntegerField(
        required=False, label='',
        help_text='Chrome for Android:</br/>' + SHIPPED_HELP_TXT),

    'shipped_ios_milestone': forms.IntegerField(
        required=False, label='',
        help_text='Chrome for iOS (RARE):<br/>' + SHIPPED_HELP_TXT),

    'shipped_webview_milestone': forms.IntegerField(
        required=False, label='',
        help_text='Android WebView:<br/>' + SHIPPED_HELP_TXT),

    'prefixed': forms.BooleanField(
        required=False, initial=False, label='Prefixed?'),

    'footprint': forms.ChoiceField(
        label='Technical footprint',
        choices=models.FOOTPRINT_CHOICES.items(),
        initial=models.MAJOR_MINOR_NEW_API),

    'search_tags': forms.CharField(
        label='Search tags', required=False,
        help_text='Comma separated keywords used only in search'),

    'comments': forms.CharField(
        label='Comments', required=False,
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
        help_text='Additional comments, caveats, info...'),

    }


class NewFeatureForm(forms.Form):

  field_order = (
      'name', 'summary', 'category', 'unlisted', 'owner', 'feature_type',
      'blink_components')
  name = ALL_FIELDS['name']
  summary = ALL_FIELDS['summary']
  category = ALL_FIELDS['category']
  unlisted = ALL_FIELDS['unlisted']
  current_user_email = users.get_current_user().email if users.get_current_user() else None
  owner = forms.CharField(
      initial=current_user_email, required=True, label='Contact emails',
      help_text=('Comma separated list of full email addresses. '
                 'Prefer @chromium.org.'))
  # Note: feature_type is done with custom HTML
  blink_components = ALL_FIELDS['blink_components']


class MetadataForm(forms.Form):

  field_order = (
      'name', 'summary', 'category', 'unlisted', 'owner', 'feature_type',
      'intent_stage', 'blink_components', 'bug_url', 'launch_bug_url',
      'impl_status_chrome', 'search_tags')
  name = ALL_FIELDS['name']
  summary = ALL_FIELDS['summary']
  category = ALL_FIELDS['category']
  unlisted = ALL_FIELDS['unlisted']
  owner = forms.CharField(
      required=False,
      label='Contact emails',
      help_text=('Comma separated list of full email addresses. '
                 'Prefer @chromium.org.'))
  feature_type = ALL_FIELDS['feature_type']
  intent_stage = forms.ChoiceField(
      required=True, label='Feature stage',
      help_text='Select the appropriate process stage.',
      initial=models.INTENT_IMPLEMENT,
      choices=models.INTENT_STAGES.items())
  blink_components = ALL_FIELDS['blink_components']
  bug_url = ALL_FIELDS['bug_url']
  launch_bug_url = ALL_FIELDS['launch_bug_url']
  impl_status_chrome = ALL_FIELDS['impl_status_chrome']
  search_tags = ALL_FIELDS['search_tags']


class NewFeature_Incubate(forms.Form):

  field_order = (
      'motivation', 'initial_public_proposal_url', 'explainer_links',
      'owner', 'blink_components', 'footprint',
      'bug_url', 'launch_bug_url', 'comments')
  motivation = ALL_FIELDS['motivation']
  initial_public_proposal_url = ALL_FIELDS['initial_public_proposal_url']
  explainer_links = ALL_FIELDS['explainer_links']
  current_user_email = users.get_current_user().email if users.get_current_user() else None
  owner = forms.CharField(
      initial=current_user_email, required=True, label='Contact emails',
      help_text=('Comma separated list of full email addresses. '
                 'Prefer @chromium.org.'))
  blink_components = ALL_FIELDS['blink_components']
  footprint = ALL_FIELDS['footprint']
  bug_url = ALL_FIELDS['bug_url']
  launch_bug_url = ALL_FIELDS['launch_bug_url']
  comments = ALL_FIELDS['comments']


class NewFeature_Prototype(forms.Form):

  field_order = (
      'spec_link', 'comments')
  initial_public_proposal_url = ALL_FIELDS['initial_public_proposal_url']
  # TODO(jrobbins): advise user to request a tag review
  spec_link = ALL_FIELDS['spec_link']
  # TODO(jrobbins): action to generate Intent to Prototype email
  comments = ALL_FIELDS['comments']


class Any_DevTrial(forms.Form):
  field_order = (
      'bug_url', 'doc_links', 'spec_link', 'intent_to_implement_url',
      'interop_compat_risks',
      'safari_views', 'safari_views_link', 'safari_views_notes',
      'ff_views', 'ff_views_link', 'ff_views_notes',
      'ie_views', 'ie_views_link', 'ie_views_notes',
      'web_dev_views', 'web_dev_views_link', 'web_dev_views_notes',
      'ergonomics_risks', 'activation_risks', 'security_risks', 'debuggability',
      'all_platforms', 'all_platforms_descr', 'wpt', 'wpt_descr',
      'sample_links', 'devrel', 'comments')

  bug_url = ALL_FIELDS['bug_url']
  doc_links = ALL_FIELDS['doc_links']
  # TODO(jrobbins): api overview link
  spec_link = ALL_FIELDS['spec_link']

  intent_to_implement_url = ALL_FIELDS['intent_to_implement_url']
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
  web_dev_views_notes = ALL_FIELDS['web_dev_views_notes']

  ergonomics_risks = ALL_FIELDS['ergonomics_risks']
  activation_risks = ALL_FIELDS['activation_risks']
  security_risks = ALL_FIELDS['security_risks']
  # TODO(jrobbins): request security and privacy reviews
  debuggability = ALL_FIELDS['debuggability']
  all_platforms = ALL_FIELDS['all_platforms']
  all_platforms_descr = ALL_FIELDS['all_platforms_descr']
  wpt = ALL_FIELDS['wpt']
  wpt_descr = ALL_FIELDS['wpt_descr']
  sample_links = ALL_FIELDS['sample_links']
  devrel = ALL_FIELDS['devrel']
  # TODO(jrobbins): generate ready for trial email
  comments = ALL_FIELDS['comments']


class NewFeature_EvalReadinessToShip(forms.Form):

  field_order = (
      'doc_links', 'tag_review', 'spec_link', 'interop_compat_risks',
      'safari_views', 'safari_views_link', 'safari_views_notes',
      'ff_views', 'ff_views_link', 'ff_views_notes',
      'ie_views', 'ie_views_link', 'ie_views_notes',
      'web_dev_views', 'web_dev_views_link', 'web_dev_views_notes',
      'shipped_milestone', 'shipped_android_milestone', 'shipped_ios_milestone',
      'shipped_webview_milestone', 'prefixed', 'comments')
  doc_links = ALL_FIELDS['doc_links']
  tag_review = ALL_FIELDS['tag_review']
  spec_link = ALL_FIELDS['spec_link']

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
  web_dev_views_notes = ALL_FIELDS['web_dev_views_notes']

  # TODO(jrobbins): ready to ship email URL
  shipped_milestone = ALL_FIELDS['shipped_milestone']
  shipped_android_milestone = ALL_FIELDS['shipped_android_milestone']
  shipped_ios_milestone = ALL_FIELDS['shipped_ios_milestone']
  shipped_webview_milestone = ALL_FIELDS['shipped_webview_milestone']
  prefixed = ALL_FIELDS['prefixed']
  comments = ALL_FIELDS['comments']


class NewFeature_OriginTrial(forms.Form):

  field_order = (
      'experiment_goals', 'experiment_timeline', 'experiment_risks',
      'experiment_extension_reason', 'ongoing_constraints',
      'origin_trial_feedback_url', 'comments')
  experiment_goals = ALL_FIELDS['experiment_goals']
  experiment_timeline = ALL_FIELDS['experiment_timeline']
  experiment_risks = ALL_FIELDS['experiment_risks']
  experiment_extension_reason = ALL_FIELDS['experiment_extension_reason']
  ongoing_constraints = ALL_FIELDS['ongoing_constraints']
  origin_trial_feedback_url = ALL_FIELDS['origin_trial_feedback_url'] # optional
  # TODO(jrobbins): action to generate intent to experiement email
  comments = ALL_FIELDS['comments']


class Any_PrepareToShip(forms.Form):

  field_order = (
      'impl_status_chrome', 'footprint', 'tag_review',
      'intent_to_implement_url', 'origin_trial_feedback_url',
      'launch_bug_url', 'comments')
  impl_status_chrome = ALL_FIELDS['impl_status_chrome']
  footprint = ALL_FIELDS['footprint']
  tag_review = ALL_FIELDS['tag_review']
  intent_to_implement_url = ALL_FIELDS['intent_to_implement_url']
  origin_trial_feedback_url = ALL_FIELDS['origin_trial_feedback_url'] # optional
  launch_bug_url = ALL_FIELDS['launch_bug_url']
  comments = ALL_FIELDS['comments']


class Any_Identify(forms.Form):

  field_order = (
      'owner', 'blink_components', 'motivation', 'explainer_links',
      'footprint', 'bug_url', 'launch_bug_url', 'comments')
  current_user_email = users.get_current_user().email if users.get_current_user() else None
  owner = forms.CharField(
      initial=current_user_email, required=True, label='Contact emails',
      help_text=('Comma separated list of full email addresses. '
                 'Prefer @chromium.org.'))
  blink_components = ALL_FIELDS['blink_components']

  motivation = ALL_FIELDS['motivation']
  explainer_links = ALL_FIELDS['explainer_links']
  footprint = ALL_FIELDS['footprint']
  bug_url = ALL_FIELDS['bug_url']
  launch_bug_url = ALL_FIELDS['launch_bug_url']
  comments = ALL_FIELDS['comments']


class Any_Implement(forms.Form):

  field_order = (
      'spec_link', 'comments')
  # TODO(jrobbins): advise user to request a tag review
  spec_link = ALL_FIELDS['spec_link']
  # TODO(jrobbins): action to generate Intent to Prototype email
  comments = ALL_FIELDS['comments']


class Existing_OriginTrial(forms.Form):

  field_order = (
      'experiment_goals', 'experiment_timeline', 'experiment_risks',
      'experiment_extension_reason', 'ongoing_constraints',
      'origin_trial_feedback_url', 'comments')
  experiment_goals = ALL_FIELDS['experiment_goals']
  experiment_timeline = ALL_FIELDS['experiment_timeline']
  experiment_risks = ALL_FIELDS['experiment_risks']
  experiment_extension_reason = ALL_FIELDS['experiment_extension_reason']
  ongoing_constraints = ALL_FIELDS['ongoing_constraints']
  origin_trial_feedback_url = ALL_FIELDS['origin_trial_feedback_url'] # optional
  # TODO(jrobbins): action to generate intent to experiement email
  comments = ALL_FIELDS['comments']


# Note: Even though this is similar to another form, it is likely to change.
class Deprecation_PrepareToShip(forms.Form):

  field_order = (
      'impl_status_chrome', 'footprint', 'tag_review',
      'intent_to_implement_url', 'origin_trial_feedback_url',
      'launch_bug_url', 'comments')
  impl_status_chrome = ALL_FIELDS['impl_status_chrome']
  footprint = ALL_FIELDS['footprint']
  tag_review = ALL_FIELDS['tag_review']
  intent_to_implement_url = ALL_FIELDS['intent_to_implement_url']
  origin_trial_feedback_url = ALL_FIELDS['origin_trial_feedback_url'] # optional
  launch_bug_url = ALL_FIELDS['launch_bug_url']
  comments = ALL_FIELDS['comments']


# Note: Even though this is similar to another form, it is likely to change.
class Deprecation_DeprecationTrial(forms.Form):

  field_order = (
      'experiment_goals', 'experiment_timeline', 'experiment_risks',
      'experiment_extension_reason', 'ongoing_constraints',
      'origin_trial_feedback_url', 'comments')
  experiment_goals = ALL_FIELDS['experiment_goals']
  experiment_timeline = ALL_FIELDS['experiment_timeline']
  experiment_risks = ALL_FIELDS['experiment_risks']
  experiment_extension_reason = ALL_FIELDS['experiment_extension_reason']
  ongoing_constraints = ALL_FIELDS['ongoing_constraints']
  origin_trial_feedback_url = ALL_FIELDS['origin_trial_feedback_url'] # optional
  comments = ALL_FIELDS['comments']

class Deprecation_Removed(forms.Form):
  comments = ALL_FIELDS['comments']
