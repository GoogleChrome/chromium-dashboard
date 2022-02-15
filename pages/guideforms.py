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

import logging
from django import forms
from django.core.validators import validate_email

# from google.appengine.api import users
from framework import users

from internals import models
from internals import processes

class MultiEmailField(forms.Field):
    def to_python(self, value):
        """Normalize data to a list of strings."""
        # Return an empty list if no input was given.
        if not value:
            return []
        return value.split(',')

    def validate(self, value):
        """Check if value consists only of valid emails."""
        # Use the parent's handling of required fields, etc.
        super(MultiEmailField, self).validate(value)
        for email in value:
            validate_email(email.strip())

SHIPPED_HELP_TXT = (
    'First milestone to ship with this status. Applies to: Enabled by '
    'default, Browser Intervention, Deprecated and Removed.')

SHIPPED_WEBVIEW_HELP_TXT = ('First milestone to ship with this status. '
                            'Applies to Enabled by default, Browser '
                            'Intervention, Deprecated, and Removed.')

SUMMARY_PLACEHOLDER_TXT = (
  'NOTE: This text describes this feature in the eventual beta release post '
  'as well as possibly in other external documents.\n\n'
  'Begin with one line explaining what the feature does. Add one or two '
  'lines explaining how this feature helps developers. Avoid language such '
  'as "a new feature". They all are or have been new features.\n\n'
  'Follow the example link below for more guidance.')


