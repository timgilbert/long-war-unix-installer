#! /usr/bin/python2.7

"""Long War installer for OS/X."""

import os, sys, argparse, subprocess, logging, tempfile, shutil, textwrap
import distutils.spawn

# Errors
class InstallError(Exception): pass
class InnoExtractorNotFound(InstallError): pass
class LongWarFileNotFound(InstallError): pass
class InnoExtractionFailed(InstallError): pass
class SteamDirectoryNotFound(InstallError): pass

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
	def __init__(self, root):
		self.root = root

	@staticmethod
	def FindInstalledGame():
		logging.debug('Looking for game installation...')
		steamRoot = os.path.expanduser('~/Library/Application Support/SteamX')
		if not os.path.isdir(steamRoot):
			logging.debug("Can't open steam root at %s", steamRoot)
			raise SteamDirectoryNotFound()

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
			game = GameDirectory(GameDirectory.FindInstalledGame())

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
	except SteamDirectoryNotFound, e:
		abort("""\
			I couldn't figure out where your steam install directory is. Please use the --game option
			to specify where to find it.""")
	except InnoExtractionFailed, e:
		abort(str(e))
	
if __name__ == '__main__': main()
