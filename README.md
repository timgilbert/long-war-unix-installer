# Long War installer for Mac

This is a work in progress, intended to make it easier for a user to install the 
[Long War mod](http://ufopaedia.org/index.php?title=Long_War) for Firaxis' XCom game.
This is basically intended to automate the process laid out in 
[this forum post](http://forums.nexusmods.com/index.php?/topic/1918524-long-war-for-mac-osx-pointers-advice/#entry17035114).

Note that Long War ships as a Windows installer. I'm writing this for OS/X, though I'm trying to 
keep it platform independent so that it could run on Linux too in theory.

This project depends on the user having [innoextract](http://constexpr.org/innoextract/) installed. 
OS/X `homebrew` users can install it via

```
brew install innoinstall
```

This only works for the Steam installation of XCom: Enemy Within right now. Getting it to work for 
Enemy Unknown or other distributions shouldn't be too hard to do.

# TODO

Back up files

Patch executables

Undo to backup

Look in `~/Library/Application Support/Steam/config/config.vdf` for "BaseInstallFolder" lines, 
use for heuristic find of XComEW files

Validate EW, not EU

Validate/update/undo hosts file

wxPython GUI 

Cross-platform stuff for Linux
