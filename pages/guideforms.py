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

import re

from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from internals import core_enums
from internals import user_models


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

class ChromedashTextarea(forms.widgets.Textarea):
    template_name = 'django/forms/widgets/chromedash-textarea.html'

    def __init__(self, attrs=None):
        # Use slightly better defaults than HTML's 20x2 box
        default_attrs = {'cols': 50, 'rows': 10,  'maxlength': MAX_LENGTH}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

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
        required=True, label=''),

    'summary': forms.CharField(
        required=True, label='',
        widget=ChromedashTextarea()),

    'owner': MultiEmailField(
        required=True, label='',
        widget=forms.EmailInput(attrs=MULTI_EMAIL_FIELD_ATTRS)),

    'editors': MultiEmailField(
        required=False, label='',
        widget=forms.EmailInput(attrs=MULTI_EMAIL_FIELD_ATTRS)),

    'accurate_as_of': forms.BooleanField(
        label='',
        widget=forms.CheckboxInput(attrs={'label': "Confirm accuracy"}),
        required=False, initial=True),

    'category': forms.ChoiceField(
        required=False, label='',
        initial=core_enums.MISC,
        choices=sorted(core_enums.FEATURE_CATEGORIES.items(), key=lambda x: x[1])),

    'feature_type': forms.ChoiceField(
        required=False, label='',
        initial=core_enums.FEATURE_TYPE_INCUBATE_ID,
        choices=sorted(core_enums.FEATURE_TYPES.items())),

    'intent_stage': forms.ChoiceField(
        required=False, label='',
        initial=core_enums.INTENT_IMPLEMENT,
        choices=list(core_enums.INTENT_STAGES.items())),

    'motivation': forms.CharField(
        label='', required=False,
        widget=ChromedashTextarea()),

    'deprecation_motivation': forms.CharField(  # Sets motivation DB field.
        label='', required=False,
        widget=ChromedashTextarea()),

    'doc_links': MultiUrlField(
        label='', required=False,
        widget=ChromedashTextarea(attrs=MULTI_URL_FIELD_ATTRS)),

    'measurement': forms.CharField(
        label='', required=False,
        widget=ChromedashTextarea(attrs={'rows': 4})),

    # 'standardization' is deprecated

    'standard_maturity': forms.ChoiceField(
        required=False, label='',
        choices=list(core_enums.STANDARD_MATURITY_CHOICES.items()),
        initial=core_enums.PROPOSAL_STD),

    'unlisted': forms.BooleanField(
        label='',
        widget=forms.CheckboxInput(attrs={'label': "Unlisted"}),
        required=False, initial=False),

    'spec_link': forms.URLField(
        required=False, label='',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    'api_spec': forms.BooleanField(
        label='',
        widget=forms.CheckboxInput(attrs={'label': "API spec"}),
        required=False, initial=False),

    'spec_mentors': MultiEmailField(
        required=False, label='',
        widget=forms.EmailInput(attrs=MULTI_EMAIL_FIELD_ATTRS)),

    'explainer_links': MultiUrlField(
        label='', required=False,
        widget=ChromedashTextarea(attrs=MULTI_URL_FIELD_ATTRS)),

    'security_review_status': forms.ChoiceField(
        label='',
        required=False,
        choices=list(core_enums.REVIEW_STATUS_CHOICES.items()),
        initial=core_enums.REVIEW_PENDING),

    'privacy_review_status': forms.ChoiceField(
        label='',
        required=False,
        choices=list(core_enums.REVIEW_STATUS_CHOICES.items()),
        initial=core_enums.REVIEW_PENDING),

    'tag_review': forms.CharField(
        label='', required=False,
        widget=ChromedashTextarea(attrs={'rows': 2})),

    'tag_review_status': forms.ChoiceField(
        label='',
        required=False,
        choices=list(core_enums.REVIEW_STATUS_CHOICES.items()),
        initial=core_enums.REVIEW_PENDING),

    'intent_to_implement_url': forms.URLField(
        required=False, label='',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    'intent_to_ship_url': forms.URLField(
        required=False, label='',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    'ready_for_trial_url': forms.URLField(
        required=False, label='',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    'intent_to_experiment_url': forms.URLField(
        required=False, label='',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    'intent_to_extend_experiment_url': forms.URLField(
        required=False, label='',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    'r4dt_url': forms.URLField(  # Sets intent_to_experiment_url in DB
        required=False, label='',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    'interop_compat_risks': forms.CharField(
        required=False, label='',
        widget=ChromedashTextarea()),

    'safari_views': forms.ChoiceField(
        required=False, label='',
        choices=list(core_enums.VENDOR_VIEWS_WEBKIT.items()),
        initial=core_enums.NO_PUBLIC_SIGNALS),

    'safari_views_link': forms.URLField(
        required=False, label='',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    'safari_views_notes': forms.CharField(
        required=False, label='',
        widget=ChromedashTextarea(
            attrs={'rows': 2, 'placeholder': 'Notes'})),

    'ff_views': forms.ChoiceField(
        required=False, label='',
        choices=list(core_enums.VENDOR_VIEWS_GECKO.items()),
        initial=core_enums.NO_PUBLIC_SIGNALS),

    'ff_views_link': forms.URLField(
        required=False, label='',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    'ff_views_notes': forms.CharField(
        required=False, label='',
        widget=ChromedashTextarea(
            attrs={'rows': 2, 'placeholder': 'Notes'})),

    'web_dev_views': forms.ChoiceField(
        required=False, label='',
        choices=list(core_enums.WEB_DEV_VIEWS.items()),
        initial=core_enums.DEV_NO_SIGNALS),

    'web_dev_views_link': forms.URLField(
        required=False, label='',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    'web_dev_views_notes': forms.CharField(
        required=False, label='',
        widget=ChromedashTextarea(
            attrs={'rows': 2, 'placeholder': 'Notes'})),

    'other_views_notes': forms.CharField(
        required=False, label='',
        widget=ChromedashTextarea(
            attrs={'rows': 4, 'placeholder': 'Notes'})),

    'ergonomics_risks': forms.CharField(
        label='', required=False,
        widget=ChromedashTextarea()),

    'activation_risks': forms.CharField(
        label='', required=False,
        widget=ChromedashTextarea()),

    'security_risks': forms.CharField(
        label='', required=False,
        widget=ChromedashTextarea()),

    'webview_risks': forms.CharField(
        label='', required=False,
        widget=ChromedashTextarea()),

    'experiment_goals': forms.CharField(
        label='', required=False,
        widget=ChromedashTextarea()),

    # TODO(jrobbins): consider splitting this into start and end fields.
    'experiment_timeline': forms.CharField(
        label='', required=False,
        widget=ChromedashTextarea(attrs={
            'rows': 2,
            'placeholder': 'This field is deprecated',
            'disabled': 'disabled'})),

    # TODO(jrobbins and jmedley): Refine help text.
    'ot_milestone_desktop_start': forms.IntegerField(
        required=False, label='',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone number'})),

    'ot_milestone_desktop_end': forms.IntegerField(
        required=False, label='',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone number'})),

    'ot_milestone_android_start': forms.IntegerField(
        required=False, label='',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone number'})),

    'ot_milestone_android_end': forms.IntegerField(
        required=False, label='',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone number'})),

    'ot_milestone_webview_start': forms.IntegerField(
        required=False, label='',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone number'})),

    'ot_milestone_webview_end': forms.IntegerField(
        required=False, label='',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone number'})),

    'experiment_risks': forms.CharField(
        label='', required=False,
        widget=ChromedashTextarea()),

    'experiment_extension_reason': forms.CharField(
        label='', required=False,
        widget=ChromedashTextarea()),

    'ongoing_constraints': forms.CharField(
        label='', required=False,
        widget=ChromedashTextarea()),

    'origin_trial_feedback_url': forms.URLField(
        required=False, label='',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    'anticipated_spec_changes': MultiUrlField(
        required=False, label='',
        widget=ChromedashTextarea(attrs=MULTI_URL_FIELD_ATTRS)),

    'finch_url': forms.URLField(
        required=False, label='',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    'i2e_lgtms': MultiEmailField(
        required=False, label='',
        widget=forms.EmailInput(attrs=MULTI_EMAIL_FIELD_ATTRS)),

    'i2s_lgtms': MultiEmailField(
        required=False, label='',
        widget=forms.EmailInput(attrs=MULTI_EMAIL_FIELD_ATTRS)),

    'r4dt_lgtms': MultiEmailField(  # Sets i2e_lgtms field.
        required=False, label='',
        widget=forms.EmailInput(attrs=MULTI_EMAIL_FIELD_ATTRS)),

    'debuggability': forms.CharField(
        label='', required=True,
        widget=ChromedashTextarea()),

    'all_platforms': forms.BooleanField(
        label='',
        widget=forms.CheckboxInput(attrs={'label': "Supported on all platforms"}),
        required=False, initial=False),

    'all_platforms_descr': forms.CharField(
        label='', required=False,
        widget=ChromedashTextarea(
            attrs={'rows': 2})),

    'wpt': forms.BooleanField(
        label='',
        widget=forms.CheckboxInput(attrs={'label': "Web Platform Tests"}),
        required=False, initial=False),

    'wpt_descr': forms.CharField(
        label='', required=False,
        widget=ChromedashTextarea()),

    'sample_links': MultiUrlField(
        label='', required=False,
        widget=ChromedashTextarea(attrs=MULTI_URL_FIELD_ATTRS)),

    'non_oss_deps': forms.CharField(
        label='', required=False,
        widget=ChromedashTextarea()),

    'bug_url': forms.URLField(
        label='',
        required=False,
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    # TODO(jrobbins): Consider a button to file the launch bug automatically,
    # or a deep link that has some feature details filled in.
    'launch_bug_url': forms.URLField(
        required=False, label='',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    'initial_public_proposal_url': forms.URLField(
        required=False, label='',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    'blink_components': forms.ChoiceField(
      required=False, label='',
      choices=[(x, x) for x in
               user_models.BlinkComponent.fetch_all_components()],
      initial=''),

    'devrel': MultiEmailField(
        required=False, label='',
        widget=forms.EmailInput(attrs=MULTI_EMAIL_FIELD_ATTRS)),

    'impl_status_chrome': forms.ChoiceField(
        required=False, label='',
        choices=list(core_enums.IMPLEMENTATION_STATUS.items())),

    'shipped_milestone': forms.IntegerField(
        required=False, label='',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone number'})),

    'shipped_android_milestone': forms.IntegerField(
        required=False, label='',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone number'})),

    'shipped_ios_milestone': forms.IntegerField(
        required=False, label='',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone number'})),

    'shipped_webview_milestone': forms.IntegerField(
        required=False, label='',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone number'})),

    'requires_embedder_support': forms.BooleanField(
      label='',
      widget=forms.CheckboxInput(attrs={'label': "Requires Embedder Support"}),
      required=False, initial=False),

    'devtrial_instructions': forms.URLField(
        required=False, label='',
        widget=forms.URLInput(attrs=URL_FIELD_ATTRS)),

    'dt_milestone_desktop_start': forms.IntegerField(
        required=False, label='',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone number'})),

    'dt_milestone_android_start': forms.IntegerField(
        required=False, label='',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone number'})),

    'dt_milestone_ios_start': forms.IntegerField(
        required=False, label='',
        widget=forms.NumberInput(attrs={'placeholder': 'Milestone number'})),

    'flag_name': forms.CharField(
        label='', required=False),

    'prefixed': forms.BooleanField(
        label='',
        widget=forms.CheckboxInput(attrs={'label': "Prefixed"}),
        required=False, initial=False),

    'search_tags': forms.CharField(
        label='', required=False),

    'comments': forms.CharField(
        label='', required=False,
        widget=ChromedashTextarea(attrs={'rows': 4})),

    }


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
        'category', 'feature_type', 'intent_stage', 'accurate_as_of'
        ),
    core_enums.INTENT_INCUBATE: make_display_specs(
        'initial_public_proposal_url', 'explainer_links',
        'requires_embedder_support'),
    core_enums.INTENT_IMPLEMENT: make_display_specs(
        'spec_link', 'standard_maturity', 'api_spec', 'spec_mentors',
        'intent_to_implement_url'),
    core_enums.INTENT_EXPERIMENT: make_display_specs(
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
    core_enums.INTENT_IMPLEMENT_SHIP: make_display_specs(
        'launch_bug_url',
        'tag_review', 'tag_review_status',
        'webview_risks',
        'measurement', 'prefixed', 'non_oss_deps',
        ),
    core_enums.INTENT_EXTEND_TRIAL: make_display_specs(
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
    core_enums.INTENT_SHIP: make_display_specs(
        'finch_url', 'anticipated_spec_changes',
        'shipped_milestone', 'shipped_android_milestone',
        'shipped_ios_milestone', 'shipped_webview_milestone',
        'intent_to_ship_url', 'i2s_lgtms'),
    core_enums.INTENT_SHIPPED: make_display_specs(
        ),
    'Misc': make_display_specs(
        ),
}
