#! /usr/bin/python2.7

'''Long War installer for OS/X.'''

import os, sys, argparse, subprocess, logging, tempfile, shutil, textwrap, re, json, datetime
import distutils.spawn

def main():
    parser = argparse.ArgumentParser(description='Install Long War on OS/X or Linux.')
    parser.add_argument('-d', '--debug', action='store_true', help='Show debugging output')
    parser.add_argument('--game-directory', help='Directory to use for game installation')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--delete', help='Mod ID to delete backup for', metavar='MOD_VERSION')
    group.add_argument('--apply', help='Filename for the Long War executable file', metavar='MOD_FILENAME')
    group.add_argument('--list', action='store_true', help='List mod backups and exit')
    group.add_argument('--patch-executable', nargs=2, metavar=('INPUT', 'OUTPUT'),
                        help='Patch the given executable and exit')
    group.add_argument('--uninstall', help='Uninstall given mod and exit', metavar='MOD_VERSION')

    args = parser.parse_args()

    loglevel = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(message)s', level=loglevel)

    try:
        if args.patch_executable:
            infile, outfile = args.patch_executable
            execPatcher = ExecutablePatcher(infile, outfile)
            execPatcher.patch()
            return

        game = GameDirectory(args.game_directory)

        if args.delete:
            game.deleteBackupTree(args.delete) ; return

        if args.list:
            game.list() ; return

        if args.uninstall:
            game.uninstall(args.uninstall) ; return

        game.apply(args.apply)

    except InnoExtractorNotFound:
        abort('''\
            In order to run this program, you must first install innoextract.
            If you've got homebrew installed, you can run this command:
            
                brew install innoextract
            
            If you aren't using homebrew, install innoextract from its homepage here: 

                http://constexpr.org/innoextract/
            ''')
    except LongWarFileNotFound, e:
        abort("Can't open file '" + str(e) + "'!")
    except NoGameDirectoryFound, e:
        abort('''\
            I couldn't figure out where your XCom install directory is. Please use the --game option
            to specify where to find it.''')
    except SteamDirectoryNotFound, e:
        abort('''\
            I couldn't figure out where your steam installation is. Please use the --game option
            to specify where to find it your game installation directory.''')
    except BackupVersionNotFound, e:
        abort('''\
            Sorry, version {version} not found. Use --list to list the available versions.'''.format(version=e))
    except InnoExtractionFailed, e:
        abort(str(e))
    except IOError, e:
        # This is mildly hacky
        abort("Can't access {}: {}".format(e.filename, e.strerror))

def abort(errmsg):
    print textwrap.dedent(errmsg)
    sys,exit(1)

def isDebug():
    '''Return true if logging is at debug or lower'''
    return logging.getLogger().level > logging.DEBUG

def getRelativePath(pathname, root):
    '''Given the full path to a file and a directory bove it, return the path from the root to the file.'''
    # Weirdly, os.path.commonprefix returns a string match instead of a directory match
    # cf http://stackoverflow.com/questions/21498939/how-to-circumvent-the-fallacy-of-pythons-os-path-commonprefix
    return os.path.relpath(pathname, os.path.commonprefix([root + os.sep, pathname]))

