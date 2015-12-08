" +-----------------------------------+
" | Vim-EPUB plugin file              |
" |                                   |
" | Part of vim-epub plugin for Vim   |
" | Released under GNU GPL version 3  |
" |                                   |
" | By Etienne Nadji <etnadji@eml.cc> |
" +-----------------------------------+

"--- Base actions / options ---------------------------------------------------

" Autocommand to make zip.vim open EPUB files
au BufReadCmd *.epub call zip#Browse(expand("<amatch>"))

" Options
au BufReadCmd *.epub let g:VimEPUB_DiffSplit = "horizontal"
au BufReadCmd *.epub let g:VimEPUB_MetaSplit = "vertical"
au BufReadCmd *.epub let g:VimEPUB_FontDefSplit = "vertical"

au BufReadCmd *.epub let g:VimEPUB_EReaderCommand = "none"
au BufReadCmd *.epub let g:VimEPUB_OpenMedia_Font = "none"
au BufReadCmd *.epub let g:VimEPUB_OpenMedia_Image = "none"

au BufReadCmd *.epub let g:VimEPUB_CleanPanels = "False"

let g:VimEPUB_EPUB_Version = "2;3"
let g:VimEPUB_Skels_Dir = "None"

"--- Python imports -----------------------------------------------------------

" Append Vim-EPUB plugin/ to python path
python import sys
python import vim
python sys.path.append(vim.eval('expand("<sfile>:h")'))

"--- Setup --------------------------------------------------------------------

" Warning for Windows users
python import platform
python if platform.system() == "Windows": vim.command("""echom 'Vim-EPUB does not work under Windows.'""")

" Get Vim-EPUB plugin/ path
python plugin_path = vim.eval('expand("<sfile>:h")')
python vim.command('let g:VimEPUB_PluginPath = "{0}"'.format(plugin_path))

"--- Functions ----------------------------------------------------------------

function! AddNewPage()
python << endOfPython
from __future__ import unicode_literals

import os

from path import path
from vim import *

from vim_epub import *

with Open_EPUB(vim.buffers) as epubs:
    # Definition of the new page's name --------------------------------------
    page_set = False

    while not page_set:
        page_name = get_user_input(vim,"New page name?")

        if epubs.has_file(path("{0}.xhtml".format(page_name))):
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
                npf.write(get_skel(vim,"xhtml_skel"))

    if page_path is not None:
        # Add the page to content.opf
        epubs.epub2_append_to_opf(
            "xhtml",
            path(page_name+".xhtml"),
            in_epub_path
        )

        epubs.backup()
        success = epubs.recompress()

        if success:
            epubs.move_new_and_clean()

	    refresh(vim,'Page {0} added.'.format(page_name+".xhtml"),True)
endOfPython
endfunction

function! AddNewCSS()
python << endOfPython
from __future__ import unicode_literals

import os

from path import path
from vim import *

from vim_epub import *

with Open_EPUB(vim.buffers) as epubs:
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
                npf.write(get_skel(vim,"css_skel"))

    if css_path is not None:
        # Add the css to content.opf
        epubs.epub2_append_to_opf(
            "css",
            path(css_name+".css"),
            in_epub_path
        )

        epubs.backup()
        success = epubs.recompress()

        if success:
            epubs.move_new_and_clean()

            refresh(vim,'CSS stylesheet "{0}" added.'.format(css_name+".css"),True)
endOfPython
endfunction

function! AddNewMedia()
python << endOfPython
from __future__ import unicode_literals

from path import path
from vim import *

from vim_epub import *

with Open_EPUB(vim.buffers) as epubs:
    # Get the filepath of the new media --------------------------------------
    media_set = False

    while not media_set:
        raw_media_path = get_user_input(vim,"Media path?")

        if raw_media_path.lower() == "c":
            media_set,do = True,False
        else:
            media_path = path(raw_media_path)

            if epubs.has_file(media_path):
                print "This media is already in the EPUB. Use another media name."
                print "Or type C (cancel)"
                continue
            else:
                media_set,do = True,True

    # Adding the new media ---------------------------------------------------

    if do:
        have_tmp_path = epubs.make_working_dir()

        if have_tmp_path:
            # Extracts the EPUB and add the media
            epubs.extract()

            epubs.add_media(raw_media_path)

            epubs.backup()

            # Recompression of the EPUB from the temporary work folder
            success = epubs.recompress()

            if success:
                epubs.move_new_and_clean()

                echom(vim,'Media {0} added.'.format(
                        path(raw_media_path).basename()
                    )
                )

                refresh(vim)
