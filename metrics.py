import webapp2

import common
import models
import settings

class StableInstances(common.JSONHandler):

  def get(self):
    try:
      bucket_id = int(self.request.get('bucket_id'))
    except:
      return super(StableInstances, self).get([])

    query = models.StableInstance.all()
    query.filter('bucket_id =', bucket_id)
    query.order('date')

    # All matching results.
    data = query.fetch(None)

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
      query.order('-day_percentage')

      # All matching results.
      data = query.fetch(None)

    super(QueryStackRank, self).get(data)


app = webapp2.WSGIApplication([
  ('/data/querystableinstances', StableInstances),
  ('/data/querystackrank', QueryStackRank)
], debug=settings.DEBUG)
