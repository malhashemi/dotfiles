-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here

-- Copilot & Completions Management
local state_file = vim.fn.stdpath("data") .. "/ai_completion_state.json"

-- Function to save state
local function save_ai_state(supermaven, copilot)
  local state = { supermaven = supermaven, copilot = copilot }
  vim.fn.writefile({ vim.fn.json_encode(state) }, state_file)
end

-- Function to load state
local function load_ai_state()
  if vim.fn.filereadable(state_file) == 1 then
    local content = vim.fn.readfile(state_file)
    if #content > 0 then
      return vim.fn.json_decode(content[1])
    end
  end
  return { supermaven = true, copilot = false }  -- defaults
end

-- Apply saved state on startup
vim.api.nvim_create_autocmd("VimEnter", {
  callback = function()
    vim.defer_fn(function()
      local state = load_ai_state()
      
      -- Set initial state tracking
      vim.g.supermaven_enabled = state.supermaven
      vim.g.copilot_enabled = state.copilot
      
      -- Apply Copilot state
      if state.copilot then
        require("copilot.suggestion").toggle_auto_trigger()
      end
      
      -- Apply Supermaven state  
      if state.supermaven then
        vim.cmd("SupermavenUseFree")  -- Activate free version first
        vim.defer_fn(function()
          vim.cmd("SupermavenStart")
        end, 100)
      else
        vim.cmd("SupermavenStop")
      end
      
      -- Show what's loaded
      vim.notify(string.format("AI Completion loaded: Supermaven %s, Copilot %s", 
        state.supermaven and "enabled" or "disabled",
        state.copilot and "enabled" or "disabled"
      ))
    end, 500)  -- Small delay to ensure plugins are loaded
  end,
})

vim.keymap.set("n", "<leader>acs", function()
  -- Check current state before toggle
  local was_enabled = vim.g.supermaven_enabled ~= false
  
  vim.cmd("SupermavenToggle")
  
  -- The state should now be opposite
  local enabled = not was_enabled
  vim.g.supermaven_enabled = enabled  -- Update the global variable
  
  vim.notify("Supermaven " .. (enabled and "enabled" or "disabled"))
  
  -- Save state
  local state = load_ai_state()
  save_ai_state(enabled, state.copilot)
end, { desc = "Toggle Supermaven" })

vim.keymap.set("n", "<leader>acc", function()
  local copilot = require("copilot.suggestion")
  copilot.toggle_auto_trigger()
  
  -- Check the new state after toggling
  local enabled = vim.b.copilot_suggestion_auto_trigger == true
  vim.g.copilot_enabled = enabled  -- Track globally
  
  vim.notify("Copilot " .. (enabled and "enabled" or "disabled"))
  
  -- Save state
  local state = load_ai_state()
  save_ai_state(state.supermaven, enabled)
end, { desc = "Toggle Copilot" })

vim.keymap.set("n", "<leader>acx", function()
  local copilot = require("copilot.suggestion")
  local copilot_enabled = vim.b.copilot_suggestion_auto_trigger ~= false
  
  if copilot_enabled then
    copilot.toggle_auto_trigger()  -- Disable Copilot
    vim.cmd("SupermavenStart")     -- Enable Supermaven
    vim.notify("Switched to Supermaven")
    save_ai_state(true, false)
  else
    vim.cmd("SupermavenStop")      -- Disable Supermaven
    copilot.toggle_auto_trigger()  -- Enable Copilot
    vim.notify("Switched to Copilot")
    save_ai_state(false, true)
  end
end, { desc = "Switch Copilot/Supermaven" })

-- Check AI completion status
vim.keymap.set("n", "<leader>aci", function()
  -- Check Supermaven more reliably
  local supermaven_status = "unknown"
  local ok, supermaven = pcall(require, "supermaven-nvim.api")
  if ok and supermaven then
    -- Try to check if it's running
    supermaven_status = (vim.g.supermaven_enabled == false) and "disabled" or "enabled"
  end
  
  -- Check Copilot status
  local copilot_status = "disabled"
  local copilot_ok, copilot_client = pcall(require, "copilot.client")
  if copilot_ok then
    copilot_status = (vim.g.copilot_enabled ~= false) and "enabled" or "disabled"
  end
  -- Also check suggestion auto trigger
  if vim.b.copilot_suggestion_auto_trigger == true then
    copilot_status = "enabled (suggestions on)"
  elseif vim.b.copilot_suggestion_auto_trigger == false then
    copilot_status = "enabled (suggestions off)"
  end
  
  vim.notify(string.format(
    "AI Completion Status:\nSupermaven: %s\nCopilot: %s\nBuffer type: %s\nFiletype: %s",
    supermaven_status,
    copilot_status,
    vim.bo.buftype == "" and "normal" or vim.bo.buftype,
    vim.bo.filetype == "" and "none" or vim.bo.filetype
  ))
end, { desc = "AI Completion Info" })

-- Manually restart Supermaven (useful to keep)
vim.keymap.set("n", "<leader>acr", function()
  vim.cmd("SupermavenRestart")
  vim.notify("Supermaven restarted")
end, { desc = "Restart Supermaven" })

vim.keymap.set("n", "<leader>r", function()
  vim.fn.setreg("+", vim.fn.fnamemodify(vim.fn.expand("%"), ":."))
  vim.notify("📋 Copied relative path to clipboard", vim.log.levels.INFO)
end, { desc = "📋 Copy relative path" })

vim.keymap.set("n", "<leader>G", "G$", { desc = "Go to end of document" })


