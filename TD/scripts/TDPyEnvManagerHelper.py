# Exported from TDPyEnvManager version 1.3.8
import argparse
import json
import queue
import re
import shutil
import sys
import os
import subprocess
import shlex
import platform
import threading
import traceback
import requests
import importlib.util
import logging
from logging.handlers import TimedRotatingFileHandler
import venv
import pathlib
from functools import partial
import yaml
try:
	import tomllib  # Python 3.11+
except ModuleNotFoundError:
	try:
		import tomli as tomllib  # type: ignore
	except ModuleNotFoundError:
		tomllib = None  # type: ignore

class TDPyEnvManagerHelper:
	"""
	A class to manage the installation and setup of Python and Conda environments for TouchDesigner.

	This class doesn't require TouchDesigner to be running and can be used as a standalone Python script.

	It gets imported as a module in TouchDesigner in the context of the TDPyEnvManager to be used as a helper class
	within the TDPyEnvManager.

	It provides methods to download and install Miniconda, create Conda environments, 
	and manage Python virtual environments. It also includes methods for logging, downloading files,
	creating .gitignore files, and verifying installations as well as various other tools and utilities.

	Example usages can be found in Samples/TDPyEnvManager folder. You will find the script and both .sh and .bat files to run the script
	using arguments to create a Conda or Python virtual environment.
	"""
	def __init__(self, mode:str|None=None, envName:str|None=None, installPath:pathlib.Path|None=None) -> None:
		"""
		Initialize the TDPyEnvManagerHelper class.

		Args:
			mode (str | None, optional): The mode used to install an environment. Can be `Conda Env` or `Python vEnv`. Defaults to None.
			envName (str | None, optional): The name of the environment to be created for a Python vEnv or a Conda Env. Defaults to None.
			installPath (pathlib.Path | None, optional): The path to the Miniconda installation, or the Python Virtual Environment. Defaults to None.
		"""
		self.startAsActive:bool = False # Only set to true if the context loaded form file is active
		self.mode:str|None = mode  # 'Conda Env' or 'Python vEnv'
		self.envName:str|None = envName  # Name of the Conda or Python Virtual Environment
		self.installPath:pathlib.Path|None = installPath  # Path for Miniconda or Python Virtual Environment
		pyVer = sys.version_info
		self.pythonVersion:str= f'{pyVer.major}.{pyVer.minor}'  # Python version to be installed
		self.logger:logging.Logger|None = None
		
		self.taskQueue:queue.Queue = queue.Queue()
		self.errorQueue:queue.Queue = queue.Queue()  # Store worker errors without killing the thread
		self.onError = None  # Optional callback: (task, exc, traceback_str) -> None
		self.runningProcess:subprocess.Popen|None = None

		self.envPath: pathlib.Path | None = None  # Path to the Conda or Python Virtual Environment
		self.executablePath: pathlib.Path | None = None  # Path to the Python executable in the environment
		self.osPath: list[str] = []  # List to store OS PATH entries
		self.sysPath: list[str] = []  # List to store sys.path entries
		self.extraPaths: list[str] = []  # Arbitrary extra paths to add to sys.path

		self.loadedFromContext: bool = False  # Flag to indicate if the environment was loaded from a context file
		self.initLoadedFromContext: bool = False  # Tracks first-load-from-context for UI/flow decisions
		self.Ready: bool = False  # Flag to indicate if the environment is ready

		self.autoSetup: bool = False  # If true, the setup will be automatic without user interaction
		self.autoSetupReqs: list[str] = []  # Optional list of requirements files to install during auto-setup

		# Start the worker thread
		self.thread:threading.Thread = threading.Thread(target=self.worker, daemon=True)

	def postInit(self) -> None:
		self.logger = self.setupLogger()
		self.logger.info("Logger initialized.")
		
		self.thread.start()

		contextYamlPath = (pathlib.Path.cwd() / 'TDPyEnvManagerContext.yaml').resolve()
		legacyContextJsonPath = (pathlib.Path.cwd() / 'TDPyEnvManagerContext.json').resolve()
		pyprojectTomlPath = (pathlib.Path.cwd() / 'pyproject.toml').resolve()

		# Convert legacy JSON context to YAML if present
		if legacyContextJsonPath.exists() and not contextYamlPath.exists():
			self.logger.info("Legacy JSON context file found. Converting to YAML.")
			self.migrateContextJsonToYaml(legacyContextJsonPath, contextYamlPath)

		contextLoaded = False

		pyprojectContext = self.loadContextFromPyproject(pyprojectTomlPath)
		if pyprojectContext is not None:
			self.logger.info("pyproject.toml context found. Loading context.")
			self.applyContextDict(pyprojectContext)
			contextLoaded = True
		else:
			isContextFileFound = self.checkForContextFile(contextYamlPath)
			if isContextFileFound:
				# Load the context file to get the install path and environment name
				self.logger.info("Context file found. Loading context.")
				self.ReadContextFromFile(contextYamlPath)
				contextLoaded = True

		if contextLoaded:
			self.loadedFromContext = True
			self.initLoadedFromContext = True

			if self.autoSetup:		
				try:
					self.autoSetupEnv()
				except Exception as e:
					self.logger.error(f"Error during auto setup from context: {e}")

			# Context loaded, link env if auto-setup didn't already do it
			if not self.Ready:
				self.logger.debug(f"Linking environment from context: {self.envPath}")
				self.linkEnv(self.envPath)

			self.loadedFromContext = True
		
		self.logger.info("TDPyEnvManagerHelper fully initialized.")

	def __del__(self) -> None:
		"""
		Clean up the worker thread when the instance is deleted.
		"""
		self.stopWorker()

	def setupLogger(self) -> logging.Logger:
		"""
		Setup the logger for the class.

		Returns:
			logging.Logger: A logger instance to be used within the helper.
		"""
		isLoggingEnvVarPassed = True if 'TOUCH_APP_LOG_LEVEL' in os.environ.keys() else False
		logLevel = os.environ['TOUCH_APP_LOG_LEVEL'] if isLoggingEnvVarPassed else 30

		logger = logging.getLogger('TDAppLogger.TDPyEnvManagerHelper')
		logger.setLevel(logLevel)
		logger.propagate = False
		
		# Add stream handler if none
		if not logger.hasHandlers():
			myHandler = logging.StreamHandler()
			myFormatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
			myHandler.setFormatter(myFormatter)
			logger.addHandler(myHandler)

			# Add rotating file handler so logs are persisted for debugging
			try:
				logPath = None
				sysPlatform = platform.system()

				# Windows: prefer %LOCALAPPDATA%\Derivative\TouchDesigner099\TDLogs
				if sysPlatform == 'Windows':
					localAppData = os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA')
					if localAppData:
						tdLogs = pathlib.Path(localAppData) / 'Derivative' / 'TouchDesigner099' / 'TDLogs'
						try:
							tdLogs.mkdir(parents=True, exist_ok=True)
							logPath = tdLogs / f'TDPyEnvManagerHelper_{str(os.getpid())}.log'
						except Exception:
							logPath = None

				# macOS: prefer ~/Library/Application Support/Derivative/TouchDesigner099/TDLogs
				elif sysPlatform == 'Darwin':
					home = pathlib.Path.home()
					tdLogs = home / 'Library' / 'Application Support' / 'Derivative' / 'TouchDesigner099' / 'TDLogs'
					try:
						tdLogs.mkdir(parents=True, exist_ok=True)
						logPath = tdLogs / f'TDPyEnvManagerHelper_{str(os.getpid())}.log'
					except Exception:
						logPath = None

				# Fallback: current working directory
				if not logPath:
					logPath = pathlib.Path.cwd() / 'TDPyEnvManager.log'

				fileHandler = TimedRotatingFileHandler(str(logPath), when='midnight', interval=1, backupCount=10, encoding='utf-8', delay=True)
				fileHandler.suffix = '%Y%m%d-%H%M%S'
				fileHandler.setFormatter(myFormatter)
				logger.addHandler(fileHandler)
				logger.debug(f"File logging enabled at {logPath}")
			
			except Exception as e:
				logger.error(f"Failed to create file handler for logger: {e}")

		logger.debug("Logger setup successfully")
		return logger
	
	def worker(self) -> None:
		"""
		Worker thread to process tasks from the task queue.
		This method runs in a separate thread and continuously checks for tasks in the queue.
		It executes the tasks and handles any exceptions that may occur during execution
		or subprocess calls.
		"""
		while True:
			task = self.taskQueue.get()
			try:
				if task is None:
					break  # Exit if None is received (shutdown signal)
			
				if callable(task):  # If it's a function, execute it
					funcName = task.func.__name__ if isinstance(task, partial) else task.__name__
					self.logger.debug(f"Starting thread task: {funcName}")
					task()

				elif isinstance(task, list):  # If it's a subprocess command, execute it
					self.logger.debug(f"Starting subprocess: {' '.join(task)}")

					if platform.system() == 'Windows':
						result = subprocess.run(task, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
					else:
						result = subprocess.run(task, capture_output=True, text=True, check=True)
					
					self.logger.debug(f"Subprocess completed with exit code {result.returncode}")
					self.logger.debug(result.stdout)
			
			except subprocess.CalledProcessError as e:
				self.logger.error(f"Subprocess failed: {e}")
				self.logger.error(f"Command was {task}")
				self.reportWorkerError(task, e)
				continue
			
			except Exception as e:
				self.logger.error(f"Error in worker thread: {e}")
				self.logger.error(f"Task was {task}")
				self.reportWorkerError(task, e)
				continue
			
			finally:
				self.taskQueue.task_done()

	def reportWorkerError(self, task, exc) -> None:
		"""
		Log and surface worker errors without stopping the worker loop.
		"""
		tb = traceback.format_exc()
		self.logger.debug(tb)

		try:
			self.errorQueue.put((task, exc, tb))
		except Exception:
			self.logger.debug("Failed to enqueue worker error", exc_info=True)

		if callable(self.onError):
			try:
				self.onError(task, exc, tb)
			except Exception:
				self.logger.debug("onError callback raised", exc_info=True)

	def checkForContextFile(self, configFile: pathlib.Path) -> bool:
		"""
		Check if the specified configuration file exists.

		Args:
			configFile (pathlib.Path): The path to the configuration file to check.

		Returns:
			bool: True if the configuration file exists, False otherwise.
		"""
		if configFile.exists():
			self.logger.info(f"Configuration file found: {configFile}")
			return True
		else:
			self.logger.info(f"Configuration file not found: {configFile}")
			return False

	def downloadFile(self, url:str, destPath:pathlib.Path, *, timeout: int = 30, skip_if_exists: bool = False) -> None:
		"""
		Download a file from the given URL to the specified destination path.

		Args:
			url (str): The URL to download the file from.
			destPath (pathlib.Path): The destination path where the file will be saved.
			timeout (int, optional): Timeout for the request in seconds. Defaults to 30.
			skip_if_exists (bool, optional): Skip download if the file already exists. Defaults to False.
		"""
		if skip_if_exists and destPath.exists():
			self.logger.debug(f"Download skipped; file already exists at {destPath}")
			return

		destPath.parent.mkdir(parents=True, exist_ok=True)
		self.logger.debug(f"Created destination folder: {destPath.parent}")

		try:
			response = requests.get(url, stream=True, timeout=timeout)
			response.raise_for_status()
			self.logger.info(f"Starting download of file from {url} to {destPath}")
			with destPath.open('wb') as file:
				for chunk in response.iter_content(chunk_size=8192):
					file.write(chunk)
			
			self.logger.info(f"Downloaded file to {destPath}")
		
		except requests.RequestException as e:
			self.logger.error(f"Failed to download file: {e}")
		
		except Exception as e:
			self.logger.error(f"Error while downloading file: {e}")

	def createGitIgnore(self, path: pathlib.Path, *, skip_if_exists: bool = True) -> None:
		"""
		Create a .gitignore file in the specified path.
		
		Args:
			path (pathlib.Path): The path where the .gitignore file will be created.
			skip_if_exists (bool, optional): Skip creation if the file already exists. Defaults to True.
		"""
		gitIgnorePath = path / ".gitignore"

		gitignoreContent = """
# Ignore everything in the virtual environment directory except this file
*
!.gitignore
"""
		try:
			if skip_if_exists and gitIgnorePath.exists():
				self.logger.debug(f".gitignore already present at {gitIgnorePath}, skipping.")
				return

			with open(gitIgnorePath, "w") as f:
				f.write(gitignoreContent)
			
			self.logger.info(f".gitignore created at: {gitIgnorePath}")
		
		except Exception as e:
			self.logger.error(f"Error creating .gitignore: {e}")

	def createCondaRc(self, path: pathlib.Path, *, skip_if_exists: bool = True) -> None:
		"""
		Create a .condarc file in the specified path.

		Args:
			path (pathlib.Path): The path where the .condarc file will be created.
			skip_if_exists (bool, optional): Skip creation if the file already exists. Defaults to True.
		"""
		self.logger.info(f"Creating .condarc file at {path}")
		
		try:
			condarc = path / ".condarc"
			if skip_if_exists and condarc.exists():
				self.logger.debug(f".condarc already present at {condarc}, skipping.")
				return

			with open(condarc, "w") as f:
				f.write("channels:\n  - conda-forge\nchannel_priority: strict\n")
		
		except Exception as e:
			self.logger.error(f"Error creating .condarc: {e}")

	def verifyConda(self, installPath: pathlib.Path) -> bool:
		"""
		Verify if Conda is installed in the specified path.

		Args:
			installPath (pathlib.Path): The path where Conda is expected to be installed.

		Raises:
			OSError: If the platform is not supported.

		Returns:
			bool: True if Conda is installed, False otherwise.
		"""
		sysPlatform = platform.system()

		if sysPlatform == 'Windows':
			condaPath = installPath / 'Scripts' / 'conda.exe'
		elif sysPlatform == 'Darwin':
			condaPath = installPath / 'bin' / 'conda'
		else:
			raise OSError(f"Unsupported platform: {sysPlatform}")

		return condaPath.exists()

	def verifyCondaLib(self, installPath: pathlib.Path) -> bool:
		"""
		Verify if the Conda library is accessible in the specified path.
		Checks if the site-packages directory is in sys.path and if the conda module can be imported.

		Args:
			installPath (pathlib.Path): The path where Conda is expected to be installed.

		Returns:
			bool: True if the Conda library is accessible, False otherwise.
		"""
		systemPlatform = platform.system()
		libFolder = 'lib' if systemPlatform == 'Darwin' else 'Lib'
		pythonFolder = f'python{self.pythonVersion}' if systemPlatform == 'Darwin' else None
		
		sitePackagesPath = installPath / libFolder / pythonFolder / 'site-packages' if pythonFolder else installPath / libFolder / 'site-packages'
		if str(sitePackagesPath.resolve()) not in sys.path:
			sys.path = [str(sitePackagesPath.resolve())] + sys.path

		importlib.invalidate_caches()
		return importlib.util.find_spec('conda') is not None

	def downloadConda(self) -> pathlib.Path:
		"""
		Download the Miniconda installer for the current platform.

		Raises:
			OSError: If the platform is not supported.

		Returns:
			pathlib.Path: The path to the downloaded Miniconda installer.
		"""
		try:
			if platform.system() == 'Windows':
				condaURL = 'https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe'
				condaInstallerPath = pathlib.Path.cwd() / 'Miniconda3-latest-Windows-x86_64.exe'
			elif platform.system() == 'Darwin':
				condaURL = 'https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh'
				condaInstallerPath = pathlib.Path.cwd() / 'Miniconda3-latest-MacOSX-arm64.sh'
			else:
				raise OSError("Unsupported operating system")

			self.logger.info(f"Downloading Miniconda installer from: {condaURL}")
			
			if not condaInstallerPath.exists():
				self.downloadFile(condaURL, condaInstallerPath, timeout=60, skip_if_exists=True)

			return condaInstallerPath

		except Exception as e:
			self.logger.error(f"Failed to download Miniconda installer: {e}")
			raise 

	def cleanDirectory(self, path: pathlib.Path) -> None:
		"""
		Clean the specified directory by removing it and its contents.

		Args:
			path (pathlib.Path): The path to the directory to be cleaned.
		"""
		self.logger.debug(f"Cleaning directory: {path}")

		if path.exists() and path.is_dir():
			shutil.rmtree(path)
			self.logger.info(f"Directory cleaned: {path}")
		
		else:
			self.logger.error(f"Directory not found: {path}")

	def installConda(self, installPath: pathlib.Path, keepInstaller: bool = False) -> None:
		"""
		Install Miniconda using the downloaded installer.

		Get the installer path from the downloadConda method.
		If the installer is not found, it will download it.

		Args:
			installPath (pathlib.Path): The path where Miniconda will be installed.
			keepInstaller (bool, optional): Keep the installer on the system,
			in the current installer location, when Miniconda is done installing. Defaults to False.

		Raises:
			OSError: If the platform is not supported.
			RuntimeError: If the installation fails with a non-zero exit code.
		"""
		self.logger.info(f"Installing conda at {installPath}.")
		condaInstallerPath = self.downloadConda()
		self.logger.info(f"Using installer: {condaInstallerPath}")

		try:
			userEnv = os.environ.copy()
			if 'PYTHONPATH' in userEnv:
				del userEnv["PYTHONPATH"]
			userEnv['CONDA_CHANNELS'] = 'conda-forge'

			# resolve and log the exact install path we will pass to the installer
			usedInstallPath = str(pathlib.Path(installPath).resolve())
			self.logger.debug(f"Installer target path: {usedInstallPath}")

			if platform.system() == 'Windows':
				command = [
					str(condaInstallerPath),
					'/S',
					'/InstallationType=JustMe',
					'/NoShortcuts=1',
					'/AddToPath=0',
					'/RegisterPython=0',
					'/NoRegistry=1',
					f'/D={usedInstallPath}'
				]
				result = subprocess.run(command, capture_output=True, check=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, env=userEnv)
			
			elif platform.system() == 'Darwin':
				# Ensure the installer script is executable
				condaInstallerPath.chmod(0o755)
				command = [
					str(condaInstallerPath),  # path to the Miniconda installer
					"-b",  # batch mode (no prompts)
					"-u",  # update if it exists
					"-p", 
					usedInstallPath  # installation path
				]
				result = subprocess.run(["/bin/bash"] + command, capture_output=True, check=True, text=True, env=userEnv)
			
			else:
				raise OSError("Unsupported operating system")

			self.logger.debug(f"Subprocess completed with exit code {result.returncode}")
			if result.stdout:
				self.logger.debug(result.stdout)

			if not keepInstaller:
				self.cleanupFile(condaInstallerPath)

		except subprocess.CalledProcessError as e:
			# Log detailed output for debugging (returncode/stdout/stderr) and cleanup
			self.logger.error(f"Failed to install Miniconda. Return code: {getattr(e, 'returncode', 'unknown')}")
			stdout = getattr(e, 'stdout', None)
			stderr = getattr(e, 'stderr', None)
			if stdout:
				self.logger.error(f"Installer stdout:\n{stdout}")
			if stderr:
				self.logger.error(f"Installer stderr:\n{stderr}")
			try:
				self.logger.error(f"Command was {command}")
			except Exception:
				pass
			if not keepInstaller:
				try:
					self.cleanupFile(condaInstallerPath)
				except Exception:
					pass
			raise 

		except Exception as e:
			# Generic exception: log full info and cleanup
			self.logger.error(f"Error while installing Miniconda: {e}")
			try:
				self.logger.error(f"Command was {command}")
			except Exception:
				pass
			if not keepInstaller:
				try:
					self.cleanupFile(condaInstallerPath)
				except Exception:
					pass
			raise 

	def cleanupFile(self, filePath: pathlib.Path) -> None:
		"""
		Clean up the specified file by removing it.

		Args:
			filePath (pathlib.Path): The path to the file to be cleaned up.
		"""
		self.logger.info(f"Cleaning up file: {filePath}")
		try:
			filePath.unlink()
			self.logger.debug(f"Removed file: {filePath}")
		except FileNotFoundError:
			self.logger.error(f"File not found for cleanup: {filePath}")
			raise FileNotFoundError(f"File not found for cleanup: {filePath}")

	"""
	Conda specifics
	"""
	def createCondaEnv(self, installPath: pathlib.Path, envName: str, pythonVersion: str, useEnv: bool = False) -> None:
		"""
		Create a Conda environment using the specified parameters.
		If the environment.yml file is present in the current working directory,
		it will be used to create the environment.
		Otherwise, a new Conda environment will be created with the specified name and Python version.
		Existing environments with the same name will be overridden.

		Args:
			installPath (pathlib.Path): The path where Conda is installed.
			envName (str): The name of the Conda environment to be created.
			pythonVersion (str): The version of Python to be installed in the environment.
			useEnv (bool, optional): Use the environment.yml to create the environment from. Defaults to False.

		Raises:
			OSError: If the platform is not supported.
			RuntimeError: If the creation of the Conda environment fails with a non-zero exit code.
		"""
		if useEnv:
			self.logger.info(f"Attempting to create Conda environment from environment.yml at {pathlib.Path.cwd() / 'environment.yml'}")
		else:
			self.logger.info(f"Attempting to create Conda environment '{envName}' at '{installPath}' with Python version {pythonVersion}.")
		
		self.logger.info(f"Existing environment with matching name will be overridden.")
		
		ogEnvName = envName
		envName = self.validateEnvName(envName)
		if ogEnvName != envName:
			self.logger.warning(f"Environment name '{ogEnvName}' was modified to '{envName}' to comply with naming conventions.")

		try:
			if platform.system() == 'Windows':
				if useEnv:
					command = [
						str(pathlib.Path(installPath) / 'Scripts' / 'conda.exe'),
						'env', 'create', '-n', envName, '-f', str((pathlib.Path.cwd() / 'environment.yml').resolve()), '-y'
					]
				else:
					command = [
						str(pathlib.Path(installPath) / 'Scripts' / 'conda.exe'),
						'create', '-n', envName, f'python={pythonVersion}', '-y', '--channel', 'conda-forge', '--override-channels'
					]
			
			elif platform.system() == 'Darwin':
				if useEnv:
					command = [
						str(pathlib.Path(installPath) / 'bin' / 'conda'),
						'env', 'create', '-n', envName, '-f', str((pathlib.Path.cwd() / 'environment.yml').resolve()), '-y'
					]		
				else:
					command = [
						str(pathlib.Path(installPath) / 'bin' / 'conda'),
						'create', '-n', envName, f'python={pythonVersion}', '-y', '--channel', 'conda-forge', '--override-channels'
					]					
	
			else:
				raise OSError("Unsupported operating system")
			
			# Log the command being executed
			self.logger.debug(f"Executing Conda command: {' '.join(command)}")
			userEnv = os.environ.copy()
			if 'PYTHONPATH' in userEnv:
				del userEnv["PYTHONPATH"]
			userEnv['CONDA_CHANNELS'] = 'conda-forge'
			userEnv['CONDARC'] = str(pathlib.Path(installPath) / '.condarc')

			result = subprocess.run(command, capture_output=True, check=True, text=True, env=userEnv)

			self.logger.debug(f"Subprocess completed with exit code {result.returncode}")
			self.logger.debug(result.stdout)
			
			if result.returncode != 0:
				self.logger.error(f"Creation failed with exit code {result.returncode}")
				self.logger.error(f"Failed to create conda env: {result.stderr}")
				
				raise RuntimeError(f"Creation failed with exit code {result.returncode}")
			
		except subprocess.CalledProcessError as e:
			self.logger.error(f"Failed to create Conda environment: {e.stderr}")
			self.logger.error(f"Command was {command}")
			raise
		
		except Exception as e:
			self.logger.error(f"Error while creating Conda environment: {e}")
			self.logger.error(f"Command was {command}")
			raise

	def verifyCondaEnv(self, condaInstallPath:str, envName:str) -> bool:
		"""
		Verify if the Conda environment exists in the specified path.

		Args:
			condaInstallPath (str): The path where Conda is installed.
			envName (str): The name of the Conda environment to be verified.

		Returns:
			bool: True if the Conda environment exists, False otherwise.
		"""
		condaEnvPath = pathlib.Path(condaInstallPath) / 'envs' / envName
		return condaEnvPath.exists()

	def activateCondaEnv(self, installPath: pathlib.Path, envName: str) -> None:
		"""
		Activate the specified Conda environment.
		
		Args:
			installPath (pathlib.Path): The path where Conda is installed.
			envName (str): The name of the Conda environment to be activated.

		Raises:
			OSError: If the platform is not supported.
			RuntimeError: If the activation fails with a non-zero exit code.
		"""
	
		userEnv = os.environ.copy()
		if 'PYTHONPATH' in userEnv:
			del userEnv["PYTHONPATH"]
		userEnv['CONDA_CHANNELS'] = 'conda-forge'
		userEnv['CONDARC'] = str(pathlib.Path(installPath) / '.condarc')
		
		try:
			if platform.system() == 'Windows':
				command = [
					str(pathlib.Path(installPath) / 'Scripts' / 'activate.bat'),
					'&&', 'conda', 'activate', self.envPath
				]
				self.runningProcess = subprocess.Popen(['cmd.exe', '/K'] + command, creationflags=subprocess.CREATE_NEW_CONSOLE, text=True, env=userEnv)
			
			elif platform.system() == 'Darwin':
				condaActivateScript = pathlib.Path(installPath) / 'bin' / 'activate'
				command = f"""
				tell application "Terminal"
					activate
					do script "source '{str(condaActivateScript.resolve())}' && conda activate {self.envPath}"
				end tell
				"""
				self.runningProcess = subprocess.Popen(["osascript", "-e", command], text=True, env=userEnv)
			
			else:
				raise OSError("Unsupported operating system")

			self.logger.info(f"Activated Conda environment: {envName}.")

			if self.runningProcess:
				self.logger.debug(f"Running process: {self.runningProcess.pid}")
			
			else:
				self.logger.error(f"Failed to start the process. {self.runningProcess.stderr}")
				self.logger.error(f"Command was {command}")
				raise RuntimeError("Failed to start the process.")

		except Exception as e:
			self.logger.error(f"Error activating Conda environment: {e}")

	def setCondaRoot(self, installPath: pathlib.Path) -> pathlib.Path:
		"""
		Set the root directory of the Conda installation.

		Args:
			installPath (pathlib.Path): The path where Conda is installed.

		Returns:
			pathlib.Path: The path where Conda is installed.
		"""
		self.installPath = installPath
		return self.installPath

	def getCondaRoot(self) -> pathlib.Path:
		"""
		Get the root directory of the Conda installation.

		Returns:
			pathlib.Path: The path where Conda is installed.
		"""
		return pathlib.Path(self.installPath).resolve()
	
	def getCondaEnvPath(self, envName: str) -> pathlib.Path:
		"""
		Get the path to the Conda environment.

		Args:
			envName (str): The name of the Conda environment.

		Returns:
			pathlib.Path: The path to the Conda environment.
		"""
		if not envName:
			self.logger.warning('No envName was provided.')
			return None
		
		envPath = pathlib.Path(envName)
		if envPath.is_absolute():
			return envPath.resolve()
		
		# Otherwise we assume that it's a local name and we resolve relative to the install path.
		return (pathlib.Path(self.installPath) / 'envs' / envName).resolve()

	def exportCondaEnvYaml(self, envPath: pathlib.Path) -> None:
		"""
		Export the Conda environment to a YAML file.
		The YAML file will be created in the current working directory.
		If the environment.yml file already exists, it will be overwritten.

		Args:
			envPath (pathlib.Path): The path to the Conda environment to be exported.
		"""
		try:
			if self.verifyCondaLib(self.installPath):
				condaEnvMod = importlib.import_module('conda.env.env')
				# Access the 'env' attribute from the imported module

				yamlPath = pathlib.Path.cwd() / 'environment.yml'
				
				envPath = pathlib.Path(envPath) if isinstance(envPath, str) else envPath
				condaEnv = condaEnvMod.from_environment(self.envName, str(envPath.resolve()))
				envAsDict = condaEnv.to_dict()
				envAsDict['channels'] = ['conda-forge'] # Force conda-forge channel

				with open(yamlPath, 'w') as file:
					yaml.dump(envAsDict, file, default_flow_style=False)
				
				self.logger.info(f"Conda environment exported to: {yamlPath}")

			else:
				self.logger.error("Conda library not found.")
				raise
		
		except Exception as e:
			self.logger.error(f"Error exporting Conda environment: {e}")
			raise
		
		return

	"""
	Python specifis
	"""
	def verifyPython(self, installPath: pathlib.Path) -> bool:
		"""
		Verify if Python is installed at the specified path (folder).

		Args:
			installPath (pathlib.Path): The folder path where Python is expected to be installed.

		Returns:
			bool: True if Python is installed, False otherwise.
		"""
		pythonPath = pathlib.Path(installPath) / 'python.exe'
		return pythonPath.exists()

	def createPythonEnv(self, installPath: str, envName: str, useReq: bool = True) -> None:
		"""
		Create a Python virtual environment using the specified name.

		Args:
			envName (str): The folder name of the Python virtual environment to be created.
			useReq (bool, optional): Use a requirements.txt file if present in the current working directory. Defaults to False.
		"""
		envName = self.validateEnvName(envName)
		envPath = pathlib.Path(installPath) / envName

		self.logger.info(f"Creating Python virtual environment '{envName}' at '{envPath}'.")
  
		# Check if the virtual environment already exists
		if not envPath.exists():
			if platform.system() == 'Windows':
				self.logger.info("Creating venv on windows")
				venv.create(envPath, with_pip=True, prompt=".")
				print("Finished creating venv at ", envPath)
			else:
				venv.create(envPath, symlinks=True, with_pip=True, prompt=".")

			self.logger.info(f"Python virtual environment '{envName}' created successfully.")
		else:
			self.logger.info(f"Python virtual environment '{envName}' already exists. Skipping creation.")

		if useReq:
			self.logger.info(f"Installing requirements from requirements.txt into {envName}.")
			pythonPath = envPath / 'Scripts' / 'python.exe' if platform.system() == 'Windows' else envPath / 'bin' / 'python'
			try:
				command = [str(pythonPath), '-m', 'pip', 'install', '-r', str(pathlib.Path.cwd() / 'requirements.txt')]

				result = subprocess.run(command, capture_output=True, text=True, check=True)
				self.logger.info(result.stdout)
				self.logger.info(f"Requirements installed successfully in {envName}.")
			
			except FileNotFoundError:
				self.logger.error(f"{str(pathlib.Path.cwd() / 'requirements.txt')} not found in the current working directory.")
				self.logger.error(f"Command was {command}")
				raise

			except subprocess.CalledProcessError as e:
				self.logger.error(f"Failed to install requirements: {e.stderr}")
				self.logger.error(f"Command was {command}")
				raise
			
			except Exception as e:
				self.logger.error(f"Error while installing requirements: {e}")
				self.logger.error(f"Command was {command}")
				raise

	def activatePythonEnv(self, envName: str) -> None:
		"""
		Open a CLI and activate the specified Python virtual environment.
		
		Args:
			envName (str): The name of the Python virtual environment to be activated.
		"""
		try:
			envPath = (pathlib.Path(self.installPath) / envName).resolve()
			if platform.system() == 'Windows':
				activateScript = envPath / 'Scripts' / 'activate.bat'
				self.runningProcess = subprocess.Popen(['cmd.exe', '/K', str(activateScript)], creationflags=subprocess.CREATE_NEW_CONSOLE, text=True)
			
			elif platform.system() == 'Darwin':
				activateScript = (envPath / 'bin' / 'activate').resolve()
				envPathParent = envPath.parent
				if not activateScript.exists():
					raise FileNotFoundError(f"Activation script not found at {activateScript}")

				cd_cmd = shlex.quote(str(envPathParent))
				source_cmd = shlex.quote(str(activateScript))
				osascriptCmd = f"""
				tell application "Terminal"
					activate
					do script "cd {cd_cmd} && source {source_cmd}"
				end tell
				"""
				self.runningProcess = subprocess.Popen(["osascript", "-e", osascriptCmd], text=True)
			
			else:
				raise OSError("Unsupported operating system")

			self.logger.info(f"Activated Python virtual environment: {envName}.")
		
		except Exception as e:
			self.logger.error(f"Error activating Python virtual environment: {e}")
	
	def setPythonRoot(self, rootPath: pathlib.Path) -> pathlib.Path:
		"""
		Set the root directory of the Python installation.

		Args:
			installPath (pathlib.Path): The path where Python is installed.

		Returns:
			pathlib.Path: The path where Python is installed.
		"""
		self.installPath = rootPath.resolve()
		return self.installPath
	
	def getPythonEnvPath(self, envName: str) -> pathlib.Path:
		"""
		Get the path to the Python virtual environment.

		Args:
			envName (str): The name of the Python virtual environment.

		Returns:
			pathlib.Path: The path to the Python virtual environment.
		"""
		p = pathlib.Path(envName)
		if p.is_absolute() or '/' in envName or '\\' in envName or envName.startswith('.'):
			return p.resolve()
		return (self.installPath / envName).resolve()
	
	def getPythonSitePackagesPath(self, envName: str) -> pathlib.Path:
		"""
		Get the path to the site-packages directory of the Python virtual environment.

		Args:
			envName (str): The name of the Python virtual environment.

		Returns:
			pathlib.Path: The path to the site-packages directory of the Python virtual environment.
		"""
		venvPath = self.getPythonEnvPath(envName)
		if not hasattr(self, 'pythonVersion') or not self.pythonVersion:
			self.pythonVersion = f"{sys.version_info.major}.{sys.version_info.minor}"
		if platform.system() == 'Windows':
			sitePackagesPath = (venvPath / 'Lib' / 'site-packages').resolve()
		else:
			sitePackagesPath = (venvPath / 'lib' / f'python{self.pythonVersion}' / 'site-packages').resolve()

		if self.validatePath(sitePackagesPath):
			return sitePackagesPath

	def exportPyEnvRequirements(self, envPath: pathlib.Path) -> None:
		"""
		Export the requirements of the Python virtual environment to a requirements.txt file.
		The requirements.txt file will be created in the current working directory.
		If the requirements.txt file already exists, it will be overwritten.

		Args:
			envPath (pathlib.Path): The path to the Python virtual environment to be exported.
		"""
		
		sitePackagesPath = self.getPythonSitePackagesPath(envPath.name)
		currentWorkingDir = pathlib.Path.cwd()
		requirementsPath = currentWorkingDir / 'requirements.txt'

		try:
			with open(requirementsPath, 'w') as file:
				for dist in importlib.metadata.distributions():
					distPath = pathlib.Path(dist.locate_file(''))
					if sitePackagesPath in distPath.parents or sitePackagesPath == distPath:
						file.write(f"{dist.metadata['Name']}=={dist.version}\n")

			self.logger.info(f"Python virtual environment requirements exported to: {requirementsPath}")
		
		except Exception as e:
			self.logger.error(f"Failed to export requirements: {e}")

		return

	"""
	PATH AND ENV LINKING
	"""
	def addToOsPath(self, path: pathlib.Path) -> None:
		"""
		Add a path to the OS PATH environment variable if not already present.

		Args:
			path (pathlib.Path): Path to add to the OS PATH.
		"""
		currentPaths = os.environ['PATH'].split(os.pathsep)
		if path not in currentPaths:
			os.environ['PATH'] = os.pathsep.join([path] + currentPaths)
		
		if path not in self.osPath and not platform.system() == 'Windows':
			self.osPath.append(path)

		# Use add_dll_directory on Windows
		if platform.system() == 'Windows' and hasattr(os, 'add_dll_directory'):
			os.add_dll_directory(path)
			if path not in self.osPath:
				self.osPath.append(path)

	def addToSysPath(self, path: pathlib.Path) -> None:
		"""
		Add a path to the sys.path if not already present.

		Args:
			path (pathlib.Path): Path to add to sys.path.
		"""
		if path not in sys.path:
			sys.path = [path] + sys.path
		
		if path not in self.sysPath:
			self.sysPath.append(path)

	def addPathsToEnvironment(self, condaEnvPath: pathlib.Path, libFolder: str, pythonFolder: str = None) -> None:
		"""
		Helper method to add paths to OS PATH and sys.path.

		Args:
			condaEnvPath (pathlib.Path): Path to Conda environment.
			libFolder (str): Library folder name.
			pythonFolder (str): Python version folder name.
		"""
		# Add Conda install paths
		condaEnvBin = condaEnvPath / 'Scripts' if platform.system() == 'Windows' else condaEnvPath / 'bin'
		self.addToOsPath(str(condaEnvBin.resolve()))

		envSitePackagesPath = condaEnvPath / libFolder / pythonFolder / 'site-packages' if pythonFolder else condaEnvPath / libFolder / 'site-packages'
		self.addToSysPath(str(envSitePackagesPath.resolve()))

	def resolveExtraPath(self, rawPath: str) -> pathlib.Path | None:
		"""
		Resolve a user-provided extra path, expanding env vars and user (~) and making it absolute.
		Returns None if the path is empty, a comment, or does not exist.
		"""
		if not rawPath:
			return None

		trimmed = rawPath.strip()
		if not trimmed:
			return None

		expanded = os.path.expandvars(trimmed)
		expanded = os.path.expanduser(expanded)
		pathObj = pathlib.Path(expanded)
		if not pathObj.is_absolute():
			pathObj = pathlib.Path.cwd() / pathObj

		try:
			pathObj = pathObj.resolve()
		except Exception:
			self.logger.error(f"Could not resolve extra path: {pathObj} (from {rawPath})")
			return None

		if not pathObj.exists():
			self.logger.warning(f"Extra path does not exist, skipping: {pathObj} (from {rawPath})")
			return None

		return pathObj

	def applyExtraPaths(self) -> None:
		"""
		Apply extraPaths entries to sys.path, resolving env vars and relative paths.
		"""
		if not getattr(self, 'extraPaths', None):
			return

		for rawPath in self.extraPaths:
			resolved = self.resolveExtraPath(rawPath)
			if not resolved:
				continue
			self.addToSysPath(str(resolved))
			self.logger.info(f"Extra path added to sys.path: {resolved}")

	def linkEnv(self, envPath: pathlib.Path) -> bool:
		"""
		Given an environment path, attempt to link the current TouchDesigner session to a venv or conda env.

		Args:
			envPath (pathlib.Path): Path to the environment folder.
		"""
		if self.mode == 'Conda Env':
			success = self.LinkCondaEnv(envPath)
		else:
			success = self.LinkPyVenv(envPath)
		
		if success:
			self.applyExtraPaths()
			self.Ready = True
			self.logger.info(f'Environment {envPath} was linked and is ready. Context is: {self.AsContext()}')

			# Generate TDPyEnvManagerContext.yaml file
			self.WriteContextToFile((pathlib.Path.cwd() / 'TDPyEnvManagerContext.yaml').resolve())

			if self.loadedFromContext:
				self.loadedFromContext = False

		else:
			self.logger.error(f'Environment {envPath} could not be linked. Context is: {self.AsContext()}')

		return success
	
	def LinkPyVenv(self, envPath: pathlib.Path) -> bool:
		"""
		Given a path to a Python virtual environment, attempt to link the current TouchDesigner session to it.

		Args:
			envPath (pathlib.Path): Path to the Python virtual environment.

		Returns:
			bool: True if successful, False otherwise.
		"""	
		try:
			os.environ['VIRTUAL_ENV'] = str(envPath)
			envPath = pathlib.Path(envPath) if isinstance(envPath, str) else envPath
			self.envPath = str(envPath.resolve())
			executablePath = envPath / 'Scripts' / 'python.exe' if platform.system() == 'Windows' else envPath / 'bin' / 'python'
			self.executablePath = executablePath.resolve()

			if not executablePath.exists():
				self.logger.error(f"Python executable not found at {executablePath}.")
				return False
			
			sitePackagesPath = self.getPythonSitePackagesPath(self.envName)
			self.sysPath = []
			self.sysPath.append(str(sitePackagesPath))

			if sitePackagesPath and str(sitePackagesPath) not in sys.path:
				sys.path = [str(sitePackagesPath)] + sys.path

			return True

		except Exception as e:
			self.logger.error(f'Could not link venv at path {envPath}. {e}')
			return False

	def LinkConda(self, installPath: pathlib.Path) -> bool:
		"""
		Given a path to a conda installation, attempt to link the current TouchDesigner session to it.
		This will allow TouchDesigner to interact with lib conda.

		Args:
			installPath (pathlib.Path): Path to the conda installation folder.

		Returns:
			bool: True if successful, False otherwise.
		"""
		condaInstallPath = self.getCondaRoot()
		if not self.validatePath(condaInstallPath):
			self.logger.error(f"Invalid Conda install path: {condaInstallPath}")
			return False

		if platform.system() == 'Windows':
			condaBin = condaInstallPath / 'condabin'
			condaScripts = condaInstallPath / 'Scripts'

			if condaBin.exists() and condaScripts.exists():
				self.addToOsPath(str(condaBin.resolve()))
				self.addToOsPath(str(condaScripts.resolve()))
			else:
				self.logger.error(f'Conda could not be loaded, paths do not exist: {condaBin, condaScripts}')
				return False

		else:
			condaBin = condaInstallPath / 'bin'
			if condaBin.exists():
				self.addToOsPath(str(condaBin.resolve()))
			else:
				self.logger.error(f'Conda could not be loaded, paths do not exist: {condaBin}')
				return False
		
		# Add Conda install site-packages path
		libFolder = 'Lib' if platform.system() == 'Windows' else 'lib'
		pythonFolder = f'{self.getHighestPyVer(condaInstallPath)}' if platform.system() == 'Darwin' else None
		sitePackagesPath = condaInstallPath / libFolder / pythonFolder / 'site-packages' if pythonFolder else condaInstallPath / libFolder / 'site-packages'
		if sitePackagesPath.exists():
			self.addToSysPath(str(sitePackagesPath.resolve()))
		else:
			self.logger.error(f'Conda could not be loaded, paths do not exist: {sitePackagesPath}')
			return False

		# Verify if the 'conda' module is available
		try:
			importlib.invalidate_caches()
			foundConda = importlib.util.find_spec('conda')
			if foundConda:
				self.logger.info(f"'conda' module successfully imported. Conda install at path {condaInstallPath} was linked.")
		
		except ModuleNotFoundError:
			self.logger.error(f"'conda' module could not be found after linking to the conda install. Ensure conda is properly installed.")
			self.logger.debug(f"Current sys.path: {sys.path}")
			return False

		except ValueError:
			self.logger.error('No value was returned for conda spec.')
			return False


		self.logger.info(f'Conda loaded from {installPath}.')
		return True

	def LinkCondaEnv(self, envPath: pathlib.Path = None) -> bool:
		"""
		Given an environment path, attempt to link the current 
		TouchDesigner session to a Conda environment.

		LinkConda must be called first to ensure the Conda install is available.

		Args:
			envPath (pathlib.Path): Path to the Conda environment.

		Returns:
			bool: True if successful, False otherwise.
		"""
		try:
			condaInstallPath = self.getCondaRoot()
			if not self.validatePath(condaInstallPath):
				self.logger.error(f"Invalid Conda install path: {condaInstallPath}")
				return False

			envPath = pathlib.Path(envPath) if isinstance(envPath, str) else envPath
			condaEnvPath = envPath.resolve() if envPath else None
			if not self.validatePath(condaEnvPath):
				self.logger.error(f"Invalid Conda environment path: {condaEnvPath}")
				return False

			else:
				self.envPath = condaEnvPath.resolve()
				self.executablePath = (condaEnvPath / 'bin' / 'python').resolve() if platform.system() == 'Darwin' else (condaEnvPath / 'python.exe').resolve()

			if platform.system() == 'Darwin':
				# Add Conda paths to OS PATH and sys.path
				self.addPathsToEnvironment(condaEnvPath, 'lib', pythonFolder=f'python{self.pythonVersion}')
			else:
				# Add Conda paths for Windows
				self.addPathsToEnvironment(condaEnvPath, 'Lib')

			# Verify the Python executable
			python_exec = self.executablePath if self.executablePath else None
			
			if not python_exec or not os.path.exists(python_exec):
				self.logger.error(f"Python executable not found at {python_exec}. Ensure the Conda environment exist and is properly set up.")
				return False

			else:
				self.logger.info(f"Conda environment {condaEnvPath.name} linked successfully.")
				return True

		except Exception as e:
			self.logger.error(f"Failed to link Conda environment at {envPath}: {e}")
			tb = e.__traceback__
			formatted_tb = traceback.format_tb(tb)
			self.logger.error("".join(formatted_tb))
			return False
		
	def unlinkEnv(self, mode: str = None) -> bool:
		"""
		Attempt to remove the current environment path from the current TouchDesigner session.

		Args:
			mode (str, optional): The mode to use for un-linking. Defaults to None.

		Returns:
			bool: True if successful, False otherwise.
		"""		
		envPath = str(self.envPath)
		
		if envPath and self.Ready:
			if self.mode == 'Conda Env':
				success = self.UnlinkCondaEnv()
			else:
				success = self.UnlinkPyVenv()
			
			if success:
				self.Ready = False
				envPath = str(self.envPath)
				self.logger.info(f'Environment {envPath} was unlinked. Context is cleared: {self.AsContext()}.')
	
		else:
			envPath = str(self.envPath)
			self.logger.info(f'Environment {envPath} was not linked. Context is: {self.AsContext()}.')

	def UnlinkCondaEnv(self) -> bool:
		"""
		Unlink the current conda environment from the current TouchDesigner session.

		Returns:
			bool: True if successful, False otherwise.
		"""

		# verify if conda install folder is still here
		condaInstallPath = self.getCondaRoot()

		# recover the paths of the install folder
		self.envPath = None
		self.executablePath = None

		condaScripts = condaInstallPath / 'Scripts'
		condaBin = condaInstallPath / 'condabin' if platform.system() == 'Windows' else condaInstallPath / 'bin'
		
		libFolder = 'Lib' if platform.system() == 'Windows' else 'lib'
		pythonFolder = f'{self.getHighestPyVer(condaInstallPath)}' if platform.system() == 'Darwin' else None
		sitePackagesPath = condaInstallPath / libFolder / pythonFolder / 'site-packages' if pythonFolder else condaInstallPath / libFolder / 'site-packages'

		condaScripts = str(condaScripts.resolve())
		condaBin = str(condaBin.resolve())
		sitePackagesPath = str(sitePackagesPath.resolve())

		# Remove non Conda install paths from sys.path
		sys.path = [p for p in sys.path if p not in self.sysPath or p == sitePackagesPath]
		self.sysPath = [sitePackagesPath] if sitePackagesPath in self.sysPath else []

		# Remove non Conda install paths from os.environ['PATH']
		osEnvironPaths = os.environ['PATH'].split(os.pathsep)
		for path in list(self.osPath):
			if path not in [condaScripts, condaBin]:
				if path in osEnvironPaths:
					osEnvironPaths.remove(path)
				
		self.osPath = [p for p in self.osPath if p in [condaScripts, condaBin]]
		os.environ['PATH'] = os.pathsep.join(osEnvironPaths)

		self.logger.debug(f'Context was: {self.AsContext()}. Remaining linked with valid conda installation, if applicable.')

		return True

	def UnlinkConda(self) -> bool:
		"""
		Unlink the current conda installation from the current TouchDesigner session.

		Returns:
			bool: True if successful, False otherwise.
		"""
		# verify if conda install folder is still here
		condaInstallPath = self.getCondaRoot()
		condaScripts = condaInstallPath / 'Scripts'
		condaBin = condaInstallPath / 'condabin' if platform.system() == 'Windows' else condaInstallPath / 'bin'
		
		libFolder = 'Lib' if platform.system() == 'Windows' else 'lib'
		pythonFolder = f'{self.getHighestPyVer(condaInstallPath)}' if platform.system() == 'Darwin' else None
		sitePackagesPath = condaInstallPath / libFolder / pythonFolder / 'site-packages' if pythonFolder else condaInstallPath / libFolder / 'site-packages'

		condaScripts = str(condaScripts.resolve())
		condaBin = str(condaBin.resolve())
		sitePackagesPath = str(sitePackagesPath.resolve())
		
		# Remove Conda install paths from sys.path
		if sitePackagesPath in sys.path:
			sys.path.remove(sitePackagesPath)

		if sitePackagesPath in self.sysPath:
			self.sysPath.remove(sitePackagesPath)

		# Remove Conda install paths from os.environ['PATH']
		osEnvironPaths = os.environ['PATH'].split(os.pathsep)
		for path in [condaScripts, condaBin]:
			if path in osEnvironPaths:
				osEnvironPaths.remove(path)

			if path in self.osPath:
				self.osPath.remove(path)

		os.environ['PATH'] = os.pathsep.join(osEnvironPaths)

		self.logger.info(f'Context was: {self.AsContext()}. Conda install unlinked.')


		return True

	def UnlinkPyVenv(self) -> bool:
		"""
		Unlink the current Python virtual environment from the current TouchDesigner session.

		Returns:
			bool: True if successful, False otherwise.
		"""
		for path in self.sysPath:
			if path in sys.path:
				sys.path.remove(path)

		self.logger.info(f'Context was: {self.AsContext()}. Resetting context.')
		
		return True
	
	def isCondaInstallPathInOSPath(self, condaInstallPath: pathlib.Path) -> bool:
		"""
		Given a conda install path, check if it's in the OS PATH or sys.path.

		Args:
			condaInstallPath (pathlib.Path): Path to the conda installation folder.

		Returns:
			bool: True if the conda install path is in the OS PATH or sys.path, False otherwise.
		"""
		condaInstallPath = str(condaInstallPath.resolve())

		for path in os.environ['PATH'].split(os.pathsep):
			if condaInstallPath in str(pathlib.Path(path).resolve()):
				return True

		for path in sys.path:
			if condaInstallPath in str(pathlib.Path(path).resolve()):
				return True
	
		return False
		
	def isCondaEnvPathInSysPath(self, condaEnvPath: pathlib.Path) -> bool:
		"""
		Given a conda environment path, check if it's in the sys.path.
		
		Args:
			condaEnvPath (pathlib.Path): Path to the conda environment.

		Returns:
			bool: True if the conda environment path is in the sys.path, False otherwise.
		"""
		condaEnvPath = str(condaEnvPath.resolve())
		for path in sys.path:
			if condaEnvPath in str(pathlib.Path(path).resolve()):
				return True
	
		return False	

	"""
	UTILS
	"""
	def validatePath(self, path: pathlib.Path) -> bool:
		"""
		Validate if the given path is writable and exists.
		Checks if the path is not None, exists, and is writable.

		Args:
			path (pathlib.Path): The path to be validated.

		Returns:
			bool: True if the path is valid, False otherwise.
		"""
		if not path:
			self.logger.debug("Path not provided.")
			return False
		
		if not path.exists():
			self.logger.debug(f"Path does not exist: {path}")
			return False
		
		if not os.access(path, os.W_OK):
			self.logger.debug(f"Path is not writable: {path}")
			return False
		
		return True

	def validateEnvName(self, envName: str) -> str:
		"""
		Validates and sanitizes an environment name.

		- Removes forbidden characters.

		Args:
			envName (str): Original environment name.

		Returns:
			str: Cleaned and valid environment name.

		"""
		forbiddenCharsPattern = r'[\/:*?"<>|\\]'
		cleanedName = re.sub(forbiddenCharsPattern, '', envName)
		return cleanedName

	def normalizeReqList(self, value) -> list[str]:
		"""
		Normalize a requirements list input to a list of strings.
		Accepts a single string or a list/tuple of items.
		"""
		if not value:
			return []
		if isinstance(value, str):
			return [value]
		if isinstance(value, (list, tuple)):
			return [str(v) for v in value if v]
		return []

	def AsContext(self) -> dict:
		"""
		Returns a dictionary representation of the current state of the TDPyEnvManagerHelper instance.

		Returns:
			dict: A dictionary containing the current state of the instance.
		"""

		def toRelativePath(path: pathlib.Path | None) -> str | None:
			"""
			Convert an absolute path to a path relative to the current working directory when possible.
			Leave already relative paths untouched.
			"""
			if not path:
				return None

			pathObj = pathlib.Path(path)
			if not pathObj.is_absolute():
				return str(pathObj)

			try:
				rel = pathObj.resolve().relative_to(pathlib.Path.cwd().resolve())
				relStr = str(rel)
				return relStr if relStr else '.'
			except Exception:
				try:
					return str(pathObj.resolve())
				except Exception:
					return str(pathObj)

		def toRelativePathStr(value: str | None) -> str | None:
			if not value:
				return None
			return toRelativePath(pathlib.Path(value))

		return {
			'active': self.Ready,
			'mode': self.mode,
			'envName': self.envName,
			'installPath': toRelativePath(self.installPath),
			'envPath': str(self.envPath) if self.envPath else None,
			'executablePath': str(self.executablePath) if self.executablePath else None,
			'osPath': list(self.osPath),
			'sysPath': list(self.sysPath),
			'pythonVersion': self.pythonVersion,
			'autoSetup': getattr(self, 'autoSetup', False),
			'autoSetupReqs': [toRelativePathStr(p) for p in (getattr(self, 'autoSetupReqs', None) or []) if p],
			'extraPaths': list(self.extraPaths) if getattr(self, 'extraPaths', None) else []
		}

	def applyContextDict(self, context: dict | None) -> None:
		"""
		Apply a context dictionary to the helper instance.
		"""
		try:
			context = context or {}
			self.startAsActive = context.get('active', self.startAsActive)
			self.mode = context.get('mode', self.mode)
			self.envName = context.get('envName', self.envName)
			installPathVal = context.get('installPath', str(self.installPath))
			self.installPath = pathlib.Path(installPathVal) if installPathVal is not None else self.installPath
			self.envPath = self.getCondaEnvPath(self.envName) if self.mode == 'Conda Env' else self.getPythonEnvPath(self.envName)
			self.executablePath = None
			self.osPath = []
			self.sysPath = []
			self.pythonVersion = context.get('pythonVersion', self.pythonVersion)
			self.autoSetup = context.get('autoSetup', False)
			self.autoSetupReqs = self.normalizeReqList(context.get('autoSetupReqs', getattr(self, 'autoSetupReqs', [])))
			self.extraPaths = context.get('extraPaths', self.extraPaths if hasattr(self, 'extraPaths') else [])
		except Exception as e:
			self.logger.error(f"Failed to apply context data: {e}")
			raise

	def loadContextFromPyproject(self, pyprojectPath: pathlib.Path) -> dict | None:
		"""
		Load context data from [tool.touchdesigner.TDPyEnvManagerContext] in pyproject.toml if present.
		"""
		try:
			if not pyprojectPath.exists():
				self.logger.info(f"Configuration file not found: {pyprojectPath}")
				return None

			if not tomllib:
				self.logger.warning("pyproject.toml found but no TOML parser available; skipping.")
				return None

			with pyprojectPath.open('rb') as file:
				parsedToml = tomllib.load(file)

			section = parsedToml.get('tool', {}).get('touchdesigner', {}).get('TDPyEnvManagerContext')
			if isinstance(section, dict):
				self.logger.info(f"Configuration file found: {pyprojectPath} [tool.touchdesigner.TDPyEnvManagerContext]")
				return section

			self.logger.info(f"[tool.touchdesigner.TDPyEnvManagerContext] not found in {pyprojectPath}")
			return None
		except Exception as e:
			self.logger.warning(f"Failed to read pyproject.toml context: {e}")
			return None
		
	def WriteContextToFile(self, filePath: pathlib.Path) -> None:
		"""
		Write the current context of the TDPyEnvManagerHelper instance to a YAML file, in the current 
		working directory. When running from TouchDesigner, the file will be written to the
		project.folder (next to the .toe file).

		Args:
			filePath (pathlib.Path): _description_
		"""
		try:
			context = self.AsContext()
			
			#Cleaning context
			context.pop('envPath')
			context.pop('executablePath')
			context.pop('osPath')
			context.pop('sysPath')

			filePath = pathlib.Path(filePath)
			targetPath = filePath.with_suffix('.yaml') if filePath.suffix.lower() == '.json' else filePath

			if targetPath.exists():
				with open(targetPath, 'r') as file:
					try:
						existing = yaml.safe_load(file)
					except Exception:
						existing = None
				if existing == context:
					self.logger.debug(f"Context file unchanged, not overwriting: {targetPath}")
					return
			
			with open(targetPath, 'w') as file:
				yaml.safe_dump(context, file, sort_keys=False)
			
			self.logger.debug(f"Context written to file: {targetPath}")
		
		except Exception as e:
			self.logger.error(f"Failed to write context to file: {e}")
			raise

	def migrateContextJsonToYaml(self, jsonPath: pathlib.Path, yamlPath: pathlib.Path) -> None:
		"""
		Convert an existing JSON context file to YAML format.

		Args:
			jsonPath (pathlib.Path): Path to the legacy JSON context.
			yamlPath (pathlib.Path): Destination YAML context path.
		"""
		try:
			with open(jsonPath, 'r') as file:
				context = json.load(file)

			with open(yamlPath, 'w') as file:
				yaml.safe_dump(context, file, sort_keys=False)

			self.logger.info(f"Migrated context from JSON to YAML at: {yamlPath}")
		except Exception as e:
			self.logger.error(f"Failed to migrate context from JSON to YAML: {e}")
			raise

	def ReadContextFromFile(self, filePath: pathlib.Path) -> None:
		"""
		Read the context of the TDPyEnvManagerHelper instance from a YAML file.
		Maintains backward compatibility with legacy JSON context files.

		Args:
		filePath (pathlib.Path): The path to the YAML context file.
		"""
		try:
			filePath = pathlib.Path(filePath)
			if filePath.suffix.lower() == '.json':
				try:
					yamlPath = filePath.with_suffix('.yaml')
					self.migrateContextJsonToYaml(filePath, yamlPath)
					filePath = yamlPath
				except Exception as e:
					self.logger.warning(f"Continuing with legacy JSON context due to migration error: {e}")

			with open(filePath, 'r') as file:
				if filePath.suffix.lower() == '.json':
					context = json.load(file)
				else:
					context = yaml.safe_load(file) or {}
				self.applyContextDict(context)

			self.logger.debug(f"Context read from file: {filePath}")
		
		except Exception as e:
			self.logger.error(f"Failed to read context from file: {e}")
			raise

	def stopWorker(self) -> None:
		"""
		Stop the worker thread by sending a shutdown signal (None) to the task queue.
		This method will block until all tasks in the queue are completed.
		"""
		self.taskQueue.put(None)
		self.taskQueue.join()
		self.logger.debug("Worker thread stopped.")

	def enqueueTask(self, task, blocking: bool = False) -> None:
		"""
		Helper to enqueue a task into the worker queue.
		If blocking is True, wait for the task to complete (task_done via worker).
		"""
		self.taskQueue.put(task)
		if blocking:
			self.taskQueue.join()	

	def appendVEnvSuffix(self, envName: str) -> str:
		"""
		Append '_vEnv' to the environment name if it doesn't already end with it.

		Args:
			envName (str): The name of the environment.

		Returns:
			str: The environment name with '_vEnv' suffix if it was not present, 
			otherwise the original name.
		"""
		return envName + "_vEnv" if not envName.endswith("_vEnv") else envName

	def getHighestPyVer(self, condaPath: str) -> str|None:
		"""
		Get the highest Python version folder in the specified conda path.
		Searches for folders matching the pattern 'lib/python*' and returns the highest version found.

		Args:
			condaPath (str): The path to the conda installation.

		Returns:
			str|None: The highest Python version folder name if found, otherwise None.
		"""
		condaPath = pathlib.Path(condaPath)
		pyFolders = list(condaPath.glob('lib/python*'))
		
		# If no Python folders are found, return None
		if not pyFolders:
			return None
		
		# Sort the folders by version (lexicographically) and return the highest one
		highestVersionFolder = max(pyFolders, key=lambda x: x.name.split('python')[-1])
		
		# Extract the version from the folder name
		highestVersion = highestVersionFolder.name.split(os.sep)[-1]
		
		return highestVersion

	def getAutoSetupReqFiles(self) -> list[pathlib.Path]:
		"""
		Get a normalized list of requirements files to install during auto-setup.
		If no list is provided in context, fall back to requirements.txt in CWD if it exists.
		"""
		reqList = self.normalizeReqList(getattr(self, 'autoSetupReqs', []))
		if not reqList:
			defaultReq = pathlib.Path.cwd() / 'requirements.txt'
			return [defaultReq] if defaultReq.exists() else []

		reqFiles = []
		for entry in reqList:
			pathObj = pathlib.Path(entry)
			if not pathObj.is_absolute():
				pathObj = pathlib.Path.cwd() / pathObj
			reqFiles.append(pathObj.resolve())
		return reqFiles

	def installRequirementsForPython(self, pythonPath: pathlib.Path, reqFiles: list[pathlib.Path]) -> None:
		"""
		Install requirements files into the environment using the specified python executable.
		"""
		if not reqFiles:
			return
		if not pythonPath or not pythonPath.exists():
			self.logger.error(f"Python executable not found for requirements install: {pythonPath}")
			return

		for reqFile in reqFiles:
			if not reqFile.exists():
				self.logger.error(f"Requirements file not found: {reqFile}")
				continue
			self.logger.info(f"Installing requirements via {pythonPath}: {reqFile}")
			cmd = [str(pythonPath), '-m', 'pip', 'install', '-r', str(reqFile)]
			self.enqueueTask(cmd, blocking=self.autoSetup)

	def autoSetupEnv(self) -> None:
		"""
		Auto-create an environment when 'autoSetup' is enabled in the context.

		Behavior:
		- If envName is an absolute path, use its last folder name as the envName.
		  For Python vEnv mode, create the vEnv under the current working directory.
		- If mode == 'Conda Env' and conda isn't installed, try to download/install Miniconda first
		  (uses existing downloadConda/installConda methods via the task queue).
		- Create the environment silently using existing createCondaEnv/createPythonEnv methods.
		- If autoSetupReqs is provided in context, install those requirements in order.
		  Otherwise, if requirements.txt exists in CWD, install it into the created env using pip.
		"""
		if not getattr(self, 'autoSetup', False):
			self.logger.debug("Auto-setup disabled; skipping.")
			return

		if not self.envName:
			self.logger.error("autoSetup enabled but no envName provided in context.")
			return

		# If envName is given as a path, derive a usable env name from the last folder
		try:
			envNamePath = pathlib.Path(self.envName)
			if envNamePath.is_absolute():
				derived = envNamePath.name
				self.logger.info(f"envName provided as absolute path. Deriving env name '{derived}' and resetting install target accordingly.")
				self.envName = derived
				# For Python vEnv, create envs relative to CWD per spec
				if self.mode == 'Python vEnv':
					self.installPath = pathlib.Path.cwd()

			# Ensure env name is valid/sanitized
			self.envName = self.validateEnvName(self.envName)
		except Exception as e:
			self.logger.error(f"Failed to derive envName: {e}")
			return

		reqFiles = self.getAutoSetupReqFiles()

		# CONDA flow
		if self.mode == 'Conda Env':
			# Ensure conda install exists (download + install if necessary)
			if not self.verifyConda(self.installPath):
				self.logger.info("Conda not found at installPath; attempting automatic download + install.")
				self.enqueueTask(partial(self.downloadConda), blocking=self.autoSetup)
				self.enqueueTask(partial(self.installConda, self.installPath, False), blocking=self.autoSetup)

			# Create conda env if missing
			if not self.verifyCondaEnv(self.installPath, self.envName):
				useEnvYml = (pathlib.Path.cwd() / 'environment.yml').exists()
				self.logger.info(f"Auto-creating Conda env '{self.envName}' (useEnvYml={useEnvYml}).")
				self.enqueueTask(partial(self.createCondaEnv, self.installPath, self.envName, self.pythonVersion, useEnvYml), blocking=self.autoSetup)

				# If requirements specified, install via pip into the created conda env
				if reqFiles:
					if platform.system() == 'Windows':
						envPython = pathlib.Path(self.installPath) / 'envs' / self.envName / 'python.exe'
					else:
						envPython = pathlib.Path(self.installPath) / 'envs' / self.envName / 'bin' / 'python'
					self.installRequirementsForPython(envPython.resolve(), reqFiles)

			# Link the created environment
			try:
				condaEnvPath = self.getCondaEnvPath(self.envName)
				self.linkEnv(condaEnvPath)
			except Exception as e:
				self.logger.error(f"Failed linking created conda env: {e}")

		# PYthon VENV flow
		elif self.mode == 'Python vEnv':
			# Ensure installPath is set to CWD if not already (per spec)
			if not self.installPath or not pathlib.Path(self.installPath).is_absolute():
				self.installPath = pathlib.Path.cwd()

			venvPath = self.getPythonEnvPath(self.envName)
			createdVenv = False
			if not venvPath.exists():
				self.logger.info(f"Auto-creating Python vEnv '{self.envName}' at '{self.installPath}'.")
				self.enqueueTask(partial(self.createPythonEnv, self.installPath, self.envName, False), blocking=self.autoSetup)
				createdVenv = True

			if createdVenv and reqFiles:
				if platform.system() == 'Windows':
					pythonPath = venvPath / 'Scripts' / 'python.exe'
				else:
					pythonPath = venvPath / 'bin' / 'python'
				self.installRequirementsForPython(pythonPath.resolve(), reqFiles)

			# Link the created venv
			try:
				self.linkEnv(self.getPythonEnvPath(self.envName))
			except Exception as e:
				self.logger.error(f"Failed linking created python venv: {e}")

		else:
			self.logger.error(f"autoSetup: unknown mode '{self.mode}'. Skipping.")
			return

		self.logger.info("Auto-setup flow complete.")

def main(args) -> None:
	"""
	Main function to set up the TDPyEnvManagerHelper.
	Parses command-line arguments and initializes the TDPyEnvManagerHelper instance.	

	Args:
		args (argparse.Namespace): The command-line arguments parsed by argparse.
	"""
	helper = TDPyEnvManagerHelper()
	helper.postInit()
	helper.logger.debug("Starting TDPyEnvManagerHelper...")

	helper.mode = args.mode or input("Enter mode (Conda Env/Python vEnv) [Python vEnv]: ").strip() or "Python vEnv"
	if helper.mode not in ["Conda Env", "Python vEnv"]:
		sys.exit("Invalid mode. Please choose 'Conda Env' or 'Python vEnv'.")

	helper.installPath = pathlib.Path(args.installPath) if args.installPath else pathlib.Path(input("Enter install path: ").strip())
	if not helper.installPath.exists():
		sys.exit(f"Invalid install path: {helper.installPath}")

	helper.envName = args.envName or input("Enter environment name [TDPyEnv]: ").strip() or "TDPyEnv"
	helper.pythonVersion = args.pythonVersion or input(f"Enter Python version [{sys.version_info.major}.{sys.version_info.minor}]: ").strip() or f"{sys.version_info.major}.{sys.version_info.minor}"
	
	clean = args.clean or input("Clean install? [Y/N]: ").strip() == 'Y'
	clean = True if clean == 'Y' or clean else False
	
	contextPath = pathlib.Path.cwd() / 'TDPyEnvManagerContext.yaml'

	if helper.mode == 'Conda Env':
		keepInstaller = args.keepInstaller or input("Keep installer? [Y/N]: ").strip() == 'Y'
		keepInstaller = True if keepInstaller == 'Y' or keepInstaller else False
	else:
		keepInstaller = False

	if helper.mode == 'Conda Env':
		if clean: 
			helper.cleanDirectory(helper.installPath)
		
		if not helper.verifyConda(helper.installPath):
			helper.taskQueue.put(helper.downloadConda)
			helper.taskQueue.join()
			helper.logger.debug("Conda downloaded successfully.")

		if not helper.verifyCondaLib(helper.installPath):
			helper.taskQueue.put(partial(helper.installConda, helper.installPath, keepInstaller))
			helper.taskQueue.join()
			helper.WriteContextToFile(contextPath)
			helper.createCondaRc(helper.installPath)
			helper.logger.debug("Conda installed successfully.")
			helper.createGitIgnore(helper.installPath)

		if not helper.verifyCondaEnv(helper.installPath, helper.envName):
			helper.taskQueue.put(partial(helper.createCondaEnv, helper.installPath, helper.envName, helper.pythonVersion))
			helper.taskQueue.join()
			helper.logger.debug("Conda environment created successfully.")
		
		helper.activateCondaEnv(helper.installPath, helper.envName)

	elif helper.mode == 'Python vEnv':
		if not helper.verifyPython(helper.installPath):
			helper.taskQueue.put(partial(helper.createPythonEnv, helper.installPath, helper.envName, True))
			helper.taskQueue.join()
			helper.WriteContextToFile(contextPath)
			helper.logger.debug("Python virtual environment created successfully.")
			helper.createGitIgnore(helper.getPythonEnvPath(helper.envName))

		helper.activatePythonEnv(helper.envName)

	else:
		sys.exit("Invalid mode")


if __name__ == "__main__":
	"""
	Main entry point for the script.
	Parses command-line arguments and calls the main function to set up the TDPyEnvManagerHelper.
	"""
	parser = argparse.ArgumentParser(description="Setup the TD Python Environment Manager")
	
	parser.add_argument(
		"--mode",
		default="Python vEnv",
		choices=["Conda Env", "Python vEnv"],
		help="The mode in which the environment should be set up"
	)
	parser.add_argument(
		"--installPath",
		default=str(pathlib.Path.cwd()),
		help="The path where Miniconda or Python Virtual Environment should be created"
	)
	parser.add_argument(
		"--envName",
		default="TDPyEnv",
		help="The name of the Conda or Python Virtual Environment"
	)
	parser.add_argument(
		"--pythonVersion",
		default=f"{sys.version_info.major}.{sys.version_info.minor}",
		help="The version of Python to be installed"
	)
	parser.add_argument(
		"--clean",
		action="store_true",
		default=False,
		help="Clean the install directory before installing"
	)
	parser.add_argument(
		"--keepInstaller",
		action="store_true",
		default=False,
		help="Clean installer after install or if install failed."
	)	
	args = parser.parse_args()
	main(args)
