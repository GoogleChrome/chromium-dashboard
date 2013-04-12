import datetime
import time

from google.appengine.api import memcache
from google.appengine.ext import db
#from google.appengine.ext.db import djangoforms

#from django.forms import ModelForm
from django import forms


SIMPLE_TYPES = (int, long, float, bool, dict, basestring, list)


class DictModel(db.Model):
  # def to_dict(self):
  #   return dict([(p, unicode(getattr(self, p))) for p in self.properties()])

  def to_dict(self):
      output = {}

      for key, prop in self.properties().iteritems():
          value = getattr(self, key)

          if value is None or isinstance(value, SIMPLE_TYPES):
              output[key] = value
          elif isinstance(value, datetime.date):
              # Convert date/datetime to ms-since-epoch ("new Date()").
              #ms = time.mktime(value.utctimetuple())
              #ms += getattr(value, 'microseconds', 0) / 1000
              #output[key] = int(ms)
              output[key] = unicode(value)
          elif isinstance(value, db.GeoPt):
              output[key] = {'lat': value.lat, 'lon': value.lon}
          elif isinstance(value, db.Model):
              output[key] = to_dict(value)
          else:
              raise ValueError('cannot encode ' + repr(prop))

      return output


# UMA metrics.
class StableInstance(DictModel):
  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now=True)

  property_name = db.StringProperty(required=True)
  bucket_id = db.IntegerProperty(required=True)
  date = db.DateProperty(verbose_name='When the data was fetched',
                             required=True)
  hits = db.IntegerProperty(required=True)
  total_pages = db.IntegerProperty()
  day_percentage = db.FloatProperty()
  rolling_percentage = db.FloatProperty()


# Feature dashboard.
class Feature(DictModel):
  """Container for a feature."""

  # Metadata.
  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now=True)

  # General info.
  category = db.StringProperty(required=True)
  feature_name = db.StringProperty(required=False)

  # Chromium details.
  launch_bug_url = db.LinkProperty()
  impl_status_chrome = db.StringProperty() #todo:make list
  shipped_milestone = db.IntegerProperty()

  owner = db.StringProperty()
  severity = db.StringProperty() #todo: make listlist

  # Standards details.
  standardization = db.StringProperty()
  prefixed = db.BooleanProperty(default=False)
  safari_temperature = db.StringProperty()
  ie_temperature = db.StringProperty()
  ff_temperature = db.StringProperty()

  # Web dev details.
  web_dev_temperature = db.StringProperty()  
  spec_link = db.LinkProperty()
  doc_links = db.StringProperty()
  tests = db.StringProperty()


class FeatureForm(forms.Form):
  title = forms.CharField(required=True)
  org = forms.CharField(required=True)
  unit = forms.CharField(required=True)
  city = forms.CharField(required=False)
  state = forms.CharField(required=False)
  country = forms.CharField(required=True)
  homepage = forms.URLField(required=False)
  google_account = forms.CharField(required=False)
  twitter_account = forms.CharField(required=False)
  email = forms.EmailField(required=False)
  lanyrd = forms.BooleanField(required=False, initial=False)

  class Meta:
    model = Feature
    #exclude = ['owner']

  # def __init__(self, *args, **keyargs):
  #   super(FeatureForm, self).__init__(*args, **keyargs)

  #   for field, val in self.fields.iteritems():
  #     if val.required:
  #       self.fields[field].widget.attrs['required'] = 'required'
