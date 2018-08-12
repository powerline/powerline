local wibox = require('wibox')
local awful = require('awful')

powerline_widget = wibox.widget.textbox()
powerline_widget:set_align('right')

function powerline(mode, widget) end

if string.find(awesome.version, 'v4') then
 	awful.spawn.with_shell('powerline-daemon -q')
 	awful.spawn.with_shell('powerline wm.awesome')
else
 	awful.util.spawn_with_shell('powerline-daemon -q')
 	awful.util.spawn_with_shell('powerline wm.awesome')
end
