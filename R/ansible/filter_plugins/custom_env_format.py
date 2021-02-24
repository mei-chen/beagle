from jinja2.utils import soft_unicode

def env_format(dict):
  list = []
  for key, value in dict.iteritems():
    list.append(soft_unicode("%s=\"%s\"") % (key, value))
  return list

class FilterModule(object):
  def filters(self):
    return {
      'custom_env_format': env_format,
    }