endOfPython
endfunction

function! AddTocPage()
python << endOfPython
from __future__ import unicode_literals
from vim import *
from vim_epub import *

with Open_EPUB(vim.buffers) as epubs:
    have_tmp_path = epubs.make_working_dir()

    if have_tmp_path:
        epubs.extract()

        toc_tree = epubs.make_TOC_tree()
        epubs.make_TOC_page(vim,toc_tree)
        epubs.epub2_predefined_append_to_opf("TocPage")

        epubs.backup()
        success = epubs.recompress()

        if success:
            epubs.move_new_and_clean()

            refresh(vim,'Table of contents page added',True)
endOfPython
endfunction

function! OpenReader()
python << endOfPython
from __future__ import unicode_literals
from vim import *
from vim_epub import *

with Open_EPUB(vim.buffers) as epub:
    epub.open_reader(vim)
endOfPython
endfunction

function! FindFontDefinition()
python << endOfPython
from __future__ import unicode_literals

from vim import *

from vim_epub import *
import vepub_css as css_utils

font_name = get_current_line(vim)

with Open_EPUB(vim.buffers) as epubs:
    available_css_files = epubs.get_files_by_extension("css")

    if available_css_files:
        location,_ = epubs.guess_destination("css")

        have_tmp_path = epubs.make_working_dir()

        if have_tmp_path:
            epubs.extract()

            cssf = []
            for css in available_css_files:
                css_file = "{0}{1}".format(epubs.temporary_epub["path"],css)
                defs = css_utils.find_font_face_src(css_file)

                if defs:
                    for fdef in defs:
                        if fdef["url"] in font_name:
                            cssf.append([css,fdef["line"]])

            if cssf:
                epubs.remove_temp_dir()

                summary = css_utils.make_fontdef_summary(
                    font_name,
                    cssf,
                    "FontDefinitions.txt"
                )

                vim.command(
                    ":{0} {1}".format(
                        get_split_cmd(vim,"fontdef"),
                        summary)
                )

                vim.command(":setl buftype=nofile bufhidden=wipe nobuflisted")

    else:
        # * xhtml *
        # SI des fichiers (X)HTML
        #    * Essai 2 * Dans les fichiers (X)HTML: Balise <style> du header
        #    * Essai 3 * Dans les fichiers (X)HTML: Style en paramètre d’une balise
        pass

    pass

endOfPython
endfunction

function! OpenMedia()
python << endOfPython
from __future__ import unicode_literals

import os

from vim import *
from vim_epub import *

media_name = get_current_line(vim)

if media_name:
    with Open_EPUB(vim.buffers) as epubs:
        # Make the temporary work folder
        have_tmp_path = epubs.make_working_dir()

        if have_tmp_path:
            epubs.extract()

            success,mfile = epubs.open_file(vim,media_name)

            if success:
                print "{0} opened. Press ENTER.".format(mfile)
            else:
                echom(vim,'VimEPUB can\'t open {0}: unknown media type.'.format(mfile))
endOfPython
endfunction

function! LinkPageToCSS()
python << endOfPython
from __future__ import unicode_literals

from vim import *
from vim_epub import *

with Open_EPUB(vim.buffers) as epubs:
    available_css_files = epubs.get_files_by_extension("css")

    if available_css_files:
        location,_ = epubs.guess_destination("css")

        if epubs.oebps["used"]:
            if "Style" in location:
                if "Styles" in location:
                    css_variant = "Styles"
                else:
                    css_variant = "Style"

        if len(available_css_files) == 1:
            css = available_css_files[0]
        else:
	    selection = True

	    while selection:
                print "Please select a CSS file to link:"

                for num,css_file in enumerate(available_css_files):
                    if location == "{0}/{1}/".format(
			    epubs.oebps["variant"],css_variant):
                        ctext = "/".join(css_file.split("/")[2:])
                        print "  {0} - {1}".format(num+1,ctext)
                    else:
                        print "  {0} - {1}".format(num+1,css_file)

                print "  C - Cancel"

                choice = get_user_input(vim,"Select?")

                if choice.lower() == "c":
                    css,selection = False,False
                else:
                    try:
                        choice = int(choice) - 1
                        css = available_css_files[choice]
			selection = False
                    except ValueError:
                        pass

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

