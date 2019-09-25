from powerline.bindings.ipython.since_7 import PowerlinePrompts
import os
c = get_config()
c.TerminalInteractiveShell.simple_prompt = False
c.TerminalIPythonApp.display_banner = False
c.TerminalInteractiveShell.prompts_class = PowerlinePrompts
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
