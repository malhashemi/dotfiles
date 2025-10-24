return {
  {
    "catppuccin/nvim",
    name = "catppuccin",
    priority = 1000,
    opts = {
      flavour = "auto",  -- Auto-detect from vim.o.background
      background = {
        light = "latte",
        dark = "mocha",
      },
      transparent_background = false,
      highlight_overrides = {
        -- Apply to ALL themes (mocha, latte, frappe, macchiato)
        all = function(colors)
          return {
            -- Cursor (for Neovide compatibility and all themes)
            Cursor = { fg = colors.base, bg = colors.mauve },
            lCursor = { fg = colors.base, bg = colors.mauve },
            TermCursor = { fg = colors.base, bg = colors.mauve },
            
            -- Set Mauve as accent color for various UI elements
            CursorLineNr = { fg = colors.mauve },
            LineNr = { fg = colors.overlay0 },
            -- Telescope
            TelescopeSelection = { bg = colors.surface0, fg = colors.mauve },
            TelescopeSelectionCaret = { fg = colors.mauve },
            TelescopeMatching = { fg = colors.mauve, bold = true },
            TelescopeBorder = { fg = colors.mauve },
            TelescopePromptBorder = { fg = colors.mauve },
            TelescopeResultsBorder = { fg = colors.mauve },
            TelescopePreviewBorder = { fg = colors.mauve },
            TelescopePromptPrefix = { fg = colors.mauve },
            -- Neo-tree
            NeoTreeCursorLine = { bg = colors.surface0 },
            NeoTreeDirectoryIcon = { fg = colors.mauve },
            NeoTreeRootName = { fg = colors.mauve, bold = true },
            NeoTreeFileName = { fg = colors.text },
            NeoTreeFileIcon = { fg = colors.mauve },
            NeoTreeFloatBorder = { fg = colors.mauve },
            -- Dashboard
            DashboardHeader = { fg = colors.mauve },
            DashboardCenter = { fg = colors.mauve },
            DashboardShortCut = { fg = colors.mauve },
            DashboardFooter = { fg = colors.mauve },
            -- BufferLine
            BufferLineIndicatorSelected = { fg = colors.mauve },
            BufferLineFill = { bg = colors.base },
            -- IndentBlankline
            IblIndent = { fg = colors.surface0 },
            IblScope = { fg = colors.mauve },
            -- Noice
            NoiceCmdlinePopupBorder = { fg = colors.mauve },
            NoiceCmdlineIcon = { fg = colors.mauve },
            -- WhichKey
            WhichKeyGroup = { fg = colors.mauve },
            WhichKey = { fg = colors.mauve },
            -- Cmp
            CmpItemAbbrMatch = { fg = colors.mauve, bold = true },
            CmpItemAbbrMatchFuzzy = { fg = colors.mauve, bold = true },
            CmpItemKindSnippet = { fg = colors.base, bg = colors.mauve },
            CmpItemKindKeyword = { fg = colors.base, bg = colors.mauve },
            CmpItemKindText = { fg = colors.base, bg = colors.mauve },
            CmpItemKindMethod = { fg = colors.base, bg = colors.mauve },
            CmpItemKindConstructor = { fg = colors.base, bg = colors.mauve },
            CmpItemKindFunction = { fg = colors.base, bg = colors.mauve },
            CmpItemKindFolder = { fg = colors.base, bg = colors.mauve },
            CmpItemKindModule = { fg = colors.base, bg = colors.mauve },
            CmpItemKindConstant = { fg = colors.base, bg = colors.mauve },
            CmpItemKindField = { fg = colors.base, bg = colors.mauve },
            CmpItemKindProperty = { fg = colors.base, bg = colors.mauve },
            CmpItemKindEnum = { fg = colors.base, bg = colors.mauve },
            CmpItemKindUnit = { fg = colors.base, bg = colors.mauve },
            CmpItemKindClass = { fg = colors.base, bg = colors.mauve },
            CmpItemKindVariable = { fg = colors.base, bg = colors.mauve },
            CmpItemKindFile = { fg = colors.base, bg = colors.mauve },
            CmpItemKindInterface = { fg = colors.base, bg = colors.mauve },
            CmpItemKindColor = { fg = colors.base, bg = colors.mauve },
            CmpItemKindReference = { fg = colors.base, bg = colors.mauve },
            CmpItemKindEnumMember = { fg = colors.base, bg = colors.mauve },
            CmpItemKindStruct = { fg = colors.base, bg = colors.mauve },
            CmpItemKindValue = { fg = colors.base, bg = colors.mauve },
            CmpItemKindEvent = { fg = colors.base, bg = colors.mauve },
            CmpItemKindOperator = { fg = colors.base, bg = colors.mauve },
            CmpItemKindTypeParameter = { fg = colors.base, bg = colors.mauve },
          }
        end,
      },
      show_end_of_buffer = false,
      term_colors = true,
      dim_inactive = {
        enabled = false,
        shade = "dark",
        percentage = 0.15,
      },
      no_italic = false,
      no_bold = false,
      no_underline = false,
      styles = {
        comments = { "italic" },
        conditionals = { "italic" },
        loops = {},
        functions = {},
        keywords = {},
        strings = {},
        variables = {},
        numbers = {},
        booleans = {},
        properties = {},
        types = {},
        operators = {},
      },
      integrations = {
        cmp = true,
        gitsigns = true,
        nvimtree = true,
        treesitter = true,
        notify = true,
        noice = true,
        mason = true,
        neotree = true,
        native_lsp = {
          enabled = true,
          virtual_text = {
            errors = { "italic" },
            hints = { "italic" },
            warnings = { "italic" },
            information = { "italic" },
          },
          underlines = {
            errors = { "underline" },
            hints = { "underline" },
            warnings = { "underline" },
            information = { "underline" },
          },
        },
        telescope = {
          enabled = true,
        },
        which_key = true,
        dashboard = true,
        alpha = true,
        mini = {
          enabled = true,
          indentscope_color = "",
        },
      },
    },
    config = function(_, opts)
      -- REMOVED: color_overrides logic - dynamic theme is now a standalone colorscheme
      
      -- Read opacity data to determine if transparency needed
      local opacity_ok, opacity_data = pcall(require, 'config.opacity-data')
      if opacity_ok and not vim.g.neovide then
        -- Terminal: Catppuccin transparent_background setting
        if opacity_data.opacity < 1.0 then
          opts.transparent_background = true
        end
      end
      
      -- Clear colors-nvim module to prevent static themes from using dynamic colors
      package.loaded["themes.colors-nvim"] = nil
      
      -- Clear Catppuccin compilation cache to force fresh highlights
      local cache_path = vim.fn.stdpath("cache") .. "/catppuccin"
      if vim.fn.isdirectory(cache_path) == 1 then
        vim.fn.delete(cache_path, "rf")
      end
      
      require("catppuccin").setup(opts)

      -- Create manual theme switch commands (keep these for manual switching)
      vim.api.nvim_create_user_command("CatppuccinLatte", function()
        vim.cmd("colorscheme catppuccin-latte")
      end, {})
      
      vim.api.nvim_create_user_command("CatppuccinFrappe", function()
        vim.cmd("colorscheme catppuccin-frappe")
      end, {})
      
      vim.api.nvim_create_user_command("CatppuccinMacchiato", function()
        vim.cmd("colorscheme catppuccin-macchiato")
      end, {})
      
      vim.api.nvim_create_user_command("CatppuccinMocha", function()
        vim.cmd("colorscheme catppuccin-mocha")
      end, {})
      
      -- NOTE: Theme loading is handled by theme-persistence.lua autocmd
      -- NOTE: Opacity is applied by opacity autocmd after ColorScheme event
    end,
    keys = {
      -- Theme switcher keymaps under <leader>ut (for theme)
      {
        "<leader>utl",
        function()
          vim.cmd("CatppuccinLatte")
          -- ColorScheme autocmd handles persistence automatically
        end,
        desc = "Catppuccin Latte",
      },
      {
        "<leader>utf",
        function()
          vim.cmd("CatppuccinFrappe")
          -- ColorScheme autocmd handles persistence automatically
        end,
        desc = "Catppuccin Frappe",
      },
      {
        "<leader>uta",
        function()
          vim.cmd("CatppuccinMacchiato")
          -- ColorScheme autocmd handles persistence automatically
        end,
        desc = "Catppuccin Macchiato",
      },
      {
        "<leader>utm",
        function()
          vim.cmd("CatppuccinMocha")
          -- ColorScheme autocmd handles persistence automatically
        end,
        desc = "Catppuccin Mocha",
      },
      {
        "<leader>utd",
        function()
          vim.cmd("colorscheme dynamic")
          -- ColorScheme autocmd handles persistence automatically
        end,
        desc = "Dynamic Theme",
      },
    },
  },
  {
    "LazyVim/LazyVim",
    opts = {
      -- Don't set default colorscheme - theme-persistence handles loading
      colorscheme = function() end,
    },
  },
}
