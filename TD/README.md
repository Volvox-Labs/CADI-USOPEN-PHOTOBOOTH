# Touchdesigner Project Template
A Touchdesigner project template using the following vvox python tools
- [vvox-tdtools](https://github.com/Volvox-Labs/vvox-tdtools)
- [td-config](https://github.com/Volvox-Labs/tdconfig)

## Template Instructions
If you are creating this project from a template, please follow the instructions below

- Rename the ```.toe``` file to represent your project
- In the ```start.bat``` script, update the ```set TOEFILE``` line with the name of your new project ```.toe``` file.
- Update the title and description of this ```README.md```
- Remove this section from the ```README.md``` file

## Prerequisits

This repo relies on python packages that are only accessible to members of the Volvox-Labs Github organization. Make sure you are signed into github in git on CMD.exe. If you're on a new machine, you can test by either cloning a Volvox-Labs repo via CMD or checking for Github.com credentials in the Windows "Credential Manager"

- git 2.27+
- Touchdesigner 2023.11760
- Python 3.11

## Install

### 1. Windows dependencies
- Install Chocolatey: [instructions](https://chocolatey.org/install)
- Using an admin Powershell terminal ```cd``` to this repo and run ```choco install .\packages.config``` to install all windows dependencies.
- Look in the ```start.bat``` file for the required version of Touchdesigner. Then [download](https://derivative.ca/download) and install.

### 2. Setup the .env file
- copy the ```.env.sample``` file, rename it ```.env```
- edit the .env file and replace the example values

### 3. Install python dependencies
- It may be helpful to log into github on you machine before installing python dependencies. The install-deps.cmd script will ask you to authenticate with Github in order to install vvox-tdtools.
- Run the install-deps.cmd script in the project root. The install-deps script will run automatically the first time the start.bat script is run but it is a good practice to run it on it's own in case there are any errors while installing dependencies.

### 4. Create the assets folder
- Only follow this step if you need your assets to be located outside of the project directory (on another drive for example)
- Create this folder and populate with assets if it does not exist
- Edit the ```ASSETS_PATH``` environment varialbe in the ```.env``` file with the path to your assets folder

### 5. Set configuration settings
- The ```config.yaml``` file is located in the config folder
- Set the ```RESX``` and ```RESY``` variables with your output resolution
- Set ```headless``` to True if this project does not require a main output window. This will only display the status view window in performance mode.

## Keyboard Shortcuts
- Ctrl+Shift+F = Open/Close Status View
- Ctrl+Shift+Alt+F = Open/Close Main window as a seperate window