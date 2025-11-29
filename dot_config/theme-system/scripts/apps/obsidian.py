"""Obsidian markdown editor theme integration"""

import json
import os
import sys
from pathlib import Path
from .base import BaseApp
from utils import get_material_colors, is_dynamic_theme


class ObsidianTheme(BaseApp):
    """Obsidian theme generator

    Method: hybrid (Style Settings for static, CSS snippets for dynamic)
    Reload: automatic (CSS snippets hot-reload)

    Special: Per-vault configuration - must iterate over configured vault paths
    """

    # GUI-only app - skip on headless systems
    requires_gui = True

    # Catppuccin flavor to Style Settings class mapping
    FLAVOR_MAP = {
        "mocha": "ctp-mocha",
        "macchiato": "ctp-macchiato",
        "frappe": "ctp-frappe",
        "latte": "ctp-latte",
    }

    # User's preferred accent (for static themes only)
    ACCENT = "ctp-accent-mauve"

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> str:
        """Convert hex color to RGB triplet string for Catppuccin CSS variables.

        Catppuccin uses RGB triplets like '203, 166, 247' instead of hex.
        """
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}"

    def __init__(self, config_home: Path):
        super().__init__("Obsidian", config_home)
        self.vault_paths = self._load_vault_paths()

    def _get_obsidian_json_path(self) -> Path:
        """Get platform-specific path to obsidian.json"""
        if sys.platform == "darwin":
            return Path.home() / "Library/Application Support/obsidian/obsidian.json"
        elif sys.platform == "win32":
            return Path(os.environ.get("APPDATA", "")) / "obsidian/obsidian.json"
        else:  # Linux
            xdg_config = Path(
                os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
            )
            return xdg_config / "obsidian/obsidian.json"

    def _load_vault_paths(self) -> list[Path]:
        """Load vault paths from Obsidian's obsidian.json"""
        obsidian_json = self._get_obsidian_json_path()

        vaults = []
        if obsidian_json.exists():
            try:
                with open(obsidian_json) as f:
                    data = json.load(f)
                for vault_id, info in data.get("vaults", {}).items():
                    vault_path = Path(info.get("path", ""))
                    # Only include vaults that exist and have .obsidian folder
                    if vault_path.exists() and (vault_path / ".obsidian").exists():
                        vaults.append(vault_path)
            except (json.JSONDecodeError, KeyError, PermissionError) as e:
                self.log_warning(f"Failed to read obsidian.json: {e}")

        return vaults

    def apply_theme(self, theme_data: dict) -> None:
        """Apply theme to all configured Obsidian vaults"""
        if not self.vault_paths:
            self.log_warning("No Obsidian vaults found")
            return

        self.log_progress(f"Updating Obsidian ({len(self.vault_paths)} vaults)")

        for vault_path in self.vault_paths:
            self._apply_to_vault(vault_path, theme_data)

    def _apply_to_vault(self, vault_path: Path, theme_data: dict) -> None:
        """Apply theme to a single vault"""
        obsidian_dir = vault_path / ".obsidian"
        if not obsidian_dir.exists():
            self.log_warning(f"Vault not initialized: {vault_path.name}")
            return

        vault_name = vault_path.name

        if is_dynamic_theme(theme_data):
            self._apply_dynamic_theme(obsidian_dir, theme_data, vault_name)
        else:
            self._apply_static_theme(obsidian_dir, theme_data, vault_name)

    def _apply_static_theme(
        self, obsidian_dir: Path, theme_data: dict, vault_name: str
    ) -> None:
        """Apply static Catppuccin theme via Style Settings"""
        variant = theme_data.get("theme", {}).get("name", "mocha")
        flavor_class = self.FLAVOR_MAP.get(variant, "ctp-mocha")

        # Update Style Settings data.json
        data_json = obsidian_dir / "plugins/obsidian-style-settings/data.json"
        if data_json.exists():
            self._update_style_settings(data_json, flavor_class)
        else:
            self.log_warning(f"Style Settings not found in {vault_name}")

        # Disable dynamic snippet if enabled
        self._toggle_snippet(obsidian_dir, "dynamic-colors", enabled=False)

        self.log_success(f"Obsidian/{vault_name}: {variant}")

    def _apply_dynamic_theme(
        self, obsidian_dir: Path, theme_data: dict, vault_name: str
    ) -> None:
        """Apply dynamic Material Design 3 theme via CSS snippet"""
        mat = get_material_colors(theme_data)
        variant = theme_data.get("theme", {}).get("variant", "dark")
        is_dark = variant != "light"

        # Generate CSS snippet
        css_content = self._generate_dynamic_css(mat, is_dark)

        # Write to snippets folder
        snippets_dir = obsidian_dir / "snippets"
        snippets_dir.mkdir(exist_ok=True)

        snippet_file = snippets_dir / "dynamic-colors.css"
        with open(snippet_file, "w") as f:
            f.write(css_content)

        # Enable the snippet
        self._toggle_snippet(obsidian_dir, "dynamic-colors", enabled=True)

        self.log_success(f"Obsidian/{vault_name}: dynamic")

    def _generate_dynamic_css(self, mat: dict, is_dark: bool) -> str:
        """Generate CSS snippet with Material Design 3 colors.

        Catppuccin uses RGB triplets (e.g., '203, 166, 247') for its internal
        variables like --ctp-accent, --ctp-h1, etc. We override ALL Catppuccin
        variables to ensure complete dynamic theming.

        Variable mapping from Catppuccin defaults to MD3:
        - Bold text (--ctp-bold): sapphire → secondary (stands out)
        - Italic text (--ctp-italic): green → tertiary (different feel)
        - Strikethrough (--ctp-strikethrough): maroon → error (deletion feel)
        - Blockquotes (--ctp-blockquote): accent → primary
        - Page title (--ctp-page-title): text → on_surface
        """
        mode_class = ".theme-dark" if is_dark else ".theme-light"

        # Get MD3 colors with fallbacks
        primary = mat.get("primary", "#cba6f7")
        secondary = mat.get("secondary", "#89b4fa")
        tertiary = mat.get("tertiary", "#a6e3a1")
        error = mat.get("error", "#f38ba8")
        background = mat.get("background", "#1e1e2e")
        surface = mat.get("surface", "#181825")
        surface_dim = mat.get("surface_dim", "#141420")
        surface_container = mat.get("surface_container", "#313244")
        surface_container_low = mat.get("surface_container_low", "#1e1e2e")
        surface_container_high = mat.get("surface_container_high", "#45475a")
        surface_container_highest = mat.get("surface_container_highest", "#585b70")
        on_surface = mat.get("on_surface", "#cdd6f4")
        on_primary = mat.get("on_primary", "#1e1e2e")
        outline = mat.get("outline", "#6c7086")
        outline_variant = mat.get("outline_variant", "#45475a")

        # Convert to RGB triplets for Catppuccin variables
        primary_rgb = self._hex_to_rgb(primary)
        secondary_rgb = self._hex_to_rgb(secondary)
        tertiary_rgb = self._hex_to_rgb(tertiary)
        error_rgb = self._hex_to_rgb(error)
        background_rgb = self._hex_to_rgb(background)
        surface_rgb = self._hex_to_rgb(surface)
        surface_dim_rgb = self._hex_to_rgb(surface_dim)
        surface_container_rgb = self._hex_to_rgb(surface_container)
        surface_container_low_rgb = self._hex_to_rgb(surface_container_low)
        surface_container_high_rgb = self._hex_to_rgb(surface_container_high)
        surface_container_highest_rgb = self._hex_to_rgb(surface_container_highest)
        on_surface_rgb = self._hex_to_rgb(on_surface)
        outline_rgb = self._hex_to_rgb(outline)
        outline_variant_rgb = self._hex_to_rgb(outline_variant)

        return f"""/* Dynamic Colors - Generated by theme system */
/* Material Design 3 colors extracted from wallpaper */
/* Complete Catppuccin variable override for dynamic theming */

{mode_class} {{
  /* ==========================================================================
   * CATPPUCCIN CORE COLORS (RGB triplets)
   * These are the base palette colors used throughout the theme
   * ========================================================================== */
  
  /* Primary accent color - used for interactive elements, links, highlights */
  --ctp-accent: {primary_rgb} !important;
  
  /* Background hierarchy (dark to light for dark mode, light to dark for light) */
  --ctp-crust: {surface_dim_rgb} !important;
  --ctp-mantle: {surface_rgb} !important;
  --ctp-base: {background_rgb} !important;
  
  /* Surface layers for elevated elements */
  --ctp-surface0: {surface_container_low_rgb} !important;
  --ctp-surface1: {surface_container_rgb} !important;
  --ctp-surface2: {surface_container_high_rgb} !important;
  
  /* Overlay colors for modals, popups, hover states */
  --ctp-overlay0: {outline_variant_rgb} !important;
  --ctp-overlay1: {outline_rgb} !important;
  --ctp-overlay2: {surface_container_highest_rgb} !important;
  
  /* Text colors */
  --ctp-text: {on_surface_rgb} !important;
  --ctp-subtext0: {outline_rgb} !important;
  --ctp-subtext1: {outline_variant_rgb} !important;

  /* ==========================================================================
   * CATPPUCCIN NAMED COLORS (RGB triplets)
   * These map semantic Catppuccin colors to MD3 equivalents
   * ========================================================================== */
  
  /* Warm colors */
  --ctp-rosewater: {primary_rgb} !important;
  --ctp-flamingo: {primary_rgb} !important;
  --ctp-pink: {primary_rgb} !important;
  --ctp-mauve: {primary_rgb} !important;
  
  /* Alert/Error colors */
  --ctp-red: {error_rgb} !important;
  --ctp-maroon: {error_rgb} !important;
  
  /* Warm accent colors */
  --ctp-peach: {secondary_rgb} !important;
  --ctp-yellow: {secondary_rgb} !important;
  
  /* Success/Nature colors */
  --ctp-green: {tertiary_rgb} !important;
  --ctp-teal: {tertiary_rgb} !important;
  
  /* Cool colors */
  --ctp-sky: {secondary_rgb} !important;
  --ctp-sapphire: {secondary_rgb} !important;
  --ctp-blue: {secondary_rgb} !important;
  --ctp-lavender: {primary_rgb} !important;

  /* ==========================================================================
   * CATPPUCCIN TEXT STYLING (RGB triplets)
   * Bold, italic, strikethrough - these make markdown text colorful
   * ========================================================================== */
  
  /* Bold text - uses sapphire by default, we use secondary for distinction */
  --ctp-bold: {secondary_rgb} !important;
  
  /* Italic text - uses green by default, we use tertiary for variety */
  --ctp-italic: {tertiary_rgb} !important;
  
  /* Strikethrough - uses maroon by default, we use error for "deleted" feel */
  --ctp-strikethrough: {error_rgb} !important;

  /* ==========================================================================
   * CATPPUCCIN HEADING COLORS (RGB triplets)
   * Each heading level can have a distinct color
   * ========================================================================== */
  --ctp-h1: {primary_rgb} !important;
  --ctp-h2: {secondary_rgb} !important;
  --ctp-h3: {tertiary_rgb} !important;
  --ctp-h4: {tertiary_rgb} !important;
  --ctp-h5: {secondary_rgb} !important;
  --ctp-h6: {primary_rgb} !important;

  /* ==========================================================================
   * CATPPUCCIN SPECIAL ELEMENTS (RGB triplets)
   * Specific UI elements with their own color settings
   * ========================================================================== */
  
  /* Page/Inline title */
  --ctp-page-title: {on_surface_rgb} !important;
  
  /* Blockquotes */
  --ctp-blockquote: {primary_rgb} !important;
  
  /* Tags */
  --ctp-tag-pill-color: {primary_rgb} !important;

  /* ==========================================================================
   * OBSIDIAN STANDARD VARIABLES (hex colors)
   * Direct Obsidian CSS variables for non-Catppuccin elements
   * ========================================================================== */
  
  /* Backgrounds */
  --background-primary: {background} !important;
  --background-primary-alt: {surface} !important;
  --background-secondary: {surface_container} !important;
  --background-secondary-alt: {surface_container_high} !important;
  --background-modifier-border: {outline_variant} !important;
  --background-modifier-form-field: {surface_container_low} !important;
  --background-modifier-hover: {surface_container} !important;
  --background-modifier-active-hover: {surface_container_high} !important;
  --background-modifier-success: {tertiary} !important;
  --background-modifier-error: {error} !important;

  /* Text */
  --text-normal: {on_surface} !important;
  --text-muted: {outline} !important;
  --text-faint: {outline_variant} !important;
  --text-accent: {primary} !important;
  --text-accent-hover: {primary} !important;
  --text-on-accent: {on_primary} !important;
  --text-error: {error} !important;
  --text-highlight-bg: {primary}33 !important;
  --text-selection: {primary}44 !important;

  /* Interactive elements */
  --interactive-normal: {surface_container} !important;
  --interactive-hover: {surface_container_high} !important;
  --interactive-accent: {primary} !important;
  --interactive-accent-hover: {primary} !important;
  --interactive-success: {tertiary} !important;
  
  /* Color accent (used by Obsidian core) */
  --color-accent: {primary} !important;
  --color-accent-1: {primary} !important;
  --color-accent-2: {secondary} !important;

  /* Links */
  --link-color: {secondary} !important;
  --link-color-hover: {secondary} !important;
  --link-external-color: {tertiary} !important;
  --link-external-color-hover: {tertiary} !important;
  --link-unresolved-color: {error} !important;
  --link-unresolved-opacity: 0.7 !important;

  /* Headings (direct override for non-Catppuccin themes) */
  --h1-color: {primary} !important;
  --h2-color: {secondary} !important;
  --h3-color: {tertiary} !important;
  --h4-color: {tertiary} !important;
  --h5-color: {secondary} !important;
  --h6-color: {primary} !important;
  --inline-title-color: {on_surface} !important;

  /* Bold and Italic (direct CSS override) */
  --bold-color: {secondary} !important;
  --italic-color: {tertiary} !important;

  /* Blockquotes */
  --blockquote-border-color: {primary} !important;
  --blockquote-color: {on_surface} !important;

  /* Code */
  --code-background: {surface_container} !important;
  --code-normal: {on_surface} !important;
  --code-comment: {outline} !important;
  --code-function: {secondary} !important;
  --code-keyword: {primary} !important;
  --code-string: {tertiary} !important;
  --code-tag: {error} !important;
  --code-value: {secondary} !important;

  /* Tags */
  --tag-color: {primary} !important;
  --tag-color-hover: {primary} !important;
  --tag-background: {surface_container} !important;
  --tag-background-hover: {surface_container_high} !important;

  /* Lists */
  --list-marker-color: {primary} !important;
  --checkbox-color: {primary} !important;
  --checkbox-color-hover: {primary} !important;
  --checklist-done-color: {primary} !important;
  --indentation-guide-color: {outline_variant} !important;
  --indentation-guide-color-active: {primary} !important;

  /* Scrollbar */
  --scrollbar-bg: transparent !important;
  --scrollbar-thumb-bg: {outline_variant} !important;
  --scrollbar-active-thumb-bg: {outline} !important;

  /* Syntax highlighting colors */
  --color-red: {error} !important;
  --color-red-rgb: {error_rgb} !important;
  --color-orange: {secondary} !important;
  --color-orange-rgb: {secondary_rgb} !important;
  --color-yellow: {secondary} !important;
  --color-yellow-rgb: {secondary_rgb} !important;
  --color-green: {tertiary} !important;
  --color-green-rgb: {tertiary_rgb} !important;
  --color-cyan: {tertiary} !important;
  --color-cyan-rgb: {tertiary_rgb} !important;
  --color-blue: {secondary} !important;
  --color-blue-rgb: {secondary_rgb} !important;
  --color-purple: {primary} !important;
  --color-purple-rgb: {primary_rgb} !important;
  --color-pink: {primary} !important;
  --color-pink-rgb: {primary_rgb} !important;

  /* Graph view */
  --graph-line: {outline_variant} !important;
  --graph-node: {primary} !important;
  --graph-node-focused: {primary} !important;
  --graph-node-tag: {tertiary} !important;
  --graph-node-attachment: {secondary} !important;
}}

/* ==========================================================================
 * DIRECT ELEMENT OVERRIDES
 * Some elements need direct CSS targeting, not just variables
 * ========================================================================== */

{mode_class} strong,
{mode_class} .cm-strong {{
  color: {secondary} !important;
}}

{mode_class} em,
{mode_class} .cm-em {{
  color: {tertiary} !important;
}}

{mode_class} del,
{mode_class} .cm-strikethrough {{
  color: {error} !important;
}}

{mode_class} .cm-hmd-internal-link,
{mode_class} .cm-link {{
  color: {secondary} !important;
}}

{mode_class} .cm-url {{
  color: {tertiary} !important;
}}
"""

    def _update_style_settings(self, data_json: Path, flavor_class: str) -> None:
        """Update Style Settings data.json with new flavor"""
        try:
            with open(data_json, "r") as f:
                data = json.load(f)

            # Update Catppuccin settings
            data["catppuccin-theme-settings@@catppuccin-theme-dark"] = flavor_class
            data["catppuccin-theme-settings@@catppuccin-theme-accents"] = self.ACCENT

            with open(data_json, "w") as f:
                json.dump(data, f, indent=2)
                f.write("\n")

        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.log_warning(f"Failed to update Style Settings: {e}")

    def _toggle_snippet(
        self, obsidian_dir: Path, snippet_name: str, enabled: bool
    ) -> None:
        """Enable or disable a CSS snippet in appearance.json"""
        appearance_json = obsidian_dir / "appearance.json"
        if not appearance_json.exists():
            return

        try:
            with open(appearance_json, "r") as f:
                data = json.load(f)

            snippets = data.get("enabledCssSnippets", [])

            if enabled and snippet_name not in snippets:
                snippets.append(snippet_name)
            elif not enabled and snippet_name in snippets:
                snippets.remove(snippet_name)

            data["enabledCssSnippets"] = snippets

            with open(appearance_json, "w") as f:
                json.dump(data, f, indent=2)
                f.write("\n")

        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.log_warning(f"Failed to update appearance.json: {e}")
