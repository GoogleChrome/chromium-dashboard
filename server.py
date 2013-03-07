# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc.
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
#

__author__ = 'ericbidelman@chromium.org (Eric Bidelman)'

import logging
import os
import webapp2

import models
import settings

from django.template.loader import render_to_string

class LoggingHandler(webapp2.RequestHandler):

  def __init__(self, request, response):
    self.initialize(request, response)

    # Settings can't be global in python 2.7 env.
    logging.getLogger().setLevel(logging.DEBUG)
    #os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'


class ContentHandler(LoggingHandler):

  def render(self, data={}, template_path=None, status=None, message=None,
             relpath=None):
    if status is not None and status != 200:
      self.response.set_status(status, message)

    # Add template data to every request.
    template_data = {
      #'is_mobile': self.is_awesome_mobile_device(),
      'prod': settings.PROD,
      'APP_TITLE': settings.APP_TITLE
    }
    template_data.update(data) # merge in other data.

    # Add CORS and Chrome Frame to all responses.
    self.response.headers.add_header('Access-Control-Allow-Origin', '*')
    self.response.headers.add_header('X-UA-Compatible', 'IE=Edge,chrome=1')
    self.response.out.write(render_to_string(template_path, template_data))

class MainHandler(ContentHandler):

  def get(self, path):
    # Default to features page.
    if not path:
     return self.redirect('/features')

    if path:
      template_file = self.request.path[1:] + '.html'
    else:
      template_file = 'index.html'

    self.render(template_path=os.path.join(template_file))


class AdminHandler(ContentHandler):

  def get(self):
    # feature = models.Feature(
    #         type=models.Resource.Type.ARTICLE, #TODO: use correct type for content.
    #         title=doc.title(),
    #         text=doc.summary(),#.decode('utf-8').decode('ascii','ignore'),
    #         publication_date=datetime.datetime.today(), #TODO: save real date.
    #         url=db.Link(result.final_url or url),
    #         #fetch_date=datetime.date.today(),
    #         #sharers
    #         )
    template_data = {
      'feature_form': models.FeatureForm()
    }
    self.render(data=template_data, template_path=os.path.join('newfeature.html'))


def handle_404(request, response, exception):
  response.write('Oops! Not Found.')
  response.set_status(404)

# Main URL routes.
routes = [
  ('/newfeature', AdminHandler),
  ('/(.*)', MainHandler),
]

app = webapp2.WSGIApplication(routes, debug=settings.DEBUG)
app.error_handlers[404] = handle_404
