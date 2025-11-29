// dot_config/zen-browser/user.js
// Zen Browser preferences - copied to profile folder
// These are applied on browser startup

// === Privacy & Security ===
user_pref("privacy.donottrackheader.enabled", true);
user_pref("privacy.trackingprotection.enabled", true);

// === Zen UI Preferences ===
user_pref("zen.theme.accent-color", "#cba6f7");  // Catppuccin Mauve
user_pref("zen.view.compact", false);
user_pref("zen.view.sidebar-expanded", true);
user_pref("zen.tabs.vertical", true);

// === Enable userChrome.css (if ever needed) ===
user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);

// === Performance ===
user_pref("gfx.webrender.all", true);
user_pref("layers.acceleration.force-enabled", true);

// === Disable Telemetry ===
user_pref("toolkit.telemetry.enabled", false);
user_pref("datareporting.healthreport.uploadEnabled", false);

// === Session Restore ===
user_pref("browser.startup.page", 3);  // Restore previous session
