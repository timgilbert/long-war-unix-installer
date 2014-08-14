# TODO

These are mostly blue-sky type things, but I hope to at least get the GUI done.

## Short term features

* Store total files in metadata and validate on uninstall
* If backup version not found, list available ones
* Log innoextract output to installation log

## Distro

* Set up dist log
* Package up .exe output as .zip, get extractor to read from it
* Handle multiple files (for bugfixes)
* Package up the zip file, README.html, and the script into a .dmg file
  * Incorporate the Linux fixes for beta 13
  * Rudimentary substitution in README - add package version, source files
* Store original distro sources in backups, so user doesn't need .dmg to roll back 
  to a previous mod version (+12MB per backup)
* Brief docs

## Refactoring

* More functional and pythonic overall
* Factor out directory-remapping stuff
* More DRY atttention is needed
* Platform independence is not a crime
* hostscanner stuff is kind of goofy
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
  * Checksum entire insalled game tree, and verify it after backups?
* Linux support
  * Some refactoring into platform-specific subclasses or whatnot
* Install for Enemy Unknown
  * Handle Mac App Store installs (only Enemy Unknown, I think?)
* Add `--backup` flag to back up a directory without overwriting files
* Back up saved games /settings / etc?
* Zip backups? Seems to only go from 27MB to 15MB
