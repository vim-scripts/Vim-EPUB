#!/usr/bin/python2
# -*- coding:Utf-8 -*-

# Vim-EPUB css python module
# Part of vim-epub plugin for Vim
# Released under GNU GPL version 3
# By Etienne Nadji <etnadji@eml.cc>

from __future__ import unicode_literals

import os

from vim_epub import vimvar

def is_cleanup(vim,field):
    if field == "panels":
        if vimvar(vim,"VimEPUB_CleanPanels") == "True":
            return True
        else:
            return False

    elif field == "all":
        if vimvar(vim,"VimEPUB_CleanPanels") == "True":
            return True

    else:
        return False

def active_cleanup(vim,field):
    if field == "panels":
        vim.command('let g:VimEPUB_CleanPanels = "True"')

def desactive_cleanup(vim,field):
    if field == "panels":
        vim.command('let g:VimEPUB_CleanPanels = "False"')

def clean_panels(vim):
    """Clean informations panels files."""

    curdir = os.path.realpath(os.curdir)

    metadatas = "{0}{1}metadatas.txt".format(curdir,os.sep)
    fontdefs = "{0}{1}FontDefinitions.txt".format(curdir,os.sep)

    for panel in [metadatas,fontdefs]:
        if os.path.exists(panel):
            os.remove(panel)

    desactive_cleanup(vim,"panels")

def cleanup(vim,clean_all=False):
    """Clean up VimEPUB temporary files not produced with vim_epub.EPUB"""

    if clean_all:
        c_all = is_cleanup(vim,"all")
    else:
        panels = is_cleanup(vim,"panels")

    if panels or c_all: clean_panels(vim)

# vim:set shiftwidth=4 softtabstop=4:
