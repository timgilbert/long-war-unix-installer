# Long War installer for Mac

This is a work in progress, intended to make it easier for a user to install the 
[Long War mod](http://ufopaedia.org/index.php?title=Long_War) for Firaxis' XCom game.
This is basically intended to automate the process laid out in 
[this forum post](http://forums.nexusmods.com/index.php?/topic/1918524-long-war-for-mac-osx-pointers-advice/#entry17035114).

Note that Long War ships as a Windows installer. I'm writing this for OS/X, though I'm trying to 
keep it platform independent so that it could run on Linux too in theory. It depends on Python 2.7
(and no other python stuff, currently).

This project depends on the user having [innoextract](http://constexpr.org/innoextract/) installed. 
OS/X `homebrew` users can install it via:

    brew install innoextract

This only works for the Steam installation of XCom: Enemy Within right now. Getting it to work for 
Enemy Unknown or other distributions shouldn't be too hard to do.

Docs are forthcoming. Meanwhile, `./install.py --help` works.

# TODO

* Docs / man page
* Apply patches from mod! ;)
* Patch executables
* Undo and revert to backup
* Validate that game is EW, not EU, or better yet handle EU-only installs
* Validate/update/undo hosts file updates to guard against phone home resets
* wxPython (etc) GUI 
* Linux support (if needed)
