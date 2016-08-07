from django import template

register = template.Library()

@register.simple_tag
def inline_file(path):
  if path[0] == '/':
    path = path[1:]

  content = ''
  with open(path, 'r') as f:
    content = f.read()
  return content