# We define all form fields here so that they can be include in one or more
# stage-specific fields without repeating the details and help text.
ALL_FIELDS = {
    'name': forms.CharField(
        required=True, label='Feature name',
        # Use a specific autocomplete value to avoid "name" autofill.
        # https://bugs.chromium.org/p/chromium/issues/detail?id=468153#c164
        widget=forms.TextInput(attrs={'autocomplete': 'feature-name'}),
        help_text=
        ('Capitalize only the first letter and the beginnings of '
         'proper nouns. '
         '<a target="_blank" href="'
         'https://github.com/GoogleChrome/chromium-dashboard/wiki/'
         'EditingHelp#feature-name">Learn more</a>. '
         '<a target="_blank" href="'
         'https://github.com/GoogleChrome/chromium-dashboard/wiki/'
         'EditingHelp#feature-name-example">Example</a>.'
        )),

    'summary': forms.CharField(
        required=True,
        widget=forms.Textarea(
            attrs={'cols': 50, 'maxlength': 500,
                   'placeholder': SUMMARY_PLACEHOLDER_TXT}),
        help_text=
        ('<a target="_blank" href="'
         'https://github.com/GoogleChrome/chromium-dashboard/wiki/'
         'EditingHelp#summary-example">Guidelines and example</a>.'
        )),

    'owner': MultiEmailField(
        required=True, label='Contact emails',
        widget=forms.EmailInput(
            attrs={'multiple': True, 'placeholder': 'email,email'}),
        help_text=('Comma separated list of full email addresses. '
                   'Prefer @chromium.org.')),

    'category': forms.ChoiceField(
        required=False,
        help_text=('Select the most specific category. If unsure, '
                   'leave as "%s".' % models.FEATURE_CATEGORIES[models.MISC]),
        initial=models.MISC,
        choices=sorted(models.FEATURE_CATEGORIES.items(), key=lambda x: x[1])),

    'feature_type': forms.ChoiceField(
        required=False,
        help_text=('Select the feature type.'),
        initial=models.FEATURE_TYPE_INCUBATE_ID,
        choices=sorted(models.FEATURE_TYPES.items())),

    'intent_stage': forms.ChoiceField(
        required=False, label='Process stage',
        help_text='Select the appropriate process stage.',
        initial=models.INTENT_IMPLEMENT,
        choices=list(models.INTENT_STAGES.items())),

    'motivation': forms.CharField(
        label='Motivation', required=False,
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
        help_text=
        ('Explain why the web needs this change. It may be useful '
         'to describe what web developers are forced to do without '
         'it. When possible, add links to your explainer '
         'backing up your claims. '
         '<a target="_blank" href="'
         'https://github.com/GoogleChrome/chromium-dashboard/wiki/'
         'EditingHelp#motivation-example">Example</a>.'
        )),

    'deprecation_motivation': forms.CharField(  # Sets motivation DB field.
        label='Motivation', required=False,
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
        help_text=
        ('Deprecations and removals must have strong reasons, backed up '
         'by measurements.  There must be clear and actionable paths forward '
         'for developers.  Please see '
         '<a target="_blank" href="'
         'https://docs.google.com/a/chromium.org/document/d/'
         '1LdqUfUILyzM5WEcOgeAWGupQILKrZHidEXrUxevyi_Y/edit?usp=sharing'
         '">Removal guidelines</a>.'
        )),

    'doc_links': forms.CharField(
        label='Doc link(s)', required=False,
        widget=forms.Textarea(
            attrs={'rows': 4, 'cols': 50, 'maxlength': 500,
                   'placeholder': 'https://\nhttps://'}),
        help_text=('Links to design doc(s) (one URL per line), if and when '
                   'available. [This is not required to send out an Intent '
                   'to Prototype. Please update the intent thread with the '
                   'design doc when ready]. An explainer and/or design doc '
                   'is sufficient to start this process. [Note: Please '
                   'include links and data, where possible, to support any '
                   'claims.]')),

    'measurement': forms.CharField(
        label='Measurement', required=False,
        widget=forms.Textarea(
            attrs={'rows': 4, 'cols': 50, 'maxlength': 500}),
        help_text=
        ('It\'s important to measure the adoption and success of web-exposed '
         'features.  Note here what measurements you have added to track the '
         'success of this feature, such as a link to the UseCounter(s) you '
         'have set up.')),

    # 'standardization' is deprecated

    'standard_maturity': forms.ChoiceField(
        required=False, label='Standard maturity',
        choices=list(models.STANDARD_MATURITY_CHOICES.items()),
        initial=models.PROPOSAL_STD,
        help_text=('How far along is the standard that this '
                   'feature implements?')),

    'unlisted': forms.BooleanField(
      required=False, initial=False,
      help_text=('Check this box for draft features that should not appear '
                 'in the feature list. Anyone with the link will be able to '
                 'view the feature on the detail page.')),

    'spec_link': forms.URLField(
        required=False, label='Spec link',
        widget=forms.URLInput(attrs={'placeholder': 'https://'}),
        help_text=('Link to spec, if and when available.  Please update the '
                   'chromestatus.com entry and the intent thread(s) with the '
                   'spec link when available.')),

    'api_spec': forms.BooleanField(
        required=False, initial=False, label='API spec',
        help_text=('The spec document has details in a specification language '
                   'such as Web IDL, or there is an exsting MDN page.')),

    'spec_mentors': forms.EmailField(
        required=False, label='Spec mentor',
        widget=forms.EmailInput(
            attrs={'multiple': True, 'placeholder': 'email'}),
        help_text=
        ('Experienced <a target="_blank" '
         'href="https://www.chromium.org/blink/spec-mentors">'
         'spec mentors</a> are available to help you improve your '
         'feature spec.')),

    'explainer_links': forms.CharField(
        label='Explainer link(s)', required=False,
        widget=forms.Textarea(
            attrs={'rows': 4, 'cols': 50, 'maxlength': 500,
                   'placeholder': 'https://\nhttps://'}),
        help_text=('Link to explainer(s) (one URL per line). You should have '
                   'at least an explainer in hand and have shared it on a '
                   'public forum before sending an Intent to Prototype in '
                   'order to enable discussion with other browser vendors, '
                   'standards bodies, or other interested parties.')),

    'security_review_status': forms.ChoiceField(
        required=False,
        choices=list(models.REVIEW_STATUS_CHOICES.items()),
        initial=models.REVIEW_PENDING,
        help_text=('Status of the security review.')),

    'privacy_review_status': forms.ChoiceField(
        required=False,
        choices=list(models.REVIEW_STATUS_CHOICES.items()),
        initial=models.REVIEW_PENDING,
        help_text=('Status of the privacy review.')),

    'tag_review': forms.CharField(
        label='TAG Review', required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'cols': 50, 'maxlength': 1480}),
        help_text=('Link(s) to TAG review(s), or explanation why this is '
                   'not needed.')),

    'tag_review_status': forms.ChoiceField(
        required=False,
        choices=list(models.REVIEW_STATUS_CHOICES.items()),
        initial=models.REVIEW_PENDING,
        help_text=('Status of the tag review.')),

    'intent_to_implement_url': forms.URLField(
        required=False, label='Intent to Prototype link',
        widget=forms.URLInput(attrs={'placeholder': 'https://'}),
        help_text=('After you have started the "Intent to Prototype" '
                   ' discussion thread, link to it here.')),

    'intent_to_ship_url': forms.URLField(
        required=False, label='Intent to Ship link',
        widget=forms.URLInput(attrs={'placeholder': 'https://'}),
        help_text=('After you have started the "Intent to Ship" discussion '
                   'thread, link to it here.')),

    'ready_for_trial_url': forms.URLField(
        required=False, label='Ready for Trial link',
        widget=forms.URLInput(attrs={'placeholder': 'https://'}),
        help_text=('After you have started the "Ready for Trial" discussion '
                   'thread, link to it here.')),

    'intent_to_experiment_url': forms.URLField(
        required=False, label='Intent to Experiment link',
        widget=forms.URLInput(attrs={'placeholder': 'https://'}),
        help_text=('After you have started the "Intent to Experiment" '
                   ' discussion thread, link to it here.')),

    'intent_to_extend_experiment_url': forms.URLField(
        required=False, label='Intent to Extend Experiment link',
        widget=forms.URLInput(attrs={'placeholder': 'https://'}),
        help_text=('If this feature has an "Intent to Extend Experiment" '
                   ' discussion thread, link to it here.')),

    'r4dt_url': forms.URLField(  # Sets intent_to_experiment_url in DB
        required=False, label='Request for Deprecation Trial link',
        widget=forms.URLInput(attrs={'placeholder': 'https://'}),
        help_text=('After you have started the "Request for Deprecation Trial" '
                   'discussion thread, link to it here.')),

    'interop_compat_risks': forms.CharField(
        required=False, label='Interoperability and Compatibility Risks',
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
        help_text=
        ('Describe the degree of <a target="_blank" '
         'href="https://www.chromium.org/blink/guidelines/'
         'web-platform-changes-guidelines#TOC-Finding-balance'
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
         'tracking bugs, or links to online conversations. '
         '<a target="_blank" href="'
         'https://github.com/GoogleChrome/chromium-dashboard/wiki/'
         'EditingHelp#interoperability-and-compatibility-risks-example">'
         'Example</a>.'
        )),

    'safari_views': forms.ChoiceField(
        required=False, label='Safari views',
        choices=list(models.VENDOR_VIEWS_WEBKIT.items()),
        initial=models.NO_PUBLIC_SIGNALS,
        help_text=(
            'See <a target="_blank" href="https://bit.ly/blink-signals">'
            'https://bit.ly/blink-signals</a>')),

    'safari_views_link': forms.URLField(
        required=False, label='',
        widget=forms.URLInput(attrs={'placeholder': 'https://'}),
        help_text='Citation link.'),

    'safari_views_notes': forms.CharField(
        required=False, label='',
        widget=forms.Textarea(
            attrs={'rows': 2, 'cols': 50, 'placeholder': 'Notes',
                   'maxlength': 1480})),

    'ff_views': forms.ChoiceField(
        required=False, label='Firefox views',
        choices=list(models.VENDOR_VIEWS_GECKO.items()),
        initial=models.NO_PUBLIC_SIGNALS,
        help_text=(
            'See <a target="_blank" href="https://bit.ly/blink-signals">'
            'https://bit.ly/blink-signals</a>')),

    'ff_views_link': forms.URLField(
        required=False, label='',
        widget=forms.URLInput(attrs={'placeholder': 'https://'}),
        help_text='Citation link.'),

    'ff_views_notes': forms.CharField(
        required=False, label='',
        widget=forms.Textarea(
            attrs={'rows': 2, 'cols': 50, 'placeholder': 'Notes',
                   'maxlength': 1480})),

    'web_dev_views': forms.ChoiceField(
        required=False, label='Web / Framework developer views',
        choices=list(models.WEB_DEV_VIEWS.items()),
        initial=models.DEV_NO_SIGNALS,
        help_text=(
            'If unsure, default to "No signals". '
            'See <a target="_blank" href="https://goo.gle/developer-signals">'
            'https://goo.gle/developer-signals</a>')),

    'web_dev_views_link': forms.URLField(
        required=False, label='',
        widget=forms.URLInput(attrs={'placeholder': 'https://'}),
        help_text='Citation link.'),

    'web_dev_views_notes': forms.CharField(
        required=False, label='',
        widget=forms.Textarea(
            attrs={'rows': 2, 'cols': 50, 'placeholder': 'Notes',
                   'maxlength': 1480}),
        help_text=('Reference known representative examples of opinion, '
                   'both positive and negative.')),

    'other_views_notes': forms.CharField(
        required=False, label='Other views',
        widget=forms.Textarea(
            attrs={'rows': 4, 'cols': 50, 'placeholder': 'Notes',
                   'maxlength': 1480}),
        help_text=('For example, other browsers.')),

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
        widget=forms.Textarea(attrs={
            'rows': 2, 'cols': 50, 'maxlength': 1480,
            'placeholder': 'This field is deprecated',
            'disabled': 'disabled'}),
        help_text=('When does the experiment start and expire? '
                   'Deprecated: '
                   'Please use the numeric fields above instead.')),

    # TODO(jrobbins and jmedley): Refine help text.
    'ot_milestone_desktop_start': forms.IntegerField(
        required=False, label='OT desktop start',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
        help_text=('First desktop milestone that will support an origin '
                   'trial of this feature.')),

    'ot_milestone_desktop_end': forms.IntegerField(
        required=False, label='OT desktop end',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
        help_text=('Last desktop milestone that will support an origin '
                   'trial of this feature.')),

    'ot_milestone_android_start': forms.IntegerField(
        required=False, label='OT android start',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
        help_text=('First android milestone that will support an origin '
                   'trial of this feature.')),

    'ot_milestone_android_end': forms.IntegerField(
        required=False, label='OT android end',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
        help_text=('Last android milestone that will support an origin '
                   'trial of this feature.')),

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
        ('If this is a repeat experiment, explain why you want to extend this '
         'experiment.  Also, fill in discussion link fields below.')),

    'ongoing_constraints': forms.CharField(
        label='Ongoing Constraints', required=False,
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
        help_text=
        ('Do you anticipate adding any ongoing technical constraints to '
         'the codebase while implementing this feature? We prefer to avoid '
         'features which require or assume a specific architecture. '
         'For most features, the answer here is "None."')),

    'origin_trial_feedback_url': forms.URLField(
        required=False, label='Origin trial feedback summary',
        widget=forms.URLInput(attrs={'placeholder': 'https://'}),
        help_text=
        ('If your feature was available as an origin trial, link to a summary '
         'of usage and developer feedback. If not, leave this empty.')),

    'finch_url': forms.URLField(
        required=False, label='Finch experiment',
        widget=forms.URLInput(attrs={'placeholder': 'https://'}),
        help_text=
        ('If your feature will roll out gradually via a '
         '<a href="go/finch" targe="_blank">Finch experiment</a>, '
         'link to it here.')),

    'i2e_lgtms': forms.EmailField(
        required=False, label='Intent to Experiment LGTM by',
        widget=forms.EmailInput(
            attrs={'multiple': True, 'placeholder': 'email'}),
        help_text=('Full email address of API owner who LGTM\'d the '
                   'Intent to Experiment email thread.')),

    'i2s_lgtms': forms.EmailField(
        required=False, label='Intent to Ship LGTMs by',
        widget=forms.EmailInput(
            attrs={'multiple': True, 'placeholder': 'email, email, email'}),
        help_text=('Comma separated list of '
                   'full email addresses of API owners who LGTM\'d '
                   'the Intent to Ship email thread.')),

    'r4dt_lgtms': forms.EmailField(  # Sets i2e_lgtms field.
        required=False, label='Request for Deprecation Trial LGTM by',
        widget=forms.EmailInput(
            attrs={'multiple': True, 'placeholder': 'email'}),
        help_text=('Full email addresses of API owners who LGTM\'d '
                   'the Request for Deprecation Trial email thread.')),

    'debuggability': forms.CharField(
        label='Debuggability', required=True,
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
        help_text=
        ('Description of the DevTools debugging support for your feature. '
         'Please follow <a target="_blank" '
         'href="https://goo.gle/devtools-checklist">the '
         'DevTools support checklist</a> for guidance.')),

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
        label='Web Platform Tests Description', required=False,
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
        widget=forms.Textarea(
            attrs={'cols': 50, 'maxlength': 500,
                   'placeholder': 'https://\nhttps://'}),
        help_text='Links to samples (one URL per line).'),

    'non_oss_deps': forms.CharField(
        label='Non-OSS dependencies', required=False,
        widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
        help_text=
        ('Does the feature depend on any code or APIs outside the Chromium '
         'open source repository and its open-source dependencies to '
         'function? (e.g. server-side APIs, operating system APIs '
         'tailored to this feature or closed-source code bundles) '
         'Yes or no. If yes, explain why this is necessary.'
         )),

    'bug_url': forms.URLField(
        required=False, label='Tracking bug URL',
        widget=forms.URLInput(attrs={'placeholder': 'https://'}),
        help_text=
        ('Tracking bug url (https://bugs.chromium.org/...). This bug '
         'should have "Type=Feature" set and be world readable. '
         'Note: This field only accepts one URL.')),

    # TODO(jrobbins): Consider a button to file the launch bug automatically,
    # or a deep link that has some feature details filled in.
    'launch_bug_url': forms.URLField(
        required=False, label='Launch bug URL',
        widget=forms.URLInput(attrs={'placeholder': 'https://'}),
        help_text=(
            'Launch bug url (https://bugs.chromium.org/...) to track launch '
            'approvals. '
            '<a target="_blank" href="'
            'https://bugs.chromium.org/p/chromium/issues/'
            'entry?template=Chrome+Launch+Feature" '
            '>Create launch bug<a>.')),

    'initial_public_proposal_url': forms.URLField(
        required=False, label='Initial public proposal URL',
        widget=forms.URLInput(attrs={'placeholder': 'https://'}),
        help_text=(
            'Link to the first public proposal to create this feature, e.g., '
            'a WICG discourse post.')),

    'blink_components': forms.ChoiceField(
      required=False, label='Blink component',
      help_text=
      ('Select the most specific component. If unsure, leave as "%s".' %
       models.BlinkComponent.DEFAULT_COMPONENT),
      choices=[(x, x) for x in models.BlinkComponent.fetch_all_components()],
      initial=[models.BlinkComponent.DEFAULT_COMPONENT]),

    'devrel': forms.EmailField(
        required=False, label='Developer relations emails',
        widget=forms.EmailInput(
            attrs={'multiple': True, 'placeholder': 'email, email'}),
        help_text='Comma separated list of full email addresses.'),

    'impl_status_chrome': forms.ChoiceField(
        required=False, label='Implementation status',
        choices=list(models.IMPLEMENTATION_STATUS.items()),
        help_text='Implementation status in Chromium'),

    'shipped_milestone': forms.IntegerField(
        required=False, label='Chrome for desktop',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
        help_text=SHIPPED_HELP_TXT),

    'shipped_android_milestone': forms.IntegerField(
        required=False, label='Chrome for Android',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
        help_text=SHIPPED_HELP_TXT),

    'shipped_ios_milestone': forms.IntegerField(
        required=False, label='Chrome for iOS (RARE)',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
        help_text=SHIPPED_HELP_TXT),

    'shipped_webview_milestone': forms.IntegerField(
        required=False, label='Android Webview',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
        help_text=SHIPPED_WEBVIEW_HELP_TXT),

    'requires_embedder_support': forms.BooleanField(
      required=False, initial=False,
      help_text=(
          'Will this feature require support in //chrome?  '
          'That includes any code in //chrome, even if that is for '
          'functionality on top of the spec.  Other //content embedders '
          'will need to be aware of that functionality. '
          'Please add a row to this '
          '<a href="https://docs.google.com/spreadsheets/d/'
          '1QV4SW4JBG3IyLzaonohUhim7nzncwK4ioop2cgUYevw/edit#gid=0'
          '" target="_blank">tracking spreadsheet</a>.')),

    'devtrial_instructions': forms.URLField(
        required=False, label='DevTrial instructions',
        widget=forms.URLInput(attrs={'placeholder': 'https://'}),
        help_text=(
            'Link to a HOWTO or FAQ describing how developers can get started '
            'using this feature in a DevTrial.  <a target="_blank" href="'
            'https://github.com/samuelgoto/WebID/blob/master/HOWTO.md'
            '">Example 1</a>.  <a target="_blank" href="'
            'https://github.com/WICG/idle-detection/blob/main/HOWTO.md'
            '">Example 2</a>.')),

    'dt_milestone_desktop_start': forms.IntegerField(
        required=False, label='DevTrial on desktop',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
        help_text=('First milestone that allows developers to try '
                   'this feature on desktop platforms by setting a flag. '
                   'When flags are enabled by default in preparation for '
                   'removal, please use the fields in the ship stage.')),

    'dt_milestone_android_start': forms.IntegerField(
        required=False, label='DevTrial on Android',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
        help_text=('First milestone that allows developers to try '
                   'this feature on desktop platforms by setting a flag. '
                   'When flags are enabled by default in preparation for '
                   'removal, please use the fields in the ship stage.')),

    'dt_milestone_ios_start': forms.IntegerField(
        required=False, label='DevTrial on iOS (RARE)',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
        help_text=('First milestone that allows developers to try '
                   'this feature on desktop platforms by setting a flag. '
                   'When flags are enabled by default in preparation for '
                   'removal, please use the fields in the ship stage.')),

    'flag_name': forms.CharField(
        label='Flag name', required=False,
        help_text='Name of the flag that enables this feature.'),

    'prefixed': forms.BooleanField(
        required=False, initial=False, label='Prefixed?'),

    'search_tags': forms.CharField(
        label='Search tags', required=False,
        help_text='Comma separated keywords used only in search'),

    'comments': forms.CharField(
        label='Comments', required=False,
        widget=forms.Textarea(attrs={
            'cols': 50, 'rows': 4, 'maxlength': 1480}),
        help_text='Additional comments, caveats, info...'),

    }