class GameDirectory(object):
    '''Class representing an installed game directory.'''
    # Location relative the the game install directory of the application bundle directory
    APP_BUNDLE = 'XCOM Enemy Unknown.app'
    # Relative location of the actual chmod +x executable
    # I guess I could use os.path.join here, but it's os/x specific
    EXECUTABLE = 'Contents/MacOS/XCOM Enemy Unknown'
    MOD_FILE_ROOT = os.path.join('XCOMData', 'XEW')
    COOKED_PC = 'CookedPCConsole'
    LOCALIZATION = 'Localization'
    UNCOMPRESSED_SIZE = '.uncompressed_size'

    def __init__(self, root=None):
        self.backups = {}
        if root is None:
            finder = GameDirectoryFinder()
            root = finder.find()
        if not os.path.isdir(root):
            logging.info("Can't open directory %s!", root)
            raise NoGameDirectoryFound()

        self.root = root
        self.backupRoot = os.path.join(self.root, Backup.BACKUP_DIRECTORY)
        self.appBundleRoot = os.path.join(self.root, GameDirectory.APP_BUNDLE)

        logging.debug('Game root directory located at %s', self.root)
        self._scanForBackups()

    def _scanForBackups(self):
        logging.debug('Scanning for available backups...')
        if not os.path.isdir(self.backupRoot):
            logging.debug("Can't find backup root %s...", self.backupRoot)
            return
        for dirname in os.listdir(self.backupRoot):
            if dirname == 'dist':
                continue # May use this location to store mod distrbution files later
            metadata = os.path.join(self.backupRoot, dirname, Backup.METADATA_FILE)
            if os.path.isfile(metadata):
                self.backups[dirname] = Backup(dirname, self.backupRoot, self)

    def list(self):
        logging.debug('Listing backups...')
        if not self.backups:
            logging.info('No backups found in %s.', self.root)
            return
        for key in sorted(self.backups.keys()):
            logging.info('%s', self.backups[key])

    def apply(self, filename):
        extractor = Extractor(filename)
        version = extractor.modname

        if version in self.backups:
            logging.debug('Overwriting old backup for mod %s', version)
            backup = self.backups[version]
        else:
            self.backups[version] = Backup(version, self.backupRoot, self)

        patcher = Patcher(version, self.backups[version])
        patcher.patch(extractor)

    def deleteBackupTree(self, version):
        if version not in self.backups:
            raise BackupVersionNotFound(version)
        self.backups[version].deleteBackupTree()
        logging.info('Deleted backup "%s"', version)

    def uninstall(self, version):
        if version not in self.backups:
            raise BackupVersionNotFound(version)
        self.backups[version].uninstall()
        logging.info('Reverted to backup "%s"', version)

    def undo(self, patchname):
        logging.debug('Undoing...')

    def getAppBundlePath(self, relativePath):
        '''Given a relative file from a patch, return its location in the installed game tree'''
        # logging.debug('# %s %s', self.root, GameDirectory.APP_BUNDLE)
        # logging.debug('# %s %s', os.path.join(self.root, GameDirectory.APP_BUNDLE), os.path.join(self.root, GameDirectory.APP_BUNDLE, relativePath))
        # logging.debug('# %s -> %s', relativePath, os.path.join(self.root, GameDirectory.APP_BUNDLE, relativePath))
        return os.path.join(self.root, GameDirectory.APP_BUNDLE, relativePath)

    def getModFilePath(self, relativePath):
        '''Given a relative file from a patch in the top-level "app" directory, return its location 
        in the installed game tree.'''
        return os.path.join(self.root, GameDirectory.MOD_FILE_ROOT, relativePath)


class Extractor(object):
    '''Extracts files from the InnoInstall packages.'''
    # Root directory of mod files in the exploded archive
    MOD_FILE_ROOT = 'app'
    SKIP_DIRECTORY = 'Long War Files'
    PATCH_DIRECTORY = r'XComGame'

    def __init__(self, filename):
        self.filename = filename
        # modname is just the file's basename with underscores instead of spaces
        self.modname = os.path.splitext(os.path.basename(filename))[0].replace(' ', '_')
        self.innoextract = distutils.spawn.find_executable('innoextract')
        self.tmp = None

    def extract(self):
        '''Extract the mod files to a temp directory, then scan them'''
        self.validate()
        logging.info('Extracting mod "{}"...'.format(self.modname))

        self.tmp = tempfile.mkdtemp(prefix='LongWarInstaller_')
        logging.debug('Created temp directory %s', self.tmp)
        os.chdir(self.tmp)
        command = [self.innoextract, '-e', '--progress=0', '--color=0', '-s', self.filename]

        if isDebug():
            DEVNULL = open(os.devnull, 'w') # squash output
            stdout, stderr = DEVNULL, DEVNULL
        else:
            stdout, stderr = None, None

        logging.debug('Running command: %s', ' '.join(command))
        result = subprocess.call(command, stdout=stdout, stderr=stderr)
        if result != 0:
            raise InnoExtractionFailed('Running "{}" returned {}!'.format(' '.join(command), result))

        self._scan()

    def cleanup(self):
        '''Remove the temp directory this was extracted into.'''
        if self.tmp is not None:
            logging.debug('Removing %s', self.tmp)
            shutil.rmtree(self.tmp)

    def validate(self):
        '''Make sure the relevant stuff is present, else throw an error'''
        if self.innoextract is None:
            raise InnoExtractorNotFound()
        if not os.path.isfile(self.filename):
            raise LongWarFileNotFound(self.filename)

    def _scan(self):
        '''After extraction, look in extracted directory to find applicable files.'''
        logging.debug('Scanning extracted mod...')
        
        self.auxilliaryFiles = []
        self.patchFiles = []

        for root, dirs, files in os.walk(self.tmp):
            if self.SKIP_DIRECTORY in dirs:
                dirs.remove(self.SKIP_DIRECTORY)
            if re.search(self.PATCH_DIRECTORY, root):
                for filename in files:
                    patchfile = PatchFile(filename, root, self.tmp)
                    self.patchFiles.append(patchfile)
            else:
                for filename in files:
                    if re.search(r'txt|jpg$', filename):
                        patchfile = PatchFile(filename, root, self.tmp)
                        self.patchFiles.append(patchfile)

