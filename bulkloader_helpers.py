from __future__ import division
from __future__ import print_function

import datetime

from google.appengine.ext import ndb
# from google.appengine.api import users
from framework import users

def email_to_list():
  def wrapper(value):
    if value == '' or value is None or value == []:
      return None
    return [str(x.strip()) for x in value.split(',')]

  return wrapper

def finalize(input_dict, instance, bulkload_state_copy):
  #print input_dict
  if instance['owner'] is None:
    del instance['owner']
  if instance['created'] is None:
    instance['created'] = datetime.datetime.utcnow()
  if instance['updated'] is None:
    instance['updated'] = datetime.datetime.utcnow()
  if instance['created_by'] is None:
   instance['created_by'] = users.User(email='admin') #users.get_current_user().email()
  if instance['updated_by'] is None:
   instance['updated_by'] = users.User(email='admin') #users.get_current_user().email()
  if instance['summary'] == '' or instance['summary'] is None:
    instance['summary'] = ' '
  return instance
