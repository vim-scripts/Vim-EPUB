#!/usr/bin/python2
# -*- coding:Utf-8 -*-

# Vim-EPUB python core file
# Part of vim-epub plugin for Vim
# Released under GNU GPL version 3
# By Etienne Nadji <etnadji@eml.cc>

from __future__ import unicode_literals

import os
import platform
import shutil
import zipfile

from subprocess import Popen, PIPE, STDOUT
from HTMLParser import HTMLParser

from path import path

from vepub_skels import *


class EPUB:
    def __init__(self,vim_buffers=None):
        if vim_buffers is None:
            self.valid = False

        else:
            epub_master_buffer = False

            for buffer in vim_buffers:
                buff = buffer.name.decode("utf8")
                if buff.endswith(".epub"):
                  epub_master_buffer = buff
                  break

            if epub_master_buffer:
                self.valid = True

                self.original_epub = {}
                self.temporary_epub = {"path":None,"have_dir":False}

                self.original_epub["path"] = path(epub_master_buffer.decode("utf8"))
                self.original_epub["zip_object"] = zipfile.ZipFile(epub_master_buffer)
                self.original_epub["zip_files"] = self.original_epub["zip_object"].namelist()

                self.oebps = {"used":False,"variant":""}

            else:
                self.valid = False

                print "No EPUB file buffer found."

    # Basic actions methods

    def make_working_dir(self):
        """
        Make a temporary dir.

        Returns:
          - extract (bool): success.
        """
        tmp_path = "{0}{2}.temp_{1}{2}".format(
                self.original_epub["path"].dirname(),
                self.original_epub["path"].namebase,
                os.sep)

        try:
            os.mkdir(tmp_path,0755)
            self.temporary_epub["have_dir"] = True
        except OSError,err:
            if err.errno == 17:
                # The folder already exists
                self.temporary_epub["have_dir"] = True
            else:
                print err.errno,":",err.strerror

        self.temporary_epub["path"] = tmp_path

        return self.temporary_epub["have_dir"]

    def extract(self,extract_path=None):
        if extract_path is None:
            if self.temporary_epub["path"] is not None:
                self.original_epub["zip_object"].extractall(
                        path=self.temporary_epub["path"]
                )
            else:
                return False
        else:
            self.original_epub["zip_object"].extractall(path=extract_path)

    def guess_destination(self,filetype):
        """
        Find the appropriate location in the EPUB tree for a new file.

          - filetype (str or None):
              "text" for (X)HTML content
              "image" for images content
              "css" for CSS
              "misc" for unknown

              None: Use this value to only determine if oebps structure
              is used and the oebps variant (OEBPS or OPS).

        Returns:
          - destination (str)
        """
        # TODO add audio,video categories

        defined = False

        for f in self.original_epub["zip_files"]:
            if not defined:
                if f.startswith("OEBPS/") or f.startswith("OPS/"):

                    self.oebps = {"used":True,"variant":""}

                    make_dir = True
                    defined = True

                    # EPUB 2 (mostly)
                    if f.startswith("OEBPS/"):
                        self.oebps["variant"] = "OEBPS"
                    # EPUB 3
                    if f.startswith("OPS/"):
                        self.oebps["variant"] = "OPS"

            if self.oebps["used"] and filetype != None:
                if filetype == "text":
                    if f.startswith("{0}/Text/".format(self.oebps["variant"])):
                        make_dir = False

                if filetype == "image":
                    if f.startswith("{0}/Images/".format(self.oebps["variant"])):
                        make_dir = False

                if filetype == "css":
                    # Sigil variant
                    if f.startswith("{0}/Styles/".format(self.oebps["variant"])):
                        css_variant = "Styles"
                        make_dir = False

                    # EPUB standard
                    if f.startswith("{0}/Style/".format(self.oebps["variant"])):
                        css_variant = "Style"
                        make_dir = False

                if filetype == "font":
                    if f.startswith("{0}/Fonts/".format(self.oebps["variant"])):
                        make_dir = False

                if filetype == "misc":
                    if f.startswith("{0}/Misc/".format(self.oebps["variant"])):
                        make_dir = False
            else:
                # TODO
                pass

        if self.oebps["used"] and filetype != None:

            if filetype == "text":
                ret = "{0}/Text/".format(self.oebps["variant"])

            if filetype == "image":
                ret = "{0}/Images/".format(self.oebps["variant"])

            if filetype == "css":
                ret = "{0}/{1}/".format(self.oebps["variant"],css_variant)

            if filetype == "font":
                ret = "{0}/Fonts/".format(self.oebps["variant"])

            if filetype == "misc":
                ret = "{0}/Misc/".format(self.oebps["variant"])

            return ret,make_dir
        else:
            return None,None

    def backup(self,filename=None):
        """Backup the original epub."""

        if filename is None:
            backup_file = "{0}.vepub.bak".format(self.original_epub["path"].abspath())
        else:
            dirpath = os.sep.join(self.original_epub["path"].abspath().splitpath()[:-1])
            backup_file = "{0}{1}{2}.epub.user.bak".format(dirpath,os.sep,filename)

        if backup_file:
            self.original_epub["path"].copy(backup_file)

            print "EPUB Backup in {0}.".format(backup_file)

            return True
        else:
            return False

    def recompress(self):
        """Recompress the EPUB file from the temporary file."""

        if self._have_correct_oebps_variant():
            os.chdir(self.temporary_epub["path"])

            if platform.system() in ["Linux","Darwin"] or "bsd" in platform.system().lower():
                nzip = unicode(self.original_epub["path"].basename())
            else:
                # Windows…
                return False

            if platform.system() == "Linux" or "bsd" in platform.system().lower:
                os.popen('zip -X -Z store "{0}" mimetype'.format(nzip)).read()
                os.popen('zip -r "{0}" META-INF/ {1}/'.format(nzip,self.oebps["variant"])).read()
                return True

            if platform.system() == "Darwin":
                os.system('zip -X "{0}" mimetype'.format(nzip))
                os.system('zip -rg "{0}" META-INF -x \*.DS_Store'.format(nzip))
                os.system('zip -rg "{0}" {1} -x \*.DS_Store'.format(nzip,self.oebps["variant"]))
                return True

    def move_new_and_clean(self):
        """Move the new EPUB file from recompress() and clean up."""

        new_epub = self.original_epub["path"].basename()
        old_epub = self.original_epub["path"].abspath()

        os.remove(old_epub)
        shutil.move(new_epub,old_epub)

        shutil.rmtree(self.temporary_epub["path"])

        return True

    def _have_correct_oebps_variant(self):
        if self.oebps["variant"]:
            if self.oebps["variant"] in ["OPS","OEBPS"]:
                return True
            else:
                return False
        else:
            self.guess_destination(None)

            if self.oebps["variant"] in ["OPS","OEBPS"]:
                return True
            else:
                return False

    # Utils

    def replace_string(self,action_field,old_string,new_string):
        def replace(source_file,old_string,new_string):
            with open(source_file,"r") as fi:
                text = fi.read()

                if old_string in text:
                    text = text.replace(old_string,new_string)

                return text

        files = self.get_files_by_extension(action_field)

        for f in files:
            file_path = None

            location,make_dir = self.guess_destination("text")

            if location == "{0}/Text/".format(self.oebps["variant"]):
                file_path = "{0}{1}".format(self.temporary_epub["path"],f)

                old_string = old_string.replace(self.oebps["variant"],"..")
                new_string = new_string.replace(self.oebps["variant"],"..")

            if file_path is not None:
                try:
                    new_text = replace(file_path,old_string,new_string)

                    os.remove(file_path)

                    with open(file_path,"w") as fi:
                        fi.write(new_text)
                except IOError,err:
                    if err.errno == 2:
                        pass

    def rename_file(self,old_path,new_path):
        old_path = "{0}{1}".format(self.temporary_epub["path"],old_path)
        new_path = "{0}{1}".format(self.temporary_epub["path"],new_path)

        if self.temporary_epub["have_dir"]:
            shutil.move(old_path,new_path)
            return True
        else:
            return False

    # Files search

    def has_file(self,file_path):
        """
        Check for a file in the EPUB's content.

          - file_path: path.path instance
        """

        for f in self.original_epub["zip_files"]:
            if file_path.ext[1:] in f:
                if file_path.basename() in f.split("/")[-1]:
                    return True

        return False

    def get_files_by_extension(self,extension):
        """
        Return all files in the EPUB's content with extension extension.

          - extension: file extension without dot (ex: "js","css").
                       Can be a list (ex: ["js","css"]).
        """

        filenames = []

        if not isinstance(extension,list):
            extension = [extension]

        for ext in extension:
            ext_string = ".{0}".format(ext)

            for f in self.original_epub["zip_files"]:
                if f.endswith(ext_string):
                    filenames.append(f)

        return filenames

    def get_files_by_extension_in_temp(self,extension):
        """
        Return all files in the temporary EPUB's content with extension extension.

          - extension: file extension without dot (ex: "js","css").
                       Can be a list (ex: ["js","css"]).
        """

        filenames = []

        if not isinstance(extension,list):
            extension = [extension]

        for ext in extension:
            ext_string = ".{0}".format(ext)

            for f in self.temporary_epub["path"].walkfiles():
                if f.ext == ext_string:
                    filenames.append(f)

        return filenames

    # EPUB 2 methods

    def epub2_append_to_opf(self,filetype,media_path,ref):
        """
        Append a file to the OPF entries (manifest + spine).

          - filetype (str):
              "xhtml"
          - media_path: path of the new file to add to the OPF.
              path.path (idem) instance
          - ref: path in the epub of the media, without "OEBPS" / "OPS".
              Ex: "Text/Section1.xhtml"
        """

        # Filetypes --------------------------------------------------------------
        # filetype : [mimetype, add in manifest, add in spine]
        # filetype : ["FILETYPE"] -> use another filetype
        filetypes = {
                "ncx":{"mime":"application/x-dtbncx+xml","manifest":True,"spine":False},
                "xhtml":{"mime":"application/xhtml+xml","manifest":True,"spine":True},
                "ttf":{"mime":"application/x-font-ttf","manifest":True,"spine":False},
                "woff":{"mime":"application/font-woff","manifest":True,"spine":False},
                "otf":{"mime":"application/font-sfnt","manifest":True,"spine":False},

                "png":{"mime":"image/png","manifest":True,"spine":False},
                "jpg":{"mime":"image/jpg","manifest":True,"spine":False},
                "gif":{"mime":"image/gif","manifest":True,"spine":False},
                "svg":{"mime":"image/svg+xml","manifest":True,"spine":False},

                # Yes, Ogg file has really text/plain as mime
                "ogg":{"mime":"text/plain","manifest":True,"spine":False},
                "css":{"mime":"text/css","manifest":True,"spine":False},
                "js":{"mime":"text/javascript","manifest":True,"spine":False},

                "mp3":{"mime":"audio/mpeg","manifest":True,"spine":False},
                "mp4":{"mime":"audio/mp4","manifest":True,"spine":False},

                # aliases
                "jpeg":{"use":"jpg"},
                }
        #-------------------------------------------------------------------------

        if "use" in filetypes[filetype]:
            ft = filetypes[filetype]["use"]
            filetype = filetypes[ft]
        else:
            filetype = filetypes[filetype]

        # Lines of the manifest, spine

        if filetype["manifest"]:
            manifest = '<item href="{0}" id="{1}" media-type="{2}" />'.format(
                    ref,
                    media_path.basename(),
                    filetype["mime"]
            )
        else:
            manifest = False

        if filetype["spine"]:
            spine = '<itemref idref="{0}" />'.format(media_path.basename())
        else:
            spine = False

        if self._have_correct_oebps_variant():
            os.chdir("{0}{1}{2}".format(self.temporary_epub["path"],self.oebps["variant"],os.sep))

            new_opf = ""

            with open("content.opf","r") as opf:
                for line in opf:
                    line = line.rstrip()

                    if "item" in line:
                        tab_item = line.split("<")[0]

                    if '</manifest>' in line:
                        if filetype["manifest"]:
                            new_opf += "\n{0}{1}".format(tab_item,manifest)
                            new_opf += "\n</manifest>"
                        else:
                            new_opf += "\n</manifest>"
                    elif '</spine>' in line:
                        if filetype["spine"]:
                            new_opf += "\n{0}{1}".format(tab_item,spine)
                            new_opf += "\n</spine>"
                        else:
                            new_opf += "\n</spine>"
                    else:
                        if line.startswith("<?xml"):
                            new_opf += "{0}".format(line)
                        else:
                            new_opf += "\n{0}".format(line)

            os.remove("content.opf")

            with open("content.opf","w") as opf:
                opf.write(new_opf)

            return True

        else:
            return False

    def epub2_predefined_append_to_opf(self,predef):
        if self._have_correct_oebps_variant():
            if predef == "TocPage":
                self.epub2_append_to_opf(
                    "xhtml",
                    path(
                        "{0}/{1}/Text/TableOfContents.xhtml".format(
                            self.temporary_epub["path"],
                            self.oebps["variant"]
                        )
                    ),
                    "Text/TableOfContents.xhtml"
                )

                return True

            return False
        else:
            return False

    # Table of contents methods

    def _make_raw_toc_list(self,toc_list):
        toc = []
        current_root = None

        for toc_item in toc_list:
            if current_root is None:
                toc.append(toc_item)
                if toc[-1]["level"] == 1:
                    current_root = toc[-1]
            else:
                if toc_item["level"] == 1:
                    toc.append(toc_item)
                    current_root = toc[-1]
                else:
                    try:
                        current_root["subtitles"].append(toc_item)
                    except KeyError:
                        current_root["subtitles"] = [toc_item]

        return toc

    def make_TOC_tree(self):
        location,make_dir = self.guess_destination("text")

        text_dir = None

        if location == "{0}/Text/".format(self.oebps["variant"]):
            text_dir = "{0}/{1}/Text/".format(self.temporary_epub["path"],self.oebps["variant"])

        if text_dir is not None:
            text_files = []
            tf = os.listdir(text_dir)

            for xhtml_file in tf:
                file_path = "{0}{1}".format(text_dir,xhtml_file)

                if os.path.isfile(file_path) and file_path.endswith(".xhtml"):
                    text_files.append(file_path)

            files_tocs = []

            for xhtml_file in text_files:
                with open(xhtml_file,"r") as xf:
                    parser = TocParser()
                    files_tocs.extend(parser.get_struct(xf.read()))

            toc = self._make_raw_toc_list(files_tocs)

            return toc

        else:
            return None

    def make_TOC_page(self,toc_tree):
        """
        Make a table  of contents page (xhtml) according  to the tree
        generated by make_TOC_tree.
        """

        location,make_dir = self.guess_destination("text")

        text_dir = None

        if location == "{0}/Text/".format(self.oebps["variant"]):
            text_dir = "{0}/{1}/Text/".format(self.temporary_epub["path"],self.oebps["variant"])

        if text_dir is not None:
            with open("{0}TableOfContents.xhtml".format(text_dir),"w") as tocf:
                tocf.write(HTML_HEAD)

                for elem in toc_tree:
                    if elem["level"] in [1,2]:
                        tocf.write('\n')

                    tocf.write('<p class="tlevel_{0}">{1}</p>\n'.format(elem["level"],elem["text"]))

                    if elem["subtitles"]:
                        for e in elem["subtitles"]:
                            tocf.write('<p class="tlevel_{0}">{1}</p>\n'.format(e["level"],e["text"]))

                tocf.write(HTML_TAIL)

                return True

    # Other methods

    def open_reader(self):
        epub_path = unicode(self.original_epub["patho"])

        if platform.system() == "Linux" or "bsd" in platform.system().lower():
            os.popen('xdg-open "{0}"'.format(epub_path)).read()
            return True
        elif platform.system() == "Darwin":
            os.system('open {0}'.format(epub_path))
            return True
        elif platform.system() == "Windows":
            return False
        else:
            return False



class TocParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.struct_elements = []
        self.current_struct_level = None
        self.current_struct_text = None

    def get_struct(self,html):
        self.feed(html)
        return self.struct_elements

    def handle_starttag(self, tag, attrs):
        if tag in ["h1","h2","h3","h4","h5","h6"]:
            self.current_struct_level = int(tag[1:])
        else:
            self.current_struct_level = None

    def handle_endtag(self, tag):
        if tag in ["h1","h2","h3","h4","h5","h6"]:
            self.struct_elements.append(
                    {
                        "level":self.current_struct_level,
                        "text":self.current_struct_text,
                    }
                )

            if self.current_struct_level == 1:
                self.struct_elements[-1]["subtitles"] = []

            self.current_struct_level = None
            self.current_struct_text = None

    def handle_data(self, data):
        if self.current_struct_level is not None:
            self.current_struct_text = data
        else:
            self.current_struct_level = None



def ask_for_refresh():
    print "Refresh the EPUB content by selecting EPUB buffer and typing :edit"

def get_current_line(vim):
    return vim.current.buffer[vim.current.window.cursor[0]-1]

def get_user_input(vim,prompt):
    vim.command('let g:EpubMode_Prompt = input("{0} ")'.format(prompt))
    print " "
    return vim.eval("g:EpubMode_Prompt")
