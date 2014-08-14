#! /usr/bin/python2.7

'''Long War installer for OS/X.'''

import os, sys, argparse, subprocess, logging, tempfile, shutil, textwrap, re, json, datetime
import fileinput, errno, zipfile
import logging.handlers, distutils.spawn

__version__ = '1.0.0'

def main():
    parser = argparse.ArgumentParser(description=textwrap.dedent('''\
        Long War Installer version {}. For instructions, see the installer's home page
        at https://github.com/timgilbert/long-war-unix-installer/''').format(__version__))
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--install', help='Filename for the Long War executable file', metavar='MOD_FILENAME')
    group.add_argument('--uninstall', nargs='?', const=True, metavar='MOD_VERSION',
                       help='Roll back to a backup and exit (defaults to currently active version)')
    group.add_argument('--list', action='store_true', help='List mod backups and exit')
    group.add_argument('--delete', help='Delete a backup and exit', metavar='MOD_VERSION')
    group.add_argument('--phone-home-enable', action='store_true', help='Enable phoning home by modifying /etc/hosts')
    group.add_argument('--phone-home-disable', action='store_true', help='Disable phoning home by modifying /etc/hosts')
    group.add_argument('--dist', nargs='+', help='Build distribution with files as input', metavar='file')
    group.add_argument('--hmm', action='store_true')

    parser.add_argument('-d', '--debug', action='store_true', help='Show debugging output on console')
    parser.add_argument('--game-directory', help='Directory to use for game installation')
    parser.add_argument('--dry-run', action='store_true', 
                        help="Log what would be done, but don't modify game directory")
    parser.add_argument('--version', action='version', version='%(prog)s version ' + __version__)

    args = parser.parse_args()

    setupConsoleLogging(args.debug)

    try:
        if args.dist is not None:
            make_distribution(args.dist)
            return

        game = GameDirectory(args.game_directory)

        if args.delete:
            game.deleteBackupTree(args.delete) ; return

        if args.list:
            game.list() ; return

        if args.uninstall is not None:
            game.uninstall(args.uninstall) ; return

        if args.phone_home_enable:
            game.phoneHomeEnable() ; return

        if args.phone_home_disable:
            game.phoneHomeDisable() ; return

        if args.install:
            game.install(args.install, args.dry_run) 

            if game.hostsScanner.isEnabled:
                logging.warn(textwrap.dedent('''
                    Warning! The mod has been installed, but phoning home is not yet disabled.
                    Before you run the game, block phoning home by running:

                        sudo ./LongWarInstaller.py --phone-home-disable'''))
            else:
                logging.info('\nPhone home is blocked. Enjoy the game!')
            return

        raise NotImplementedError('Whoops! Not sure what to do', args)

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
    except PhoneHomePermissionDenied, e:
        abort('''\
            Permission denied opening {}. You must run this program as root to enable or disable ''' +
            '''phoning home.'''.format(HostsFileScanner.HOSTS))
    except EnemyWithinNotFound, e:
        abort('''\
            I couldn't find an Enemy Within directory! This installer only works for the games with Enemy 
            Within instaled. Get in touch via github if you want this feature.''')
    except ActiveBackupFoundDuringInstall, e:
        abort('''\
            You're trying to install long war, but it has already been installed. Please uninstall 
            the previous installation by running this script again with the --uninstall option:

                ./LongWarInstaller.py --uninstall
            ''')
    except NoActiveBackupFoundDuringUninstall, e:
        abort('''\
            You're trying to uninstall long war, but I can't see a currently active version of it 
            installed already. To force uninstallation, use the --list option to see the backups,
            then use an argument to --uninstall to explicitly roll back to that version:

                ./LongWarInstaller.py --list
                Long_War_3_Beta_13-88-3-0b13: installer version 0.9.1, applied at 2014-08-12 23:07:19

                ./LongWarInstaller.py --uninstall Long_War_3_Beta_13-88-3-0b13
            ''')
    except GameHasNotPhonedHome, e:
        msg ='''\
            I couldn't find the Feral Interactive directory in App Support. Before you install Long War, 
            you need to make sure phoning home is not disabled, launch the game, and exit to the desktop 
            from the main menu.'''
        if not e.args[0]:           # If args[0] is true, phoning home is enabled
            msg += '\n\n' + '''
            Note that phoning home is currently *disabled*. Enable it by running as root with the 
            --phone-home-enable option, launch the game, exit, and then running the installer as root
            again with the --phone-home-disable option to turn it off. Once that is done you can install 
            Long War and run the game as usual.'''
        abort(msg)
    except (OSError, IOError), e:
        # This is mildly sloppy
        abort("Can't access {}: {}".format(e.filename, e.strerror))

def make_distribution(files):
    '''Given a list of filenames, extract each one in turn into a distribution directory. Then 
    copy the script and README.html to it and make a .dmg image based on the first filename.'''
    dist = Distribution(files)
    dmg = dist.create()
    logging.info('Created distribution %s as %s', dist, dmg)

def abort(errmsg):
    logging.error(textwrap.dedent(errmsg))
    sys.exit(1)

def isDebug():
    '''Return true if logging is at debug or lower'''
    return logging.getLogger().level > logging.DEBUG

def copyOrWarn(original, destination):
    '''Try to copy the original file to the destination. If it fails, emit a warning.'''
    try:
        shutil.copy(original, destination)
    except (OSError, IOError), e:
        logging.warning("Can't copy %s to %s: %s", original, destination, e.strerror)

def removeOrWarn(target):
    ''''Remove the given file, issuing a warning (but not exiting) if it doesn't work'''
    try:
        os.unlink(target)
    except (OSError, IOError), e:
        logging.warning("Can't remove %s: %s", target, e.strerror)

def getRelativePath(pathname, root):
    '''Given the full path to a file and a directory above it, return the path from the root to the file.'''
    # Weirdly, os.path.commonprefix returns a string match instead of a directory match
    # cf http://stackoverflow.com/questions/21498939/how-to-circumvent-the-fallacy-of-pythons-os-path-commonprefix
    return os.path.relpath(pathname, os.path.commonprefix([root + os.sep, pathname]))

def setupConsoleLogging(debug=False):
    '''Set up logging to the console. If debug is true, log to the console at DEBUG (else INFO).'''
    loglevel = logging.DEBUG if debug else logging.INFO
    rootlogger = logging.getLogger()
    console = logging.StreamHandler()
    console.setLevel(loglevel)
    console.setFormatter(logging.Formatter('%(message)s'))
    rootlogger.addHandler(console)
    rootlogger.setLevel(logging.DEBUG)

class GameDirectory(object):
    '''Class representing an installed game directory.'''
    # Location relative the the game install directory of the application bundle directory
    APP_BUNDLE = 'XCOM Enemy Unknown.app'
    # Relative location of the actual chmod +x executable
    # I guess I could use os.path.join here, but it's os/x specific
    EXECUTABLE = 'Contents/MacOS/XCOM Enemy Unknown'
    MOD_FILE_ROOT = 'XCOMData/XEW'
    COOKED_PC = 'CookedPCConsole'
    LOCALIZATION = 'Localization'
    UNCOMPRESSED_SIZE = '.uncompressed_size'
    OVERRIDE_DIRECTORY = 'Contents/Resources/MacOverrides/XEW'
    # If this is present, app has phoned home
    PHONE_HOME_INDICATOR = 'Contents/Frameworks/QuincyKit.framework'
    FERAL_MACINIT = '~/Library/Application Support/Feral Interactive/XCOM Enemy Unknown/XEW/MacInit'

    def __init__(self, root=None):
        self.backups = {}
        self.activeBackup = None
        if root is None:
            root = GameDirectoryFinder().find()
        if not os.path.isdir(root):
            logging.info("Can't open directory %s!", root)
            raise NoGameDirectoryFound()

        self.root = root
        self.backupRoot = os.path.join(self.root, Backup.BACKUP_DIRECTORY)
        self.appBundleRoot = os.path.join(self.root, GameDirectory.APP_BUNDLE)
        self.hasPhonedHome = os.path.exists(self.getAppBundlePath(GameDirectory.PHONE_HOME_INDICATOR))
        logging.debug('Game root directory located at %s', self.root)
        self._scanForBackups()

        self.hostsScanner = HostsFileScanner()
        logging.debug('Phone home: %s', 'enabled' if self.hostsScanner.isEnabled else 'disabled')

        self.feralRoot = os.path.expanduser(GameDirectory.FERAL_MACINIT)

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
                backup = Backup(dirname, self.backupRoot, self)
                if backup.active: 
                    self.activeBackup = backup
                self.backups[dirname] = backup

    def _validateHasPhonedHome(self):
        '''Make sure the user has run the game with phone home enabled at least once, else 
        throw an exception.'''
        if not self.hasPhonedHome:
            raise GameHasNotPhonedHome(self.hostsScanner.isEnabled)

    def _validateHasEnemyWith(self):
        '''Make sure the user has run the game with phone home enabled at least once, else 
        throw an exception.'''
        if not os.path.isdir(os.path.join(self.root, GameDirectory.MOD_FILE_ROOT)):
            raise EnemyWithinNotFound

    def list(self):
        logging.debug('Listing backups...')
        logging.info('Phoning home is currently %s.', 
                  'enabled' if self.hostsScanner.isEnabled else 'blocked')
        if self.hasPhonedHome:
            logging.info('The game has phoned home at least once.')
        else:
            logging.info('The game has NOT phoned home yet, so Long War will not work.')
        if not self.backups:
            logging.info('No backups found in %s.', self.root)
            return
        for key in sorted(self.backups.keys()):
            logging.info('%s', self.backups[key])

    def install(self, filename, dryRun=False):
        self._validateHasPhonedHome()
        self._validateHasEnemyWith()
        extractor = Extractor(filename)
        version = extractor.modname

        if self.activeBackup is not None:
            raise ActiveBackupFoundDuringInstall

        if version in self.backups:
            # Could quit with an error here
            logging.info('Overwriting old backup for mod %s', version)
            newBackup = self.backups[version]
        else:
            # Create new backup
            newBackup = Backup(version, self.backupRoot, self)
            self.activeBackup = newBackup

        newBackup.setupInstallLog()

        # Extract and patch
        patcher = Patcher(version, newBackup, self, dryRun)
        patcher.install(extractor)
        
        logging.info('Applied mod version "%s" to game directory.', version)
        logging.info('Install log available in "%s"', newBackup.installLog)

    def deleteBackupTree(self, version):
        if version not in self.backups:
            raise BackupVersionNotFound(version)
        self.backups[version].deleteBackupTree()
        logging.info('Deleted backup "%s"', version)

    def uninstall(self, version=True):
        '''Uninstall the given backup version. If version is True, uninstall the active version.'''
        if version == True:
            if self.activeBackup is None:
                raise NoActiveBackupFoundDuringUninstall
            doomedBackup = self.activeBackup
        elif version not in self.backups:
            raise BackupVersionNotFound(version)
        else:
            doomedBackup = self.backups[version]
        doomedBackup.uninstall()
        logging.info('Reverted to backups for Long War "%s"', doomedBackup.version)
        logging.info('Uninstall log available in "%s"', doomedBackup.uninstallLog)

    def undo(self, patchname):
        logging.debug('Undoing...')

    def getAppBundlePath(self, relativePath):
        '''Given a relative file from a patch, return its location in the installed game tree'''
        appBundleRelative = re.sub(r'^XComGame/Localization/[A-Za-z]{3}/([^\.]+\.[A-Za-z]{3})$', 
                                   r'Contents/Resources/MacOverrides/XEW/\1', 
                                   relativePath)
        return os.path.join(self.appBundleRoot, appBundleRelative)

    def getModFilePath(self, relativePath):
        '''Given a relative file from a patch in the top-level "app" directory, return its location 
        in the installed game tree.'''
        return os.path.join(self.root, GameDirectory.MOD_FILE_ROOT, relativePath)

    def phoneHomeDisable(self):
        if not self.hostsScanner.isEnabled:
            logging.warn('Phone home is already disabled.')
            return
        self.hostsScanner.disable()

    def phoneHomeEnable(self):
        if self.hostsScanner.isEnabled:
            logging.warn('Phone home is already enabled.')
            return
        self.hostsScanner.enable()

    def nukeFeralDirectory(self):
        '''Delete all files in the feral directory.'''
        logging.debug('Removing files from feral directory %s...', self.feralRoot)
        for fn in (os.path.join(self.feralRoot, f) for f in os.listdir(self.feralRoot)):
            if os.path.isdir(fn): continue # skip .git
            logging.debug('Removing feral file %s...', fn)
            removeOrWarn(fn)

class FeralDirectory(object):
    # Maps from paths relative to the extract directory to paths in the MacInit folder
    RENAME_PATHS = {'XComGame/Config/DefaultGameCore.ini': 'XComGameCore.ini',
                    'XComGame/Config/DefaultLoadouts.ini': 'XComLoadouts.ini'}
    @classmethod
    def feralMacinitCopy(cls, relativePath):
        '''Return the filename relative to the feral MacInit folder that this file should be 
        copied to, or None if it shouldn't be copied there.'''
        return cls.RENAME_PATHS.get(relativePath, None)

class TempDirectory(object):
    '''Mixin class for dealing with temp files'''
    TEMP_PREFIX = 'LongWar_Extract_'
    def __init__(self, prefix=None):
        self.tmp = None
        self.prefix = prefix or self.TEMP_PREFIX

    def __enter__(self):
        '''Create a temp directory, returning the directory path'''
        self.tmp = tempfile.mkdtemp(prefix=self.prefix)
        logging.debug('Created temp directory %s', self.tmp)
        return self.tmp

    def __exit__(self, type, value, traceback):
        '''Remove the temp directory, if it has been created.'''
        if self.tmp is not None:
            logging.debug('Removing %s', self.tmp)
            shutil.rmtree(self.tmp)

class AbstractExtractor(object):
    '''Base class for Inno and Zip extractors.'''
    # Root directory of mod files in the exploded archive
    MOD_FILE_ROOT = 'app'
    SKIP_DIRECTORY = 'Long War Files'
    PATCH_DIRECTORY = r'XComGame'
    TEMP_PREFIX = 'LongWar_Extract_'

    def __init__(self, filename, directory=None):
        '''Create a new instance. If directory is None, create a temp directory which will be 
        deleted on __exit__. Otherwise, extract into directory and do not clean it up afterwards.'''
        self.filename = filename
        # modname is just the file's basename with underscores instead of spaces
        # XXX FIXME - modname member, modName() method, yikes!
        self.modname = self.modName(filename)
        self.directory = directory
        self.tmp = None

    def __enter__(self):
        '''Extract the mod files to a temp directory, then scan them'''
        target = self.directory
        if target is None:
            target = tempfile.mkdtemp(prefix=self.TEMP_PREFIX)
            self.tmp = target
        logging.info('Extracting mod "%s" to %s...', self.modname, target)
        self.extract(target)
        self._scan(target)

    def __exit__(self, type, value, traceback):
        '''Remove the temp directory, if it has been created.'''
        if self.tmp is not None:
            logging.debug('Removing temp extraction directory %s', self.tmp)
            shutil.rmtree(self.tmp)

    # Could use @abstractmethod per http://stackoverflow.com/a/13646263/87990
    def extract(self, extractRoot):
        raise NotImplementedError('Subclasses should override extract()!')

    def validate(self):
        '''Make sure the relevant stuff is present, else throw an error'''
        if self.innoextract is None:
            raise InnoExtractorNotFound()
        if not os.path.isfile(self.filename):
            raise LongWarFileNotFound(self.filename)

    def _scan(self, extractRoot):
        '''After extraction, look in extracted directory to find applicable files.'''
        self.patchFiles = []

        for root, dirs, files in os.walk(extractRoot):
            if self.SKIP_DIRECTORY in dirs:
                dirs.remove(self.SKIP_DIRECTORY)
            if re.search(self.PATCH_DIRECTORY, root):
                for filename in files:
                    patchfile = PatchFile(filename, root, extractRoot)
                    self.patchFiles.append(patchfile)
            else:
                for filename in files:
                    if re.search(r'txt|jpg$', filename):
                        patchfile = PatchFile(filename, root, extractRoot)
                        self.patchFiles.append(patchfile)
        logging.debug('Extracted %d mod files from %s', len(self.patchFiles), self.modname)

    # TODO this should be a function
    @staticmethod
    def modName(path):
        return os.path.splitext(os.path.basename(path))[0].replace(' ', '_')

    @staticmethod
    def getExtractor(installationFilePath, targetDirectory=None):
        '''Factory method - return the correct instance based on the file's extension.'''
        classmap = {'.exe': InnoExtractor, '.zip': ZipExtractor}
        _, extension = os.path.splitext(installationFilePath)
        klass = classmap[extension]
        return klass(installationFilePath, targetDirectory)

# TODO move this somewhere logical
def runCommand(command):
    '''Run the given command list via subprocess.call() and return the exit value'''
    # A fancier script would log innoextract output to the log files if we're at debug
    if isDebug():
        stdout, stderr = None, None
    else:
        DEVNULL = open(os.devnull, 'w') # squash output
        stdout, stderr = DEVNULL, DEVNULL

    logging.debug('Running command: %s', ' '.join(command))
    result = subprocess.call(command, stdout=stdout, stderr=stderr)
    logging.debug('Return value: %s', result)
    return result

class InnoExtractor(AbstractExtractor):
    TEMP_PREFIX = 'LongWar_ExtInno_'
    def __init__(self, filename, directory=None):
        super(InnoExtractor, self).__init__(filename, directory)
        self.innoextract = distutils.spawn.find_executable('innoextract')

    def extract(self, extractRoot):
        '''Extract the mod files to a temp directory, then scan them'''
        self.validate()

        command = [self.innoextract, '--extract', '--progress=0', '--color=0', #'--silent', 
                   '--output-dir', extractRoot, self.filename]

        # # A fancier script would log innoextract output to the log files if we're at debug
        # if not isDebug():
        #     DEVNULL = open(os.devnull, 'w') # squash output
        #     stdout, stderr = DEVNULL, DEVNULL
        # else:
        #     stdout, stderr = None, None

        # logging.debug('Running command: %s', ' '.join(command))
        # result = subprocess.call(command, stdout=stdout, stderr=stderr)
        result = runCommand(command)
        if result != 0:
            raise InnoExtractionFailed('Running "{}" returned {}!'.format(' '.join(command), result))

    def validate(self):
        '''Make sure the relevant stuff is present, else throw an error'''
        if self.innoextract is None:
            raise InnoExtractorNotFound()
        # Probably should do this elsewhere
        if not os.path.isfile(self.filename):
            raise LongWarFileNotFound(self.filename)

class ZipExtractor(AbstractExtractor):
    TEMP_PREFIX = 'LongWar_ExtZip_'
    def __init__(self, filename, directory=None):
        super(ZipExtractor, self).__init__(filename)

    def extract(self):
        '''Extract the mod files to a temp directory, then scan them'''
        super(ZipExtractor, self).__enter__()
        logging.debug('Zip extractor ready to go!')

