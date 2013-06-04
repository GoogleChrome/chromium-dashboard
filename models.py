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

  @staticmethod
  def format_for_template(self):
    d = self.to_dict()
    d['id'] = self.key().id()
    d['category'] = FEATURE_CATEGORIES[self.category]
    d['visibility'] = VISIBILITY_CHOICES[self.visibility]
    d['impl_status_chrome'] = IMPLEMENATION_STATUS[self.impl_status_chrome]
    #d['owner'] = ', '.join(self.owner)
    return d

  def format_for_edit(self):
    d = self.to_dict()
    d['id'] = self.key().id
    d['owner'] = ', '.join(self.owner)
    return d

  # Metadata.
  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now=True)

  # General info.
  category = db.IntegerProperty(required=True)
  feature_name = db.StringProperty(required=True)
  summary = db.StringProperty(required=True)

  # Chromium details.
  bug_url = db.LinkProperty()
  impl_status_chrome = db.IntegerProperty(required=True)
  shipped_milestone = db.StringProperty(required=True)

  owner = db.ListProperty(db.Email, required=True)
  footprint = db.IntegerProperty()
  visibility = db.IntegerProperty(required=True)

  #webbiness = db.IntegerProperty() # TODO: figure out what this is

  # Standards details.
  standardization = db.IntegerProperty(required=True)
  prefixed = db.BooleanProperty()

  safari_views = db.IntegerProperty(required=True)
  ie_views = db.IntegerProperty(required=True)
  ff_views = db.IntegerProperty(required=True)

  safari_views_link = db.LinkProperty()
  ff_views_link = db.LinkProperty()
  ie_views_link = db.LinkProperty()

  # Web dev details.
  #web_dev_temperature = db.StringProperty()  
  spec_link = db.LinkProperty()
  #doc_links = db.StringProperty()
  #tests = db.StringProperty()


class PlaceholderCharField(forms.CharField):

  def __init__(self, *args, **kwargs):
    #super(forms.CharField, self).__init__(*args, **kwargs)

    attrs = {}
    if kwargs.get('placeholder'):
      attrs['placeholder'] = kwargs.get('placeholder')
      del kwargs['placeholder']

    label = kwargs.get('label') or ''
    if label:
      del kwargs['label']

    self.max_length = kwargs.get('max_length') or None

    super(forms.CharField, self).__init__(label=label,
        widget=forms.TextInput(attrs=attrs), *args, **kwargs)


# class PlaceholderForm(forms.Form):
#   def __init__(self, *args, **kwargs):
#     super(PlaceholderForm, self).__init__(*args, **kwargs)
     
#     for field_name in self.fields:
#      field = self.fields.get(field_name)  
#      if field:
#        if type(field.widget) in (forms.TextInput, forms.DateInput):
#          field.widget = forms.TextInput(attrs={'placeholder': field.label})


CSS = 0
WEBCOMPONENTS = 1
MISC = 2
SECURITY = 3
MULTIMEDIA = 4
DOM = 5
FILE = 6
OFFLINE = 7
DEVICE = 8
COMMUNICATION = 9
STORAGE = 10
JAVASCRIPT = 11
NETWORKING = 12
INPUT = 13
PERFORMANCE = 14
WEBGL = 15

FEATURE_CATEGORIES = {
  CSS: 'CSS',
  WEBCOMPONENTS: 'Web Components',
  MISC: 'Misc',
  SECURITY: 'Security',
  MULTIMEDIA: 'Multimedia',
  DOM: 'DOM',
  FILE: 'File APIs',
  OFFLINE: 'Offline',
  DEVICE: 'Device',
  COMMUNICATION: 'Communication',
  STORAGE: 'Storage',
  JAVASCRIPT: 'JavaScript',
  NETWORKING: 'Networking',
  INPUT: 'Input',
  PERFORMANCE: 'Performance',
  WEBGL: 'WebGL',
  }

NOT_ACTIVE = 0
PROPOSED = 1
STARTED = 2
EXPERIMENTAL = 3
CANARY_DEV = 4
BETA = 5
STABLE = 6
DEPRECATED = 7

IMPLEMENATION_STATUS = {
  NOT_ACTIVE: 'No active development',
  PROPOSED: 'Proposed',
  STARTED: 'Started',
  EXPERIMENTAL: 'Experimental',
  CANARY_DEV: 'Canary / Dev channel',
  BETA: 'Beta channel',
  STABLE: 'Stable channel',
  DEPRECATED: 'Deprecated',
  }

