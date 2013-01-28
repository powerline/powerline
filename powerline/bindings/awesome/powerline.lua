local wibox = require('wibox')
local awful = require('awful')

powerline_widget = wibox.widget.textbox()
powerline_widget:set_align('right')

function powerline(mode, widget) end

bindings_path = string.gsub(debug.getinfo(1).source:match('@(.*)$'), '/[^/]+$', '')
powerline_cmd = bindings_path .. '/powerline.sh'
awful.util.spawn_with_shell('ps ax -u $USER | grep "' .. powerline_cmd .. '" | grep -v grep || (' .. powerline_cmd .. ')')
