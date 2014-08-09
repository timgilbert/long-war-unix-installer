# Long War installer for Mac

This is a work in progress, intended to make it easier for a user to install the 
[Long War mod](http://ufopaedia.org/index.php?title=Long_War) for Firaxis' XCom game.
This is basically intended to automate the process laid out in 
[this forum post](http://forums.nexusmods.com/index.php?/topic/1918524-long-war-for-mac-osx-pointers-advice/?p=17340474).

This script is still in active development, so while I welcome pull requests, please check with me first.

Note that Long War ships as a Windows installer. I'm writing this for OS/X, though I'm trying to 
keep it platform independent so that it could run on Linux too in theory. It depends on Python 2.7
(and no other python stuff, currently).

Note: for detailed information about XCom modding, please see 
[the excellent Modding Tools page](http://wiki.tesnexus.com/index.php/Modding_Tools_-_XCOM:EU_2012) 
on the Nexus wiki.

See also [this Linux installer by wghost](https://github.com/wghost/LongWar-Linux).

# Installation for the impatient

**Note!** This is currently alpha-quality software. You may want to back up your installation directory 
before you try it. If something goes wrong, enable phoning home, pull up the game's properties in Steam, 
and choose "Verify Integrity of Game Cache." (This will probably re-download the entire game.)

* Launch the game once and quit
* Download the installer script
* Apply the mod:

```
./LongWarInstaller.py --apply "$HOME/Downloads/Long War 3 EW Beta 12-88-3-0b12.exe" -d
```

* Disable phoning home:

```
sudo ./LongWarInstaller.py --phone-home-disable
```

* Launch the game and enjoy Long War

## Dependencies

I have only tested this script with the Steam version of *XCom: Enemy Within*. To my knowledge, it will not work 
with the Mac App Store version. It will not currently work with *XCom: Enemy Unknown*, only with the expansion.

I have also only ever tested this on OS/X 10.9.4 (Maverick). The actual code is straightforward, portable 
Python and I've been running it with OS/X's built-in python interpreter, which is 2.7.5.

This project depends on the user having [innoextract](http://constexpr.org/innoextract/) installed. 
OS/X [homebrew](http://brew.sh/) users can install it via:

    brew install innoextract

If you don't have homebrew, you'll want to download `innoextract` from the above site and install it
manually.

## Detailed Installation Steps

1. Get the relevant files

  * Download the LongWarInstaller.py script somewhere (or `git clone` this project)
  * Download the Windows *Long War* installer from the "Files" tab of [its homepage](http://www.nexusmods.com/xcom/mods/88/).
    You want the Enemy Within (EW) version. As I write this, the most recent version is "Long War 3 Beta 13-88-3-0b13".
  * Make sure you've got `innoextract` installed (see [Dependencies][#Dependencies]).

2. Install *XCom: Enemy Within* from Steam.

3. Launch the game at least once.
  * When you run the game for the first time, it will download some updates from a server at Firaxis. This is 
    known as "phoning home" and is completely unrelated to Steam's auto-update system.
  * If the game doesn't phone home at least once before you install the mod, it will crash when you launch it.
  * It is sufficient to launch the game, get to the main menu, and then quit to get *XCom* to phone home.

4. Block [phoning home](#Phoning-Home).
  * After the game has phoned home one time, you'll want to disable phoning home, otherwise various parts 
    of the mod will be overwritten the next time you launch it and you'll probably crash to desktop.

5. Launch the game.

If Long War has been installed sucessfully, you'll notice some changes.
* The button on the bottom left from the main menu will say "Long War" instead of "Start Game".
* When you start a new game, your difficulty levels will not include "Beginner", but will range 
  from "Normal" to "Impossible".
* On your first mission, you'll have six operatives deployed, and they'll all be wearing 
  [red](http://en.wikipedia.org/wiki/Redshirt_(character)).

## Phoning Home

When you run *XCom* for the first time, it will download some updates from a server at Firaxis. This is 
known as "phoning home" and is completely unrelated to Steam's auto-update system.

If the game doesn't phone home at least once before you install the mod, it will crash when you launch it.

It is sufficient to launch the game, get to the main menu, and then quit to get *XCom* to phone home.

Phoning home can be disabled by adding the following two entries to the `/etc/hosts` file:

    127.0.0.1 prod.xcom-ew.firaxis.com
    127.0.0.1 prod.xcom.firaxis.com

The script is able to add and remove these entries itself, though it needs to be run as root in order to 
do so. You can block and enable phoning home passing flags to the script.

To disable phoning home by adding the above entries to `/etc/hosts`:

    sudo ./LongWarInstaller.py --phone-home-disable 

To re-enable it by removing those entries:

    sudo ./LongWarInstaller.py --phone-home-enable 

## Usage

Docs are forthcoming. Meanwhile, `./install.py --help` works. Basically once you've downloaded the mod
somewhere, do this:

    ./LongWarInstaller.py --apply "$HOME/Downloads/Long War 3 EW Beta 12-88-3-0b12.exe" -d

### Backups

The script will back up the files it's about to modify before it copies anything from the mod to your 
installed game directory. Currently the backups are stored under `Long-War-Backups` under the game 
installation directory (typically `~/Library/Application Support/Steam/SteamApps/common/XCom-Enemy-Unknown`).

You can see a list of mods that have been backed up using the `--list` option:

  	% ./LongWarInstaller.py --list
	  Long_War_3_Beta_13-88-3-0b13: applied at 2014-08-04 20:19:00

...and should be able to roll back an installation by using the `--uninstall` option to the script. 

	  % ./LongWarInstaller.py --uninstall Long_War_3_Beta_13-88-3-0b13
	  Reverted to backup "Long_War_3_Beta_13-88-3-0b13"

**However, note that rollback is not completely tested!** I try to be careful, but I make 
no guarantees. If nothing else, you should be able to revert to your vanilla install by using the 
"Verify Integrity of Game Cache" option from Steam.

## TODO

* Backup renamed files from feral directory, and restore on mod uninstallation
* Docs / man page
* Add `--backup` flag to back up a directory without overwriting files
* Interactive mode for script (y/n for overwriting files, etc)
* Validate that game is EW, not EU, or better yet handle EU-only installs
  * We should at least make sure `XCOMData/XEW` exists, else exit with an error message
* Verify mod uninstallation with git
  * Uninstall should remove `MacInit/*.ini`
* Add docs on verifying successful installation: correct second wave options, 6 operatives in 
  red during first mission, proper weapon names, etc.
* Version installer, git-flow if need be, etc
* Post-installation, verify that phone home is disabled and warn if not

### Blue Sky TODO
* fork / exec as `sudo $@` to gain root privs for enable / disable hosts
* Checksums of backed up files, probably [following this algorithm](http://stackoverflow.com/a/3431835/87990)?
  * Checksum entire insalled game tree, and verify it after backups
* wxPython (etc) GUI 
  * Install as an app via pyfreeze
  * But I'd like the script to be functional as well
* Linux support
  * Some refactoring into platform-specific subclasses or whatnot
* Handle Mac App Store installs
* Catch exceptions at root level and have option to paste logs into pastebin or whatever

## Bugs

* Multiple applications grow the new files list in backups each time
* Root level files are installed in `XCOMData/XEW` instead of at the root
* Running without -d logs at INFO to file log (should be DEBUG)

## Etc

As I write this in early August 2014, users have reported several bugs after applying Long War to
their XCom: EW installations on OS/X. I don't know much about modding and probably can't help with 
these issues; I'm just focused on getting the installer script to work. Please see 
[the official Long War mod forum](http://forums.nexusmods.com/index.php?/forum/665-xcom-file-discussions/)
for help with the mod itself.

Big ups to nexusmod user Anderkent, who first figured out how to install Long War on OS/X, 
and of course to the authors of Long War.
