# Long War installer for Mac

This is a work in progress, intended to make it easier for a user to install the 
[Long War mod](http://ufopaedia.org/index.php?title=Long_War) for Firaxis' XCom game.
This is basically intended to automate the process laid out in 
[this forum post](http://forums.nexusmods.com/index.php?/topic/1918524-long-war-for-mac-osx-pointers-advice/#entry17035114).

**Note: this doesn't work yet!** Also, this script is still in active development, so while I 
welcome pull requests, please check with me first.

Note that Long War ships as a Windows installer. I'm writing this for OS/X, though I'm trying to 
keep it platform independent so that it could run on Linux too in theory. It depends on Python 2.7
(and no other python stuff, currently).

This project depends on the user having [innoextract](http://constexpr.org/innoextract/) installed. 
OS/X `homebrew` users can install it via:

    brew install innoextract

This only works for the Steam installation of XCom: Enemy Within right now. Getting it to work for 
Enemy Unknown or other distributions shouldn't be too hard to do.

Note: for detailed information about XCom modding, please see 
[the excellent Modding Tools page](http://wiki.tesnexus.com/index.php/Modding_Tools_-_XCOM:EU_2012) 
on the Nexus wiki.

## Usage

Docs are forthcoming. Meanwhile, `./install.py --help` works. Basically once you've downloaded the mod
somewhere, do this:

    ./install.py --apply "$HOME/Downloads/Long War 3 EW Beta 12-88-3-0b12.exe" -d

The most functional part of this is currently the ability to patch the executable file.

	./install.py --patch-executable "XCOM Enemy Within" "XCOM Enemy Within.patched" -d

## TODO

* Interactive mode for script (y/n for overwrting files, etc)
* Docs / man page
* Apply patches from mod! ;)
* Validate that game is EW, not EU, or better yet handle EU-only installs
* Validate/update/undo hosts file updates to guard against phone home resets
* wxPython (etc) GUI 
* Linux support (if needed)
* Copy Localization files to MacOverrides inside .app
* Optional param to set backup directory root? Might be more linux friendly
* Checksums of backed up files, probably [following this algorithm](http://stackoverflow.com/a/3431835/87990)?
* Add --backup flag to back up a directory without overwriting files

## Bugs

* Multiple backups grow the new files list each time
* Root level files are installed in XCOMData/XEW instead of at the root