# These are shown in a top card for all processes.
METADATA_FIELDS = [
     'name', 'summary', 'unlisted', 'owner',
     'category',
     'feature_type', 'intent_stage',
     'search_tags',
     # Implemention
     'impl_status_chrome',
     'blink_components',
     'bug_url', 'launch_bug_url',
]

def define_form_class_using_shared_fields(class_name, field_spec_list):
  """Define a new subsblass of forms.Form with the given fields, in order."""
  # field_spec_list is normally just a list of simple field names,
  # but entries can also have syntax "form_field=shared_field".
  class_dict = {'field_order': []}
  for field_spec in field_spec_list:
    form_field_name = field_spec.split('=')[0]  # first or only
    shared_field_name = field_spec.split('=')[-1] # last or only
    class_dict[form_field_name] = ALL_FIELDS[shared_field_name]
    class_dict['field_order'].append(form_field_name)

  return type(class_name, (forms.Form,), class_dict)


NewFeatureForm = define_form_class_using_shared_fields(
    'NewFeatureForm',
    ('name', 'summary',
     'unlisted', 'owner',
     'blink_components', 'category'))
    # Note: feature_type is done with custom HTML


MetadataForm = define_form_class_using_shared_fields(
    'MetadataForm', METADATA_FIELDS)


NewFeature_Incubate = define_form_class_using_shared_fields(
    'NewFeature_Incubate',
    ('motivation', 'initial_public_proposal_url', 'explainer_links',
     'bug_url', 'launch_bug_url', 'comments'))

