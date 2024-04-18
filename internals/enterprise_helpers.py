# Copyright 2024 Google Inc.
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

from datetime import datetime

from api import channels_api
from internals.core_enums import *
from internals.core_models import FeatureEntry

CHANNEL_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

def _str_to_datetime(dt):
  return datetime.strptime(dt, CHANNEL_DATETIME_FORMAT)

def needs_default_first_notification_milestone(
    existing_feature: FeatureEntry | None = None,
    new_fields: dict = {}) -> bool:
  """Returns whether we should create a default value for first_enterprise_notification_milestone.

  If a feature required a first_enterprise_notification_milestone field and a valid value is not
  available, we generate a deafult one.

  Args:
    existing_feature: FeatureEntry Optional feature that needs to be updated.
    new_fields: dict Fields that will be used to update or create the feature.
  """
  milestone = None
  has_valid_milestone_in_new_fields = False
  if new_fields.get('first_enterprise_notification_milestone'):
    milestone = int(new_fields['first_enterprise_notification_milestone'])
    channel_details = channels_api.construct_specified_milestones_details(milestone, milestone)
    has_valid_milestone_in_new_fields = (
      milestone in channel_details and
      _str_to_datetime(channel_details[milestone]['stable_date']) > datetime.now())

  existing_impact = ENTERPRISE_IMPACT_NONE
  if existing_feature is not None and existing_feature.enterprise_impact is not None:
    existing_impact = existing_feature.enterprise_impact
  new_impact = int(new_fields.get('enterprise_impact', existing_impact))

  # We are creating a new feature
  if existing_feature is None:
    # All enterprise features need this
    if new_fields['feature_type'] == FEATURE_TYPE_ENTERPRISE_ID:
      return not has_valid_milestone_in_new_fields
    # All breaking changes need this
    if new_impact > ENTERPRISE_IMPACT_NONE:
      return not has_valid_milestone_in_new_fields
    return False

  # We are updating a feature that already has a notification milestone
  if existing_feature.first_enterprise_notification_milestone is not None:
    return False

  # The enterprise feature we are updating does not have the field
  if existing_feature.feature_type == FEATURE_TYPE_ENTERPRISE_ID:
    return not has_valid_milestone_in_new_fields

  # The breaking change stays a breaking change
  if new_impact > ENTERPRISE_IMPACT_NONE:
    return not has_valid_milestone_in_new_fields

  return False

def is_update_first_notification_milestone(feature: FeatureEntry, new_fields: dict) -> bool:
  """Returns whether the milestone can be used to update first_enterprise_notification_milestone.

  Args:
    existing_feature: FeatureEntry feature that needs to be updated.
    new_fields: dict Fields that will be used to update or create the feature.
  """
  milestone = new_fields.get('first_enterprise_notification_milestone')
  if not milestone:
    return False
  milestone = int(milestone)

  # We cannot set a milestone that has already been released
  milestone_details = channels_api.construct_specified_milestones_details(milestone, milestone)
  if (milestone not in milestone_details or
      _str_to_datetime(milestone_details[milestone]['stable_date']) <= datetime.now()):
    return False

  # We cannot update the milestone of a feature that has already been announced
  if feature.first_enterprise_notification_milestone != None:
    milestone = feature.first_enterprise_notification_milestone
    previous_milestone_details = channels_api.construct_specified_milestones_details(milestone,
                                                                                     milestone)
    if (milestone in previous_milestone_details and
        _str_to_datetime(previous_milestone_details[milestone]['stable_date']) <= datetime.now()):
      return False

  if feature.feature_type == FEATURE_TYPE_ENTERPRISE_ID:
    return True

  # The breaking change stays a breaking change or becomes a breaking change
  existing_impact = feature.enterprise_impact or ENTERPRISE_IMPACT_NONE
  new_impact = int(new_fields.get('enterprise_impact', existing_impact))
  return new_impact > ENTERPRISE_IMPACT_NONE


def get_default_first_notice_milestone_for_feature() -> int:
  next_stable_version = channels_api.construct_chrome_channels_details()['beta']['version']
  return next_stable_version


def should_remove_first_notice_milestone(feature, new_fields):
  """Returns whether we remove first_enterprise_notification_milestone from a feature.

  An unannounced feature that does not require to be announced should removed the notice milestone.

  Args:
    existing_feature: FeatureEntry feature that needs to be updated.
    new_fields: dict Fields that will be used to update or create the feature.
  """
  if feature.first_enterprise_notification_milestone == None:
    return False

  if feature.feature_type == FEATURE_TYPE_ENTERPRISE_ID:
    return False

  existing_impact = feature.enterprise_impact or ENTERPRISE_IMPACT_NONE
  new_impact = int(new_fields.get('enterprise_impact', existing_impact))
  if new_impact > ENTERPRISE_IMPACT_NONE:
    return False

  milestone = feature.first_enterprise_notification_milestone
  milestone_details = channels_api.construct_specified_milestones_details(milestone, milestone)
  if (milestone in milestone_details and
      _str_to_datetime(milestone_details[milestone]['stable_date']) > datetime.now()):
    return True

  return False
