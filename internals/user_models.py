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

# Import needed to reference a class within its own class method.
# https://stackoverflow.com/a/33533514
from __future__ import annotations

import logging
from typing import Optional

from google.cloud import ndb  # type: ignore

from framework import rediscache
from framework import users
import hack_components
import settings


class UserPref(ndb.Model):
  """Describes a user's application preferences."""

  email = ndb.StringProperty(required=True)

  # True means that user should be sent a notification email after each change
  # to each feature that the user starred.
  notify_as_starrer = ndb.BooleanProperty(default=True)

  # True means that we sent an email message to this user in the past
  # and it bounced.  We will not send to that address again.
  bounced = ndb.BooleanProperty(default=False)

  # A list of strings identifying on-page help cue cards that the user
  # has dismissed (clicked "X" or "GOT IT").
  dismissed_cues = ndb.StringProperty(repeated=True)

  @classmethod
  def get_signed_in_user_pref(cls):
    """Return a UserPref for the signed in user or None if anon."""
    signed_in_user = users.get_current_user()
    if not signed_in_user:
      return None

    user_pref_list = UserPref.query().filter(
        UserPref.email == signed_in_user.email()).fetch(1)
    if user_pref_list:
      user_pref = user_pref_list[0]
    else:
      user_pref = UserPref(email=signed_in_user.email())
    return user_pref

  @classmethod
  def dismiss_cue(cls, cue):
    """Add cue to the signed in user's dismissed_cues."""
    user_pref = cls.get_signed_in_user_pref()
    if not user_pref:
      return  # Anon users cannot store dismissed cue names.

    if cue not in user_pref.dismissed_cues:
      user_pref.dismissed_cues.append(cue)
      user_pref.put()

  @classmethod
  def get_prefs_for_emails(cls, emails: list[str]) -> list[UserPref]:
    """Return a list of UserPrefs for each of the given emails."""
    result: list[UserPref] = []
    CHUNK_SIZE = 25  # Query 25 at a time because IN operator is limited to 30.
    chunks = [emails[i : i + CHUNK_SIZE]
              for i in range(0, len(emails), CHUNK_SIZE)]
    for chunk_emails in chunks:
      q = UserPref.query()
      q = q.filter(UserPref.email.IN(chunk_emails))
      chunk_prefs: list[UserPref] = q.fetch(None)
      result.extend(chunk_prefs)
      found_set = set(up.email for up in chunk_prefs)

      # Make default prefs for any user that does not already have an entity.
      new_prefs = [UserPref(email=e) for e in chunk_emails
                   if e not in found_set]
      for np in new_prefs:
        np.put()
        result.append(np)

    return result


class AppUser(ndb.Model):
  """Describes a user for permission checking."""

  email = ndb.StringProperty(required=True)
  is_admin = ndb.BooleanProperty(default=False)
  is_site_editor = ndb.BooleanProperty(default=False)
  created = ndb.DateTimeProperty(auto_now_add=True)
  updated = ndb.DateTimeProperty(auto_now=True)
  last_visit = ndb.DateTimeProperty()
  notified_inactive = ndb.BooleanProperty()

  def put(self, **kwargs):
    """when we update an AppUser, also delete in rediscache."""
    key = super(AppUser, self).put(**kwargs)
    cache_key = 'user|%s' % self.email
    rediscache.delete(cache_key)

  def delete(self, **kwargs):
    """when we delete an AppUser, also delete in rediscache."""
    key = super(AppUser, self).key.delete(**kwargs)
    cache_key = 'user|%s' % self.email
    rediscache.delete(cache_key)

  @classmethod
  def get_app_user(cls, email: str) -> Optional[AppUser]:
    """Return the AppUser for the specified user, or None."""
    cache_key = 'user|%s' % email
    cached_app_user = rediscache.get(cache_key)
    if cached_app_user:
      return cached_app_user

    query = cls.query()
    query = query.filter(cls.email == email)
    found_app_user: Optional[AppUser] = query.get()
    if found_app_user is None:
      return None
    rediscache.set(cache_key, found_app_user)
    return found_app_user


