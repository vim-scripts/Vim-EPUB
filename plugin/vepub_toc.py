#!/usr/bin/python2
# -*- coding:Utf-8 -*-

# Vim-EPUB html toc parser python module
# Part of vim-epub plugin for Vim
# Released under GNU GPL version 3
# By Etienne Nadji <etnadji@eml.cc>

from __future__ import unicode_literals

from HTMLParser import HTMLParser

class TocParser(HTMLParser):
    """Parse HTML to get <hX> tags"""

    def __init__(self):
        HTMLParser.__init__(self)

        self.struct_elements = []

        self.current_struct_level = None
        self.current_struct_text = None
        self.current_struct_id = False

    def get_struct(self,html,source):
        self.source = source

        self.feed(html)

        return self.struct_elements

    def handle_starttag(self, tag, attrs):
        if tag in ["h1","h2","h3","h4","h5","h6"]:
            self.current_struct_level = int(tag[1:])

            if attrs:
                for attr in attrs:
                    if attr[0] == "id":
                        self.current_struct_id = attr[1]

        else:
            self.current_struct_level = None

    def handle_endtag(self, tag):
        if tag in ["h1","h2","h3","h4","h5","h6"]:
            self.struct_elements.append(
                    {
                        "level":self.current_struct_level,
                        "text":self.current_struct_text,
                        "id":self.current_struct_id,
                        "source":self.source
                    }
                )

            if self.current_struct_level == 1:
                self.struct_elements[-1]["subtitles"] = []

            self.current_struct_level = None
            self.current_struct_text = None
            self.current_struct_id = False

    def handle_data(self, data):
        if self.current_struct_level is not None:
            self.current_struct_text = data
        else:
            self.current_struct_level = None

# vim:set shiftwidth=4 softtabstop=4:
