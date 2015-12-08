#!/usr/bin/python2
# -*- coding:Utf-8 -*-

# Vim-EPUB nav python module
# Part of vim-epub plugin for Vim
# Released under GNU GPL version 3
# By Etienne Nadji <etnadji@eml.cc>

from __future__ import unicode_literals

class Nav():
    """<nav> element of EPUB3 toc/nav.html file"""
    def __init__(self):
        self.elems = []

    def tohtml(self):
        if self.elems:
            html = '<nav epub:type="toc" id="toc">\n<ol>\n'

            for elem in self.elems:
                html += elem.tohtml()

            html += '</ol>\n</nav>'

            return html
        else:
            return '<nav epub:type="toc" id="toc">\n</nav>'

    def add_navpoint(self,navpoint):
        self.elems.append(navpoint)

class NavPoint(Nav):
    """
    <li> element embedded into <nav> element of EPUB3 toc/nav.html
    file.
    """

    def __init__(self):
        Nav.__init__(self)
        self.text = "Untitled"
        self.src = "untitled.xhtml"
        self.anchor = ""

    def __str__(self):
        return self.text

    def tohtml(self):
        if self.anchor:
            source = "{0}#{1}".format(
                    self.src,
                    self.anchor
            )
        else:
            source = self.src

        li = '<li><a href="{0}">{1}</a>'.format(
                source,
                self.text
            )

        if self.elems:
            html = "\n{0}\n<ol>\n".format(li)

            for elem in self.elems:
                html += elem.tohtml()

            html = "{0}\n</li></ol>".format(html)

        else:
            html = '\n{0}</li>'.format(li)

        return html

# vim:set shiftwidth=4 softtabstop=4:
