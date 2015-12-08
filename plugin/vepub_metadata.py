#!/usr/bin/python2
# -*- coding:Utf-8 -*-

# Vim-EPUB metadata python module
# Part of vim-epub plugin for Vim
# Released under GNU GPL version 3
# By Etienne Nadji <etnadji@eml.cc>

from __future__ import unicode_literals

import os

from lxml import etree

class MetadataItem():
    """
    Represents the value  of a metadata to format it  properly into a
    Vim buffer.
    """

    def __init__(self,group):
        self.lines = []
        self.group = group
    def tostring(self,short_title=False,carac="-"):
        text = ""

        for line in self.lines:
            if line["formats"]:
                if line["formats"] == "title":
                    if short_title:
                        try:
                            title = line["text"].split(":")[1].strip()
                        except IndexError:
                            title = line["text"]
                        text = "{0}\n{1}".format(text,title)
                        text = "{0}\n{1}".format(text,len(title)*"-")
                    else:
                        text = "{0}\n{1}".format(text,line["text"])
                        text = "{0}\n{1}".format(text,len(line["text"])*carac)
            else:
                text = "{0}\n{1}".format(text,line["text"])

        return text
    def add_line(self,text,formats=False):
        self.lines.append({"text":text,"formats":formats})
    def __str__(self):
        return self.group

def _get_attrib(data_tag,attrib):
    """
    Get an attribute attrib in a data_tag:

    <tag attribute="something"></tag>

    Returns 'something'

    Remove Dublin Core prefixes.
    """

    d = False

    for attr in data_tag[1]:
        if attr.split("}")[-1] == attrib:
            d = attr
            break

    if d:
        return data_tag[1][d]
    else:
        return False

def _simple_format(tag,tagname,title):
    """Return a simple MetadataItem, typically for a tag without attributes"""

    mline = MetadataItem(tagname)

    mline.add_line(title,"title")
    mline.add_line(tag[0])

    return mline

def _format_meta(meta_tag):
    mline = MetadataItem("meta")

    name = _get_attrib(meta_tag,"name")
    content = _get_attrib(meta_tag,"content")

    if meta_tag[0] is None:
        title = "Misc: {0}".format(name)
        mline.add_line(title,"title")
        mline.add_line(content)
    else:
        title = "Misc: {0}".format(name)
        mline.add_line(title,"title")
        mline.add_line(content)
        mline.add_line(meta_tag[0])

    return mline
def _format_date(date_tag):
    mline = MetadataItem("date")

    t = _get_attrib(date_tag,"event")

    if t in ["original-publication","ops-publication"]:
        t = " ".join(t.split("-"))
        t.capitalize()

    title = "Date: {0}".format(t.capitalize())

    mline.add_line(title,"title")
    mline.add_line(date_tag[0])

    return mline
def _format_identifier(id_tag):
    mline = MetadataItem("identifiers")

    scheme = _get_attrib(id_tag,"scheme")
    id_type = _get_attrib(id_tag,"id")

    if id_tag[0]:
        title = "Identifier: {0}".format(id_type)
        id_text = "{0}: {1}".format(scheme,id_tag[0])

        mline.add_line(title,"title")
        mline.add_line(id_text)

        return mline
    else:
        return ""
def _format_creator(crea_tag):
    """
    Read dc:creator content and return a MetadataItem.

    Format role attribute into a human-readable value.
    """
    mline = MetadataItem("creators")

    role = _get_attrib(crea_tag,"role")

    if crea_tag[0]:
        if role == "aut":
            role = "Author"
        if role == "edt":
            role = "Editor"

        title = "Creator: {0}".format(role)
        mline.add_line(title,"title")
        mline.add_line(crea_tag[0])

        return mline
    else:
        return ""
