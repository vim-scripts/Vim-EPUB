#!/usr/bin/python2
# -*- coding:Utf-8 -*-

# Vim-EPUB python core file

# Part of vim-epub plugin for Vim
# Released under GNU GPL version 3

# By Etienne Nadji <etnadji@eml.cc>

#--- builtin -------------------------------------

from __future__ import unicode_literals

import os
import platform
import shutil
import zipfile

from subprocess import Popen, PIPE, STDOUT

#--- third parts ---------------------------------

import epub
import epubdiff

from path import path

#--- Vim-EPUB ------------------------------------

import vepub_nav
import vepub_toc

#=== EPUB Class ================================================================

class EPUB:
    """
    EPUBs class.

    A representation  of the  epub file currently  edited and  of the
    temporary epub file folder used to bypass zip.vim read-only.
    """

    def __init__(self,vim_buffers=None):
        """
        Init method.

        vim_buffers: vim.buffers from vim python module.
        """

        if vim_buffers is None:
            self.valid = False

        else:
            # Find the  epub's zip.vim buffer to get  the edited epub
            # filepath.

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

                self.original_epub["path"] = path(
                        to_unicode_or_bust(epub_master_buffer)
                )
                self.original_epub["zip_object"] = zipfile.ZipFile(epub_master_buffer)
                self.original_epub["zip_files"] = self.original_epub["zip_object"].namelist()

                self.oebps = {"used":False,"variant":""}

            else:
                # No epub file found

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
        """Extract the EPUB to a temporary folder"""

        if extract_path is None:
            if self.temporary_epub["path"] is not None:
                self.original_epub["zip_object"].extractall(
                        path=self.temporary_epub["path"]
                )
                return True

            else:
                return False
        else:
            self.original_epub["zip_object"].extractall(path=extract_path)

            return True

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
            if filetype == "html": filetype = "text"

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

    def add_media(self,raw_media_path):
        if self.temporary_epub["have_dir"]:

            media_path = path(raw_media_path)
            media_name = media_path.basename()

            if media_path.ext[1:].lower() in ["jpg","jpeg","png","gif"]:
                media_type = "image"
            elif media_path.ext[1:].lower() in ["css"]:
                media_type = "css"
            elif media_path.ext[1:].lower() in ["html","xhtml"]:
                media_type = "text"
            elif media_path.ext[1:].lower() in ["ttf","woff","otf"]:
                media_type = "font"
            elif media_path.ext[1:].lower() in ["mp3","mp4","ogg"]:
                media_type = "audio"
            else:
                print "Unknown format:",media_path.ext[1:]
                media_type = "misc"

            # Find the appropriate folder in the EPUB file for the new media.
            add_in,make_dir = self.guess_destination(media_type)

            if make_dir:
                try:
                    os.mkdir(
                        "{0}{1}{2}".format(
                            self.temporary_epub["path"],
                            os.sep,
                            add_in
                        )
                    )
                except OSError:
                    pass

            in_epub_path = None

            if self.oebps["variant"] in add_in:
                # TODO add audio,video categories

                valid = False
                for mt in [
                    "Text","Images","Style","Styles","Fonts","Misc"
                    ]:

                    if mt in add_in:
                        valid = True

                if valid:
                    in_epub_path = "{0}{1}{2}".format(
                        self.temporary_epub["path"],
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
                        return self.epub2_append_to_opf(
                            media_path.ext[1:].lower(),
                            media_path,
                            in_epub_oebps_path
                        )

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
                os.popen('zip -r "{0}" *'.format(nzip))
                return True

            if platform.system() == "Darwin":
                os.system('zip -X "{0}" mimetype'.format(nzip))
                os.system('zip -rg "{0}" META-INF -x \*.DS_Store'.format(nzip))
                os.system('zip -rg "{0}" *'.format(nzip))
                os.system('zip -rg "{0}" {1} -x \*.DS_Store'.format(nzip,self.oebps["variant"]))
                return True

    def move_new_and_clean(self):
        """Move the new EPUB file from recompress() and clean up."""

        new_epub = self.original_epub["path"].basename()
        old_epub = self.original_epub["path"].abspath()

        os.remove(old_epub)
        shutil.move(new_epub,old_epub)

        self.remove_temp_dir()

        return True

    def remove_temp_dir(self):
        """Remove the temporary epub directory"""
        shutil.rmtree(self.temporary_epub["path"])

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
        """Rename old_path into new_path."""

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

    def get_current_buffer_file(self,vim,temp_dir=False):
        """
        As the name of the method says.

        vim: vim from vim module.
        temp_dir: return the filepath of the current buffer, but the
                  filepath in the temporary epub folder.
        """

        fname = vim.current.buffer.name.decode("utf8").split("::")[-1]

        if temp_dir:
            return "{0}{1}".format(self.temporary_epub["path"],fname)
        else:
            return fname

    def get_file(self,file_path,temp_dir=False):
        """
        Check for a file in the EPUB's content and return it's path.

          - file_path: path.path instance
        """

        if self.has_file(file_path):
            for f in self.original_epub["zip_files"]:
                if file_path.ext[1:] in f:
                    if file_path.basename() in f.split("/")[-1]:
                        if temp_dir:
                            return "{0}{1}".format(self.temporary_epub["path"],f)
                        else:
                            return f
        else:
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
                "html":{"mime":"text/html","manifest":True,"spine":True},
                "ttf":{"mime":"application/x-font-ttf","manifest":True,"spine":False},
                "woff":{"mime":"application/font-woff","manifest":True,"spine":False},
                "otf":{"mime":"application/font-sfnt","manifest":True,"spine":False},

                "png":{"mime":"image/png","manifest":True,"spine":False},
                "jpg":{"mime":"image/jpg","manifest":True,"spine":False},
                "gif":{"mime":"image/gif","manifest":True,"spine":False},
                "svg":{"mime":"image/svg+xml","manifest":True,"spine":False},

                # Yes, Ogg file really have text/plain as mime
                "ogg":{"mime":"text/plain","manifest":True,"spine":False},
                "css":{"mime":"text/css","manifest":True,"spine":False},
                "js":{"mime":"text/javascript","manifest":True,"spine":False},

                "mp3":{"mime":"audio/mpeg","manifest":True,"spine":False},
                "mp4":{"mime":"audio/mp4","manifest":True,"spine":False},

                # aliases
                "jpeg":{"use":"jpg"},
                "htm":{"use":"html"},
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

                    if _desunicode("item") in line:
                        tab_item = line.split("<".encode("utf8"))[0]

                    if _desunicode('</manifest>') in line:
                        if filetype["manifest"]:
                            new_opf += "\n{0}{1}".format(tab_item,manifest)
                            new_opf += "\n</manifest>"
                        else:
                            new_opf += "\n</manifest>"
                    elif _desunicode('</spine>') in line:
                        if filetype["spine"]:
                            new_opf += "\n{0}{1}".format(tab_item,spine)
                            new_opf += "\n</spine>"
                        else:
                            new_opf += "\n</spine>"
                    else:
                        if line.startswith(_desunicode("<?xml")):
                            new_opf += "{0}".format(line)
                        else:
                            new_opf = new_opf + "\n" + to_unicode_or_bust(line)

            os.remove("content.opf")

            # Convert the damn OPF into str (not unicode)
            new_opf = new_opf.encode("utf8")

            with open("content.opf","w") as opf:
                opf.write(new_opf)

            return True

        else:
            return False

    def epub2_predefined_append_to_opf(self,predef):
        """
        Method for the lazy man I am.

        Append predefined things to OPF.

        predef values:
            "TocPage" − Add the table of contents made by Vim-EPUB.
        """

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
                xhtml_source = xhtml_file[len(self.temporary_epub["path"])+1:]

                if self.oebps["used"]:
                    xhtml_source = xhtml_source[len(self.oebps["variant"])+1:]

                with open(xhtml_file,"r") as xf:
                    parser = vepub_toc.TocParser()
                    files_tocs.extend(
                            parser.get_struct(
                                xf.read(),
                                xhtml_source
                            )
                    )

            toc = self._make_raw_toc_list(files_tocs)

            return toc

        else:
            return None

    def _make_ncx(self,toc_tree):
        def _make_navmap(toc_tree):
            def get_navpoint(elem,nav_map):
                recursions = elem["level"] - 1

                if recursions:
                    recur_done = 0
                    sup_navpoint = nav_map.nav_point[-1]

                    while recur_done < recursions:
                      try:
                        sup_navpoint = sup_navpoint.nav_point[-1]
                      except IndexError:
                        break
                      recur_done += 1

                    return sup_navpoint
                else:
                    return nav_map

            nav_map = epub.ncx.NavMap()

            for elem in toc_tree:
                if not "source" in elem:
                    elem["source"] = None
                if not "id" in elem:
                    elem["id"] = ""

                if elem["id"]:
                    source = "{0}#{1}".format(elem["source"],elem["id"])
                else:
                    source = elem["source"]

                nav_point = epub.ncx.NavPoint()
                nav_point.add_label(elem["text"])
                nav_point.src = source

                nav_master = get_navpoint(elem,nav_map)
                nav_master.add_point(nav_point)

                if elem["subtitles"]:
                    for sub in elem["subtitles"]:
                        if not "source" in sub:
                            sub["source"] = None
                        if not "id" in sub:
                            sub["id"] = ""

                        if sub["id"]:
                            source = "{0}#{1}".format(sub["source"],sub["id"])
                        else:
                            source = sub["source"]

                        nav_point = epub.ncx.NavPoint()
                        nav_point.add_label(sub["text"])
                        nav_point.src = source

                        nav_master = get_navpoint(sub,nav_map)
                        nav_master.add_point(nav_point)

            return nav_map.as_xml_element().toxml()

        temp_1 = "{0}tmp.xml".format(self.temporary_epub["path"])
        temp_2 = "{0}tmp2.xml".format(self.temporary_epub["path"])

        with open(temp_1,"w") as tp1:
            tp1.write(_make_navmap(toc_tree))

        os.system(
                "xmllint --format --recover {0} > {1}".format(
                    temp_1,
                    temp_2
                )
        )

        navmap = ""

        with open(temp_2,"r") as t:
            xml_declaration = True
            for line in t:
                if xml_declaration:
                    xml_declaration = False
                    continue
                else:
                    navmap += line

        for xml in [temp_1,temp_2]:
            os.remove(xml)

        return navmap

    def _make_nav(self,toc_tree):
        def _make_navmap(toc_tree):
            def get_navpoint(elem,nav_map,added):
                for litem in added:
                    if elem["level"] - 1 == litem[0]:
                        return litem[1]

                return nav_map

            nav_map = vepub_nav.Nav()
            added = []

            for elem in toc_tree:
                nav_point = vepub_nav.NavPoint()
                nav_point.text = elem["text"]

                if "source" in elem:
                    nav_point.src = elem["source"]
                if "id" in elem:
                    nav_point.anchor = elem["id"]

                nav_master = get_navpoint(elem,nav_map,added)
                nav_master.add_navpoint(nav_point)

                if elem["level"] == 1:
                    added = [[elem["level"],nav_point]]
                else:
                    added.append([elem["level"],nav_point])

                if elem["subtitles"]:
                    for sub in elem["subtitles"]:

                        nav_point = vepub_nav.NavPoint()
                        nav_point.text = sub["text"]

                        if "source" in elem:
                            nav_point.src = sub["source"]
                        if "id" in elem:
                            nav_point.anchor = sub["id"]

                        nav_master = get_navpoint(sub,nav_map,added)
                        nav_master.add_navpoint(nav_point)

                        added.append([sub["level"],nav_point])

            return nav_map.tohtml()

        return _make_navmap(toc_tree)

    def make_TOC(self,vim,epub2=True,epub3=True):
        """
        Make  the  *internal*  Table  Of Contents,  not  a  Table  Of
        Contents page.

        vim: vim from vim module.
        epub2 (bool): make TOC as understood by EPUB2?
        epub3 (bool): make TOC as understood by EPUB3?

        You can set epub2 & epub3 to True, it is compatibility mode.

        You can  also set epub2 &  epub3 to False, but  that would be
        stupid.
        """

        toc_tree = self.make_TOC_tree()

        if epub2 or epub3:
            make = True

        if make:
            if epub2:
                self.epub2_make_ncx(vim,toc_tree)

            if epub3:
                self.make_nav(vim,toc_tree)

            return True
        else:
            # Seriously…
            return False

    def epub2_make_ncx(self,vim,toc_tree):
        ncx = self.get_files_by_extension("ncx")

        output_file = False

        if ncx:
            output_file = ncx[0]
            new = False
        else:
            self.guess_destination(None)

            if self.oebps["used"]:
                output_file = "{0}/toc.ncx".format(self.oebps["variant"])
            else:
                output_file = "toc.ncx"

            new = True

        if output_file:
            output_file = "{0}{1}".format(self.temporary_epub["path"],output_file)

            # NCX "header" + <navMap>
            if new:
                header = get_skel(vim,"ncx_head")
            else:
                header = ""
                with open(output_file,"r") as ncx:
                    record = True

                    for line in ncx:
                        if record:
                            if "<navMap>" in line:
                                record = False
                            else:
                                header += line

            # navpoints
            navpoints = self._make_ncx(toc_tree)

            # NCX "footer"
            footer = get_skel(vim,"ncx_tail")

            # Write all to output_file

            if not new:
                os.remove(output_file)

            with open(output_file,"w") as ncx:
                for section in [header,navpoints,footer]:
                    ncx.write(section)

    def make_nav(self,vim,toc_tree):
        nav = False

        for fname in ["toc.html","toc.xhtml","nav.html","nav.xhtml"]:
            fname = path(fname)

            if self.has_file(fname):
                nav = self.get_file(fname,True)
                break

        output_file = False

        if nav:
            new = False
        else:
            if self.oebps["used"]:
                output_file = "{0}{1}{2}{3}".format(self.temporary_epub["path"],self.oebps["variant"],os.sep,"nav.html")
            else:
                output_file = "{0}{1}".format(self.temporary_epub["path"],"nav.html")
            new = True

        if output_file:
            # NAV "header" + <navMap>
            if new:
                header = get_skel(vim,"nav_head")
            else:
                header = ""
                with open(output_file,"r") as ncx:
                    record = True

                    for line in ncx:
                        if record:
                            if "<body>" in line:
                                record = False
                            else:
                                header += line

            # navpoints
            navpoints = self._make_nav(toc_tree)

            # NAV "footer"
            footer = get_skel(vim,"nav_tail")

            # Write all to output_file

            print output_file

            if not new:
                os.remove(output_file)

            with open(output_file,"w") as nav:
                for section in [header,navpoints,footer]:
                    nav.write(section)

    def make_TOC_page(self,vim,toc_tree):
        """
        Make a table  of contents page (xhtml) according  to the tree
        generated by make_TOC_tree.
        """

        location,make_dir = self.guess_destination("text")

        text_dir = None

        if location == "{0}/Text/".format(self.oebps["variant"]):
            text_dir = "{0}/{1}/Text/".format(
                    self.temporary_epub["path"],
                    self.oebps["variant"]
            )

        if text_dir is not None:
            with open("{0}TableOfContents.xhtml".format(text_dir),"w") as tocf:
                tocf.write(get_skel(vim,"xhtml_head"))

                for elem in toc_tree:
                    if elem["level"] in [1,2]:
                        tocf.write('\n')

                    tocf.write(
                            '<p class="tlevel_{0}">{1}</p>\n'.format(
                                elem["level"],
                                elem["text"]
                            )
                    )

                    if elem["subtitles"]:
                        for e in elem["subtitles"]:
                            tocf.write(
                                    '<p class="tlevel_{0}">{1}</p>\n'.format(
                                        e["level"],
                                        e["text"]
                                    )
                            )

                tocf.write(get_skel(vim,"xhtml_tail"))

                return True

    # Other methods

    def open_reader(self,vim):
        """Open the EPUB reader defined by the OS"""

        custom_command = vim.eval("g:VimEPUB_OpenCommand")
        if custom_command.lower() == "none":
            custom_command = False

        epub_path = unicode(self.original_epub["path"])

        if platform.system() == "Linux" or "bsd" in platform.system().lower():
            if custom_command:
                os.popen(
                        '{0} "{1}"'.format(
                            custom_command,
                            epub_path
                        )
                ).read()
            else:
                os.popen(
                        'xdg-open "{0}"'.format(epub_path)
                ).read()

            return True

        elif platform.system() == "Darwin":
            if custom_command:
                os.system(
                        'open -a "{0}" {1}'.format(
                            custom_command,
                            epub_path
                        )
                )
            else:
                os.system('open {0}'.format(epub_path))

            return True

        elif platform.system() == "Windows":
            return False

        else:
            return False

    def open_diff(self,vim,epub2):
        """
        Use epubdiff to  produce a diff between current  EPUB and the
        EPUB  with  epub2  filepath  and  open a  vim  split  to show
        this diff.
        """

        epub2 = path(epub2)

        if epub2.isfile():
            # Try to remove the diff file if it already exists
            try:
                os.remove(".vepub.diff")
            except OSError,err:
                if err.errno == 2:
                    pass

            # Make the diff
            checker = epubdiff.EpubDiff(
                    self.original_epub["path"].realpath(),
                    epub2.realpath()
                    )
            checker.check()

            # Writes it in a file
            with open(".vepub.diff","w") as df:
                first = True
                for diff_elem in checker.difflog:
                    for dde in diff_elem:
                        if isinstance(dde,tuple):
                            if first:
                                df.write("{0}: ".format(dde[1]))
                                first = False
                            else:
                                df.write("\n{0}: ".format(dde[1]))
                        else:
                            dde = to_unicode_or_bust(dde) + "\n"
                            df.write(dde.encode('utf-8'))

            # Open the  diff in the correct split and  make the split
            # buffer disappear of buffers list if closed.
            vim.command(":{0} .vepub.diff".format(get_split_cmd(vim,"diff")))
            vim.command(":setl buftype=nofile bufhidden=wipe nobuflisted")

            return True
        else:
            return False

#===============================================================================



#=== Functions =================================================================

# Functions to manage this shitty unicode/str compat.

def to_unicode_or_bust(obj, encoding='utf-8'):
    """By Kumar McMillan"""

    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj

def _desunicode(s): return s.encode("utf8")

def merge_html(file_1,file_2,output_file):
    """Merge file_1 and file_2 into output_file"""

    try:
        output_file = path(output_file)
        os.remove(output_file.realpath())
    except OSError,err:
        if err.errno == 2:
            pass

    file_1,file_1_contents = path(file_1),""
    file_2,file_2_contents = path(file_2),""

    with open(file_1.realpath(),"r") as fi:
        record = True

        for line in fi:
            if record:
                if line.strip() == "</body>":
                    record = False
                else:
                    file_1_contents += line

    with open(file_2.realpath(),"r") as fi:
        record = False

        for line in fi:
            if record:
                file_2_contents += line
            else:
                if line.strip() == "<body>":
                    record = True

    with open(output_file.realpath(),"w") as fi:
        fi.write(file_1_contents)
        fi.write("\n")
        fi.write(file_2_contents)

    return True

# Python/Vim utilities

def refresh(vim,msg=False,msg_echom=False):
    """
    Refresh the Vim buffers and show a message.

    msg: False:  do nothing
         String: message to show

    msg_echom: use :echom to show a permanent message
    """

    if msg:
        if msg_echom:
            echom(vim,msg)
        else:
            print msg

    vim.command(":edit")

def normal(vim,keys,silent=True,end_in_normal_mode=False):
    """
    Do normal mode moves/commands.

    keys (str): sequence to execute in normal mode
    silent (bool): execute with silent! … or not
    end_in_normal_mode: Make Vim return into normal mode at the end of the sequence.
    """

    if end_in_normal_mode:
        if not keys.endswith("\<esc>"):
            keys = keys + "\<esc>"

    if silent:
        normal_maps = ':silent! execute "normal! {0}"'.format(keys)
    else:
        normal_maps = ':execute "normal! {0}"'.format(keys)

    vim.command(normal_maps)

def cat_in_buffer(vim,filepath,silent=True):
    """Cat/Dump a file into the current buffer"""

    if silent:
        vim.command(':silent! r !cat "{0}"'.format(filepath))
    else:
        vim.command(':r !cat "{0}"'.format(filepath))

def get_current_line(vim):
    """Shorcut function to get vim current buffer's current line"""

    try:
        return vim.current.buffer[vim.current.window.cursor[0]-1]
    except IndexError:
        return False

def get_next_line(vim):
    """
    Shorcut function to get current  vim buffer's line next to the
    current one.
    """

    try:
        return vim.current.buffer[vim.current.window.cursor[0]]
    except IndexError:
        return False

def get_user_input(vim,prompt,erase=True):
    """Use g:VimEPUB_Prompt as a variable to get user input"""

    vim.command('let g:VimEPUB_Prompt = input("{0} ")'.format(prompt))
    print " "

    uinput = to_unicode_or_bust(vim.eval("g:VimEPUB_Prompt"))

    if erase:
        vim.command('let g:VimEPUB_Prompt = "None"')

    return uinput

def echom(vim,message):
    """Shorcut function for :echom"""
    vim.command("""echom '{0}'""".format(message))

def get_split_cmd(vim,target):
    """Get the Vim-EPUB option to make the correct split."""

    if target == "diff":
        try:
            split = vim.eval("g:VimEPUB_DiffSplit")
        except:
            return "sp"
    elif target == "metadatas":
        try:
            split = vim.eval("g:VimEPUB_MetaSplit")
        except:
            return "vsp"
    else:
        return "sp"

    if split.lower() in ["sp","vsp"]:
        return split.lower()

    if split.lower() == "horizontal":
        return "sp"
    elif split.lower() == "vertical":
        return "vsp"
    else:
        return "sp"

def get_epub_version(vim):
    epub_versions = vim.eval("g:VimEPUB_EPUB_Version")

    if len(epub_versions.split(";")) > 1:
        epub_versions = [int(version) for version in epub_versions.split(";")]
    else:
        epub_versions = [int(epub_versions)]

    if len(epub_versions):
        if len(epub_versions) > 1:
            # Compatibility between EPUB2 & EPUB3 : g:VimEPUB_EPUB_Version = "2;3"
            return "compatibility"

        else:
            if epub_versions[0] == 2:
                # EPUB2 only: g:VimEPUB_EPUB_Version = "2"
                return "epub2"

            elif epub_versions[0] == 3:
                # EPUB3 only: g:VimEPUB_EPUB_Version = "3"
                return "epub3"

    else:
        return "epub3"

def get_skel(vim,skel_name,get_filepath=False):
    """
    Get code  snippets/skeletons in  the correct filepath  and return
    its text, or its filepath (if get_filepath set to True).

    skel_name (str): skeleton name
    get_filepath (bool): See above.
    """

    skels_dir = vim.eval("g:VimEPUB_Skels_Dir")
    plugin_dir = vim.eval("g:VimEPUB_PluginPath")

    if skels_dir.lower() == "none":
        skels_dir = path("{0}{1}skels{1}".format(plugin_dir,os.sep))
    else:
        skels_dir = path(skels_dir).realpath()

    skel = None

    for f in skels_dir.files():
        if f.namebase == skel_name:
            skel = f.realpath()
            break

    if skel is None:
        return False
    else:
        if get_filepath:
            return skel
        else:
            with open(skel,"r") as sf:
                return sf.read()

def make_new_epub(vim,filename):
    """
    Make   a   new    epub   file   from   a    template   based   on
    g:VimEPUB_EPUB_Version value.
    """

    def copy(template,filename):
        new_file = "{0}{1}{2}.epub".format(
                os.path.realpath(os.curdir),
                os.sep,
                filename
        )

        shutil.copy(template,new_file)

        return new_file

    epub_version = get_epub_version(vim)

    do = True

    template = get_skel(
            vim,
            "epub_{0}".format(epub_version),
            get_filepath=True
    )

    if template:
        return copy(template,filename)

    else:
        for version in ["epub3","epub2","compatibility"]:
            temp = get_skel(
                    vim,
                    "epub_{0}".format(version),
                    get_filepath=True
            )

            if temp: break

        if temp:
            return copy(temp,filename)

        else:
            return False