ImplStatus_Incubate = define_form_class_using_shared_fields(
    'ImplStatus_Incubate',
    ('requires_embedder_support',
     ))


NewFeature_Prototype = define_form_class_using_shared_fields(
    'NewFeature_Prototype',
    ('spec_link', 'standard_maturity', 'api_spec', 'spec_mentors',
     'intent_to_implement_url', 'comments'))
  # TODO(jrobbins): advise user to request a tag review


Any_DevTrial = define_form_class_using_shared_fields(
    'Any_DevTrial',
    ('bug_url', 'devtrial_instructions', 'doc_links',
     'interop_compat_risks',
     'safari_views', 'safari_views_link', 'safari_views_notes',
     'ff_views', 'ff_views_link', 'ff_views_notes',
     'web_dev_views', 'web_dev_views_link', 'web_dev_views_notes',
     'other_views_notes',
     'security_review_status', 'privacy_review_status',
     'ergonomics_risks', 'activation_risks', 'security_risks', 'debuggability',
     'all_platforms', 'all_platforms_descr', 'wpt', 'wpt_descr',
     'sample_links', 'devrel', 'ready_for_trial_url', 'comments'))
  # TODO(jrobbins): api overview link


ImplStatus_DevTrial = define_form_class_using_shared_fields(
    'ImplStatus_InDevTrial',
    ('dt_milestone_desktop_start', 'dt_milestone_android_start',
     'dt_milestone_ios_start',
     'flag_name'))


NewFeature_EvalReadinessToShip = define_form_class_using_shared_fields(
    'NewFeature_EvalReadinessToShip',
    ('doc_links', 'tag_review', 'spec_link',
     'standard_maturity', 'interop_compat_risks',
     'safari_views', 'safari_views_link', 'safari_views_notes',
     'ff_views', 'ff_views_link', 'ff_views_notes',
     'web_dev_views', 'web_dev_views_link', 'web_dev_views_notes',
     'other_views_notes',
     'prefixed', 'non_oss_deps', 'comments'))


ImplStatus_AllMilestones = define_form_class_using_shared_fields(
    'ImplStatus_AllMilestones',
    ('shipped_milestone', 'shipped_android_milestone',
     'shipped_ios_milestone', 'shipped_webview_milestone'))


ImplStatus_EvalReadinessToShip = define_form_class_using_shared_fields(
    'ImplStatus_AllMilestones',
    ('shipped_milestone', 'shipped_android_milestone',
     'shipped_ios_milestone', 'shipped_webview_milestone',
     'measurement'))


NewFeature_OriginTrial = define_form_class_using_shared_fields(
    'NewFeature_OriginTrial',
    ('experiment_goals', 'experiment_risks',
     'experiment_extension_reason', 'ongoing_constraints',
     'origin_trial_feedback_url', 'intent_to_experiment_url',
     'intent_to_extend_experiment_url',
     'i2e_lgtms', 'comments'))


