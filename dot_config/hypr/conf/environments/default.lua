local HOME = os.getenv("HOME") or ""
local current_path = os.getenv("PATH") or ""

if HOME ~= "" then
    hl.env("PATH", HOME .. "/.cargo/bin:" .. HOME .. "/.local/bin:" .. current_path)
end

-- Wayland/session identity
hl.env("DESKTOP_SESSION", "Hyprland")
hl.env("XDG_CURRENT_DESKTOP", "Hyprland")
hl.env("XDG_SESSION_DESKTOP", "Hyprland")
hl.env("XDG_SESSION_TYPE", "wayland")

-- Toolkit backends
hl.env("GDK_BACKEND", "wayland,x11,*")
hl.env("GDK_SCALE", "1")
hl.env("CLUTTER_BACKEND", "wayland")
hl.env("QT_QPA_PLATFORM", "wayland;xcb")
hl.env("QT_QPA_PLATFORMTHEME", "qt6ct")
hl.env("QT_WAYLAND_DISABLE_WINDOWDECORATION", "1")
hl.env("SDL_VIDEODRIVER", "wayland")
hl.env("MOZ_ENABLE_WAYLAND", "1")
hl.env("OZONE_PLATFORM", "wayland")
hl.env("ELECTRON_OZONE_PLATFORM_HINT", "wayland")

-- Cursor
hl.env("XCURSOR_THEME", "Bibata-Modern-Ice")
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")

-- Quickshell
hl.env("QS_NO_RELOAD_POPUP", "1")

hl.config({
    xwayland = {
        force_zero_scaling = true,
    },
})
