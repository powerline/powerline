# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.theme import requires_segment_info
from powerline.editors import (EditorTernaryOp, EditorCached, EditorFunc,
                               EditorNone, EditorBinaryOp, EditorWinPos,
                               EditorStr, editor_input_addon)
from powerline.editors.vim import VimBufferVar
from powerline.segments import Segment, with_docstring


@requires_segment_info
class CurrentTag(Segment):
	def __call__(self, segment_info, pl, flags='s'):
		return segment_info['input']['tagbar_tag_{0}'.format(flags)] or None

	def startup(self, pl, shutdown_event, flags='s'):
		return editor_input_addon((
			'tagbar_tag_{0}'.format(flags),
			(
				EditorTernaryOp(
					EditorFunc('exists', ':Tagbar'),
					EditorCached(
						'tagbar_tag_{0}'.format(flags),
						EditorBinaryOp('.', VimBufferVar('changedtick'), EditorStr('-'), EditorWinPos()[0]),
						EditorFunc('tagbar#currenttag', '%s', '', flags),
						cache_type='buffer',
					),
					EditorNone()
				),
				EditorNone()
			),
			'str',
		))


current_tag = with_docstring(CurrentTag(),
'''Return tag that is near the cursor.

:param str flags:
	Specifies additional properties of the displayed tag. Supported values:

	* s - display complete signature
	* f - display the full hierarchy of the tag
	* p - display the raw prototype

	More info in the `official documentation`_ (search for 
	“tagbar#currenttag”).

	.. _`official documentation`: https://github.com/majutsushi/tagbar/blob/master/doc/tagbar.txt
''')
