from os import listdir
from os.path import join as join_path
from os.path import exists as path_exists
from os.path import isdir
from json import loads as load_json

from importlib.util import spec_from_file_location as module_spec
from importlib.util import module_from_spec

from zipfile import ZipFile
from shutil import rmtree

APP_DIRECTORY = __file__.replace("\\", "/")[:-11]

def app_dir(package_name):
    """Returns the local directory for a package."""
    return join_path(APP_DIRECTORY, package_name)

class Manifest(object):
    def __init__(self, package_name):
        """
        A Manifest gives information about an installed package.
        If manifest.json exists in the package directoy, information is loaded from here.
        Manifest entries:
        - package: The package name.
        - main: The Python file to run (local to app directory). Defaults to __init__.py.
        - name: The human-readable app name.
        - version: The application version.
        - author: Authorship credits.
        - dependencies: List of packages that this one depends on.
        - library: Boolean whether the package is a library package (not to be launched as an app).
        """
        if not path_exists(app_dir(package_name)):
            raise ValueError("The package " + str(package_name) + " is not installed.")
        self.package = package_name
        if path_exists(join_path(APP_DIRECTORY, self.package, "__init__.py")):
            self.main = join_path(APP_DIRECTORY, self.package, "__init__.py")
        else:
            self.main = None
        self.name = self.package
        self.version = 0
        self.author = ""
        self.dependencies = []
        self.library = True
        self.directory = app_dir(self.package)
        if path_exists(join_path(APP_DIRECTORY, self.package, "manifest.json")):
            self._load_json()
        
    def _load_json(self):
        f = open(join_path(APP_DIRECTORY, self.package, "manifest.json"), "rb")
        for key, value in dict(load_json(f.read())).items():
            setattr(self, key, value)
        f.close()
        
    def get(self, key: str, default=None):
        if hasattr(self, key):
            return getattr(self, key)
        else:
            return default

def get_packages():
    """Returns a list of installed packages."""
    packages = []
    for item in listdir(APP_DIRECTORY):
        if isdir(app_dir(item)):
            packages.append(item)
            
def import_library(package_name: str):
    """Returns the module provided by the library."""
    info = Manifest(package_name)
    if not info.library:
        raise ValueError("The specified package is not a library.")
    spec = module_spec(package_name, join_path(APP_DIRECTORY, package_name, info.main))
    lib = module_from_spec(spec)
    spec.loader.exec_module(lib)
    return lib

def is_needed(package_name: str):
    """Returns True if the specified package is depended on by another installed one."""
    deps = []
    for pkg in get_packages():
        for dep in Manifest(pkg).dependencies:
            if dep not in deps:
                deps.append(dep)
    return package_name in deps

def install(filepath: str):
    """
    Install an package from a Zip file.
    A vaild Polaron app installer contains a single directory with the package name.
    Returns the list of dependencies for the newly installed app.
    """
    if not path_exists(filepath):
        raise ValueError("The specified path", filepath, "is not valid.")
    zf = ZipFile(filepath)
    if len(zf.namelist()) > 1:
        zf.close()
        raise ValueError("The specified file does not contain a Polaron app.")
    pkg = zf.namelist()[0]
    zf.extractall(APP_DIRECTORY)
    zf.close()
    return Manifest(pkg).dependencies

def uninstall(package_name: str):
    """Uninstalls the specified package."""
    if path_exists(app_dir(package_name)):
        if is_needed(package_name):
            raise ValueError("The package", package_name, "is depended on by another.")
        rmtree(app_dir(package_name), ignore_errors=True)