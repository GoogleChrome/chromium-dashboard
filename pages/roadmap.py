from __future__ import division
from __future__ import print_function

# -*- coding: utf-8 -*-
# Copyright 2021 Google Inc.
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

__author__ = 'shivam.agrawal.2000@gmail.com (Shivam Agarwal)'

from framework import basehandlers
import settings

class RoadmapHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'roadmap.html'

  def get_template_data(self):
    return {}


app = basehandlers.FlaskApplication([
  ('/roadmap', RoadmapHandler),
], debug=settings.DEBUG)
