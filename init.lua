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
