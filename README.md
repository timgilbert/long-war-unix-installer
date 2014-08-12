# Long War installer for Mac

This script is intended to install the [Long War mod](http://ufopaedia.org/index.php?title=Long_War) for 
Firaxis' [XCom: Enemy Unknown](http://www.xcom.com/) game on OS/X. It basically automates the manual process 
laid out in 
[this forum post](http://forums.nexusmods.com/index.php?/topic/1918524-long-war-for-mac-osx-pointers-advice/?p=17340474).

This script is still in active development, so while I welcome pull requests, please check with me first.

## Installation for the impatient

**Note!** This is currently alpha-quality software. You may want to back up your installation directory 
before you try it. If something goes wrong, enable phoning home, pull up the game's properties in Steam, 
and choose "Verify Integrity of Game Cache." (This will probably re-download the entire game.)

* Launch the game once and quit
* `brew install innoextract`
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

For more information, see [the detailed installation instructions](https://github.com/timgilbert/long-war-unix-installer/blob/master/docs/Installation.md).

## Usage

`LongWarInstaller.py --help` works. Here are the main flags:

`LongWarInstaller.py --apply path-to-installer.exe`: install the given mod, making a backup.

`LongWarInstaller.py --list`: list the existing backups.

`LongWarInstaller.py --uninstall Long_War_3_Beta_13-88-3-0b13`: uninstall the given mod, and 
revert to the backup we made when we installed it.

`LongWarInstaller.py --phone-home-enable` and `LongWarInstaller.py --phone-home-disable`: 
enable or diable [phoning home](https://github.com/timgilbert/long-war-unix-installer/blob/master/docs/Installation.md#phoning-home).

The following options are mostly used for testing:

`LongWarInstaller.py --delete Long_War_3_Beta_13-88-3-0b13`: delete the given backup. This is
permanent, exercise caution.

`--debug`: log debug messages to the console.

`--dry-run`: if this is set during installation, do not alter anything in the installed game 
directory (but output what would be done).

## Backups

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

* Add `--backup` flag to back up a directory without overwriting files
* Interactive mode for script (y/n for overwriting files, etc)
* Validate that game is EW, not EU, or better yet handle EU-only installs
  * We should at least make sure `XCOMData/XEW` exists, else exit with an error message
* Verify mod uninstallation with git
  * Backup renamed files from feral directory, and restore on mod uninstallation
  * Uninstall should remove `MacInit/*.ini`

### Blue Sky TODO
* fork / exec as `sudo $@` to gain root privs for enable / disable hosts
* Checksums of backed up files, probably [following this algorithm](http://stackoverflow.com/a/3431835/87990)?
  * Checksum entire insalled game tree, and verify it after backups?
* wxPython (or PySide, kivy, etc) GUI 
  * Install as an app via py2app or pyinstaller
  * But I'd like the script to be functional as well
* Linux support
  * Some refactoring into platform-specific subclasses or whatnot
* Install for Enemy Unknown
  * Handle Mac App Store installs (only Enemy Unknown, I think?)
* Catch exceptions at root level and have option to paste logs into pastebin or whatever

## Bugs

* Multiple applications grow the new files list in backups each time
* Root level files are installed in `XCOMData/XEW` instead of at the root

# State of the Mod

As I write this in early August 2014, users have reported several bugs after applying Long War to
their XCom: EW installations on OS/X. I don't know much about modding and probably can't help with 
these issues; I'm just focused on getting the installer script to work. Please see 
[the official Long War mod forum](http://forums.nexusmods.com/index.php?/forum/665-xcom-file-discussions/)
for help with the mod itself.

Currently the mod crashes to desktop on launch quite often. There should be a fix for this in the works.

## Etc

For detailed information about XCom modding, please see 
[the excellent Modding Tools page](http://wiki.tesnexus.com/index.php/Modding_Tools_-_XCOM:EU_2012) 
on the Nexus wiki.

See also [this Linux installer by wghost](https://github.com/wghost/LongWar-Linux).

Big ups to nexusmod user Anderkent, who first figured out how to install Long War on OS/X, 
and of course to the authors of Long War.
