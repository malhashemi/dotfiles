hl.config({
    general = {
        gaps_in  = 10,
        gaps_out = 20,
        border_size = 2,
        col = {
            active_border   = { colors = {on_primary, on_primary, primary, primary, primary, on_primary, on_primary}, angle = 0 },
            inactive_border = on_primary,
        },
        resize_on_border = true,
        allow_tearing = false,
        layout = "dwindle",
    }
})