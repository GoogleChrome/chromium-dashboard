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
import re

from django import forms
from django.forms.widgets import Textarea, Input
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

# from google.appengine.api import users
from framework import users

from internals import models
from internals import processes


# This is the longest string that a cloud ndb StringProperty seems to accept.
# Fields that accept a URL list can be longer, provided that each individual
# URL is no more than this length.
MAX_LENGTH = 1400


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


def validate_url(value):
    """Check that the value matches the single URL regex, ignoring whitespace before and after."""
    if (re.match(URL_REGEX, value.strip())):
        pass
    else:
        raise ValidationError('Invalid URL', code=None, params={'value': value})


class MultiUrlField(forms.Field):
    def to_python(self, value):
        """Normalize data to a list of strings."""
        # Return an empty list if no input was given.
        if not value:
            return []
        return value.split(r'\s+')

    def validate(self, value):
        """Check if value consists only of valid urls."""
        # Use the parent's handling of required fields, etc.
        super(MultiUrlField, self).validate(value)
        for url in value:
            validate_url(url.strip())

class ChromedashTextInput(forms.widgets.Input):
    template_name = 'django/forms/widgets/text.html'


class ChromedashTextarea(forms.widgets.Textarea):
    template_name = 'django/forms/widgets/chromedash-textarea.html'

    def __init__(self, attrs=None):
        # Use slightly better defaults than HTML's 20x2 box
        default_attrs = {'cols': 50, 'rows': 10,  'maxlength': MAX_LENGTH}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


SHIPPED_HELP_TXT = (
    'First milestone to ship with this status. Applies to: Enabled by '
    'default, Browser Intervention, Deprecated and Removed.')

SHIPPED_WEBVIEW_HELP_TXT = ('First milestone to ship with this status. '
                            'Applies to Enabled by default, Browser '
                            'Intervention, Deprecated, and Removed.')

# Patterns from https://www.oreilly.com/library/view/regular-expressions-cookbook/9781449327453/ch04s01.html
# Removing single quote ('), backtick (`), and pipe (|) since they are risky unless properly escaped everywhere.
# Also removing ! and % because they have special meaning for some older email routing systems.
USER_REGEX = '[A-Za-z0-9_#$&*+/=?{}~^.-]+'
DOMAIN_REGEX = r"(([A-Za-z0-9-]+\.)+[A-Za-z]{2,6})"

EMAIL_ADDRESS_REGEX = USER_REGEX + '@' + DOMAIN_REGEX
EMAIL_ADDRESSES_REGEX = EMAIL_ADDRESS_REGEX + '([ ]*,[ ]*' + EMAIL_ADDRESS_REGEX + ')*'

MULTI_EMAIL_FIELD_ATTRS = {
    'title':"Enter one or more comma-separated complete email addresses.",
    # Don't specify type="email" because browsers consider multiple emails
    # invalid, regardles of the multiple attribute.
    'type': 'text',
    'multiple': True,
    'placeholder': 'user1@domain.com, user2@chromium.org',
    'pattern': EMAIL_ADDRESSES_REGEX
}

# Simple http URLs
PORTNUM_REGEX = "(:[0-9]+)?"
URL_REGEX = "(https?)://" + DOMAIN_REGEX + PORTNUM_REGEX + r"(/[^\s]*)?"
URL_PADDED_REGEX = r"\s*" + URL_REGEX + r"\s*"

URL_FIELD_ATTRS = {
    'title': 'Enter a full URL https://...',
    'placeholder': 'https://...',
    'pattern': URL_PADDED_REGEX
}

MULTI_URL_FIELD_ATTRS = {
    'title': 'Enter one or more full URLs, one per line:\nhttps://...\nhttps://...',
    'multiple': True,
    'placeholder': 'https://...\nhttps://...',
    'rows': 4, 'cols': 50, 'maxlength': 5000,
    'chromedash_single_pattern': URL_REGEX,
    'chromedash_split_pattern': r"\s+"
}