ImplStatus_OriginTrial = define_form_class_using_shared_fields(
    'ImplStatus_OriginTrial',
    ('ot_milestone_desktop_start', 'ot_milestone_desktop_end',
     'ot_milestone_android_start', 'ot_milestone_android_end',
     'experiment_timeline',  # deprecated
     ))


Most_PrepareToShip = define_form_class_using_shared_fields(
    'Most_PrepareToShip',
    ('tag_review', 'tag_review_status', 'non_oss_deps',
     'origin_trial_feedback_url',
     'launch_bug_url', 'intent_to_ship_url', 'i2s_lgtms', 'comments'))


Any_Ship = define_form_class_using_shared_fields(
    'Any_Ship',
    ('launch_bug_url', 'finch_url', 'comments'))


Existing_Prototype = define_form_class_using_shared_fields(
    'Existing_Prototype',
    ('owner', 'blink_components', 'motivation', 'explainer_links',
     'spec_link', 'standard_maturity', 'api_spec', 'bug_url', 'launch_bug_url',
     'intent_to_implement_url', 'comments'))


Existing_OriginTrial = define_form_class_using_shared_fields(
    'Existing_OriginTrial',
    ('experiment_goals', 'experiment_risks',
     'experiment_extension_reason', 'ongoing_constraints',
     'intent_to_experiment_url', 'intent_to_extend_experiment_url',
     'i2e_lgtms', 'origin_trial_feedback_url', 'comments'))


