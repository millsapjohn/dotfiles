vim.g.loaded = 1
vim.g.loaded_netrwplugin = 1
local opt = vim.opt
local fn = vim.fn
local g = vim.g
local cmd = vim.cmd

opt.cursorline = true
opt.shiftwidth = 4
opt.autoindent = true
opt.tabstop = 4
opt.softtabstop = 4
opt.expandtab = true
opt.joinspaces = true
opt.encoding = "utf-8"
opt.smartindent = true
opt.wrap = off
opt.number = true
opt.ignorecase = true
opt.smartcase = true
opt.hlsearch = false
opt.breakindent = true
opt.showmode = false

local install_path = fn.stdpath('data') .. '/site/pack/packer/start/packer.nvim'
local install_plugins = false

if fn.empty(fn.glob(install_path)) > 0 then
    print('Installing packer...')
    local packer_url = 'https://github.com/wbthomason/packer.nvim'
    fn.system({'git', 'clone', '--depth', '1', packer_url, install_path})

    cmd('packadd packer.nvim')
    install_plugins = true
end

require('packer').startup(function(use)
    use 'wbthomason/packer.nvim'

    use 'nvim-lualine/lualine.nvim'
    
    use 'kyazdani42/nvim-tree.lua'

    use 'nvim-lua/plenary.nvim'

    use 'neovim/nvim-lspconfig'

    use({
        "j-hui/fidget.nvim",
        config = function()
            require("fidget").setup()
        end
    })

    use 'hrsh7th/nvim-cmp'

    use({
        "hrsh7th/cmp-nvim-lsp",
        "hrsh7th/cmp-vsnip",
        "hrsh7th/cmp-path",
        "hrsh7th/cmp-buffer",
        after = { "hrsh7th/nvim-cmp" },
        requires = { "hrsh7th/nvim-cmp" },
    })

    use 'hrsh7th/vim-vsnip'

    use 'simrat39/rust-tools.nvim'

    use 'nvim-lua/popup.nvim'
    
    use {
        'catppuccin/nvim',
        as = 'catppuccin',
        config = function()
            require('catppuccin').setup {
                flavour = 'macchiato'
            }
            vim.api.nvim_command 'colorscheme catppuccin'
        end
    }

    if install_plugins then
        require('packer').sync()
    end
end)

require('lualine').setup({
    options = {
        theme = 'onedark',
        icons_enabled = true,
        component_separators = '|',
        section_separators = '',
    },
continue})

require('nvim-tree').setup()

if install_plugins then
   return
end

vim.o.completeopt = "menuone,noinsert,noselect"

vim.opt.shortmess = vim.opt.shortmess + "c"

local function on_attach(client, buffer)
end

local opts = {
    tools = {
        runnables = {
            use_telescope = true,
        },
        inlay_hints = {
            auto = true,
            show_parameter_hints = false,
            parameter_hints_prefix = "",
            other_hints_prefix = "",
        },
    },
    server = {
        on_attach = on_attach,
        settings = {
            ["rust-analyzer"] = {
                checkOnSave = {
                    command = "clippy",
                },
            },
        },
    },
}

require("rust-tools").setup(opts)

local cmp = require("cmp")
cmp.setup({
    preselect = cmp.PreselectMode.None,
    snippet = {
        expand = function(args)
            vim.fn["vsnip#anonymous"](args.body)
        end,
    },
    mapping = {
        ["<C-p>"] = cmp.mapping.select_prev_item(),
        ["<C-n>"] = cmp.mapping.select_next_item(),
        ["<S-Tab>"] = cmp.mapping.select_prev_item(),
        ["<Tab>"] = cmp.mapping.select_next_item(),
        ["<C-d>"] = cmp.mapping.scroll_docs(-4),
        ["<C-f>"] = cmp.mapping.scroll_docs(4),
        ["<C-Space>"] = cmp.mapping.complete(),
        ["<C-e>"] = cmp.mapping.close(),
        ["<CR>"] = cmp.mapping.confirm({
            behavior = cmp.ConfirmBehavior.Insert,
            select = true,
        }),
    },

    sources = {
        { name = "nvim_lsp" },
        { name = "vsnip" },
        { name = "path" },
        { name = "buffer" },
    },
})
