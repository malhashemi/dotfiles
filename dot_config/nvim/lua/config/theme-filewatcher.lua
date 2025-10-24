-- Theme File Watcher
-- Automatically reloads theme when external files change
-- Triggered by FocusGained and BufEnter events

local M = {}

-- Files to watch
local config_dir = vim.fn.stdpath('config')
local files_to_watch = {
  colors = config_dir .. '/lua/themes/colors-nvim.lua',
  state = config_dir .. '/lua/themes/theme-state.lua',
  opacity = config_dir .. '/lua/config/opacity-data.lua',
}

-- Track last modification times
local last_mtimes = {}

--- Check if file has been modified since last check
--- @param filepath string Path to file
--- @return boolean true if file was modified
local function file_changed(filepath)
  if vim.fn.filereadable(filepath) ~= 1 then
    return false
  end
  
  local stat = vim.loop.fs_stat(filepath)
  if not stat then
    return false
  end
  
  local current_mtime = stat.mtime.sec
  local last_mtime = last_mtimes[filepath]
  
  if last_mtime and current_mtime ~= last_mtime then
    last_mtimes[filepath] = current_mtime
    return true
  elseif not last_mtime then
    last_mtimes[filepath] = current_mtime
  end
  
  return false
end

--- Reload dynamic theme
local function reload_dynamic_theme()
  -- Unload cached colors module
  package.loaded['themes.colors-nvim'] = nil
  package.loaded['config.opacity-data'] = nil
  
  -- Reload colorscheme (will re-require modules)
  vim.cmd("colorscheme dynamic")
  
  vim.notify("Dynamic theme reloaded", vim.log.levels.INFO, { title = "Theme System" })
end

--- Reload static theme
local function reload_static_theme()
  -- Unload opacity data module
  package.loaded['config.opacity-data'] = nil
  
  -- Clear Catppuccin cache
  local cache_path = vim.fn.stdpath("cache") .. "/catppuccin"
  if vim.fn.isdirectory(cache_path) == 1 then
    vim.fn.delete(cache_path, "rf")
  end
  
  -- Reload current Catppuccin flavor
  local current = vim.g.colors_name
  if current and current:match("^catppuccin") then
    vim.cmd("colorscheme " .. current)
    vim.notify("Static theme reloaded", vim.log.levels.INFO, { title = "Theme System" })
  end
end

--- Reload opacity settings
local function reload_opacity()
  -- Call opacity manager's reload function directly
  -- This ensures Neovide picks up changes immediately
  local ok, opacity_manager = pcall(require, 'config.opacity-manager')
  if ok and opacity_manager.reload then
    opacity_manager.reload()
    vim.notify("Opacity updated", vim.log.levels.INFO, { title = "Theme System" })
  end
end

--- Check all watched files for changes
local function check_for_changes()
  local colors_changed = file_changed(files_to_watch.colors)
  local state_changed = file_changed(files_to_watch.state)
  local opacity_changed = file_changed(files_to_watch.opacity)
  
  -- Priority order: state (theme switch), colors (dynamic update), opacity (transparency)
  if state_changed then
    -- Theme type changed (static <-> dynamic)
    local ok, theme_state = pcall(require, 'themes.theme-state')
    package.loaded['themes.theme-state'] = nil -- Clear cache
    
    if ok and theme_state then
      if theme_state.is_dynamic then
        vim.defer_fn(reload_dynamic_theme, 50)
      else
        local flavor = theme_state.theme_name or "mocha"
        vim.defer_fn(function()
          vim.cmd("colorscheme catppuccin-" .. flavor)
        end, 50)
      end
    end
  elseif colors_changed and vim.g.colors_name == "dynamic" then
    -- Dynamic theme colors updated (e.g., wallpaper change)
    vim.defer_fn(reload_dynamic_theme, 50)
  elseif opacity_changed then
    -- Opacity value changed
    vim.defer_fn(reload_opacity, 50)
  end
end

--- Initialize file watcher
function M.setup()
  -- Initialize modification times
  for name, filepath in pairs(files_to_watch) do
    if vim.fn.filereadable(filepath) == 1 then
      local stat = vim.loop.fs_stat(filepath)
      if stat then
        last_mtimes[filepath] = stat.mtime.sec
      end
    end
  end
  
  -- Watch for file changes on focus gain and buffer enter
  vim.api.nvim_create_autocmd({'FocusGained', 'BufEnter'}, {
    group = vim.api.nvim_create_augroup('ThemeFileWatcher', { clear = true }),
    callback = check_for_changes,
    desc = "Auto-reload theme when config files change externally"
  })
end

return M
