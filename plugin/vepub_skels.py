#!/usr/bin/python2
# -*- coding:Utf-8 -*-

# Vim-EPUB code skeletons file
# Part of vim-epub plugin for Vim
# Released under GNU GPL version 3
# By Etienne Nadji <etnadji@eml.cc>

XHTML_HEAD = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title></title>
</head>
<body>
"""

XHTML_TAIL = """</body>
</html>"""

XHTML_SKEL = XHTML_HEAD + XHTML_TAIL

TOC_CSS_SKEL = """p {text-align:left;}
.tlevel_1 {}
.tlevel_2 {}
.tlevel_3 {}
.tlevel_4 {}
.tlevel_5 {}
.tlevel_6 {}
"""

CSS_SKEL = """/* Structure */

h1 {page-break-before: always;}

/* Content */

body {}
p {}

sup {font-size: 67%;vertical-align: 33%;}

/* IDs */
/* Classes */
/* Fonts */

"""

NCX_HEAD = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx version="2005-1" xml:lang="en" xmlns="http://www.daisy.org/z3986/2005/ncx/">
    <head>
    </head>
    <docTitle>
        <text></text>
    </docTitle>
"""

# vim:set shiftwidth=4 softtabstop=4:
