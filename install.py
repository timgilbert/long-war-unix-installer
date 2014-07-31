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
	def __init__(self, filename):
		self.filename = filename
		self.modname = os.path.splitext(os.path.basename(filename))[0]
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

	def cleanup(self):
		if self.tmp is not None:
			logging.debug('Removing %s', self.tmp)
			shutil.rmtree(self.tmp)

	def validate(self):
		"""Make sure the relevant stuff is present, else throw an error"""
		if self.innoextract is None:
			raise InnoExtractorNotFound()
		if not os.path.isfile(self.filename):
			raise LongWarFileNotFound(self.filename)

class GameDirectory(object):
	"""Class representing an installed game directory."""

	def __init__(self, root=None):
		if root is None:
			finder = GameDirectoryFinder()
			root = finder.find()
		self.root = root
		logging.debug('Game root directory located at %s', self.root)


# TODO: refactor into platform-specific subclasses
class GameDirectoryFinder(object):
	STEAM_LIBRARY_ROOT = '~/Library/Application Support/Steam' 
	STEAM_CONFIG_FILE = 'config/config.vdf'
	GAME_ROOT = 'SteamApps/common/XCom-Enemy-Unknown'

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
	parser.add_argument('-d', '--debug', action='store_true', help='Show debugging output')

	args = parser.parse_args()

	loglevel = logging.DEBUG if args.debug else logging.INFO
	logging.basicConfig(format='%(message)s', level=loglevel)

	try:
		if args.game is not None:
			game = GameDirectory(args.game)
		else:
			game = GameDirectory()

		extractor = Extractor(args.filename)

		#extractor.extract()

		extractor.cleanup()

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