PSA_Implement = define_form_class_using_shared_fields(
    'Any_Implement',
    ('motivation', 'spec_link', 'standard_maturity', 'comments'))
  # TODO(jrobbins): advise user to request a tag review


PSA_PrepareToShip = define_form_class_using_shared_fields(
    'PSA_PrepareToShip',
    ('tag_review',
     'intent_to_implement_url', 'origin_trial_feedback_url',
     'launch_bug_url', 'intent_to_ship_url', 'comments'))


Deprecation_Implement = define_form_class_using_shared_fields(
    'Deprecation_Implement',
    ('motivation=deprecation_motivation',
     'spec_link', 'comments'))

# Note: Even though this is similar to another form, it is likely to change.
Deprecation_PrepareToShip = define_form_class_using_shared_fields(
    'Deprecation_PrepareToShip',
    ('impl_status_chrome', 'tag_review',
     'intent_to_implement_url', 'origin_trial_feedback_url',
     'launch_bug_url', 'comments'))


# Note: Even though this is similar to another form, it is likely to change.
Deprecation_DeprecationTrial = define_form_class_using_shared_fields(
    'Deprecation_DeprecationTrial',
    ('experiment_goals', 'experiment_risks',
     'ot_milestone_desktop_start', 'ot_milestone_desktop_end',
     'ot_milestone_android_start', 'ot_milestone_android_end',
     'experiment_timeline',  # deprecated
     'experiment_extension_reason', 'ongoing_constraints',
     'intent_to_experiment_url=r4dt_url',
     'intent_to_extend_experiment_url',
     'i2e_lgtms=r4dt_lgtms',  # form field name matches underlying DB field.
     'origin_trial_feedback_url', 'comments'))


# Note: Even though this is similar to another form, it is likely to change.
Deprecation_PrepareToShip = define_form_class_using_shared_fields(
    'Deprecation_PrepareToShip',
    ('impl_status_chrome',
     'intent_to_ship_url', 'i2s_lgtms',
     'launch_bug_url', 'comments'))


Deprecation_Removed = define_form_class_using_shared_fields(
    'Deprecation_Removed',
    ('comments',))


Flat_Metadata = define_form_class_using_shared_fields(
    'Flat_Metadata',
    (# Standardizaton
     'name', 'summary', 'unlisted', 'owner',
     'category',
     'feature_type', 'intent_stage',
     'search_tags',
     # Implementtion
     'impl_status_chrome',
     'blink_components',
     'bug_url', 'launch_bug_url',
     'comments'))


Flat_Identify = define_form_class_using_shared_fields(
    'Flat_Identify',
    (# Standardization
    # TODO(jrobbins): display deprecation_motivation instead when deprecating.
     'motivation', 'initial_public_proposal_url', 'explainer_links',

     # Implementtion
    'requires_embedder_support'))


Flat_Implement = define_form_class_using_shared_fields(
    'Flat_Implement',
    (# Standardization
     'spec_link', 'standard_maturity', 'api_spec', 'spec_mentors',
     'intent_to_implement_url'))


Flat_DevTrial = define_form_class_using_shared_fields(
    'Flat_DevTrial',
    (# Standardizaton
     'devtrial_instructions', 'doc_links',
     'interop_compat_risks',
     'safari_views', 'safari_views_link', 'safari_views_notes',
     'ff_views', 'ff_views_link', 'ff_views_notes',
     'web_dev_views', 'web_dev_views_link', 'web_dev_views_notes',
     'other_views_notes',
     'security_review_status', 'privacy_review_status',
     'ergonomics_risks', 'activation_risks', 'security_risks', 'debuggability',
     'all_platforms', 'all_platforms_descr', 'wpt', 'wpt_descr',
     'sample_links', 'devrel', 'ready_for_trial_url',

     # TODO(jrobbins): UA support signals section

     # Implementation
     'dt_milestone_desktop_start', 'dt_milestone_android_start',
     'dt_milestone_ios_start',
     'flag_name'))
  # TODO(jrobbins): api overview link


Flat_OriginTrial = define_form_class_using_shared_fields(
    'Flat_OriginTrial',
    (# Standardization
     'experiment_goals',
     'experiment_risks',
     'experiment_extension_reason', 'ongoing_constraints',
     # TODO(jrobbins): display r4dt_url instead when deprecating.
     'intent_to_experiment_url', 'intent_to_extend_experiment_url',
     'i2e_lgtms',
     'origin_trial_feedback_url',

     # Implementation
     'ot_milestone_desktop_start', 'ot_milestone_desktop_end',
     'ot_milestone_android_start', 'ot_milestone_android_end',
     'experiment_timeline',  # deprecated
    ))


