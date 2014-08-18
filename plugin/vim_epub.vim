" +-----------------------------------+
" | Vim-EPUB plugin file              |
" | Part of vim-epub plugin for Vim   |
" | Released under GNU GPL version 3  |
" | By Etienne Nadji <etnadji@eml.cc> |
" +-----------------------------------+

python import sys
python import vim
python sys.path.append(vim.eval('expand("<sfile>:h")'))

"--- Sorry Windows users ! ----------------------------------------------------

python import platform
python if platform.system() == "Windows": vim.command("""echom 'Vim-EPUB does not work under Windows.'""")

"--- Functions ----------------------------------------------------------------

function! AddNewPage()
python << endOfPython
from __future__ import unicode_literals

import os

from path import path
from vim import *

from vim_epub import *
from vepub_skels import *

def get_user_input(prompt):
    vim.command('let g:EpubMode_Prompt = input("{0} ")'.format(prompt))
    print " "
    return vim.eval("g:EpubMode_Prompt")

epubs = EPUB(vim.buffers)

if epubs.valid:
    # Definition of the new page's name --------------------------------------
    page_set = False

    while not page_set:
        page_name = get_user_input("New page name?")

        if epubs.has_file(path(page_name+".xhtml")):
            print "This page already exists. Use another page name."
            continue
        else:
            page_set = True

    # Find the appropriate folder in the EPUB file for the new page.
    add_in,make_dir = epubs.guess_destination("text")
    # Make the temporary work folder
    have_tmp_path = epubs.make_working_dir()

    # Extracts the EPUB and write the new page --------------------------------
    if have_tmp_path:
        epubs.extract()

        if make_dir:
            try:
                os.mkdir(
                    "{0}{1}{2}".format(
                        epubs.temporary_epub["path"],
                        os.sep,
                        add_in
                    )
                )
            except OSError:
                pass

        page_path = None

        if add_in == "OEBPS/Text/":
            page_path = "{0}{1}{2}{1}{3}.xhtml".format(
                epubs.temporary_epub["path"],
                os.sep,
                add_in,
                page_name
            )
            in_epub_path = "Text{0}{1}.xhtml".format(os.sep,page_name)

        # Write the new page
        if page_path is not None:
            with open(page_path,"w") as npf:
                npf.write(XHTML_SKEL)

    if page_path is not None:
        # Add the page to content.opf
        epubs.epub2_append_to_opf(
            "xhtml",
            path(page_name+".xhtml"),
            in_epub_path
        )
        # Backup the old EPUB
        epubs.backup()
        # Recompression of the EPUB from the temporary work folder
        success = epubs.recompress()

        # Delete the original EPUB file _____________________________________
        if success:
            # Déplacement du nouveau fichier et nettoyage ___________________
            epubs.move_new_and_clean()

            # Rechargement du fichier EPUB __________________________________
            vim.command(
                """echom 'Page "{0}" added.'""".format(
                    page_name+".xhtml"
                )
            )
            print "Refresh the EPUB content by selecting EPUB buffer and typing :edit"
endOfPython
endfunction

function! AddNewCSS()
python << endOfPython
from __future__ import unicode_literals

import os

from path import path
from vim import *

from vim_epub import *
from vepub_skels import *

def get_user_input(prompt):
    vim.command('let g:EpubMode_Prompt = input("{0} ")'.format(prompt))
    print " "
    return vim.eval("g:EpubMode_Prompt")

epubs = EPUB(vim.buffers)

if epubs.valid:
    # Definition of the new css stylesheet's name ----------------------------
    css_set = False

    while not css_set:
        css_name = get_user_input("New CSS stylesheet name?")

        if epubs.has_file(path(css_name+".css")):
            print "This CSS stylesheet already exists. Use another name."
            continue
        else:
            css_set = True

    # Find the appropriate folder in the EPUB file for the new css.
    add_in,make_dir = epubs.guess_destination("css")
    # Make the temporary work folder
    have_tmp_path = epubs.make_working_dir()

    # Extracts the EPUB and write the new css ---------------------------------
    if have_tmp_path:
        epubs.extract()

        if make_dir:
            try:
                os.mkdir(
                    "{0}{1}{2}".format(
                        epubs.temporary_epub["path"],
                        os.sep,
                        add_in
                    )
                )
            except OSError:
                pass

        css_path = None

        if add_in == "OEBPS/Styles/":
            css_path = "{0}{1}{2}{1}{3}.css".format(
                epubs.temporary_epub["path"],
                os.sep,
                add_in,
                css_name
            )
            in_epub_path = "Styles{0}{1}.css".format(os.sep,css_name)

        # Write the new css
        if css_path is not None:
            with open(css_path,"w") as npf:
                npf.write(CSS_SKEL)

    if css_path is not None:
        # Add the css to content.opf
        epubs.epub2_append_to_opf(
            "css",
            path(css_name+".css"),
            in_epub_path
        )
        # Backup the old EPUB
        epubs.backup()
        # Recompression of the EPUB from the temporary work folder
        success = epubs.recompress()

        # Delete the original EPUB file _____________________________________
        if success:
            # Déplacement du nouveau fichier et nettoyage ___________________
            epubs.move_new_and_clean()

            # Rechargement du fichier EPUB __________________________________
            vim.command(
                """echom 'CSS stylesheet "{0}" added.'""".format(
                    css_name+".xhtml"
                )
            )
            ask_for_refresh()
endOfPython
endfunction

function! AddNewMedia()
python << endOfPython
from __future__ import unicode_literals

import os
import shutil
import zipfile

from path import path
from vim import *

from vim_epub import *

def get_user_input(prompt):
    vim.command('let g:EpubMode_Prompt = input("{0} ")'.format(prompt))
    print " "
    return vim.eval("g:EpubMode_Prompt")

