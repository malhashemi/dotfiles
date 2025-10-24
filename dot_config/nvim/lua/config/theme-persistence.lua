-- Theme Persistence
-- Automatically saves and loads colorscheme preference
-- Triggered by ColorScheme autocmd events

local M = {}

-- Use JSON for simpler parsing and compatibility
local state_file = vim.fn.stdpath('data') .. '/theme-state.json'

--- Load saved theme from state file
--- @return string Colorscheme name to load
function M.load_saved_theme()
  if vim.fn.filereadable(state_file) == 1 then
    local ok, json_str = pcall(vim.fn.readfile, state_file)
    if ok and json_str and #json_str > 0 then
      local decoded = vim.fn.json_decode(table.concat(json_str, '\n'))
      if decoded and decoded.colorscheme then
        return decoded.colorscheme
      end
    end
  end
  
  -- Default fallback based on background
  return vim.o.background == "light" and "catppuccin-latte" or "catppuccin-mocha"
end

--- Save current theme to state file
--- @param colorscheme_name string Name of colorscheme
function M.save_theme(colorscheme_name)
  local data = {
    colorscheme = colorscheme_name,
    last_updated = os.date('%Y-%m-%d %H:%M:%S')
  }
  
  local encoded = vim.fn.json_encode(data)
  local file = io.open(state_file, 'w')
  if file then
    file:write(encoded)
    file:close()
  end
end

--- Initialize persistence system
function M.setup()
  -- Load saved theme on startup (deferred to ensure plugins loaded)
  vim.defer_fn(function()
    local colorscheme = M.load_saved_theme()
    
    -- Validate colorscheme exists
    local ok = pcall(vim.cmd.colorscheme, colorscheme)
    if not ok then
      vim.notify(
        string.format("Saved colorscheme '%s' not found, using fallback", colorscheme),
        vim.log.levels.WARN
      )
      local fallback = vim.o.background == "light" and "catppuccin-latte" or "catppuccin-mocha"
      pcall(vim.cmd.colorscheme, fallback)
    end
  end, 0)
  
  -- Save theme on every colorscheme change
  vim.api.nvim_create_autocmd('ColorScheme', {
    group = vim.api.nvim_create_augroup('ThemePersistence', { clear = true }),
    callback = function(args)
      M.save_theme(args.match)
    end,
    desc = "Save colorscheme preference for next startup"
  })
end

return M
