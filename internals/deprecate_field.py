import logging

from internals.core_enums import STANDARD_MATURITY_BACKFILL
from framework.basehandlers import FlaskHandler
from internals.core_models import Feature

class WriteStandardMaturityHandler(FlaskHandler):

  def get_template_data(self, **kwargs):
    """Writes standard_maturity field from the old standardization field."""
    self.require_cron_header()
    q = Feature.query()
    features = q.fetch()
    update_count = 0
    for feature in features:
      if ((feature.standardization is not None and feature.standardization > 0)
           and (feature.standard_maturity is None or feature.standard_maturity == 0)):
        update_count += 1
        feature.standard_maturity = STANDARD_MATURITY_BACKFILL[feature.standardization]
        feature.put(notify=False)

    logging.info(
        f'{update_count} features updated with standard_maturity field.')
    return 'Success'
