#! /usr/bin/python2.7

"""Long War installer for OS/X."""

import os, sys, argparse, subprocess, logging, tempfile, shutil, textwrap, re
import distutils.spawn

# Errors
class InstallError(Exception): pass
class InnoExtractorNotFound(InstallError): pass
class LongWarFileNotFound(InstallError): pass
class InnoExtractionFailed(InstallError): pass
class SteamDirectoryNotFound(InstallError): pass
class NoGameDirectoryFound(InstallError): pass

class Extractor(object):
	"""Extracts files from the InnoInstall packages."""
	SKIP_DIRECTORY = 'Long War Files'
	PATCH_DIRECTORY = r'XComGame'

	def __init__(self, filename):
		self.filename = filename
		# modname is just the file's basename with underscores instead of spaces
		self.modname = os.path.splitext(os.path.basename(filename))[0].replace(' ', '_')
		self.innoextract = distutils.spawn.find_executable('innoextract')
		self.tmp = None

	def extract(self):
		self.validate()
		logging.info('Extracting mod "{}"...'.format(self.modname))

		self.tmp = tempfile.mkdtemp(prefix='LongWarInstaller_')
		logging.debug('Created temp directory %s', self.tmp)
		os.chdir(self.tmp)
		command = [self.innoextract, '-e', '-s', self.filename]
		logging.debug('Running command: %s', ' '.join(command))

		DEVNULL = open(os.devnull, 'w') # squash output
		result = subprocess.call(command, stdout=DEVNULL, stderr=DEVNULL)
		if result != 0:
			raise InnoExtractionFailed('Running "{}" returned {}!'.format(' '.join(command), result))

		self.scan()

	def cleanup(self):
		"""Remove the temp directory this was extracted into."""
		if self.tmp is not None:
			logging.debug('Removing %s', self.tmp)
			shutil.rmtree(self.tmp)

	def validate(self):
		"""Make sure the relevant stuff is present, else throw an error"""
		if self.innoextract is None:
			raise InnoExtractorNotFound()
		if not os.path.isfile(self.filename):
			raise LongWarFileNotFound(self.filename)

	def scan(self):
		"""After extraction, look in extracted directory to find applicable files."""
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
						self.auxilliaryFiles.append(self._relativePath(root, filename))

		# logging.debug('Aux: %s', self.auxilliaryFiles)
		# logging.debug('Patch: %s', self.patchFiles)

	def _relativePath(self, root, filename):
		"""Given an absolute path to a filename, return its patch relative to self.tmp"""
		path = os.path.join(root, filename)
		return path.replace(self.tmp + '/', '') # This is slightly dirty

class PatchFile(object):
	"""Represents a single file to be patched from the mod"""
	def __init__(self, filename, extractDir, extractRoot):
		self.filename = filename
		self.extractRoot = extractRoot
		self.extractedPath = os.path.join(extractDir, filename)
		# Path relative to the 'app' directory
		self.relativePath = self.extractedPath.replace(
			os.path.join(extractRoot, 'app') + os.sep, '')

	def __repr__(self):
		return '<path:{}>'.format(self.relativePath)
		
	def getExtractedPath(self):
		"""Full path to the extracted location in the temp directory"""
		return self.extractedPath

	def getBackupPath(self, backupRoot):
		"""Full path to where this file would belong relative to the given backup folder"""
		return os.path.join(backupRoot, 'app', self.relativePath)

	def getGamePath(self, gameRoot):
		"""Full path to where this file would belong in the game folder"""
		return os.path.join(gameRoot, 'XCOMData', 'XEW', self.relativePath)

class GameDirectory(object):
	"""Class representing an installed game directory."""
	BACKUP_DIRECTORY = 'Long-War-Backups'

	def __init__(self, root=None):
		if root is None:
			finder = GameDirectoryFinder()
			root = finder.find()
		if not os.path.isdir(root):
			logging.info("Can't open directory %s!", root)
			raise NoGameDirectoryFound()
		self.root = root
		logging.debug('Game root directory located at %s', self.root)
		self.backups = None
		self.scan()

	def getBackupDirectory(self, version):
		return os.path.join(self.root, self.BACKUP_DIRECTORY, version)

	def scan(self):
		logging.debug('Scanning for available backups...')
		backupRoot = os.path.join(self.root, self.BACKUP_DIRECTORY)
		if not os.path.isdir(backupRoot):
			logging.debug("Can't find backup root %s...", backupRoot)
			return

	def list(self):
		logging.debug('Listing backups...')

	def apply(self, filename):
		extractor = Extractor(filename)
		
		patcher = Patcher(extractor.modname, self)
		patcher.patch(extractor)

	def undo(self, patchname):
		logging.debug('Undoing...')		

class Backup(object):
	"""Represents a single backup directory"""
	def __init__(self, directory):
		pass

class Patcher(object):
	"""Consolidates logic for applying a patch"""

	def __init__(self, version, directory):
		self.version = version
		self.directory = directory
		self.extractor = None
		self.backupRoot = None
		self.brandNewFiles = []

	def patch(self, extractor):
		logging.debug('Applying patch %s...', self.version)

		self.extractor = extractor
		extractor.extract()

		self.createBackupDirectory(self.version)

		self.patchExecutable()

		for modFile in extractor.patchFiles:
			self.backupFile(modFile)
			#self.copyFile(modFile)

		self.writeBackupMetadata()

		extractor.cleanup()

	def patchExecutable(self): 
		logging.debug('Patching executable...')

	def backupFile(self, patchfile):
		replacementLocation = patchfile.getExtractedPath()
		backupLocation = patchfile.getBackupPath(self.backupRoot)
		gameLocation = patchfile.getGamePath(self.directory.root)

		# Check to see whether the file exists in the game directory
		if not os.path.exists(gameLocation):
			logging.debug("File %s doesn't exist in game directory, marking as new", gameLocation)
			self.brandNewFiles.append(patchfile)
			return

		logging.debug('Backing up %s to %s...', gameLocation, backupLocation)
		parent = os.path.dirname(backupLocation)
		if not os.path.isdir(parent):
			os.makedirs(parent)
		shutil.copy(gameLocation, backupLocation)

	def createBackupDirectory(self, version):
		self.backupRoot = self.directory.getBackupDirectory(version)
		if os.path.isdir(self.backupRoot):
			# Already exists
			return
		os.makedirs(self.backupRoot)
		logging.debug('Created new backup directory %s', self.backupRoot)

	def copyFile(self, filename):
		logging.debug('Copying file %s...', filename)

	def writeBackupMetadata(self):
		logging.debug('Writing backup metadata...')
		logging.debug('New files: %s', self.brandNewFiles)

# TODO: refactor into platform-specific subclasses
class GameDirectoryFinder(object):
	STEAM_LIBRARY_ROOT = '~/Library/Application Support/Steam' 
	STEAM_CONFIG_FILE = 'config/config.vdf'
	GAME_ROOT = 'SteamApps/common/XCom-Enemy-Unknown-TEST'

	def __init__(self):
		self.steamRoot = os.path.expanduser(self.STEAM_LIBRARY_ROOT)
		if not os.path.isdir(self.steamRoot):
			logging.debug("Can't open steam root at %s", self.steamRoot)
			raise SteamDirectoryNotFound()

	def find(self):
		for root in self._findSteamInstallRoots():
			guess = os.path.join(root, self.GAME_ROOT)
			if os.path.isdir(guess):
				return guess
			#logging.debug("No game directory found in %s", guess)
		raise NoGameDirectoryFound()

 	def _findSteamInstallRoots(self):
 		allRoots = [self.steamRoot] + self._readSteamConfig()

 		return allRoots

 	def _readSteamConfig(self):
 		result = []

 		# Grub through the steam config files to find alternate install directories
 		config = os.path.join(self.steamRoot, self.STEAM_CONFIG_FILE)
 		if not os.path.exists(config):
 			logging.debug("Warning: can't open steam config file %s to find alternate install directories", config)
 			return result

 		with open(config) as f:
 			for line in f:
 				match = re.match(r'^\s*"BaseInstallFolder[^"]+"\s+"(.+)"\s*$', line)
 				if match is not None:
 					result.append(match.group(1))
 					logging.debug('Found steam install directory %s!', match.group(1))
 		return result

def abort(errmsg):
	print textwrap.dedent(errmsg)
	sys,exit(1)

def main():
	parser = argparse.ArgumentParser(description='Install Long War on OS/X.')
	parser.add_argument('filename', help='Filename for the Long War executable file')
	parser.add_argument('--game', help='Directory to use for game installation')
	parser.add_argument('--list', action='store_true', help='List mod backups and exit')
	parser.add_argument('--uninstall', help='Uninstall given mod and exit')
	parser.add_argument('-d', '--debug', action='store_true', help='Show debugging output')

	args = parser.parse_args()

	loglevel = logging.DEBUG if args.debug else logging.INFO
	logging.basicConfig(format='%(message)s', level=loglevel)

	try:
		game = GameDirectory(args.game)

		if args.list:
			game.list()
			return

		if args.uninstall:
			game.uninstall(args.uninstall)
			return

		game.apply(args.filename)
		#extractor = Extractor(args.filename)

		#extractor.extract()

		#extractor.cleanup()

	except InnoExtractorNotFound:
		abort("""\
			In order to run this program, you must first install innoextract.
			If you've got homebrew installed, you can run this command:
			
				brew install innoextract
			
			If you aren't using homebrew, install innoextract from its homepage here: 

				http://constexpr.org/innoextract/
			""")
	except LongWarFileNotFound, e:
		abort("Can't open file '" + str(e) + "'!")
	except NoGameDirectoryFound, e:
		abort("""\
			I couldn't figure out where your XCom install directory is. Please use the --game option
			to specify where to find it.""")
	except SteamDirectoryNotFound, e:
		abort("""\
			I couldn't figure out where your steam installation is. Please use the --game option
			to specify where to find it your game installation directory.""")
	except InnoExtractionFailed, e:
		abort(str(e))
	
if __name__ == '__main__': main()
