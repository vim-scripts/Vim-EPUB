" +-----------------------------------+
" | Vim-EPUB plugin file              |
" | Part of vim-epub plugin for Vim   |
" | Released under GNU GPL version 3  |
" | By Etienne Nadji <etnadji@eml.cc> |
" +-----------------------------------+

"--- Base actions / options ---------------------------------------------------

au BufReadCmd *.epub call zip#Browse(expand("<amatch>"))

let g:VimEPUB_DiffSplit = "horizontal"
let g:VimEPUB_OpenCommand = "None"
let g:VimEPUB_EPUB_Version = "2;3"

"--- Python imports -----------------------------------------------------------

python import sys
python import vim
python sys.path.append(vim.eval('expand("<sfile>:h")'))

" Warning for Windows users
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

epubs = EPUB(vim.buffers)

if epubs.valid:
    # Definition of the new page's name --------------------------------------
    page_set = False

    while not page_set:
        page_name = get_user_input(vim,"New page name?")

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

        if add_in == "{0}/Text/".format(epubs.oebps["variant"]):
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
            ask_for_refresh()
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

epubs = EPUB(vim.buffers)

if epubs.valid:
    # Definition of the new css stylesheet's name ----------------------------
    css_set = False

    while not css_set:
        css_name = get_user_input(vim,"New CSS stylesheet name?")

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

        if epubs.oebps["used"]:
            if "Style" in add_in:
                if "Styles" in add_in:
                    css_variant = "Styles"
                else:
                    css_variant = "Style"

        if add_in == "{0}/{1}/".format(epubs.oebps["variant"],css_variant):
            css_path = "{0}{1}{2}{1}{3}.css".format(
                epubs.temporary_epub["path"],
                os.sep,
                add_in,
                css_name
            )
            in_epub_path = "{0}{1}{2}.css".format(css_variant,os.sep,css_name)

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

epubs = EPUB(vim.buffers)

if epubs.valid:
    # Obtention du chemin du nouveau media -----------------------------------
    media_set = False
    while not media_set:
        raw_media_path = get_user_input(vim,"Media path?")

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

        if epubs.oebps["variant"] in add_in:
            # TODO add audio,video categories

            valid = False
            for mt in ["Text","Images","Style","Styles","Fonts","Misc"]:
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
from __future__ import unicode_literals
from vim import *
from vim_epub import *

epubs = EPUB(vim.buffers)
if epubs.valid:
    epubs.open_reader(vim)
endOfPython
endfunction

function! LinkPageToCSS()
python << endOfPython
from __future__ import unicode_literals
from vim import *
from vim_epub import *

epubs = EPUB(vim.buffers)

if epubs.valid:
    available_css_files = epubs.get_files_by_extension("css")

    if available_css_files:
        location,make_dir = epubs.guess_destination("css")

        if epubs.oebps["used"]:
            if "Style" in add_in:
                if "Styles" in location:
                    css_variant = "Styles"
                else:
                    css_variant = "Style"

        if len(available_css_files) == 1:
            css = available_css_files[0]
        else:
            print "Please select a CSS file to link:"

            count = 1
            for css_file in available_css_files:
                if location == "{0}/{1}/".format(epubs.oebps["variant"],css_variant):
                    ctext = "/".join(css_file.split("/")[2:])
                    print "  {0} - {1}".format(count,ctext)
                else:
                    print "  {0} - {1}".format(count,css_file)

                count += 1

            print "  C - Cancel"

            choice = get_user_input(vim,"Select?")

            if choice.lower() == "c":
                css = False
            else:
                choice = int(choice) - 1
                css = available_css_files[choice]

    if css:
        css_href = None

        if location == "{0}/{1}/".format(epubs.oebps["variant"],css_variant):
            css_href = "../{0}/{1}".format(css_variant,css.split("/")[-1])

        if css_href is not None:
            link_text = '<link href="{0}" rel="stylesheet" type="text/css"/>'.format(css_href)

            vim.command(':r!echo \'{0}\\n\''.format(link_text))
endOfPython
endfunction

function! RenameFile()
python << endOfPython
from __future__ import unicode_literals
from vim import *
from vim_epub import *

epubs = EPUB(vim.buffers)

if epubs.valid:
    # Get vim current line
    old_filename = get_current_line(vim)

    # Get the new filename -----------------------------
    new_filename = get_user_input(
        vim,
        "New filename of {0}?".format(
            old_filename.split("/")[-1]
        )
    )

    new_filename = "{0}/{1}".format(
        "/".join(old_filename.split("/")[:-1]),
        new_filename
    )
    #---------------------------------------------------

    # Adds the file extension if not added in the prompt
    old_file_ext = old_filename.split(".")[-1]

    if not new_filename.endswith(old_file_ext):
        # Only  if the file  has NO  extension (user can  use another
        # extension)
        if len(new_filename.split(".")) == 1:
            new_filename = "{0}.{1}".format(new_filename,old_file_ext)
    #---------------------------------------------------

    print "New filename:",new_filename

    have_tmp_path = epubs.make_working_dir()

    if have_tmp_path:
        epubs.extract()

        renamed = epubs.rename_file(old_filename,new_filename)

        if renamed:
            # Modifies the references to the renamed file in the other files
            # of the EPUB.
            epubs.replace_string(["xhtml","html"],old_filename,new_filename)

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
                    """echom 'File renamed to {0}.'""".format(new_filename)
                )
                ask_for_refresh()
endOfPython
endfunction

function! BackupEPUB()
python << endOfPython
from __future__ import unicode_literals
from vim import *
from vim_epub import *

epubs = EPUB(vim.buffers)
if epubs.valid:
    backup_name = get_user_input(vim,"Backup name?")

    if backup_name:
        epubs.backup(backup_name)
endOfPython
endfunction

function! DiffEPUB()
python << endOfPython
from vim import *
from vim_epub import *

epubs = EPUB(vim.buffers)

if epubs.valid:
    epub1_name = epubs.original_epub["path"].basename()

    print "Actual EPUB:",epub1_name

    epub2 = get_user_input(vim,"Compare with?")
    success = epubs.open_diff(vim,epub2)

    if not success:
        print "{0} is not a file/doesn't exist".format(epub2.realpath())
endOfPython
endfunction

function! DiffLastEPUB()
python << endOfPython
from __future__ import unicode_literals

from vim import *
from vim_epub import *

epubs = EPUB(vim.buffers)

if epubs.valid:
    epub2 = "{0}.vepub.bak".format(epubs.original_epub["path"].abspath())
    success = epubs.open_diff(vim,epub2)

    if not success:
        print "{0} is not a file/doesn't exist".format(epub2.realpath())
endOfPython
endfunction

function! MergeFiles()
python << endOfPython
from __future__ import unicode_literals

import os
import copy

from vim import *
from vim_epub import *

epubs = EPUB(vim.buffers)

if epubs.valid:
    have_tmp_path = epubs.make_working_dir()

    if have_tmp_path:
        epubs.extract()

        f1 = os.sep.join(get_current_line(vim).split("/"))
        f2 = os.sep.join(get_next_line(vim).split("/"))
        f1_name = copy.deepcopy(f1)
        f2_name = copy.deepcopy(f2)

        f1 = "{0}{1}".format(epubs.temporary_epub["path"],f1)
        f2 = "{0}{1}".format(epubs.temporary_epub["path"],f2)

        output_selected = False
        output_file = None

        while not output_selected:
            print "Merge {0} into:\n".format(f2_name)
            print "1. {0}".format(f1_name)
            print "2. A new file"
            print "3. Cancel\n"

            choice = get_user_input(vim,"Choice?")

            try:
                choice = int(choice)

                output_selected = True
                merge = True

                #--- Merge F1 and F2 into F1… ----------------------------------

                if choice == 1:
                    output_file = f1
                    new_file = False

                #--- … or Merge F1 and F2 into a new file… ---------------------

                if choice == 2:
                    correct = False
                    new_file = True

                    # Enter the new page name ----------------------------------
                    while not correct:
                        page_name = get_user_input(vim,"New page name?")

                        if not page_name.endswith(".xhtml"):
                            page_name += ".xhtml"

                        if not epubs.has_file(path(page_name)):
                            correct = True

                    # Find the appropriate folder in the EPUB file for the new page.
                    add_in,make_dir = epubs.guess_destination("text")

                    if make_dir:
                        try:
                            os.mkdir(
                                "{0}{1}".format(
                                    epubs.temporary_epub["path"],
                                    add_in
                                )
                            )
                        except OSError:
                            pass

                    page_path = None

                    if add_in == "{0}/Text/".format(epubs.oebps["variant"]):
                        page_path = "{0}{1}{2}".format(
                            epubs.temporary_epub["path"],
                            add_in,
                            page_name
                        )
                        in_epub_path = "Text{0}{1}".format(os.sep,page_name)

                    output_file = page_path

                #--- … or cancel -----------------------------------------------

                if choice == 3:
                    epubs.remove_temp_dir()
                    merge,output_selected = False,True

            except ValueError:
                pass

        if merge:
            temp_merged_file = epubs.temporary_epub["path"] + "tmp_html.html"

            success = merge_html(f1,f2,temp_merged_file)

            if success:
                # --- Operations on files --------------------------------------
                if new_file:
                    answered = False

                    while not answered:
                        print "Do Vim-EPUB have to remove merged files?"

                        choice = get_user_input(vim,"[yes/no]")

                        if choice.lower()[0] in ["y","n"]:
                            if choice.lower()[0] == "y":
                                remove_merged = True
                            if choice.lower()[0] == "n":
                                remove_merged = False
                            answered = True

                    os.chdir(epubs.temporary_epub["path"])
                    shutil.move(temp_merged_file,output_file)

                    if remove_merged:
                        os.remove(f1)
                        os.remove(f2)
                else:
                    os.remove(f1)
                    os.remove(f2)
                    os.chdir(epubs.temporary_epub["path"])
                    shutil.move(temp_merged_file,f1)

                # --- Make the new EPUB and ends -------------------------------

                recompress = epubs.recompress()

                if recompress:
                    # Replace the old epub file with the new and clean the temporary
                    # work folder.
                    epubs.move_new_and_clean()

                    # Rechargement du fichier EPUB __________________________________
                    vim.command(
                        """echom 'Files {0} and {1} merged in {2}.'""".format(
                            f1_name,f2_name,output_file
                        )
                    )
                    ask_for_refresh()