Flat_PrepareToShip = define_form_class_using_shared_fields(
    'Flat_PrepareToShip',
    (# Standardization
     'tag_review', 'tag_review_status',
     'intent_to_ship_url', 'i2s_lgtms',
     # Implementation
     'measurement',
     'non_oss_deps'))


Flat_Ship = define_form_class_using_shared_fields(
    'Flat_Ship',
    (# Implementation
     'finch_url',
     'shipped_milestone', 'shipped_android_milestone',
     'shipped_ios_milestone', 'shipped_webview_milestone'))


FIELD_NAME_TO_DISPLAY_TYPE = {
    'doc_links': 'urllist',
    'explainer_links': 'urllist',
    'sample_links': 'urllist',
    # Otherwise, FIELD_TYPE_TO_DISPLAY_TYPE is used.
    }

FIELD_TYPE_TO_DISPLAY_TYPE = {
    forms.BooleanField: 'bool',
    forms.URLField: 'url',
    # choice, char, int can all render as plain text.
    }


def make_human_readable(field_name):
  return field_name.replace('_', ' ').capitalize()


def make_display_spec(field_name):
  """Return a tuple of field info that can easily be sent in JSON."""
  form_field = ALL_FIELDS[field_name]
  display_name = form_field.label or make_human_readable(field_name)
  field_type = (FIELD_NAME_TO_DISPLAY_TYPE.get(field_name) or
                FIELD_TYPE_TO_DISPLAY_TYPE.get(type(form_field)) or
                'text')
  return (field_name, display_name, field_type)


def make_display_specs(*shared_field_names):
  """Return a list of field specs for each of the fields named in the args."""
  return [make_display_spec(field_name)
          for field_name in shared_field_names]


DEPRECATED_FIELDS = ['standardization']

DISPLAY_IN_FEATURE_HIGHLIGHTS = [
    'name', 'summary',
    'motivation', 'deprecation_motivation',
    'unlisted', 'owner',
    'search_tags',
    # Implementtion
    'impl_status_chrome',
    'blink_components',
    'bug_url',
    'comments',
]

DISPLAY_FIELDS_IN_STAGES = {
    'Metadata': make_display_specs(
        'category', 'feature_type', 'intent_stage',
        ),
    models.INTENT_INCUBATE: make_display_specs(
        'initial_public_proposal_url', 'explainer_links',
        'requires_embedder_support'),
    models.INTENT_IMPLEMENT: make_display_specs(
        'spec_link', 'standard_maturity', 'api_spec', 'spec_mentors',
        'intent_to_implement_url'),
    models.INTENT_EXPERIMENT: make_display_specs(
        'devtrial_instructions', 'doc_links',
        'interop_compat_risks',
        'safari_views', 'safari_views_link', 'safari_views_notes',
        'ff_views', 'ff_views_link', 'ff_views_notes',
        'web_dev_views', 'web_dev_views_link', 'web_dev_views_notes',
        'other_views_notes',
        'security_review_status', 'privacy_review_status',
        'ergonomics_risks', 'activation_risks', 'security_risks',
        'debuggability',
        'all_platforms', 'all_platforms_descr', 'wpt', 'wpt_descr',
        'sample_links', 'devrel', 'ready_for_trial_url',
        'dt_milestone_desktop_start', 'dt_milestone_android_start',
        'dt_milestone_ios_start',
        'flag_name'),
    models.INTENT_IMPLEMENT_SHIP: make_display_specs(
        'launch_bug_url',
        'tag_review', 'tag_review_status',
        'measurement', 'prefixed', 'non_oss_deps',
        ),
    models.INTENT_EXTEND_TRIAL: make_display_specs(
        'experiment_goals', 'experiment_risks',
        'experiment_extension_reason', 'ongoing_constraints',
        'origin_trial_feedback_url', 'intent_to_experiment_url',
        'r4dt_url',
        'intent_to_extend_experiment_url',
        'i2e_lgtms', 'r4dt_lgtms',
        'ot_milestone_desktop_start', 'ot_milestone_desktop_end',
        'ot_milestone_android_start', 'ot_milestone_android_end',
        'experiment_timeline',  # Deprecated
        ),
    models.INTENT_SHIP: make_display_specs(
        'finch_url',
        'shipped_milestone', 'shipped_android_milestone',
        'shipped_ios_milestone', 'shipped_webview_milestone',
        'intent_to_ship_url', 'i2s_lgtms'),
    models.INTENT_SHIPPED: make_display_specs(
        ),
    'Misc': make_display_specs(
        ),
}
