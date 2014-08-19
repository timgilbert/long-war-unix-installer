These are various features I'd like to get done at some point.

## Short term features

* Store total files in backup metadata and validate on uninstall

## Distro (in `dist` branch)

* Store original distro sources in backups, so user doesn't need .dmg to roll back 
  to a previous mod version (+12MB per backup)
  * Might as well write the script in there too, it's only 52K
* Make the .dmg look nice, for instance via http://stackoverflow.com/a/1513578/87990

## Refactoring

* More functional and pythonic overall
* Factor out directory-remapping stuff
* More DRY atttention is needed
* Platform independence is not a crime
* Tests (once the script is broken out into independent class files)
  * Should be able to set up test distros, etc

## GUI

* write one with wxPython, PySide, kivy, etc
* Install as an app via py2app or pyinstaller
* But I'd like the script to be functional as well
* Catch exceptions at root level and have option to paste logs into pastebin or whatever?

## Etc

* fork / exec as `sudo $@` to gain root privs for enable / disable hosts
* Checksums of backed up files, probably [following this algorithm](http://stackoverflow.com/a/3431835/87990)?
  * Checksum entire installed game tree, and verify it after backups?
  * Not sure this is really worthwhile from a safety standpoint
* Linux support
  * Some refactoring into platform-specific subclasses or whatnot
* Install for Enemy Unknown
  * Handle Mac App Store installs (only Enemy Unknown, I think?)
* Add `--backup` flag to back up a directory without overwriting files
* Back up saved games /settings / etc?
* Zip backups? Seems to only go from 27MB to 15MB, maybe not worth the hassle