with Open_EPUB(vim.buffers) as epubs:
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

            epubs.backup()
            success = epubs.recompress()

            if success:
                epubs.move_new_and_clean()
                refresh(vim,'File renamed to {0}.'.format(new_filename),True)
endOfPython
endfunction

function! BackupEPUB()
python << endOfPython
from __future__ import unicode_literals
from vim import *
from vim_epub import *

with Open_EPUB(vim.buffers) as epubs:
    backup_name = get_user_input(vim,"Backup name?")
    if backup_name: epubs.backup(backup_name)
endOfPython
endfunction

function! DiffEPUB()
python << endOfPython
from vim import *
from vim_epub import *

with Open_EPUB(vim.buffers) as epubs:
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

with Open_EPUB(vim.buffers) as epubs:
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

with Open_EPUB(vim.buffers) as epubs:
    have_tmp_path = epubs.make_working_dir()

    if have_tmp_path:
        abort = False

        try:
            f1 = os.sep.join(get_current_line(vim).split("/"))
            f2 = os.sep.join(get_next_line(vim).split("/"))
        except AttributeError:
            abort = True

        if abort:
            epubs.remove_temp_dir()

            print "Can't merge: invalid files."
        else:
            epubs.extract()

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
                            for f in [f1,f2]:
                                os.remove(f)
                    else:
                        for f in [f1,f2]:
                            os.remove(f)
                        os.chdir(epubs.temporary_epub["path"])
                        shutil.move(temp_merged_file,f1)

                    # --- Make the new EPUB and ends -------------------------------

                    recompress = epubs.recompress()

                    if recompress:
                        epubs.move_new_and_clean()

                        refresh(
                            vim,
                            'Files {0} and {1} merged in {2}.'.format(f1_name,f2_name,output_file),
                            True
                        )
endOfPython
endfunction

function! RemoveUnusedMedias()
python << endOfPython
from __future__ import unicode_literals

from vim import *

from vim_epub import *

with Open_EPUB(vim.buffers) as epubs:
    texts = epubs.get_files_by_extension(["html","xhtml"])

    medias = []
    m = epubs.get_files_by_extension(["gif","png","jpg","jpeg","svg","css"])

    location,_ = epubs.guess_destination(None)
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
                epubs.move_new_and_clean()

                refresh(vim,"Unused medias removed",True)
        else:
            epubs.remove_temp_dir()
endOfPython
endfunction

function! UpdateTOC()
python << endOfPython
from __future__ import unicode_literals

from vim import *
from vim_epub import *

with Open_EPUB(vim.buffers) as epubs:
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
            echom(vim,'g:VimEPUB_EPUB_Version: Invalid parameter value'))
            echom(vim,'-> Invalid Value: {0}, elem {1}'.format(epub_versions,version))
            echom(vim,'-> See documentation')

            correct_versions = False

    if correct_versions:
        have_tmp_path = epubs.make_working_dir()

        if have_tmp_path:
            epubs.extract()

            if len(epub_versions) > 1:
                # Compatibility between EPUB2 & EPUB3 : g:VimEPUB_EPUB_Version = "2;3"
                success = epubs.make_TOC(vim,epub2=True,epub3=True)

            else:
                if epub_versions[0] == 2:
                    # EPUB2 only: g:VimEPUB_EPUB_Version = "2"
                    success = epubs.make_TOC(vim,epub2=True,epub3=False)

                elif epub_versions[0] == 3:
                    # EPUB3 only: g:VimEPUB_EPUB_Version = "3"
                    success = epubs.make_TOC(vim,epub2=False,epub3=True)

                else:
                    success = None

            if success:
                recompress = epubs.recompress()
                if recompress:
                    epubs.move_new_and_clean()

                    refresh(vim)
endOfPython
endfunction

function! ViewMetadatas()
python << endOfPython
from __future__ import unicode_literals

from vim import *

from vim_epub import *
import vepub_metadata as metadata

with Open_EPUB(vim.buffers) as epubs:
	have_tmp_path = epubs.make_working_dir()

	if have_tmp_path:
	    epubs.extract()

	    opf_file = epubs.get_file(path("content.opf"),True)

	    if opf_file:
		    metadatas_file = "metadatas.txt"

		    metadata.do_all(opf_file,metadatas_file,True)
		    epubs.remove_temp_dir()

		    vim.command(
			    ":{0} {1}".format(
				    get_split_cmd(vim,"metadatas"),
				    metadatas_file)
		    )
		    vim.command(":setl buftype=nofile bufhidden=wipe nobuflisted")