def _format_contributor(crea_tag):
    """
    Read dc:contributor content and return a MetadataItem.

    Format role attribute into a human-readable value.
    """
    mline = MetadataItem("contributors")

    role = _get_attrib(crea_tag,"role")

    if crea_tag[0]:
        if role == "aut":
            role = "Author"
        if role in ["edt","red"]:
            role = "Editor"

        title = "Contributor: {0}".format(role)
        mline.add_line(title,"title")
        mline.add_line(crea_tag[0])

        return mline
    else:
        return ""
def _format_description(desc_tag):
    """Read dc:description content and return a MetadataItem."""

    mline = MetadataItem("none")

    desc = " ".join([i.strip() for i in desc_tag[0].split('\n')])
    desc.strip()

    mline.add_line("Description","title")
    mline.add_line(desc)

    return mline

def _format_title(title_tag): return _simple_format(title_tag,"none","EPUB's title")
def _format_publisher(pub_tag): return _simple_format(pub_tag,"none","Publisher")
def _format_language(lang_tag): return _simple_format(lang_tag,"none","Language")
def _format_rights(rights_tag): return _simple_format(rights_tag,"none","Rights")
def _format_subject(sub_tag): return _simple_format(sub_tag,"none","Subject")

def read_OPF(opf_file):
    tree = etree.parse(opf_file)

    root_tag = False

    for element in tree.iter():
        if element.tag.split("}")[-1] == "metadata":
            root_tag = element
            break

    if root_tag is not None:
        datas = root_tag.getchildren()

        opf_tags = [
            "identifier","meta","date","title","description",
            "publisher","creator","language","rights","contributor",
            "subject"
        ]

        raw_tags = {}

        for md in datas:
            md_tag = md.tag.split("}")[-1]

            if md_tag in opf_tags:
                raw_tags[md_tag] = [md.text,md.attrib]

        formaters = {
                "date":_format_date,
                "meta":_format_meta,
                "identifier":_format_identifier,
                "title":_format_title,
                "description":_format_description,
                "publisher":_format_publisher,
                "creator":_format_creator,
                "language":_format_language,
                "rights":_format_rights,
                "contributor":_format_contributor,
                "subject":_format_subject,
        }

        metadatas = []

        for md in raw_tags.items():
            if md[0] in formaters:
                metadatas.append(formaters[md[0]](md[1]))
            else:
                pass

        return raw_tags,metadatas

def make_OPF_summary(metadatas,output_file,grouped=False):
    try:
        os.remove(os.path.realpath(output_file))
    except OSError,err:
        if err.errno == 2:
            pass

    if grouped:
        groups = {"none":[]}

        with open(output_file,"w") as out:
            out.write("\t+------------------+\n")
            out.write("\t| EPUB's metadatas |\n")
            out.write("\t+------------------+\n\n")

            for md in metadatas:
                if md.group is None:
                    groups["none"].append(md)
                else:
                    if md.group in groups:
                        groups[md.group].append(md)
                    else:
                        groups[md.group] = [md]

            for group in groups.items():
                if group[0] == "none":
                    for elem in group[1]:
                        out.write(
                                "{0}\n".format(
                                    elem.tostring(carac="=").strip()
                                )
                        )

                        out.write("\n")

                else:
                    out.write(
                            "{0}\n".format(group[0].capitalize())
                    )

                    out.write(
                            "{0}\n".format(len(group[0]) * "=")
                    )

                    for elem in group[1]:
                        out.write(
                                "{0}\n".format(
                                    elem.tostring(True).strip()
                                )
                        )

                    out.write("\n")
    else:
        with open(output_file,"w") as out:
            out.write("\t+------------------+\n")
            out.write("\t| EPUB's metadatas |\n")
            out.write("\t+------------------+\n\n")

            for md in metadatas:
                out.write("{0}\n".format(md.tostring()))

def do_all(opf_file,output_file,grouped=False):
    metadatas,mtext = read_OPF(opf_file)
    make_OPF_summary(mtext,output_file,grouped)

# vim:set shiftwidth=4 softtabstop=4:
