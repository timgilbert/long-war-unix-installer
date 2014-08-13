# TODO

These are mostly blue-sky type things, but I hope to at least get the GUI done.

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
* Mod patches / bugfixes?
* Code could use a good refactor to a more functional style
* Add `--backup` flag to back up a directory without overwriting files

