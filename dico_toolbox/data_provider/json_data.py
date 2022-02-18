
import json
import re

class JsonData:
  """Basic handling of json data"""

  def __init__(self, json_string):
    self.data = json.loads(json_string)

  def _filter_list(self, regex, iterable):
    """Filter list items by regular expression"""
    return list(filter(regex.search, iterable))

  def _filter_dict(self, regex, dictionnary):
    """Filter dictionnary items by regular expression"""
    return {k:v for k,v in dictionnary.items() if regex.search(k)}


  def _filter(self, regular_expression, object):
    """Filter objects by reuglar expression"""
    result = None
    regex = re.compile(regular_expression)
    if isinstance(object, dict):
      result = self._filter_dict(regex, object)
    elif isinstance(object, list):
      result = self._filter_list(regex, object)

    return result