# rednotmd: Convert a RedNotebook database to a tree of MarkDown files (for Obsidian)

This code is kept here for future reference. It comes without any warranty.

The purpose of the program is to help in migrating from RedNotebook to Obsidian as a note-organizing software. 

The main program, `rednotmd.py` takes an input directory containing the `.txt` files of a RedNotebook database and converts these to a collection of MarkDown-formatted files that are organized in 'year'/'month' subdirectories of the output directory.

The module `txt2tagsmw.py` is a slightly modified version of `txt2tags.py` (see [txt2tags source code](https://github.com/txt2tags/txt2tags/tree/v3). It takes care of converting RedNotebook's txt2tags markup to MarkDown markup as used by Obsidian.

# Changes made in this fork:

* The script looks for a folder "Export" in the directory it is ran from, this allows you to take your extracted RedNotebook data instead of looking for it originally referenced at './RedNotebook/data/'
* Added the ability to process the 'U' character
