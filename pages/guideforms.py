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

from django.utils.html import conditional_escape, escape
from django.utils.safestring import mark_safe

from framework import users
from internals import core_enums
from internals import processes
from internals import user_models
import settings


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
        required=True, label='',
        widget=ChromedashTextInput()),

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
      initial=[settings.DEFAULT_COMPONENT]),

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
    def simple_html_output(self):
        """
        Output HTML. Used by override of as_table() to support chromedash uses only.
        Simplified to drop support for hidden form fields and errors at the top,
        which we are not using.
        Added field 'name' property for use in the normal_row template.
        Added 'value' and 'checked' properties.
        Added 'field' and 'errors' to avoid use of slots.
        """
        output = []

        # Attributes for all fields except checkbox.
        attrs = 'name="%(name)s" value="%(value)s" field="%(field)s" errors="%(errors)s" %(html_class_attr)s'
        # Attributes for checkbox fields.
        checkbox_attrs = 'name="%(name)s" value="%(value)s"  checked="%(checked)s" errors="%(errors)s" %(html_class_attr)s'

        # Create the row template used for every field.
        normal_row = '<chromedash-form-field ' + attrs + '></chromedash-form-field>'
        checkbox_row = '<chromedash-form-field ' + checkbox_attrs + '></chromedash-form-field>'

        for name, field in self.fields.items():
            html_class_attr = ''
            bf = self[name]
            bf_errors = self.error_class(bf.errors)

            # Get value and checked for the field
            value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))

            row_template = normal_row
            checked = False
            if hasattr(field.widget, 'check_test'):
                # Must be a checkbox field.
                row_template = checkbox_row
                if field.widget.check_test(value):
                    checked = True

                # accurate_as_of field should always be checked, regardless of
                # the current value. This is only necessary if the feature
                # has been created before this field was added.
                if name == 'accurate_as_of':
                    checked = True
                    value = True

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

            output.append(row_template % {
                'name': name,
                'errors': escape(bf_errors),
                'field': escape(bf),
                'value': escape(value),
                'checked': checked,
                'html_class_attr': html_class_attr,
                'css_classes': css_classes,
                'field_name': bf.html_name,
            })

        return mark_safe('\n'.join(output))

    def as_table(self):
        "Return this form rendered as HTML <tr>s -- excluding the <table></table>."
        return self.simple_html_output()

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

Verify_Accuracy = define_form_class_using_shared_fields(
    'Verify_Accuracy',
    ('summary', 'owner', 'editors', 'impl_status_chrome', 'intent_stage',
    'dt_milestone_android_start', 'dt_milestone_desktop_start',
    'dt_milestone_ios_start', 'ot_milestone_android_start',
    'ot_milestone_android_end', 'ot_milestone_desktop_start',
    'ot_milestone_desktop_end', 'ot_milestone_webview_start',
    'ot_milestone_webview_end', 'shipped_android_milestone',
    'shipped_ios_milestone', 'shipped_milestone', 'shipped_webview_milestone',
    'accurate_as_of')
)

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