class PatchFile(object):
    '''Represents a single file to be patched from the mod'''
    def __init__(self, filename, extractDir, extractRoot):
        self.filename = filename
        self.extractRoot = extractRoot
        self.extractedPath = os.path.join(extractDir, filename)
        # Path relative to the 'app' directory
        self.relativePath = getRelativePath(self.extractedPath, os.path.join(self.extractRoot, AbstractExtractor.MOD_FILE_ROOT))
        _, extension = os.path.splitext(self.extractedPath)
        self.isUpk = GameDirectory.COOKED_PC in self.extractedPath and extension in ['.upk']
        self.isOverride = GameDirectory.LOCALIZATION in self.extractedPath and extension in ['.int', '.esn']
        self.feralPath = FeralDirectory.feralMacinitCopy(self.relativePath)

    def __repr__(self):
        spec = ''
        if self.isUpk: spec += ' (upk)'
        if self.isOverride: spec += ' (override)'
        if self.feralPath is not None: 
            spec += ' (feral: {})'.format(self.feralPath)
        return '<path:{}{}>'.format(self.relativePath, spec)
        
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
    FERAL_DIRECTORY = 'feral'
    METADATA_FILE = 'metadata.json'
    IGNORE_FILES_IN_BACKUP = ['.DS_Store']
    # These attributes will be persisted in metadata.json
    SERIALIZED_FIELDS = ['applied', 'newModFiles', 'newAppBundleFiles', 'installerVersion', 'active']

    def __init__(self, version, allBackupsRoot, gameDirectory):
        self.version = version
        self.allBackupsRoot = allBackupsRoot
        self.root = os.path.join(allBackupsRoot, version)
        self.appBundleRoot = os.path.join(self.root, Backup.APP_BUNDLE_DIRECTORY)
        self.modFileRoot = os.path.join(self.root, Backup.MOD_FILE_DIRECTORY)
        self.feralRoot = os.path.join(self.root, Backup.FERAL_DIRECTORY)
        self.gameDirectory = gameDirectory
        self.newModFiles = {}
        self.newAppBundleFiles = {}
        self.metadataFile = os.path.join(self.root, Backup.METADATA_FILE)
        self.applied = None
        self.active = False
        self.installerVersion = __version__
        self.totalModFiles = 0
        self.totalAppBundleFiles = 0
        self.installLog = os.path.join(self.root, 'install.log')
        self.uninstallLog = os.path.join(self.root, 'uninstall.log')
        self._loadMetadata()

    def __str__(self):
        return ('{self.version}: installer version {self.installerVersion}, applied at ' +
                '{self.applied}{active}').format(self=self, active=' (ACTIVE)' if self.active else '')

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

    def setupInstallLog(self):
        '''Begin logging messages to the install.log file for this backup'''
        self._setupFileLog(self.installLog)

    def setupUninstallLog(self):
        '''Begin logging messages to the install.log file for this backup'''
        self._setupFileLog(self.uninstallLog)

    def _setupFileLog(self, logPath):
        self._touch()
        oldLogExists = os.path.isfile(logPath)
        handler = logging.handlers.RotatingFileHandler(logPath, backupCount=9)
        if oldLogExists:
            handler.doRollover() # Hacky but seems to work, we get a new log file per execution
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-7s %(message)s'))
        rootLogger = logging.getLogger()
        rootLogger.addHandler(handler)
        logging.debug('Long War Installer, version {}'.format(__version__))

    def backupModFile(self, patchFile):
        self._touch()
        backupLocation = self._getBackupModPath(patchFile.relativePath)
        gameLocation = self.gameDirectory.getModFilePath(patchFile.relativePath)

        # Check to see whether the file already exists in the game directory; if it doesn't we 
        # will remove it when the user backs out this backup
        if not os.path.exists(gameLocation):
            logging.debug("File %s doesn't exist in game directory, marking as new", gameLocation)
            self.newModFiles[patchFile.relativePath] = True
            return

        self._copyFile(gameLocation, backupLocation)
        self.totalModFiles += 1

        # Check for .uncompressed_size files
        if patchFile.isUpk:
            # TODO Make this a gameDirectory method returning None or pathname
            uncompressed = gameLocation + GameDirectory.UNCOMPRESSED_SIZE
            if os.path.isfile(uncompressed):
                logging.debug('Found uncompressed_size file %s, backing it up...', uncompressed)
                # This is slightly dirty
                self._copyFile(uncompressed, backupLocation + GameDirectory.UNCOMPRESSED_SIZE)

    def backupOverrideFile(self, patchFile):
        '''Back up a localization file to the override directory inside the .app bundle'''
        filename = os.path.basename(patchFile.extractedPath)
        # TODO: this should be a gameDirectory method too
        relativePath = os.path.join(GameDirectory.OVERRIDE_DIRECTORY, filename)
        gameLocation = self.gameDirectory.getAppBundlePath(relativePath)
        if os.path.isfile(gameLocation):
            logging.debug('Backing up override file %s', gameLocation)
            self.backupAppBundleFile(relativePath)
        else:
            logging.debug('Marking override file %s as new...', relativePath)
            self.newAppBundleFiles[relativePath] = True
    
    def backupFeralDirectory(self):
        '''Copy all of the files in the feral MacInit directory to the backup'''
        for filename in os.listdir(self.gameDirectory.feralRoot):
            original = os.path.join(self.gameDirectory.feralRoot, filename)
            if not os.path.isfile(original): continue
            target = os.path.join(self.feralRoot, filename)
            logging.debug('Backing up feral file %s', target)
            self._copyFile(original, target)
    
    def _copyFile(self, original, destination):
        '''Copy original to destination, creating directories if need be'''
        logging.debug('Backing up %s to %s...', original, destination)
        parent = os.path.dirname(destination)
        if not os.path.isdir(parent):
            os.makedirs(parent)
        shutil.copy(original, destination)
    
    def backupAppBundleFile(self, relativePath):
        '''Given a file relative to the app bundle root, back it up in the backup tree'''
        original = self.gameDirectory.getAppBundlePath(relativePath)
        backup = self.getAppBundleBackupLocation(relativePath)
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

    def uninstall(self):
        '''Restore all files from this backup to the game directory.'''
        self.setupUninstallLog()

        # This could use some refactoring for DRY-related maladies
        logging.debug('Reverting app bundle files from %s to %s', self.version, self.gameDirectory.root)
        for root, dirs, files in os.walk(self.appBundleRoot):
            for backupPath in (os.path.join(root, f) for f in files if f not in Backup.IGNORE_FILES_IN_BACKUP):
                relativePath = self._getRelativeAppBundlePath(backupPath)
                gamePath = self.gameDirectory.getAppBundlePath(relativePath)
                logging.debug('Restoring app bundle path %s to %s', backupPath, gamePath)
                copyOrWarn(backupPath, gamePath)

        logging.debug('Reverting mod files from %s to %s', self.version, self.gameDirectory.root)
        for root, dirs, files in os.walk(self.modFileRoot):
            for backupPath in (os.path.join(root, f) for f in files if f not in Backup.IGNORE_FILES_IN_BACKUP):
                relativePath = self._getRelativeModFilePath(backupPath)
                gamePath = self.gameDirectory.getModFilePath(relativePath)
                logging.debug('Restoring mod file path %s to %s', backupPath, gamePath)
                copyOrWarn(backupPath, gamePath)

        logging.debug('Reverting feral files from %s to %s', self.version, self.feralRoot)
        self.gameDirectory.nukeFeralDirectory()
        # This should probably be a function
        for filename in os.listdir(self.feralRoot):
            original = os.path.join(self.feralRoot, filename)
            if not os.path.isfile(original): continue
            target = os.path.join(self.gameDirectory.feralRoot, filename)
            logging.debug('Restoring feral file %s', original)
            copyOrWarn(original, target)

        logging.debug('Removing new files added in patch')
        for addedPath in (self.gameDirectory.getModFilePath(f) for f in self.newModFiles.keys()):
            logging.debug('Removing mod file %s', addedPath)
            removeOrWarn(addedPath)
        for addedPath in (self.gameDirectory.getAppBundlePath(f) for f in self.newAppBundleFiles.keys()):
            logging.debug('Removing app bundle file %s', addedPath)
            removeOrWarn(addedPath)
        self.active = False
        self.writeBackupMetadata()

    def _getRelativeAppBundlePath(self, absolutePath):
        return getRelativePath(absolutePath, self.appBundleRoot)

    def _getRelativeModFilePath(self, absolutePath):
        return getRelativePath(absolutePath, self.modFileRoot)

    def _getBackupModPath(self, relativePath):
        '''Full path to where this file would belong relative to the given backup folder'''
        return os.path.join(self.root, Backup.MOD_FILE_DIRECTORY, relativePath)

    def _touch(self):
        '''Create the backup directory if it doesn't exist, and update the last-modified time of the backup'''
        if not os.path.isdir(self.root):
            logging.debug('Creating new backup directory at %s', self.root)
            os.makedirs(self.root)
        if not os.path.isdir(self.appBundleRoot):
            logging.debug('Creating new app bundle backup directory at %s', self.appBundleRoot)
            os.makedirs(self.appBundleRoot)
        if not os.path.isdir(self.feralRoot):
            logging.debug('Creating new feral backup directory at %s', self.feralRoot)
            os.makedirs(self.feralRoot)
        self.applied = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _serialize(self):
        '''Simple-minded serialization'''
        return { attr: getattr(self, attr) for attr in Backup.SERIALIZED_FIELDS }

    def _deserialize(self, decodedJson):
        '''Simple-minded deserialization'''
        for attr in Backup.SERIALIZED_FIELDS:
            if hasattr(self, attr) and attr in decodedJson:
                setattr(self, attr, decodedJson[attr])