class PatchFile(object):
    '''Represents a single file to be patched from the mod'''
    def __init__(self, filename, extractDir, extractRoot):
        self.filename = filename
        self.extractRoot = extractRoot
        self.extractedPath = os.path.join(extractDir, filename)
        # Path relative to the 'app' directory
        self.relativePath = getRelativePath(self.extractedPath, os.path.join(self.extractRoot, Extractor.MOD_FILE_ROOT))
        _, extension = os.path.splitext(self.extractedPath)
        self.isUpk = GameDirectory.COOKED_PC in self.extractedPath and extension in ['.upk']
        self.isOverride = GameDirectory.LOCALIZATION in self.extractedPath and extension in ['.int', '.esn']

    def __repr__(self):
        return '<path:{}{}{}>'.format(self.relativePath, ' (upk)' if self.isUpk else '', 
                                      ' (override)' if self.isOverride else '')
        
    def getExtractedPath(self):
        '''Full path to the extracted location in the temp directory'''
        return self.extractedPath

    def getBackupPath(self, backupRoot):
        '''Full path to where this file would belong relative to the given backup folder'''
        return os.path.join(backupRoot, 'app', self.relativePath)

    def getGamePath(self, gameRoot):
        '''Full path to where this file would belong in the game folder'''
        if self.relativePath.startswith('XComGame'):
            return os.path.join(gameRoot, 'XCOMData', 'XEW', self.relativePath)
        else:
            return os.path.join(gameRoot, self.relativePath)

