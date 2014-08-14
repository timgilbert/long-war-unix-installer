# Long War installer for Mac

This script is intended to install the [Long War mod](http://ufopaedia.org/index.php?title=Long_War) for 
Firaxis' [XCom: Enemy Within](http://www.xcom.com/) game on OS/X. It basically automates the manual process 
laid out in 
[this forum post](http://forums.nexusmods.com/index.php?/topic/1918524-long-war-for-mac-osx-pointers-advice/?p=17340474).

This script is still in active development, so while I welcome pull requests, please check with me first.

Note that this only works with the Steam version of Enemy Unknown, and you must have the Enemy Within expansion.

## Installation for the impatient

**Note!** This is currently beta-quality software. You may want to back up your installation directory 
before you try it. If something goes wrong, enable phoning home, pull up the game's properties in Steam, 
and choose "Verify Integrity of Game Cache." (This will probably re-download the entire game.)

* Launch the game once and quit
* `brew install innoextract`
* Download the [OS/X Long War installer `.dmg` file](http://www.nexusmods.com/xcom/mods/88/) and double-click it
* Install the mod:

```
% cd /Volumes/Long-War-Mac-Installer
% ./LongWarInstaller.py --install
```

* Disable phoning home by modifying `/etc/hosts`:

```
sudo ./LongWarInstaller.py --phone-home-disable
```

* Disable Steam updates and cloud sync

* Launch the game and enjoy Long War

You can uninstall the mod via `./LongWarInstaller.py --uninstall`.

For more information, see 
[the detailed installation instructions](https://github.com/timgilbert/long-war-unix-installer/blob/master/docs/Installation.md).

## Usage

For usage information, run `LongWarInstaller.py --help`. See also the 
[installation instructions](https://github.com/timgilbert/long-war-unix-installer/blob/master/docs/Installation.md).


## Known Bugs (in the installer)

* Root level files are installed in `XCOMData/XEW` instead of at the root

# State of the Mod

As I write this in mid-August 2014, users have reported several bugs after applying Long War to
their XCom: EW installations on OS/X. I don't know much about modding and probably can't help with 
these issues; I'm just focused on getting the installer script to work. Please see 
[the official Long War mod forum](http://forums.nexusmods.com/index.php?/forum/665-xcom-file-discussions/)
for help with the mod itself.

Currently the mod crashes to desktop on launch quite often. There should be a fix for this in the works.
I've noticed that having lots of free RAM on launch helps a lot.

There is also a bug where buying weapons will result in a CTD. A fix has been implemented for the Linux
version of Long War, and it will eventually be released in beta 14.

If you have a problem running the script, please 
[file an issue here](https://github.com/timgilbert/long-war-unix-installer/issues).

## Etc

For detailed information about XCom modding, please see 
[the excellent Modding Tools page](http://wiki.tesnexus.com/index.php/Modding_Tools_-_XCOM:EU_2012) 
on the Nexus wiki.

See also [this Linux installer by wghost](https://github.com/wghost/LongWar-Linux).

Big ups to nexusmod user Anderkent, who first figured out how to install Long War on OS/X, and to 
wghost81 who has forged ahead with the Linux version, and of course to the authors of Long War
without whom none of this would be possible.

For future plans, see [TODO.md](https://github.com/timgilbert/long-war-unix-installer/blob/master/docs/TODO.md)