epubs = EPUB(vim.buffers)

if epubs.valid:
    # Obtention du chemin du nouveau media -----------------------------------
    media_set = False
    while not media_set:
        raw_media_path = get_user_input("Media path?")

        media_path = path(raw_media_path)
        #media_name = media_path.basename()

        if epubs.has_file(media_path):
            print "This media is already in the EPUB. Use another media name."
            continue
        else:
            media_set = True

    media_name = media_path.basename()

    if media_path.ext[1:].lower() in ["jpg","jpeg","png","gif"]:
        media_type = "image"
    elif media_path.ext[1:].lower() in ["css"]:
        media_type = "css"
    elif media_path.ext[1:].lower() in ["html","xhtml"]:
        media_type = "html"
    elif media_path.ext[1:].lower() in ["ttf","woff","otf"]:
        media_type = "font"
    elif media_path.ext[1:].lower() in ["mp3","mp4","ogg"]:
        media_type = "audio"
    else:
        print "Unknown format:",media_path.ext[1:]
        media_type = "misc"

    # --------------------------------------------------------------------

    # Find the appropriate folder in the EPUB file for the new media.
    add_in,make_dir = epubs.guess_destination(media_type)

    # Make the temporary work folder
    have_tmp_path = epubs.make_working_dir()

    # Extracts the EPUB and add the media --------------------------------
    if have_tmp_path:
        epubs.extract()

        if make_dir:
            try:
                os.mkdir(
                    "{0}{1}{2}".format(
                        epubs.temporary_epub["path"],
                        os.sep,
                        add_in
                    )
                )
            except OSError:
                pass

        in_epub_path = None

        if "OEBPS" in add_in:
            # TODO add audio,video categories

            valid = False
            for mt in ["Text","Images","Styles","Fonts","Misc"]:
                if mt in add_in:
                    valid = True

            if valid:
                in_epub_path = "{0}{1}{2}".format(
                    epubs.temporary_epub["path"],
                    add_in,
                    media_name
                )
                in_epub_oebps_path = "{0}/{1}".format(
                    add_in.split("/")[1],
                    media_name
                )

        if in_epub_path is not None:
            shutil.copy(raw_media_path,in_epub_path)

    if in_epub_path is not None:
        # Add the media to content.opf
        epubs.epub2_append_to_opf(
            media_path.ext[1:].lower(),
            media_path,
            in_epub_oebps_path
        )
        # Backup the old EPUB
        epubs.backup()
        # Recompression of the EPUB from the temporary work folder
        success = epubs.recompress()

        # Delete the original EPUB file _____________________________________
        if success:
            # Replace the old epub file with the new and clean the temporary
            # work folder.
            epubs.move_new_and_clean()

            # Rechargement du fichier EPUB __________________________________
            vim.command(
                """echom 'Media "{0}" added.'""".format(media_name)
            )
            ask_for_refresh()
endOfPython
endfunction

function! AddTocPage()
python << endOfPython
from __future__ import unicode_literals
from vim import *
from vim_epub import *

epubs = EPUB(vim.buffers)

if epubs.valid:
    have_tmp_path = epubs.make_working_dir()

    if have_tmp_path:
        epubs.extract()

        toc_tree = epubs.make_TOC_tree()
        epubs.make_TOC_page(toc_tree)
        epubs.epub2_predefined_append_to_opf("TocPage")

        # Backup the old EPUB
        epubs.backup()
        # Recompression of the EPUB from the temporary work folder
        success = epubs.recompress()

        if success:
            # Replace the old epub file with the new and clean the temporary
            # work folder.
            epubs.move_new_and_clean()

            # Rechargement du fichier EPUB __________________________________
            vim.command(
                """echom 'Table of contents page added.'"""
            )
            ask_for_refresh()
endOfPython
endfunction

function! OpenReader()
python << endOfPython
from vim import *
from vim_epub import *

epubs = EPUB(vim.buffers)
if epubs.valid:
    epubs.open_reader()
endOfPython
endfunction

function! LinkPageToCSS()
python << endOfPython
from vim import *
from vim_epub import *

def get_user_input(prompt):
    vim.command('let g:EpubMode_Prompt = input("{0} ")'.format(prompt))
    print " "
    return vim.eval("g:EpubMode_Prompt")

epubs = EPUB(vim.buffers)

if epubs.valid:
    available_css_files = epubs.get_files_by_extension("css")

    if available_css_files:
        location,make_dir = epubs.guess_destination("css")

        if len(available_css_files) == 1:
            css = available_css_files[0]
        else:
            print "Please select a CSS file to link:"

            count = 1
            for css_file in available_css_files:
                if location == "OEBPS/Styles/":
                    ctext = "/".join(css_file.split("/")[2:])
                    print "  {0} - {1}".format(count,ctext)
                else:
                    print "  {0} - {1}".format(count,css_file)

                count += 1

            print "  C - Cancel"

            choice = get_user_input("Select?")

            if choice.lower() == "c":
                css = False
            else:
                choice = int(choice) - 1
                css = available_css_files[choice]

    if css:
        css_href = None

        if location == "OEBPS/Styles/":
            css_href = "../Styles/{0}".format(css.split("/")[-1])

        if css_href is not None:
            link_text = '<link href="{0}" rel="stylesheet" type="text/css"/>'.format(css_href)

            vim.command(':r!echo \'{0}\\n\''.format(link_text))
endOfPython
endfunction

"--- Vim commands -------------------------------------------------------------

command! AddEmptyPage call AddNewPage()
command! AddEmptyCSS call AddNewCSS()
command! AddTocPage call AddTocPage()

command! AddMedia call AddNewMedia()

command! LinkToCss call LinkPageToCSS()

command! OpenReader call OpenReader()
