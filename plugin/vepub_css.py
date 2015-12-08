#!/usr/bin/python2
# -*- coding:Utf-8 -*-

# Vim-EPUB css python module
# Part of vim-epub plugin for Vim
# Released under GNU GPL version 3
# By Etienne Nadji <etnadji@eml.cc>

from __future__ import unicode_literals

import os

from vim_epub import to_unicode_or_bust,desunicode

def make_fontdef_summary(font_name,sources,output_file):
    if sources:
        output_file = "{0}{1}{2}".format(
                os.path.realpath(os.curdir),
                os.sep,
                output_file
        )

        print output_file

        for ops in ["OEBPS","OPS"]:
            if font_name.startswith(ops):
                font_name = font_name[len(ops):]

        with open(output_file,"w") as out:
            tirets = (len(font_name)-3) * "-"

            nl = "+{0}-------------------------+\n".format(tirets)
            fl = desunicode("\t| Définitions of ") + desunicode(font_name) + desunicode(" font |\n")

            out.write("\t+{0}-------------------------+\n".format(tirets))
            out.write(desunicode("\t| Définitions of ") + desunicode(font_name) + desunicode(" font |\n"))
            out.write("\t+{0}-------------------------+\n\n".format(tirets))

            fonts = []
            for font_def in sources:
                file_def = font_def[0]
                line_def = font_def[1]

                for ops in ["OEBPS","OPS"]:
                    if file_def.startswith(ops):
                        file_def = file_def[len(ops):]

                out.write("File: {0}\nLine: {1}\n\n".format(file_def,line_def))

        return output_file
    else:
        return False

def find_font_face_src(css_file):
    """
    Return a list of dictionnaries as:

        [{
            "url":src of the font,
            "line":line of the src definition in css_file
        },…]
    """

    def _look_attribs(line,uniline=False):
        if uniline:
            lsplited = []

            for l in line.split("{")[1:]:
                if ";" in l:
                    lsplited += l.split(";")
                else:
                    lsplited += l

            for i in lsplited:
                if "src:" in i:
                    if "url(" in i and ");" in line:
                        path = i.split("(")[1].split(")")[0]

                        if path.startswith("'"):
                            path = path.split("'")[1]

                        while path.startswith(".."):
                            path = path.split("..")[1]

                        return path
        else:
            if "src:" in line:
                if "url(" in line and ");" in line:
                    path = line.split("(")[1].split(")")[0]

                    if path.startswith("'"):
                        path = path.split("'")[1]

                    while path.startswith(".."):
                        path = path.split("..")[1]

                    return path

    sources,line_nb = [],1

    with open(css_file,"r") as css:
        look_at_attribs = False

        for line in css:
            line = line.rstrip().strip()

            if line.endswith("}"):
                look_at_attribs = False

            if look_at_attribs:
                ret = _look_attribs(line)

                if ret:
                    sources.append({"url":ret,"line":line_nb})
            else:
                if line.startswith("@font-face"):
                    if line.endswith("{"):
                        look_at_attribs = True
                    else:
                        ret = _look_attribs(line,True)

                        if ret:
                            sources.append({"url":ret,"line":line_nb})

            line_nb += 1

    return sources

# vim:set shiftwidth=4 softtabstop=4:
