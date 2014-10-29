# vim-epub

A Vim plugin for EPUB edition.
Released under GNU GPL 3 (check LICENSE file).

With Vim, you [can already edit an epub file](https://github.com/etnadji/vim-epub/wiki/How-Vim-EPUB-open-EPUB-files-(and-why-it-can’t-work-under-Windows))  and modify it's content, and save, and so on.

But the EPUB file is read-only: you can't add files and do many other things.

**vim-epub** is here to make you free of stupid tasks like extracting the EPUB, add the file you want to add, recompress in 2-steps the EPUB, re-open Vim.

## Installation

### Supported operating systems

#### Unices

- BSDs
- Mac OS
- GNU/Linux distributions

#### And Windows?

**Short version:** Vim-EPUB _can’t work under Microsoft Windows_.

**Long version**:  See [here](https://github.com/etnadji/vim-epub/wiki/How-Vim-EPUB-open-EPUB-files-(and-why-it-can’t-work-under-Windows)).

### Vim

You need a copy of Vim compiled with python support.

### Needed programs

You need the `unzip` programm in order to make zip.vim (built-in) work. It is frequently installed by default on newbies distributions like Ubuntu, Linux Mint…

In Debian-like GNU/Linux distributions:

`sudo apt-get install unzip`

You also needs `pandoc` programm.

Again:

`sudo apt-get install pandoc`

### Plugin managers

#### [Vundle](https://github.com/gmarik/vundle)
  - Add `Bundle 'etnadji/vim-epub'` or `Bundle 'https://github.com/etnadji/vim-epub'` to .vimrc
  - Run `:BundleInstall`

#### [Pathogen](https://github.com/tpope/vim-pathogen)
  - `git clone https://github.com/etnadji/vim-epub ~/.vim/bundle/vim-epub`

#### [NeoBundle](https://github.com/Shougo/neobundle.vim)
  - Add `NeoBundle 'https://github.com/etnadji/vim-epub'` to .vimrc
  - Run `:NeoBundleInstall`

#### [vim-plug](https://github.com/junegunn/vim-plug)
  - Add `Plug 'https://github.com/etnadji/vim-epub'` to .vimrc
  - Run `:PlugInstall`

## Notable features

- Adding medias (XHTML, CSS, fonts, images…)
- Add a _Table of contents_ page.
- Provide a menu to easily link XHTML and CSS contents.
- Merge, rename files embedded in the EPUB
- Check the differences between the current EPUB and another.

### And more:

The full list of features / commands is available on the [wiki](https://github.com/etnadji/vim-epub/wiki/Features) or doc files ([en](https://github.com/etnadji/vim-epub/blob/master/doc/vim-epub.txt) /[fr](https://github.com/etnadji/vim-epub/blob/master/doc/vim-epub-french.txt)):
`:help vim-epub.txt` or `:help vim-epub-french.txt`

## Contribute!

See TODO.md.