class Patcher(object):
    '''Consolidates logic for installing a mod into a tree.'''

    def __init__(self, version, backup, gameDirectory, dryRun=False):
        self.version = version
        self.backup = backup
        self.gameDirectory = gameDirectory
        self.dryRun = dryRun

    def install(self, extractor):
        logging.debug('Installing mod %s...', self.version)

        # Back up feral files, then nuke feral directory, then copy and rename new feral files
        self.backup.backupFeralDirectory()
        self.gameDirectory.nukeFeralDirectory()

        with extractor as extracted:
            for modFile in extracted.patchFiles:
                self.backup.backupModFile(modFile)
                self.copyModFile(modFile)
                if modFile.isUpk:
                    self.removeUncompressedSize(modFile)
                if modFile.isOverride:
                    logging.debug('Copying override to override directory')
                    self.backup.backupOverrideFile(modFile)
                    self.copyOverrideFile(modFile)
                if modFile.feralPath is not None:
                    self.copyAndRenameFeralFile(modFile)

        self.backup.active = True
        self.backup.writeBackupMetadata()

    def copyModFile(self, patchfile):
        target = self.gameDirectory.getModFilePath(patchfile.relativePath)
        logging.debug('Copying mod file %s to %s...', patchfile, target)
        if not self.dryRun:
            copyOrWarn(patchfile.extractedPath, target)

    def removeUncompressedSize(self, modfile):
        filename = modfile.relativePath + GameDirectory.UNCOMPRESSED_SIZE
        uncompressed = self.gameDirectory.getModFilePath(filename)
        if os.path.exists(uncompressed):
            logging.debug('Removing uncompressed file %s', uncompressed)
            if not self.dryRun:
                removeOrWarn(uncompressed)

    def copyOverrideFile(self, patchfile):
        target = self.gameDirectory.getAppBundlePath(patchfile.relativePath)
        logging.debug('Copying override file %s to %s...', patchfile, target)
        if not self.dryRun:
            copyOrWarn(patchfile.extractedPath, target)
    
    def copyAndRenameFeralFile(self, patchfile):
        target = os.path.join(self.gameDirectory.feralRoot, patchfile.feralPath)
        logging.debug('Copying feral file %s to %s', patchfile, target)
        if not self.dryRun:
            copyOrWarn(patchfile.extractedPath, target)
        
# TODO: refactor into platform-specific subclasses
class GameDirectoryFinder(object):
    STEAM_LIBRARY_ROOT = '~/Library/Application Support/Steam' 
    STEAM_CONFIG_FILE = 'config/config.vdf'
    GAME_ROOT = 'SteamApps/common/XCom-Enemy-Unknown'

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
    into memory (roughly 40MB).

    NOTE: patching the executable does not currently seem to be necessary for with Mac or Linux.
    This code does seem to work, so it's here in case it will be useful in the future.'''

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

class HostsFileScanner(object):
    HOSTS = '/etc/hosts'
    PATTERNS = [re.compile(r'^[^#\s]*\S+\s+prod\.xcom\.firaxis\.com'),
                re.compile(r'^[^#\s]*\S+\s+prod\.xcom-ew\.firaxis\.com'),
                re.compile(r'^\s*#\s*Long-War-Installer:')]
    PHONE_HOME_DISABLE_TEXT = textwrap.dedent('''\
        # Long-War-Installer: if the following two lines are present, XCom phone home is disabled.
        127.0.0.1 prod.xcom-ew.firaxis.com
        127.0.0.1 prod.xcom.firaxis.com
        ''').strip().rstrip()

    def __init__(self):
        self._state = None

    @property
    def isEnabled(self):
        if self._state is None:
            self._state = not self._xcomEntryExists()
        return self._state

    def enable(self):
        '''Turn on phoning home by removing xcom entries from the hosts file'''
        count = 0
        try:
            logging.debug('Enabling phone home...')
            for line in fileinput.input(HostsFileScanner.HOSTS, inplace=1):
                if any(pattern.match(line) for pattern in HostsFileScanner.PATTERNS):
                    logging.debug('Removing phone home line %s', line.rstrip())
                    count += 1
                else:
                    sys.stdout.write(line)
        except (OSError, IOError), e:
            if e.errno == errno.EACCES:
                raise PhoneHomePermissionDenied(e)
            else:
                raise e
        logging.info('Removed %d lines from %s to enable phone home', count, HostsFileScanner.HOSTS)

    def disable(self):
        '''Turn off phoning home by adding xcom entries to the hosts file'''
        try:
            logging.debug('Disabling phone home...')
            with open(HostsFileScanner.HOSTS, 'a') as f:
                f.write(HostsFileScanner.PHONE_HOME_DISABLE_TEXT)
        except (OSError, IOError), e:
            if e.errno == errno.EACCES:
                raise PhoneHomePermissionDenied(e)
            else:
                raise e
        count = sum(1 for line in HostsFileScanner.PHONE_HOME_DISABLE_TEXT.splitlines())
        logging.info('Added %d lines to %s to disable phone home', count, HostsFileScanner.HOSTS)

    def _xcomEntryExists(self):
        '''Scan hosts file. If a known XCom hosts is found, return True, else return False.'''
        logging.debug('Scanning %s for unlock state', HostsFileScanner.HOSTS)
        with open(HostsFileScanner.HOSTS, 'r') as f:
            for line in f:
                if any(pattern.match(line.rstrip()) for pattern in HostsFileScanner.PATTERNS):
                    return True
        return False