class Backup(object):
    '''Represents a single backup directory'''

    # Directory to keep all the backups in, relative to game root
    BACKUP_DIRECTORY = 'Long-War-Backups'
    # Directory in the backup tree representing files backed up from the "xcomm.app" directory
    # in the installed game directory (OS/X)
    APP_BUNDLE_DIRECTORY = 'app-bundle'
    MOD_FILE_DIRECTORY = 'mod-files'
    METADATA_FILE = 'metadata.json'
    IGNORE_FILES_IN_BACKUP = ['.DS_Store']

    def __init__(self, version, allBackupsRoot, gameDirectory):
        self.version = version
        self.allBackupsRoot = allBackupsRoot
        self.root = os.path.join(allBackupsRoot, version)
        self.appBundle = os.path.join(self.root, Backup.APP_BUNDLE_DIRECTORY)
        self.modFileRoot = os.path.join(self.root, Backup.MOD_FILE_DIRECTORY)
        self.gameDirectory = gameDirectory
        self.newFiles = []
        self.metadataFile = os.path.join(self.root, Backup.METADATA_FILE)
        self.applied = False
        self.totalModFiles = 0
        self.totalAppBundleFiles = 0
        self._loadMetadata()

    def __str__(self):
        return '{self.version}: applied at {self.applied}'.format(self=self)

    def _loadMetadata(self):
        if not os.path.isfile(self.metadataFile):
            logging.debug("Can't find metadata file at %s", self.metadataFile)
            return
        with open(self.metadataFile) as input:
            try:
                self._deserialize(json.load(input, encoding='utf-8'))
            except (ValueError, KeyError), e:
                logging.error('Error loading json from %s: %s, %s', self.metadataFile, e.__class__, e)
                sys.exit(1)

    def backupModFile(self, patchfile):
        self._touch()
        backupLocation = self._getBackupModPath(patchfile.relativePath)
        gameLocation = self.gameDirectory.getModFilePath(patchfile.relativePath)

        # Check to see whether the file already exists in the game directory; if it doesn't we 
        # will remove it when the user backs out this backup
        if not os.path.exists(gameLocation):
            logging.debug("File %s doesn't exist in game directory, marking as new", gameLocation)
            self.newFiles.append(patchfile.relativePath)
            return

        self._copyFile(gameLocation, backupLocation)
        self.totalModFiles += 1

        # Check for .uncompressed_size files
        if patchfile.isUpk:
            uncompressed = gameLocation + GameDirectory.UNCOMPRESSED_SIZE
            if os.path.isfile(uncompressed):
                logging.debug('Found uncompressed_size file %s, backing it up...', uncompressed)
                # This is slightly dirty
                self._copyFile(uncompressed, backupLocation + GameDirectory.UNCOMPRESSED_SIZE)

    
    def _copyFile(self, original, destination):
        '''Copy original to destination, creating directories if need be'''
        logging.debug('Backing up %s to %s...', original, destination)
        parent = os.path.dirname(destination)
        if not os.path.isdir(parent):
            os.makedirs(parent)
        shutil.copy(original, destination)
    
    def backupAppBundleFile(self, patchfile):
        '''Given a file relative to the app bundle root, back it up in the backup tree'''
        original = self.gameDirectory.getAppBundlePath(patchfile)
        backup = self.getAppBundleBackupLocation(GameDirectory.EXECUTABLE)
        self.totalAppBundleFiles += 1
        self._copyFile(original, backup)

    def getAppBundleBackupLocation(self, relativePath):
        return os.path.join(self.root, Backup.APP_BUNDLE_DIRECTORY, relativePath)

    def backupExecutable(self):
        logging.debug('Backing up executable')
        self.backupAppBundleFile(GameDirectory.EXECUTABLE)

    def deleteBackupTree(self):
        '''Remove entire backup tree'''
        shutil.rmtree(self.root)

    def writeBackupMetadata(self):
        logging.debug('Writing backup metadata...')
        with open(os.path.join(self.root, self.METADATA_FILE), 'w') as output:
            json.dump(self._serialize(), output, encoding='utf-8', 
                      indent=4, sort_keys=True, separators=(',', ': '))
        #logging.debug('New files: %s', self.brandNewFiles)

    def uninstall(self):
        # XXX Clean up nomenclature and refactor for clarity
        logging.debug('Reverting app bundle files from %s to %s', self.version, self.gameDirectory.root)
        for root, dirs, files in os.walk(self.appBundle):
            for filename in files:
                if filename in Backup.IGNORE_FILES_IN_BACKUP:
                    continue
                backupPath = self.getAppBundleBackupLocation(filename)
                relativePath = self._getRelativeAppBundlePath(backupPath)
                gamePath = self.gameDirectory.getAppBundlePath(relativePath)
                # logging.debug('abs  %s', absolutePath)
                # logging.debug('rel  %s', relativePath)
                # logging.debug('game %s', gamePath)
                logging.debug('Restoring app bundle path %s to %s', backupPath, gamePath)
        logging.debug('Reverting mod files from %s to %s', self.version, self.gameDirectory.root)
        for root, dirs, files in os.walk(self.modFileRoot):
            for filename in files:
                if filename in Backup.IGNORE_FILES_IN_BACKUP:
                    continue
                backupPath = self._getBackupModPath(filename)
                relativePath = self._getRelativeModFilePath(backupPath)
                gamePath = self.gameDirectory.getGameFilePath(relativePath) # XXX Broken
                logging.debug('Restoring mod file path %s to %s', backupPath, gamePath)


    def _getRelativeAppBundlePath(self, absolutePath):
        return self._getRelativePath(Backup.APP_BUNDLE_DIRECTORY, absolutePath)

    def _getRelativeModFilePath(self, absolutePath):
        return self._getRelativePath(Backup.MOD_FILE_DIRECTORY, absolutePath)

    def _getRelativePath(self, relativeRoot, absolutePath):
        # This is slightly dirty
        absolutePath = absolutePath.replace(os.path.join(self.root, Backup.APP_BUNDLE_DIRECTORY) + os.sep, '')
        return os.path.join(GameDirectory.APP_BUNDLE, absolutePath)

    def _getBackupModPath(self, relativePath):
        '''Full path to where this file would belong relative to the given backup folder'''
        return os.path.join(self.root, Backup.MOD_FILE_DIRECTORY, relativePath)

    def _touch(self):
        '''Create the backup directory if it doesn't exist, and update the last-modified time of the backup'''
        if not os.path.isdir(self.root):
            logging.debug('Creating new backup directory at %s', self.root)
            os.makedirs(self.root)
        if not os.path.isdir(self.appBundle):
            logging.debug('Creating new app bundle backup directory at %s', self.appBundle)
            os.makedirs(self.appBundle)
        self.applied = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _serialize(self):
        '''Simple-minded serialization'''
        return {
            'applied': self.applied,
            'newFiles': self.newFiles
        }

    def _deserialize(self, decodedJson):
        '''Simple-minded serialization'''
        for att in ['applied', 'newFiles']:
            setattr(self, att, decodedJson[att])

