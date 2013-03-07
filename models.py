from google.appengine.api import memcache
from google.appengine.ext import db
#from google.appengine.ext.db import djangoforms

#from django.forms import ModelForm
from django import forms


class DictModel(db.Model):
  def to_dict(self):
    return dict([(p, getattr(self, p)) for p in self.properties()])


class Feature(DictModel):
  """Container for a feature."""

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
