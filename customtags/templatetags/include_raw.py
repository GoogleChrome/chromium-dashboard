from django.template import loader
from google.appengine.ext.webapp import template

register = template.create_template_register()

@register.simple_tag
def include_raw(path):
  return loader.find_template(path)[0]
 