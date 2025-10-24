return {
  {
    "CopilotC-Nvim/CopilotChat.nvim",
    opts = {
      model = "claude-3.5-sonnet", -- Change default model here
      -- Other available models:
      -- "gpt-4.1" (default)
      -- "claude-3.5-sonnet"
      -- "claude-3.7-sonnet" 
      -- "o3-mini"
      -- "o4-mini"
      -- "gemini-2.0-flash"
      -- "gemini-2.5-pro"
      
      temperature = 0.1, -- Lower = more focused, higher = more creative
      
      window = {
        layout = "vertical",
        width = 0.5,
      },
      
      auto_insert_mode = true, -- Enter insert mode when opening chat
    },
    keys = {
      -- Add model selection keybinding
      { "<leader>am", "<cmd>CopilotChatModels<cr>", desc = "Select model" },
    },
  },
}