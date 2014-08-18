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

          - filetype (str):
              "text" for (X)HTML content
              "image" for images content
              "css" for CSS
              "misc" for unknown

        Returns:
          - destination (str)
        """
        # TODO add audio,video categories

        defined = False
        oebps = False

        for f in self.original_epub["zip_files"]:
            if f.startswith("OEBPS/") and not defined:
                oebps = True
                make_dir = True
                defined = True

            if oebps:
                if filetype == "text":
                    if f.startswith("OEBPS/Text/"):
                        make_dir = False
                if filetype == "image":
                    if f.startswith("OEBPS/Images/"):
                        make_dir = False
                if filetype == "css":
                    if f.startswith("OEBPS/Styles/"):
                        make_dir = False
                if filetype == "font":
                    if f.startswith("OEBPS/Fonts/"):
                        make_dir = False
                if filetype == "misc":
                    if f.startswith("OEBPS/Misc/"):
                        make_dir = False
            else:
                # TODO
                pass

        if oebps:
            if filetype == "text":
                ret = "OEBPS/Text/"
            if filetype == "image":
                ret = "OEBPS/Images/"
            if filetype == "css":
                ret = "OEBPS/Styles/"
            if filetype == "font":
                ret = "OEBPS/Fonts/"
            if filetype == "misc":
                ret = "OEBPS/Misc/"

            return ret,make_dir
        else:
            return None,None

    def backup(self):
        """Backup the original epub."""

        backup_file = "{0}.bak".format(self.original_epub["path"].abspath())
        self.original_epub["path"].copy(backup_file)
        print "EPUB Backup in {0}.".format(backup_file)

        return True

    def recompress(self):
        """Recompress the EPUB file from the temporary file."""
        os.chdir(self.temporary_epub["path"])

        if platform.system() in ["Linux","Darwin"] or "bsd" in platform.system().lower():
            nzip = unicode(self.original_epub["path"].basename())
        else:
            # Windows…
            return False

        if platform.system() == "Linux" or "bsd" in platform.system().lower:
            os.popen('zip -X -Z store "{0}" mimetype'.format(nzip)).read()
            os.popen('zip -r "{0}" META-INF/ OEBPS/'.format(nzip)).read()
            return True

        if platform.system() == "Darwin":
            os.system('zip -X "{0}" mimetype'.format(nzip))
            os.system('zip -rg "{0}" META-INF -x \*.DS_Store'.format(nzip))
            os.system('zip -rg "{0}" OEBPS -x \*.DS_Store'.format(nzip))
            return True

    def move_new_and_clean(self):
        """Move the new EPUB file from recompress() and clean up."""

        new_epub = self.original_epub["path"].basename()
        old_epub = self.original_epub["path"].abspath()

        os.remove(old_epub)
        shutil.move(new_epub,old_epub)

        shutil.rmtree(self.temporary_epub["path"])

        return True

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

    # EPUB 2 methods

    def epub2_append_to_opf(self,filetype,media_path,ref):
        """
        Append a file to the OPF entries (manifest + spine).

          - filetype (str):
              "xhtml"
          - media_path: path of the new file to add to the OPF.
              path.path (idem) instance
          - ref: path in the epub of the media, without "OEBPS".
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

        os.chdir("{0}OEBPS{1}".format(self.temporary_epub["path"],os.sep))

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

    def epub2_predefined_append_to_opf(self,predef):
        if predef == "TocPage":
            self.epub2_append_to_opf(
                "xhtml",
                path(
                    "{0}/OEBPS/Text/TableOfContents.xhtml".format(
                        self.temporary_epub["path"]
                    )
                ),
                "Text/TableOfContents.xhtml"
            )

            return True

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

        if location == "OEBPS/Text/":
            text_dir = "{0}/OEBPS/Text/".format(self.temporary_epub["path"])

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

        if location == "OEBPS/Text/":
            text_dir = "{0}/OEBPS/Text/".format(self.temporary_epub["path"])

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
