local wezterm = require 'wezterm'
return {
    window_background_opacity = 0.7,
    font = wezterm.font 'JetBrains Mono',
    -- changing initial size doesn't seem to be working right now...
    initial_cols = 80,
    initial_rows = 40,
}
