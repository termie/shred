import ConfigParser
import logging
import sys

class Shred(object):
  def __init__(self):
    self._filters = {}
    self._apps = {}
    self._pipelines = {}
    self._composites = {}
    pass

  def __str__(self):
    return "filters:\n%s\n\napps:\n%s\n\npipelines:\n%s\n\ncomposites:\n%s" % (
        pprint.pformat(self._filters),
        pprint.pformat(self._apps),
        pprint.pformat(self._pipelines),
        pprint.pformat(self._composites))

  def parse_configparser(self, cp):
    for s in cp.sections():
      if s.startswith('filter:'):
        self._parse_filter(cp, s)
      elif s.startswith('app:'):
        self._parse_app(cp, s)
      elif s.startswith('pipeline:'):
        self._parse_pipeline(cp, s)
      elif s.startswith('composite:'):
        self._parse_composite(cp, s)

  def _parse_filter(self, cp, s):
    f = cp.get(s, 'paste.filter_factory')
    mod, fact = f.split(':')
    self._filters[s[len('filter:'):]] = (mod, fact)

  def _parse_app(self, cp, s):
    f = cp.get(s, 'paste.app_factory')
    mod, fact = f.split(':')
    self._apps[s[len('app:'):]] = (mod, fact)

  def _parse_pipeline(self, cp, s):
    self._pipelines[s[len('pipeline:'):]] = cp.get(s, 'pipeline').split()

  def _parse_composite(self, cp, s):
    paths = cp.options(s)
    c = {}
    for p in paths:
      if p.startswith('/'):
        c[p] = cp.get(s, p)
    self._composites[s[len('composite:'):]] = c

  def load(self, name):
    if name in self._composites:
      return self._load_composite(name)
    elif name in self._pipelines:
      return self._default_app(self._load_pipeline(name))
    elif name in self._apps:
      return self._default_app(self._load_app(name))

  def _load_composite(self, name):
    pass

  def _load_pipeline(self, name):
    pipe = self._pipelines[name]
    pipe_r = list(reversed(pipe))

    base_app = self._load_app(pipe_r.pop(0))
    app = base_app
    for f in pipe_r:
      filt = self._load_filter(f)
      app = filt(app)
    return app

  def _load_filter(self, name):
    mod = __import__(self._filters[name][0])
    mod = sys.modules[self._filters[name][0]]
    object_chain = self._filters[name][1].split('.')
    current = mod
    for x in object_chain:
      current = getattr(current, x)
    fact = current
    return fact({})

  def _load_app(self, name):
    mod = __import__(self._apps[name][0])
    mod = sys.modules[self._apps[name][0]]

    object_chain = self._apps[name][1].split('.')
    current = mod
    for x in object_chain:
      current = getattr(current, x)

    fact = current
    return fact({})

  def _default_app(self, app):
    """Wrap an app in a default router."""
    return app
    pass


class Error(Exception):
  pass

# Paste.Deploy interface
def loadapp(s, name):
  if not s.startswith('config:'):
    raise Error('shred only supports "config:"-style configurations: %s' % s)

  cp = ConfigParser.RawConfigParser()
  cp.read(s[len('config:'):])
  sh = Shred()
  sh.parse_configparser(cp)
  return sh.load(name)
