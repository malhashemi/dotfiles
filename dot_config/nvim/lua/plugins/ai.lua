return {
  -- Configure Copilot to be disabled by default
  {
    "zbirenbaum/copilot.lua",
    opts = {
      suggestion = {
        enabled = false,  -- Start disabled
        auto_trigger = false,
      },
      panel = {
        enabled = false,
      },
    },
  },

  -- Supermaven stays enabled (default from LazyVim extra)
  {
    "supermaven-inc/supermaven-nvim",
    opts = {
      disable_inline_completion = false,  -- Keep enabled
      keymaps = {
        accept_suggestion = "<Tab>",
        clear_suggestion = "<C-]>",
        accept_word = "<C-j>",
      },
      ignore_filetypes = {},  -- Don't ignore any filetypes
      log_level = "info",
      disable_keymaps = false,
    },
    config = function(_, opts)
      require("supermaven-nvim").setup(opts)
      -- Ensure it's started and using free version
      vim.api.nvim_create_autocmd("VimEnter", {
        callback = function()
          vim.defer_fn(function()
            -- Activate free version
            vim.cmd("SupermavenUseFree")
            vim.cmd("SupermavenStart")
          end, 100)
        end,
      })
      
      -- Force Supermaven to recognize buffers (THIS IS NEEDED FOR IT TO WORK!)
      vim.api.nvim_create_autocmd({"BufEnter", "BufWinEnter", "TextChanged", "TextChangedI"}, {
        callback = function()
          local bufnr = vim.api.nvim_get_current_buf()
          local filetype = vim.bo[bufnr].filetype
          
          -- Only for actual code files
          if filetype ~= "" and filetype ~= "TelescopePrompt" and filetype ~= "NvimTree" then
            -- Force update context
            pcall(function()
              local api = require("supermaven-nvim.api")
              if api and api.is_running and api.is_running() then
                -- Trigger context update
                vim.defer_fn(function()
                  vim.cmd("doautocmd CursorMoved")
                end, 10)
              end
            end)
          end
        end,
      })
    end,
  },

  -- Add which-key group for AI
  {
    "folke/which-key.nvim",
    opts = {
      spec = {
        { "<leader>a", group = "ai", mode = { "n", "v" } },  -- Copilot Chat (restored)
        { "<leader>ac", group = "completions", mode = "n" },  -- Completions
      },
    },
  },
}