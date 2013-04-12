import webapp2

import common
import models
import settings


class StableInstances(common.JSONHandler):

  def get(self):
    data = models.StableInstance.all().order('-date').fetch(limit=None)
    super(StableInstances, self).get(data)


class QueryStackRank(common.JSONHandler):

  def get(self):
    # Find last date data was fetched by pulling one entry.
    result = models.StableInstance.all().order('-date').get()

    data = []
    if result:
      data_last_added_on = result.date

      query = models.StableInstance.all()
      query.filter('date =', data_last_added_on)
      query.order('-hits')

      data = query.fetch(limit=None)

    super(QueryStackRank, self).get(data)


app = webapp2.WSGIApplication([
  ('/data/querystableinstances', StableInstances),
  ('/data/querystackrank', QueryStackRank)
], debug=settings.DEBUG)