endOfPython
endfunction

function! CleanFromExports()
python << endOfPython
from __future__ import unicode_literals

import os

from vim import *
from vim_epub import get_skel,normal,cat_in_buffer

vim.command(
    ':silent! %!pandoc --from=html --to=markdown | ' \
    'pandoc --from=markdown --to=html'
)

normal(vim,"ggO",True,True)
cat_in_buffer(vim,get_skel(vim,"xhtml_head",True))
normal(vim,"GGo",True,True)
cat_in_buffer(vim,get_skel(vim,"xhtml_tail",True))
normal(vim,"ggdd",True)
endOfPython
endfunction

function! NewEPUB()
python << endOfPython
from __future__ import unicode_literals

import os
from vim import *
from vim_epub import *

filename = ""
while not filename:
    filename = get_user_input(vim,"Name of the EPUB?")

if filename.endswith(".epub"):
    filename = filename.split(".epub")[0]

answered = False
while not answered:
    addbuffs = get_user_input(
        vim,
        "Include current buffers? [yes/no]"
    )

    if addbuffs.lower()[0] in ["y","n"]:

        if addbuffs.lower()[0] == "y": add_buffers = True
        if addbuffs.lower()[0] == "n": add_buffers = False

        answered = True

new_file = make_new_epub(vim,filename)

if new_file:
    vim.command(":silent! edit {0}".format(new_file))

    # Reload Vim configuration to add Vim-EPUB commands
    vim.command(":silent! source $MYVIMRC")

    # Adding files in the current buffers to the new EPUB:
    if add_buffers:
        with Open_EPUB(vim.buffers) as epubs:
            have_tmp_path = epubs.make_working_dir()

            if have_tmp_path:
                epubs.extract()

                files = []
                for buffer in vim.buffers:
                    fname = buffer.name
                    real_path = os.path.realpath(fname)

                    if fname in files:
                        continue
                    if fname == new_file:
                        continue
                    if not os.path.exists(real_path):
                        continue
                    if fname.endswith(".epub"):
                        continue

                    files.append(fname)

                for media in files:
                    epubs.add_media(media)

                # Backup the old EPUB
                epubs.backup()
                # Recompression of the EPUB from the temporary work folder
                success = epubs.recompress()

                # Delete the original EPUB file
                if success:
                    # Replace the old epub file with the new and clean the 
                    # temporary work folder.
                    epubs.move_new_and_clean()

    refresh(vim)

endOfPython
endfunction

"--- Vim commands -------------------------------------------------------------

" Make new EPUB

command! NewEPUB call NewEPUB()

" Add generated/empty medias
au BufReadCmd *.epub command! AddEmptyPage call AddNewPage()
au BufReadCmd *.epub command! AddEmptyCSS call AddNewCSS()
au BufReadCmd *.epub command! AddTocPage call AddTocPage()

" Add existing medias
au BufReadCmd *.epub command! AddMedia call AddNewMedia()

" Table of contents
au BufReadCmd *.epub command! UpdateToc call UpdateTOC()

" Edition commands
au BufReadCmd *.epub command! LinkToCss call LinkPageToCSS()

" Prospection
au BufReadCmd *.epub command! FindFontDefinition call FindFontDefinition()
au BufReadCmd *.epub command! ViewMetadatas call ViewMetadatas()

" Files manipulation
au BufReadCmd *.epub command! RenameFile call RenameFile()
au BufReadCmd *.epub command! BackupEPUB call BackupEPUB()
au BufReadCmd *.epub command! DiffEPUB call DiffEPUB()
au BufReadCmd *.epub command! DiffLastEPUB call DiffLastEPUB()
au BufReadCmd *.epub command! MergeFiles call MergeFiles()
au BufReadCmd *.epub command! RemoveUnusedMedias call RemoveUnusedMedias()

" Opening things in an external program
au BufReadCmd *.epub command! OpenReader call OpenReader()
au BufReadCmd *.epub command! OpenMedia call OpenMedia()

" Clean the HTML files with pandoc
au BufReadCmd *.epub command! CleanFromExports call CleanFromExports()
au Filetype html command! CleanFromExports call CleanFromExports()
" Autocommand for editing EPUB files with Vim and Sigil
au BufRead /tmp/Sigil/scratchpad/* command! CleanFromExports call CleanFromExports()