# We define all form fields here so that they can be include in one or more
# stage-specific fields without repeating the details and help text.
ALL_FIELDS = {
    'name': forms.CharField(
        required=True, label='Feature name',
        widget=ChromedashTextInput()),

    'summary': forms.CharField(
        required=True,
        widget=ChromedashTextarea()),

    'owner': MultiEmailField(
        required=True, label='Feature owners',
        widget=forms.EmailInput(attrs=MULTI_EMAIL_FIELD_ATTRS)),

    'editors': MultiEmailField(
        required=False, label='Feature editors',
        widget=forms.EmailInput(attrs=MULTI_EMAIL_FIELD_ATTRS)),

    'category': forms.ChoiceField(
        required=False,
        initial=models.MISC,
        choices=sorted(models.FEATURE_CATEGORIES.items(), key=lambda x: x[1])),

    'feature_type': forms.ChoiceField(
        required=False,
        initial=models.FEATURE_TYPE_INCUBATE_ID,
        choices=sorted(models.FEATURE_TYPES.items())),

    'intent_stage': forms.ChoiceField(
        required=False, label='Process stage',
        initial=models.INTENT_IMPLEMENT,
        choices=list(models.INTENT_STAGES.items())),

    'motivation': forms.CharField(
        label='Motivation', required=False,
        widget=ChromedashTextarea()),

    'deprecation_motivation': forms.CharField(  # Sets motivation DB field.
        label='Motivation', required=False,
        widget=ChromedashTextarea()),

    'doc_links': MultiUrlField(
        label='Doc link(s)', required=False,
        widget=ChromedashTextarea(attrs=MULTI_URL_FIELD_ATTRS)),

    'measurement': forms.CharField(
        label='Measurement', required=False,
        widget=ChromedashTextarea(attrs={'rows': 4})),

    # 'standardization' is deprecated

    'standard_maturity': forms.ChoiceField(
        required=False, label='Standard maturity',
        choices=list(models.STANDARD_MATURITY_CHOICES.items()),
        initial=models.PROPOSAL_STD),

    'unlisted': forms.BooleanField(
      label="Unlisted",
      widget=forms.CheckboxInput(attrs={'label': "Unlisted"}),
      required=False, initial=False),

    'spec_link': forms.URLField(
        required=False, label='Spec link',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    'api_spec': forms.BooleanField(
        label='API spec',
        widget=forms.CheckboxInput(attrs={'label': "API spec"}),
        required=False, initial=False),

    'spec_mentors': MultiEmailField(
        required=False, label='Spec mentor',
        widget=forms.EmailInput(attrs=MULTI_EMAIL_FIELD_ATTRS)),

    'explainer_links': MultiUrlField(
        label='Explainer link(s)', required=False,
        widget=ChromedashTextarea(attrs=MULTI_URL_FIELD_ATTRS)),

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
        widget=ChromedashTextarea(attrs={'rows': 2}),
        help_text=('Link(s) to TAG review(s), or explanation why this is '
                   'not needed.')),

    'tag_review_status': forms.ChoiceField(
        required=False,
        choices=list(models.REVIEW_STATUS_CHOICES.items()),
        initial=models.REVIEW_PENDING,
        help_text=('Status of the tag review.')),

    'intent_to_implement_url': forms.URLField(
        required=False, label='Intent to Prototype link',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    'intent_to_ship_url': forms.URLField(
        required=False, label='Intent to Ship link',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS),
        help_text=('After you have started the "Intent to Ship" discussion '
                   'thread, link to it here.')),

    'ready_for_trial_url': forms.URLField(
        required=False, label='Ready for Trial link',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS),
        help_text=('After you have started the "Ready for Trial" discussion '
                   'thread, link to it here.')),

    'intent_to_experiment_url': forms.URLField(
        required=False, label='Intent to Experiment link',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS),
        help_text=('After you have started the "Intent to Experiment" '
                   ' discussion thread, link to it here.')),

    'intent_to_extend_experiment_url': forms.URLField(
        required=False, label='Intent to Extend Experiment link',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS),
        help_text=('If this feature has an "Intent to Extend Experiment" '
                   ' discussion thread, link to it here.')),

    'r4dt_url': forms.URLField(  # Sets intent_to_experiment_url in DB
        required=False, label='Request for Deprecation Trial link',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS),
        help_text=('After you have started the "Request for Deprecation Trial" '
                   'discussion thread, link to it here.')),

    'interop_compat_risks': forms.CharField(
        required=False, label='Interoperability and Compatibility Risks',
        widget=ChromedashTextarea(),
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
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS),
        help_text='Citation link.'),

    'safari_views_notes': forms.CharField(
        required=False, label='',
        widget=ChromedashTextarea(
            attrs={'rows': 2, 'placeholder': 'Notes'})),

    'ff_views': forms.ChoiceField(
        required=False, label='Firefox views',
        choices=list(models.VENDOR_VIEWS_GECKO.items()),
        initial=models.NO_PUBLIC_SIGNALS,
        help_text=(
            'See <a target="_blank" href="https://bit.ly/blink-signals">'
            'https://bit.ly/blink-signals</a>')),

    'ff_views_link': forms.URLField(
        required=False, label='',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS),
        help_text='Citation link.'),

    'ff_views_notes': forms.CharField(
        required=False, label='',
        widget=ChromedashTextarea(
            attrs={'rows': 2, 'placeholder': 'Notes'})),

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
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS),
        help_text='Citation link.'),

    'web_dev_views_notes': forms.CharField(
        required=False, label='',
        widget=ChromedashTextarea(
            attrs={'rows': 2, 'placeholder': 'Notes'}),
        help_text=('Reference known representative examples of opinion, '
                   'both positive and negative.')),

    'other_views_notes': forms.CharField(
        required=False, label='Other views',
        widget=ChromedashTextarea(
            attrs={'rows': 4, 'placeholder': 'Notes'}),
        help_text=('For example, other browsers.')),

    'ergonomics_risks': forms.CharField(
        label='Ergonomics Risks', required=False,
        widget=ChromedashTextarea(),
        help_text=
        ('Are there any other platform APIs this feature will frequently be '
         'used in tandem with? Could the default usage of this API make it '
         'hard for Chrome to maintain good performance (i.e. synchronous '
         'return, must run on a certain thread, guaranteed return timing)?')),

    'activation_risks': forms.CharField(
        label='Activation Risks', required=False,
        widget=ChromedashTextarea(),
        help_text=
        ('Will it be challenging for developers to take advantage of this '
         'feature immediately, as-is? Would this feature benefit from '
         'having polyfills, significant documentation and outreach, and/or '
         'libraries built on top of it to make it easier to use?')),

    'security_risks': forms.CharField(
        label='Security Risks', required=False,
        widget=ChromedashTextarea(),
        help_text=
        ('List any security considerations that were taken into account '
         'when designing this feature.')),

    'webview_risks': forms.CharField(
        label='WebView application risks', required=False,
        widget=ChromedashTextarea(),
        help_text=
        ('Does this intent deprecate or change behavior of existing APIs, '
         'such that it has potentially high risk for Android WebView-based '
         'applications? (See <a href="'
         'https://new.chromium.org/developers/webview-changes/'
         '" target="_blank">here</a> for a definition of "potentially high '
         'risk", information on why changes to this platform carry higher '
         'risk, and general rules of thumb for which changes have higher or '
         'lower risk) If so:'
         '<ul>'
         '<li>Please use a base::Feature killswitch (<a href="'
         'https://source.chromium.org/chromium/chromium/src/+/main:third_party/blink/public/common/features.h'
         '" target="_blank">examples here</a>) that can '
         'be flipped off in case of compat issues</li>'
         '<li>Consider reaching out to android-webview-dev@chromium.org for '
         'advice</li>'
         '<li>If you are not sure, just put "not sure" as the answer here and '
         'the API owners can help during the review of your intent-to-ship</li>'
         '</ul>')),

    'experiment_goals': forms.CharField(
        label='Experiment Goals', required=False,
        widget=ChromedashTextarea(),
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
        widget=ChromedashTextarea(attrs={
            'rows': 2,
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
        required=False, label='OT Android start',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
        help_text=('First android milestone that will support an origin '
                   'trial of this feature.')),

    'ot_milestone_android_end': forms.IntegerField(
        required=False, label='OT Android end',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
        help_text=('Last android milestone that will support an origin '
                   'trial of this feature.')),

    'ot_milestone_webview_start': forms.IntegerField(
        required=False, label='OT WebView start',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
        help_text=('First WebView milestone that will support an origin '
                   'trial of this feature.')),

    'ot_milestone_webview_end': forms.IntegerField(
        required=False, label='OT WebView end',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
        help_text=('Last WebView milestone that will support an origin '
                   'trial of this feature.')),

    'experiment_risks': forms.CharField(
        label='Experiment Risks', required=False,
        widget=ChromedashTextarea(),
        help_text=
        ('When this experiment comes to an end are there any risks to the '
         'sites that were using it, for example losing access to important '
         'storage due to an experimental storage API?')),

    'experiment_extension_reason': forms.CharField(
        label='Experiment Extension Reason', required=False,
        widget=ChromedashTextarea(),
        help_text=
        ('If this is a repeat experiment, explain why you want to extend this '
         'experiment.  Also, fill in discussion link fields below.')),

    'ongoing_constraints': forms.CharField(
        label='Ongoing Constraints', required=False,
        widget=ChromedashTextarea(),
        help_text=
        ('Do you anticipate adding any ongoing technical constraints to '
         'the codebase while implementing this feature? We prefer to avoid '
         'features which require or assume a specific architecture. '
         'For most features, the answer here is "None."')),

    'origin_trial_feedback_url': forms.URLField(
        required=False, label='Origin trial feedback summary',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS),
        help_text=
        ('If your feature was available as an origin trial, link to a summary '
         'of usage and developer feedback. If not, leave this empty.')),

    'anticipated_spec_changes': MultiUrlField(
        required=False, label='Anticipated spec changes',
        widget=ChromedashTextarea(attrs=MULTI_URL_FIELD_ATTRS),
        help_text=
        ('Open questions about a feature may be a source of future web compat '
         'or interop issues. Please list open issues (e.g. links to known '
         'github issues in the project for the feature specification) whose '
         'resolution may introduce web compat/interop risk (e.g., changing '
         'to naming or structure of the API in a '
         'non-backward-compatible way).')),

    'finch_url': forms.URLField(
        required=False, label='Finch experiment',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS),
        help_text=
        ('If your feature will roll out gradually via a '
         '<a href="go/finch" targe="_blank">Finch experiment</a>, '
         'link to it here.')),

    'i2e_lgtms': MultiEmailField(
        required=False, label='Intent to Experiment LGTM by',
        widget=forms.EmailInput(attrs=MULTI_EMAIL_FIELD_ATTRS),
        help_text=('Full email address of API owner who LGTM\'d the '
                   'Intent to Experiment email thread.')),

    'i2s_lgtms': MultiEmailField(
        required=False, label='Intent to Ship LGTMs by',
        widget=forms.EmailInput(attrs=MULTI_EMAIL_FIELD_ATTRS),
        help_text=('Comma separated list of '
                   'full email addresses of API owners who LGTM\'d '
                   'the Intent to Ship email thread.')),

    'r4dt_lgtms': MultiEmailField(  # Sets i2e_lgtms field.
        required=False, label='Request for Deprecation Trial LGTM by',
        widget=forms.EmailInput(attrs=MULTI_EMAIL_FIELD_ATTRS),
        help_text=('Full email addresses of API owners who LGTM\'d '
                   'the Request for Deprecation Trial email thread.')),

    'debuggability': forms.CharField(
        label='Debuggability', required=True,
        widget=ChromedashTextarea(),
        help_text=
        ('Description of the DevTools debugging support for your feature. '
         'Please follow <a target="_blank" '
         'href="https://goo.gle/devtools-checklist">the '
         'DevTools support checklist</a> for guidance.')),

    'all_platforms': forms.BooleanField(
        label='Supported on all platforms?',
        widget=forms.CheckboxInput(attrs={'label': "Supported on all platforms"}),
        required=False, initial=False, 
        help_text=
        ('Will this feature be supported on all six Blink platforms '
         '(Windows, Mac, Linux, Chrome OS, Android, and Android WebView)?')),

    'all_platforms_descr': forms.CharField(
        label='Platform Support Explanation', required=False,
        widget=ChromedashTextarea(
            attrs={'rows': 2}),
            help_text=(
                'Explain why this feature is, or is not, '
                'supported on all platforms.')),

    'wpt': forms.BooleanField(
        label='Web Platform Tests',
        widget=forms.CheckboxInput(attrs={'label': "Web Platform Tests"}),
        required=False, initial=False, 
        help_text='Is this feature fully tested in Web Platform Tests?'),

    'wpt_descr': forms.CharField(
        label='Web Platform Tests Description', required=False,
        widget=ChromedashTextarea(),
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

    'sample_links': MultiUrlField(
        label='Samples links', required=False,
        widget=ChromedashTextarea(attrs=MULTI_URL_FIELD_ATTRS),
        help_text='Links to samples (one URL per line).'),

    'non_oss_deps': forms.CharField(
        label='Non-OSS dependencies', required=False,
        widget=ChromedashTextarea(),
        help_text=
        ('Does the feature depend on any code or APIs outside the Chromium '
         'open source repository and its open-source dependencies to '
         'function? (e.g. server-side APIs, operating system APIs '
         'tailored to this feature or closed-source code bundles) '
         'Yes or no. If yes, explain why this is necessary.'
         )),

    'bug_url': forms.URLField(
        required=False, label='Tracking bug URL',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    # TODO(jrobbins): Consider a button to file the launch bug automatically,
    # or a deep link that has some feature details filled in.
    'launch_bug_url': forms.URLField(
        required=False, label='Launch bug URL',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    'initial_public_proposal_url': forms.URLField(
        required=False, label='Initial public proposal URL',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    'blink_components': forms.ChoiceField(
      required=False, label='Blink component',
      choices=[(x, x) for x in models.BlinkComponent.fetch_all_components()],
      initial=[models.BlinkComponent.DEFAULT_COMPONENT]),

    'devrel': MultiEmailField(
        required=False, label='Developer relations emails',
        widget=forms.EmailInput(attrs=MULTI_EMAIL_FIELD_ATTRS),
        help_text='Comma separated list of full email addresses.'),

    'impl_status_chrome': forms.ChoiceField(
        required=False, label='Implementation status',
        choices=list(models.IMPLEMENTATION_STATUS.items())),

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
      label='Requires Embedder Support',
      widget=forms.CheckboxInput(attrs={'label': "Requires Embedder Support"}),
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
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS),
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
        label='Prefixed?',
        widget=forms.CheckboxInput(attrs={'label': "Prefixed"}),
        required=False, initial=False),

    'search_tags': forms.CharField(
        label='Search tags', required=False),

    'comments': forms.CharField(
        label='Comments', required=False,
        widget=ChromedashTextarea(attrs={'rows': 4})),

    }

# These are shown in a top card for all processes.
METADATA_FIELDS = [
     'name', 'summary', 'unlisted', 'owner',
     'editors', 'category',
     'feature_type', 'intent_stage',
     'search_tags',
     # Implemention
     'impl_status_chrome',
     'blink_components',
     'bug_url', 'launch_bug_url',
]

class ChromedashForm(forms.Form):
    def simple_html_output(self, normal_row, help_text_html):
        """
        Output HTML. Used by override of as_table() to support chromedash uses only.
        Simplified to drop support for hidden form fields and errors at the top, 
        which we are not using.
        Added field 'name' property for use in the normal_row template.
        """
        output = []

        for name, field in self.fields.items():
            html_class_attr = ''
            bf = self[name]
            bf_errors = self.error_class(bf.errors)

            # Create a 'class="..."' attribute if the row should have any
            # CSS classes applied.
            css_classes = bf.css_classes()
            if css_classes:
                html_class_attr = ' class="%s"' % css_classes

            if bf.label:
                label = conditional_escape(bf.label)
                label = bf.label_tag(label) or ''
            else:
                label = ''

            if field.help_text:
                help_text = help_text_html % field.help_text
            else:
                help_text = ''

            output.append(normal_row % {
                'name': name,
                'errors': bf_errors,
                'label': label,
                'field': bf,
                'help_text': help_text,
                'html_class_attr': html_class_attr,
                'css_classes': css_classes,
                'field_name': bf.html_name,
            })

        return mark_safe('\n'.join(output))

    def as_table(self):
        "Return this form rendered as HTML <tr>s -- excluding the <table></table>."
        label = '<span slot="label">%(label)s</span>'
        field = '<span slot="field">%(field)s</span>'
        error = '<span slot="error">%(errors)s</span>'
        help = '<span slot="help">%(help_text)s</span>'
        html = '<chromedash-form-field name="%(name)s" %(html_class_attr)s>' + label + field + error + help + '%(label)s' + '</chromedash-form-field>'
        return self.simple_html_output(
            normal_row=html,
            help_text_html='<span class="helptext">%s</span>'
        )

def define_form_class_using_shared_fields(class_name, field_spec_list):
  """Define a new subsblass of forms.Form with the given fields, in order."""
  # field_spec_list is normally just a list of simple field names,
  # but entries can also have syntax "form_field=shared_field".
  class_dict = {'field_order': []}
  for field_spec in field_spec_list:
    form_field_name = field_spec.split('=')[0]  # first or only
    shared_field_name = field_spec.split('=')[-1] # last or only
    properties = ALL_FIELDS[shared_field_name]
    class_dict[form_field_name] = properties
    class_dict['field_order'].append(form_field_name)

  return type(class_name, (ChromedashForm,), class_dict)


NewFeatureForm = define_form_class_using_shared_fields(
    'NewFeatureForm',
    ('name', 'summary',
     'unlisted', 'owner', 'editors',
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
     'ot_milestone_webview_start', 'ot_milestone_webview_end',
     'experiment_timeline',  # deprecated
     ))


Most_PrepareToShip = define_form_class_using_shared_fields(
    'Most_PrepareToShip',
    ('tag_review', 'tag_review_status', 'non_oss_deps',
     'webview_risks', 'anticipated_spec_changes', 'origin_trial_feedback_url',
     'launch_bug_url', 'intent_to_ship_url', 'i2s_lgtms', 'comments'))


Any_Ship = define_form_class_using_shared_fields(
    'Any_Ship',
    ('launch_bug_url', 'finch_url', 'comments'))


Existing_Prototype = define_form_class_using_shared_fields(
    'Existing_Prototype',
    ('owner', 'editors', 'blink_components', 'motivation', 'explainer_links',
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
     'webview_risks',
     'intent_to_implement_url', 'origin_trial_feedback_url',
     'launch_bug_url', 'comments'))


# Note: Even though this is similar to another form, it is likely to change.
Deprecation_DeprecationTrial = define_form_class_using_shared_fields(
    'Deprecation_DeprecationTrial',
    ('experiment_goals', 'experiment_risks',
     'ot_milestone_desktop_start', 'ot_milestone_desktop_end',
     'ot_milestone_android_start', 'ot_milestone_android_end',
     'ot_milestone_webview_start', 'ot_milestone_webview_end',
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
     'editors', 'category',
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
     'ot_milestone_webview_start', 'ot_milestone_webview_end',
     'experiment_timeline',  # deprecated
    ))


Flat_PrepareToShip = define_form_class_using_shared_fields(
    'Flat_PrepareToShip',
    (# Standardization
     'tag_review', 'tag_review_status',
     'webview_risks', 'anticipated_spec_changes',
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
    'unlisted', 'owner', 'editors',
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
        'webview_risks',
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
        'ot_milestone_webview_start', 'ot_milestone_webview_end',
        'experiment_timeline',  # Deprecated
        ),
    models.INTENT_SHIP: make_display_specs(
        'finch_url', 'anticipated_spec_changes',
        'shipped_milestone', 'shipped_android_milestone',
        'shipped_ios_milestone', 'shipped_webview_milestone',
        'intent_to_ship_url', 'i2s_lgtms'),
    models.INTENT_SHIPPED: make_display_specs(
        ),
    'Misc': make_display_specs(
        ),
}