def list_with_component(l, component):
  return [x for x in l if x.id() == component.key.integer_id()]

def list_without_component(l, component):
  return [x for x in l if x.id() != component.key.integer_id()]


class FeatureOwner(ndb.Model):
  """Describes subscribers of a web platform feature."""
  created = ndb.DateTimeProperty(auto_now_add=True)
  updated = ndb.DateTimeProperty(auto_now=True)
  name = ndb.StringProperty(required=True)
  email = ndb.StringProperty(required=True)
  twitter = ndb.StringProperty()
  blink_components = ndb.KeyProperty(repeated=True)
  primary_blink_components = ndb.KeyProperty(repeated=True)
  watching_all_features = ndb.BooleanProperty(default=False)

  def add_to_component_subscribers(self, component_id):
    """Adds the user to the list of Blink component subscribers."""
    c = BlinkComponent.get_by_id(component_id)
    if c:
      # Add the user if they're not already in the list.
      if not len(list_with_component(self.blink_components, c)):
        self.blink_components.append(c.key)
        return self.put()
    return None

  def remove_from_component_subscribers(
      self, component_id, remove_as_owner=False):
    """Removes the user from the list of Blink component subscribers or as
       the owner of the component.
    """
    c = BlinkComponent.get_by_id(component_id)
    if c:
      if remove_as_owner:
        self.primary_blink_components = (
            list_without_component(self.primary_blink_components, c))
      else:
        self.blink_components = list_without_component(self.blink_components, c)
        self.primary_blink_components = (
            list_without_component(self.primary_blink_components, c))
      return self.put()
    return None

  def add_as_component_owner(self, component_id):
    """Adds the user as the Blink component owner."""
    c = BlinkComponent.get_by_id(component_id)
    if c:
      # Update both the primary list and blink components subscribers if the
      # user is not already in them.
      self.add_to_component_subscribers(component_id)
      if not len(list_with_component(self.primary_blink_components, c)):
        self.primary_blink_components.append(c.key)
      return self.put()
    return None

  def remove_as_component_owner(self, component_id):
    return self.remove_from_component_subscribers(
        component_id, remove_as_owner=True)


class BlinkComponent(ndb.Model):

  name = ndb.StringProperty(required=True, default=settings.DEFAULT_COMPONENT)
  created = ndb.DateTimeProperty(auto_now_add=True)
  updated = ndb.DateTimeProperty(auto_now=True)

  @property
  def subscribers(self):
    q = FeatureOwner.query(FeatureOwner.blink_components == self.key)
    q = q.order(FeatureOwner.name)
    return q.fetch(None)

  @property
  def owners(self):
    q = FeatureOwner.query(FeatureOwner.primary_blink_components == self.key)
    q = q.order(FeatureOwner.name)
    return q.fetch(None)

  @classmethod
  def fetch_all_components(self, update_cache=False):
    """Returns the list of blink components."""
    key = 'blinkcomponents'

    components = rediscache.get(key)
    if components is None or update_cache:
      # TODO(jrobbins): Re-implement fetching the list of blink components
      # by getting it via the monorail API.
      pass

    if not components:
      components = sorted(hack_components.HACK_BLINK_COMPONENTS)
      logging.info('using hard-coded blink components')

    return components

  @classmethod
  def update_db(self):
    """Updates the db with new Blink components from the json endpoint"""
    new_components = self.fetch_all_components(update_cache=True)
    existing_comps = self.query().fetch(None)
    for name in new_components:
      if not len([x.name for x in existing_comps if x.name == name]):
        logging.info('Adding new BlinkComponent: ' + name)
        c = BlinkComponent(name=name)
        c.put()

  @classmethod
  def get_by_name(self, component_name: str) -> Optional[BlinkComponent]:
    """Fetch blink component with given name."""
    q = self.query()
    q = q.filter(self.name == component_name)
    component = q.fetch(1)
    if not component:
      logging.error('%s is an unknown BlinkComponent.' % (component_name))
      return None
    return component[0]