endOfPython
endfunction

function! RemoveUnusedMedias()
python << endOfPython
from __future__ import unicode_literals

from vim import *

from vim_epub import *

epubs = EPUB(vim.buffers)

if epubs.valid:
    texts = epubs.get_files_by_extension(["html","xhtml"])

    medias = []
    m = epubs.get_files_by_extension(["gif","png","jpg","jpeg","svg","css"])

    location,make_dir = epubs.guess_destination(None)
    if epubs.oebps["used"]:
        for media in m:
            if epubs.oebps["variant"] in m:
                medias.append(
                    media.replace(epubs.oebps["variant"],"..")
                )
            else:
                medias.append(media)
    else:
        medias = m

    have_tmp_path = epubs.make_working_dir()

    if have_tmp_path:
        epubs.extract()

        used_medias = []

        for text_file in texts:
            tf = epubs.temporary_epub["path"]+text_file

            with open(tf,"r") as tfo:
                for line in tfo:
                    for media in medias:
                        if media in line:
                            if not media in used_medias:
                                used_medias.append(media)

        unused_medias = []

        if len(medias) != len(used_medias):
            for media in medias:
                if not media in used_medias:
                    unused_medias.append(media)

        if unused_medias:
            print "Remove medias:\n"

            for media in unused_medias:
                removing = True

                while removing:
                    do_remove = get_user_input(vim,"Remove {0} [yes/no]?".format(media))

                    if do_remove.lower()[0] in ["y","n"]:

                        do_remove = do_remove.lower()[0]

                        if do_remove == "y":
                            os.remove(
                                "{0}{1}".format(epubs.temporary_epub["path"],media)
                            )

                            removing = False
                        else:
                            removing = False

                    else:
                        pass

            success = epubs.recompress()
            if success:
                # Replace the old epub file with the new and clean the temporary
                # work folder.
                epubs.move_new_and_clean()

                # Rechargement du fichier EPUB __________________________________
                vim.command("""echom 'Unused medias removed'""")
                ask_for_refresh()
        else:
            epubs.remove_temp_dir()
endOfPython
endfunction

function! UpdateTOC()
python << endOfPython
from __future__ import unicode_literals

from vim import *
from vim_epub import *

epubs = EPUB(vim.buffers)

if epubs.valid:
    correct_versions = True

    epub_versions = vim.eval("g:VimEPUB_EPUB_Version")

    if len(epub_versions.split(";")) > 1:
        epub_versions = [int(version) for version in epub_versions.split(";")]
    else:
        epub_versions = [int(epub_versions)]

    for version in epub_versions:
        if version in [2,3]:
            pass
        else:
            vim.command("""echom 'g:VimEPUB_EPUB_Version: Invalid parameter value'""")
            vim.command("""echom '-> Invalid Value: {0}, elem {1}'""".format(epub_versions,version))
            vim.command("""echom '-> See documentation'""")

            correct_versions = False

    if correct_versions:
        have_tmp_path = epubs.make_working_dir()

        if have_tmp_path:
            epubs.extract()

            if len(epub_versions) > 1:
                # Compatibility between EPUB2 & EPUB3 : g:VimEPUB_EPUB_Version = "2;3"
                success = epubs.make_TOC(epub2=True,epub3=True)

            else:
                if epub_versions[0] == 2:
                    # EPUB2 only: g:VimEPUB_EPUB_Version = "2"
                    success = epubs.make_TOC(epub2=True,epub3=False)

                elif epub_versions[0] == 3:
                    # EPUB3 only: g:VimEPUB_EPUB_Version = "3"
                    success = epubs.make_TOC(epub2=False,epub3=True)

                else:
                    success = None

            if success:
                recompress = epubs.recompress()
                if recompress:
                    # Replace the old epub file with the new and clean the temporary
                    # work folder.
                    epubs.move_new_and_clean()

                    # Rechargement du fichier EPUB __________________________________
                    ask_for_refresh()

endOfPython
endfunction

"--- Vim commands -------------------------------------------------------------

" Add generated/empty medias
command! AddEmptyPage call AddNewPage()
command! AddEmptyCSS call AddNewCSS()
command! AddTocPage call AddTocPage()

" Add existing medias
command! AddMedia call AddNewMedia()

" Table of contents
command! UpdateToc call UpdateTOC()

" Edition commands
command! LinkToCss call LinkPageToCSS()

" Files manipulation
command! RenameFile call RenameFile()
command! BackupEPUB call BackupEPUB()
command! DiffEPUB call DiffEPUB()
command! DiffLastEPUB call DiffLastEPUB()
command! MergeFiles call MergeFiles()
command! RemoveUnusedMedias call RemoveUnusedMedias()

" Others
command! OpenReader call OpenReader()
