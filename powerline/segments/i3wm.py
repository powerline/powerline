# vim:fileencoding=utf-8:noet

from powerline.theme import requires_segment_info
import i3

def calcgrp( w ):
	group = ["workspace"]
	if w['urgent']: group.append( 'w_urgent' )
	if w['visible']: group.append( 'w_visible' )
	if w['focused']: return "w_focused" #group.append( 'w_focused' )
	return group

def workspaces( pl ):
	'''Return workspace list

	Highlight groups used: ``workspace, visible, focused, urgent``
	'''
	return [ {'contents': w['name'], 'highlight_group': calcgrp( w )} for w in i3.get_workspaces() ]
