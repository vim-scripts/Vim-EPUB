# vim-epub

A Vim plugin for EPUB edition.
Released under GNU GPL 3 (check LICENSE file).

With Vim, you can already edit an epub file:

`au BufReadCmd *.epub call zip#Browse(expand("<amatch>"))`

And modify it's content, and save, and so on.

But you can't add files.
Tidy the code.
Make the table of contents. *Oh wait, you can. But that’s boring.*

**vim-epub** is here to make you free of stupid tasks like extracting the EPUB, add the file you want to add, recompress in 2-steps the EPUB, re-open Vim.

In fact, Vim-EPUB does this for you.

## Installation

### Supported operating systems

#### Unices

- BSDs
- Mac OS
- GNU/Linux distributions

#### And Windows?

**Short version:** Vim-EPUB _can’t work under Microsoft Windows_.

**Long version**: To work, vim-epub needs a functionnal zip.vim, wich is a default vim plugin. Sadly, zip.vim only works in unices, like BSDs,GNU/Linux distributions and Mac OS.

### Vim

You need a copy of Vim compiled with python support. To check if your copy has this:

`:version`

If you have '+python' in the output, it's alright. Otherwise, install another version of Vim.

### Needed programs

You need the `unzip` in order to make zip.vim (built-in) work. It is frequently installed by default on newbies distributions like Ubuntu, Linux Mint…

In Debian-like GNU/Linux distributions:

`sudo apt-get install unzip`

### Plugin managers

Use your plugin manager of choice.

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

## State of the art

In the state of the art, vim-epub can:

- Add an empty page (XHTML).
- Add an empty CSS stylesheet.
- Add a _Table of contents_ page.
- Add medias (images, etc.).
- Make your OS open the EPUB with its selected reader.
- Provide a menu to easily link XHTML and CSS contents.

## Todo

1. Improve `AddMedia` command.
2. `MakeTOC`, a command to make the toc.ncx
