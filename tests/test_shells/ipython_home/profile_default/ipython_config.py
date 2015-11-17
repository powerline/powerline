import os
c = get_config()
c.InteractiveShellApp.extensions = ['powerline.bindings.ipython.post_0_11']
c.TerminalInteractiveShell.autocall = 1
c.Powerline.config_paths = [os.path.abspath('powerline/config_files')]
c.Powerline.theme_overrides = {
	'in': {
		'segment_data': {
			'virtualenv': {
				'display': False
			}
		}
	}
}
c.Powerline.config_overrides = {
	'common': {
		'default_top_theme': 'ascii'
	}
}