FOOTPRINT_CHOICES = {
  0: 'F0',
  1: 'F1',
  2: 'F2',
  3: 'F3',
  4: 'F4',
  }

VISIBILITY_CHOICES = {
  0: 'Likely in mainstream tech news',
  1: 'Warrants its own article on a site like html5rocks.com',
  2: 'Covered as part of a larger article but not on its own',
  3: 'Only a very small number of web developers will care about',
  4: "So small it doesn't need to be covered in this dashboard.",
  }

FIRST_PROPOSER = 0
IN_DEV = 1
PUBLIC_SUPPORT = 2
MIXED_SIGNALS = 3
NO_PUBLIC_SIGNALS = 4
PUBLIC_SKEPTICISM = 5
OPPOSED = 6

VENDOR_VIEWS = {
  FIRST_PROPOSER: 'In development (first proposer)',
  IN_DEV: 'In development',
  PUBLIC_SUPPORT: 'Documented public support',
  MIXED_SIGNALS: 'Mixed public signals',
  NO_PUBLIC_SIGNALS: 'No public signals',
  PUBLIC_SKEPTICISM: 'Public skepticism',
  OPPOSED: 'Opposed',
  }

STANDARDIZATION = {
  0: 'De-facto standard',
  1: 'Established standard',
  2: 'Working draft or equivalent',
  3: "Editor's draft specification",
  4: 'Public discussion',
  5: 'No public discussion / Not standards track',
  }


class FeatureForm(forms.Form):
  
  category = forms.ChoiceField(required=True, choices=FEATURE_CATEGORIES.items())

  feature_name = PlaceholderCharField(required=True, placeholder='Feature name')
  #feature_name = forms.CharField(required=True, label='Feature name')
  
  summary = forms.CharField(label='', required=True,
      widget=forms.Textarea(attrs={'cols': 50, 'placeholder': 'Summary'}))

  owner = PlaceholderCharField(
      required=True, placeholder='Owner(s) email',
      help_text='Owner (@chromium.org username or a full email).')
  
  bug_url = forms.URLField(label='Bug URL',
                           help_text='OWP Launch Tracking or crbug.')

  impl_status_chrome = forms.ChoiceField(required=True,
                                         label='Status in Chromium',
                                         choices=IMPLEMENATION_STATUS.items())

  shipped_milestone = forms.CharField(
      label='Earliest version full feature shipped to desktop',
      help_text='(X = not shipped yet, ? = unknown)')

  standardization = forms.ChoiceField(
      label='Standardization', choices=STANDARDIZATION.items(),
      help_text=("The standardization status of the API. In bodies that don't "
                 "use this nomenclature, use the closest equivalent."))


  footprint  = forms.ChoiceField(label='Technical footprint',
                                 choices=FOOTPRINT_CHOICES.items())

  visibility  = forms.ChoiceField(
      label='Developer visibility',
      choices=VISIBILITY_CHOICES.items(),
      help_text=('How much press / media / web developer buzz will this '
                 'feature generate?'))

  safari_views = forms.ChoiceField(label='Documented Safari views',
                                   choices=VENDOR_VIEWS.items(),
                                   initial=NO_PUBLIC_SIGNALS)
  safari_views_link = forms.URLField(label='Link')

  ff_views = forms.ChoiceField(label='Documented Firefox views',
                               choices=VENDOR_VIEWS.items(),
                               initial=NO_PUBLIC_SIGNALS)
  ff_views_link = forms.URLField(label='Link')


  ie_views = forms.ChoiceField(label='Documented IE views',
                               choices=VENDOR_VIEWS.items(),
                               initial=NO_PUBLIC_SIGNALS)
  ie_views_link = forms.URLField(label='Link')

  prefixed = forms.BooleanField(required=False, initial=False, label='Prefixed?')

  spec_link = forms.URLField(label='Spec link',
                             help_text="Prefer an editor's draft.")

  
  class Meta:
    model = Feature
    exclude = ('safari_views_link', 'ff_views_link', 'ie_views_link',)

  def __init__(self, *args, **keyargs):
    super(FeatureForm, self).__init__(*args, **keyargs)

    meta = getattr(self, 'Meta', None)
    exclude = getattr(meta, 'exclude', [])

    for field_name in exclude:
     if field_name in self.fields:
       del self.fields[field_name]

    for field, val in self.fields.iteritems():
      if val.required:
       self.fields[field].widget.attrs['required'] = 'required'
