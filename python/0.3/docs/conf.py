import sys, os
sys.path.insert(0, os.path.abspath(".."))

extensions = ['sphinx.ext.autodoc']
autodoc_member_order = 'bysource'

source_suffix = '.rst'
master_doc = 'index'

project = u'Teleport'
copyright = u'2016, Alexei Boronine'

version = '0.3.1'
release = '0.3.1'

html_theme = 'alabaster'

htmlhelp_basename = 'teleportdocs'
