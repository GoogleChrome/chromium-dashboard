from __future__ import division
from __future__ import print_function

import logging

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

import google.cloud.logging

client = google.cloud.logging.Client()
client.get_default_handler()
client.setup_logging()


@register.simple_tag
def inline_file(path):
  if path[0] == '/':
    path = path[1:]

  content = ''
  try:
    with open(path, 'r') as f:
      content = f.read()
  except IOError, e:
    logging.error('inline_file cannot read file - ' + str(e))
  return mark_safe(content)
