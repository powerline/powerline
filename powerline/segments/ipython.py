# vim:fileencoding=utf-8:noet

from powerline.theme import requires_segment_info


@requires_segment_info
def prompt_count(pl, segment_info):
	return str(segment_info['ipython'].prompt_count)