class Patcher(object):
    '''Consolidates logic for applying a patch'''

    def __init__(self, version, backup):
        self.version = version
        self.backup = backup
        self.extractor = None
        self.brandNewFiles = []

    def patch(self, extractor):
        logging.debug('Applying patch %s...', self.version)

        self.extractor = extractor
        extractor.extract()

        for modFile in extractor.patchFiles:
            self.backup.backupModFile(modFile)
            self.copyFile(modFile)

        self.patchExecutable()

        self.backup.writeBackupMetadata()

        extractor.cleanup()
        logging.info('Applied mod "%s"', self.version)

    def patchExecutable(self): 
        logging.debug('Patching executable...')
        self.backup.backupExecutable()

    def copyFile(self, filename):
        logging.debug('Copying file %s...', filename)

# TODO: refactor into platform-specific subclasses
class GameDirectoryFinder(object):
    STEAM_LIBRARY_ROOT = '~/Library/Application Support/Steam' 
    STEAM_CONFIG_FILE = 'config/config.vdf'
    GAME_ROOT = 'SteamApps/common/XCom-Enemy-Unknown-TEST' # TODO change this for distribution

    def __init__(self):
        self.steamRoot = os.path.expanduser(GameDirectoryFinder.STEAM_LIBRARY_ROOT)
        if not os.path.isdir(self.steamRoot):
            logging.debug("Can't open steam root at %s", self.steamRoot)
            raise SteamDirectoryNotFound()

    def find(self):
        for root in self._findSteamInstallRoots():
            guess = os.path.join(root, GameDirectoryFinder.GAME_ROOT)
            if os.path.isdir(guess):
                return guess
            #logging.debug("No game directory found in %s", guess)
        raise NoGameDirectoryFound()

    def _findSteamInstallRoots(self):
        allRoots = [self.steamRoot] + self._readSteamConfig()

        return allRoots

    def _readSteamConfig(self):
        '''Grub through the steam config files to find alternate install directories. This is very 
        simple-minded regex parsing which could easily fail, but it's just a heuristic.'''
        result = []

        config = os.path.join(self.steamRoot, GameDirectoryFinder.STEAM_CONFIG_FILE)
        if not os.path.exists(config):
            logging.debug("Warning: can't open steam config file %s to find alternate install directories", config)
            return result

        with open(config) as f:
            for line in f:
                match = re.match(r'^\s*"BaseInstallFolder[^"]+"\s+"(.+)"\s*$', line)
                if match is not None:
                    result.append(match.group(1))
                    logging.debug('Found steam install directory %s', match.group(1))
        return result

class ExecutablePatcher(object):
    '''Code to patch an executable file. This code is pretty simple-minded and loads the whole file 
    into memory (roughly 40MB).'''

    PATCH_STRINGS = [
        (u'''XComGame\Config\DefaultGameCore.ini''', u'''--PATCH-\Config\DefaultGameCore.ini'''),
        (u'''XComGame\Config\DefaultLoadouts.ini''', u'''--PATCH-\Config\DefaultLoadouts.ini''')
    ]

    def __init__(self, infile, outfile):
        self.infile = infile
        self.outfile = outfile

    def patch(self):
        '''Read file from self.infile, make replacements, and write changes to self.outfile, 
        overwriting it if it exists. Note that infile and outfile can be the same filename.'''
        with open(self.infile, 'rb') as input:
            contents = input.read()

        # This is where the magic happens
        total = 0
        for target, replacement in ExecutablePatcher.PATCH_STRINGS:
            assert len(target) == len(replacement)
            target, replacement = target.encode('utf-32-be'), replacement.encode('utf-32-be')
            count = contents.count(target)
            if count <= 0:
                logging.warning('Could not find target string "%s" in input file %s', target, self.infile)
                continue
            total += count # Hopefully this is accurate
            contents = contents.replace(target, replacement)
            logging.debug('Replaced %d occurences of %s in %s', count, target, self.infile)

        with open(self.outfile, 'wb') as output:
            output.write(contents)
        logging.info('Patched %d strings in "%s" as "%s"', total, self.infile, self.outfile)

# Errors
class InstallError(Exception): pass
class InnoExtractorNotFound(InstallError): pass
class LongWarFileNotFound(InstallError): pass
class InnoExtractionFailed(InstallError): pass
class SteamDirectoryNotFound(InstallError): pass
class NoGameDirectoryFound(InstallError): pass
class BackupVersionNotFound(InstallError): pass

if __name__ == '__main__': main()
