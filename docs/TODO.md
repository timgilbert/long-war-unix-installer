# TODO

These are mostly blue-sky type things, but I hope to at least get the GUI done.

## Short term features

* Store total files in metadata and validate on uninstall
* If backup version not found, list available ones

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
* Mod patches / bugfixes?
* Code could use a good refactor to a more functional style
  * And to facilitate platform independence
  * hostscanner stuff is clumsy
  * Tests (once the script is broken out into independent class files)
* Add `--backup` flag to back up a directory without overwriting files
* Install script in Long-War-Backups?
* Back up saved games /settings / etc?
* Zip backups? Seems to only go from 27MB to 15MB
