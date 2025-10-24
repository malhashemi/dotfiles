return {
  "folke/snacks.nvim",
  opts = {
    explorer = {
      enabled = true,
    },
    picker = {
      sources = {
        explorer = {
          hidden = true,
          follow = true,
          ignored = true,
        },
      },
    },
  },
}