class Distribution(object):
    TARGET_DIRECTORY = 'dist'
    TEMP_PREFIX = 'LongWar_Dist_'

    def __init__(self, files):
        self.files = files
        self.version = AbstractExtractor.modName(files[0])
        self.dmg = os.path.join(Distribution.TARGET_DIRECTORY, self.version + '-OSX.dmg')
        # For now we're assuming that we run --dist from the installer script itself
        self.script = os.path.realpath(__file__)

    def __repr__(self):
        return '<Distribution {v}, {n} files>'.format(v=self.version, n=len(self.files))

    def create(self):
        '''Create a .dmg file and return its location'''
        logging.debug('Creating distribution based on %s...', self.files)

        with TempDirectory('LongWar_Dist_') as distDir:
            zipFile = self.createZip(distDir)
            logging.debug('Created zip archive %s', zipFile)
            # Copy script to dist directory
            shutil.copy2(self.script, distDir)
            logging.debug('Copied %s, version %s, to %s', self.script, __version__, distDir)
            self.copyReadmeHtml(distDir)

            self.createDmg(self.dmg, distDir)

        return self.dmg

    def copyReadmeHtml(self, distDir):
        '''Copy the README.html file from the doc/ directory into the dist directory, replaceing its values.'''
        # This is the simple version
        html = os.path.join(os.path.dirname(self.script), 'docs', 'README.html')
        shutil.copy2(html, distDir)
        logging.debug('Copied README %s to %s', html, distDir)

    def createZip(self, distDir):
        '''Extract each file from self.filenames in turn, with newer files overwriting older ones, into a
        temp directory. Create a zip file in distDir with a name based on self.version, and return its path.'''
        zipName = os.path.join(distDir, self.version + '-OSX.zip')
        with TempDirectory('LongWar_DistZip_') as zipDir: 
            # Extract every file to a directory
            for filename in self.files:
                logging.debug('Extracting %s', filename)
                with AbstractExtractor.getExtractor(filename, zipDir) as extracted:
                    logging.debug('Huzzah')
            # Now create a zip file
            with zipfile.ZipFile(zipName, 'w', zipfile.ZIP_DEFLATED) as distZip:
                for root, dirs, files in os.walk(zipDir):
                    for basename in files:
                        filename = os.path.join(root, basename)
                        if os.path.isfile(filename): # regular files only
                            # FIXME: relapth still broken
                            # archivePath = os.path.join(os.path.relpath(root, relRoot), self.version + '-OSX', basename)
                            archivePath = os.path.join(self.version + '-OSX', os.path.relpath(root, distDir), basename)
                            logging.debug('Adding %s to archive as %s', filename, archivePath)
                            distZip.write(filename, archivePath)
        return zipName

    def createDmg(self, dmg, distDir):
        '''Create a .dmg image in the given file containing the directory given.'''
        volname = 'Long-War-Mac-Installer'
        logging.info('Creating disk image "%s"...', dmg)
        command = ['hdiutil', 'create', dmg, '-volname', volname, '-fs', 'HFS+', '-srcfolder', distDir]
        result = runCommand(command)
        logging.debug('Created %s from %s, return value %s', dmg, distDir, result)

# Errors
class InstallError(Exception): pass
class InnoExtractorNotFound(InstallError): pass
class LongWarFileNotFound(InstallError): pass
class InnoExtractionFailed(InstallError): pass
class SteamDirectoryNotFound(InstallError): pass
class NoGameDirectoryFound(InstallError): pass
class BackupVersionNotFound(InstallError): pass
class PhoneHomePermissionDenied(InstallError): pass
class GameHasNotPhonedHome(InstallError): pass
class EnemyWithinNotFound(InstallError): pass
class ActiveBackupFoundDuringInstall(InstallError): pass
class NoActiveBackupFoundDuringUninstall(InstallError): pass

if __name__ == '__main__': main()
