if !has('python')
  echohl ErrorMsg
  echomsg 'You need vim compiled with Python 2 support for Powerline to work.'
  echohl None
  finish
endif

python << EOF
try:
  from powerline.ext.vim import source_plugin
  source_plugin()
except ImportError:
  import sys
  print >> sys.stderr, "Powerline was not found."
  print >> sys.stderr, "Refer to https://github.com/Lokaltog/powerline"
EOF
