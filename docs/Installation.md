# Long War installation instructions (OS/X)

1. Install *XCom: Enemy Within* from Steam.

2. Launch the game at least once.
  * When you run the game for the first time, it will download some updates from a server at Firaxis. This is 
    known as "[phoning home](#phoning-home)" and is completely unrelated to Steam's auto-update system.
  * If the game doesn't phone home at least once before you install the mod, it will crash when you launch it.
  * It is sufficient to launch the game, get to the main menu, and then quit to get *XCom* to phone home.

3. Get the Long War files installer and mount it.
  * Download the OS/X version of the installer (a `.dmg` file) from the 
    [Long War home page]((http://www.nexusmods.com/xcom/mods/88/).
  * Double-click the `.dmg` file to mount it. A disk image will pop up with three files on it.

4. Open a terminal and cd into the disk image, you'll need to run commands from here.
```sh
% cd /Volumes/Long-War-Mac-Installer/
```

5. Install the mod
  * Run `LongWarInstaller.py` with the `--install` option.
```sh
% ./LongWarInstaller.py --install 
Extracting mod "Long_War_3_Beta_13-88-3-0b13-OSX" to temp directory...
Applied mod version "Long_War_3_Beta_13-88-3-0b13-OSX" to game directory.
Install log available in "/Users/whatever/Library/Application Support/Steam/SteamApps/common/XCom-Enemy-Unknown/Long-War-Backups/Long_War_3_Beta_13-88-3-0b13-OSX/install.log"
```

6. Block [phoning home](#phoning-home).
  * After the game has phoned home one time, you'll want to disable phoning home, otherwise various parts 
    of the mod will be overwritten the next time you launch it and you'll probably crash to desktop.
  * You should also turn off automatic updates and cloud sync from Steam.
```sh
% sudo ./LongWarInstaller.py --phone-home-disable
Added 3 lines to /etc/hosts to disable phone home
```

7. Launch the game.

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

## Dependencies and Requirements

I have only tested this script with the Steam version of *XCom: Enemy Within*. To my knowledge, it will not work 
with the Mac App Store version. It will not currently work with *XCom: Enemy Unknown*, only with the expansion.

I have also only ever tested this on OS/X 10.9.4 (Mavericks). The actual code is straightforward, portable 
Python and I've been running it with OS/X's built-in python interpreter, which is 2.7.5. It should work with 
homebrew python just as easily. It does need at least Python 2.7.

This project depends on the user having  installed. 
OS/X [homebrew](http://brew.sh/) users can install it via:

    brew install innoextract

If you don't have homebrew, you'll want to download `innoextract` from the above site and install it
manually.

## Backups

The script will back up the files it's about to modify before it copies anything from the mod to your 
installed game directory. Currently the backups are stored under `Long-War-Backups` under the game 
installation directory (typically `~/Library/Application Support/Steam/SteamApps/common/XCom-Enemy-Unknown`).

You can see a list of mods that have been backed up using the `--list` option:

    % ./LongWarInstaller.py --list
    Phoning home is currently enabled.
    The game has phoned home at least once.
    Long_War_3_Beta_13-88-3-0b13: applied at 2014-08-04 20:19:00

The installer keeps track of what version of the mod is currently installed, and will refuse to install 
a new version until you've rolled back to the vanilla installation. You can do so with the 
`--uninstall` option to the script. 

    % ./LongWarInstaller.py --uninstall 
    Reverted to backups for Long War "Long_War_3_Beta_13-88-3-0b13"
    Uninstall log available in "/Users/whatever/Library/Application Support/Steam/SteamApps/common/XCom-Enemy-Unknown/Long-War-Backups/Long_War_3_Beta_13-88-3-0b13/uninstall.log"

Each backup is roughly 27MB. You can delete one with the --delete flag, but be warned that this is 
*permanent*.

    % ./LongWarInstaller.py --delete Long_War_3_Beta_13-88-3-0b13
    Deleted backup "Long_War_3_Beta_13-88-3-0b13"

# Verification

If Long War has been installed sucessfully, you'll notice some changes:

The button on the bottom left from the main menu will say "Long War" instead of "Start Game".
![Main Menu](https://github.com/timgilbert/long-war-unix-installer/blob/master/docs/images/Long-War-Main-Menu.jpg)

When you start a new game, your difficulty levels will not include "Beginner", but will range 
from "Normal" to "Impossible".
![New Game Options](https://github.com/timgilbert/long-war-unix-installer/blob/master/docs/images/Long-War-New-Game-Options.jpg)

On your first mission, you'll have six operatives deployed, and they'll all be wearing 
[red](http://en.wikipedia.org/wiki/Redshirt_(character)).
![First Mission Dropship](https://github.com/timgilbert/long-war-unix-installer/blob/master/docs/images/Long-War-First-Mission-Dropship.jpg)

Here they are deployed:
![First Mission weapons](https://github.com/timgilbert/long-war-unix-installer/blob/master/docs/images/Long-War-First-Mission-Weapons.jpg)

Note that the character's weapon is called "Assault Rifle."

If you see four operatives in grey, or if their weapons say "EXALT assault rifle", something went 
wrong with the installation.

# Something went wrong!

If you get an error in the installer (like a traceback or other unexpected result), please 
[open an issue on github](https://github.com/timgilbert/long-war-unix-installer/issues).

If there is a problem with the mod itself, your best bet is to ask for help on the 
[official Long War forums](http://forums.nexusmods.com/index.php?/forum/665-xcom-file-discussions/).
The people there are super helpful and many of the mod authors keep track of it. Make sure to 
note that you are running on the Mac version, as it's comparatively new.
