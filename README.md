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

See also [this Linux installer by wghost](https://github.com/wghost/LongWar-Linux).

## Usage

Docs are forthcoming. Meanwhile, `./install.py --help` works. Basically once you've downloaded the mod
somewhere, do this:

    ./install.py --apply "$HOME/Downloads/Long War 3 EW Beta 12-88-3-0b12.exe" -d

The most functional part of this is currently the ability to patch the executable file.

	./install.py --patch-executable "XCOM Enemy Within" "XCOM Enemy Within.patched" -d

### Backups

The script will back up the files it's about to modify before it copies anything from the mod to your 
installed game directory. Currently the backups are stored under `Long-War-Backups` under the game 
installation directory (typically `~/Library/Application Support/Steam/SteamApps/common/XCom-Enemy-Unknown`).

You should be able to roll back an installation by using the `--uninstall` option to the script. You 
can see a list of mods that have been backed up using the `--list` option:

	% ./install.py --list
	Long_War_3_Beta_13-88-3-0b13: applied at 2014-08-04 20:19:00

	% ./install.py --uninstall Long_War_3_Beta_13-88-3-0b13
	Reverted to backup "Long_War_3_Beta_13-88-3-0b13"

**However, please note that this is alpha-quality software at best!** I try to be careful but make 
no guarantees. If nothing else, you should be able to revert to your vanilla install by using the 
"Verify Integrity of Game Cache" option from Steam.

## TODO

* Before run, validate whether game has been run once 
  * Existence of Feral directory should indicate this
  * If it doesn't exist, validate that phone home is unblocked prior to first run
* Apply patches from mod! ;)
  * Needs some tweaks to deal with Feral directory
  * [Anderkent's post here](http://forums.nexusmods.com/index.php?/topic/1918524-long-war-for-mac-osx-pointers-advice/?p=17283439)
    is an excellent summary
  * Uninstall should remove `MacInit/*.ini`
* Docs / man page
* Add `--backup` flag to back up a directory without overwriting files
* Interactive mode for script (y/n for overwriting files, etc)
* Validate that game is EW, not EU, or better yet handle EU-only installs
  * We should at least make sure `XCOMData/XEW` exists, else exit with an error message

### Blue Sky TODO
* exec as `sudo $@` to gain root privs for enable / disable hosts
* Checksums of backed up files, probably [following this algorithm](http://stackoverflow.com/a/3431835/87990)?
  * Checksum entire insalled game tree, and verify it after backups
* wxPython (etc) GUI 
  * Install as an app via pyfreeze
  * But I'd like the script to be functional as well
* Linux support
  * Some refactoring into platform-specific subclasses or whatnot
* Handle Mac App Store installs

## Bugs

* Multiple backups grow the new files list each time
* Root level files are installed in XCOMData/XEW instead of at the root

# State of the Mod

As I write this in early August 2014, users have reported several bugs after applying Long War to
their XCom: EW installations on OS/X. I don't know much about modding and probably can't help with 
these issues; I'm just focused on getting the installer script to work. Please see 
[the official Long War mod forum](http://forums.nexusmods.com/index.php?/forum/665-xcom-file-discussions/)
for help with the mod itself.
