hl.on("hyprland.start", function ()
    hl.exec_cmd("hyprctl setcursor Bibata-Modern-Ice 24")

    -- Session is uwsm-managed: uwsm preloads/exports the environment (systemd +
    -- D-Bus activation), and signalling readiness here activates
    -- graphical-session.target, which pulls the user services
    -- (elephant/walker/voice-typerd) and the xdg-desktop-portals on its own.
    -- Guarded by the uwsm env-preloader marker so it is a harmless no-op outside
    -- a uwsm session.
    hl.exec_cmd("bash -lc '[ -f \"${XDG_RUNTIME_DIR}/uwsm/env_session.conf\" ] && exec uwsm finalize XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP XDG_SESSION_TYPE'")

    hl.exec_cmd("/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1")
    hl.exec_cmd("bash -lc 'pgrep -x awww-daemon >/dev/null || exec awww-daemon --quiet'")
    hl.exec_cmd("bash -lc 'sleep 1; awww restore || true'")
    hl.exec_cmd("bash -lc 'pkill qs 2>/dev/null || true; exec qs -p \"$HOME/.config/quickshell/bar\"'")
    hl.exec_cmd("bash -lc 'sleep 1; exec qs -p \"$HOME/.config/quickshell/wallpaper\"'")
    hl.exec_cmd("bash -lc 'sleep 2; exec qs -p \"$HOME/.config/quickshell/voice\"'")
    hl.exec_cmd("~/.config/hypr/scripts/gtk.sh")
    -- swaync is started by its packaged systemd user unit (swaync.service,
    -- WantedBy=graphical-session.target) — not launched here, to avoid the
    -- double-start that left swaync.service intermittently failed under uwsm.
    hl.exec_cmd("hypridle")
    hl.exec_cmd("wl-paste --watch cliphist store")
    hl.exec_cmd("bash -lc 'pgrep -x kdeconnectd >/dev/null || setsid -f kdeconnectd >/dev/null 2>&1'")
    hl.exec_cmd("~/.config/hypr/scripts/cleanup.sh")
end)
