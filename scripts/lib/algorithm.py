_algorithm_list = [ ]
_base_module = None


# If the MRtrix3 code repository has been cloned, the files corresponding to different algorithms accessible for a particular
#   script are found in a sub-directory of scripts/src/, with that sub-directory named after the script. Additionally, new
#   files can be added to this sub-directory, and will be made available from the main script and appear in the help page.
# If MRtrix3 is installed from a package, then the script will auto-extract based on the instructions given to PyInstaller,
#   and the relevant algorithm files will instead be found in the temporary directory generated by the extractor, in a
#   sub-directory named after the script.


# This function needs to be safe to run in order to populate the help page; that is, no app initialisation has been run
def getList():
  import os, sys
  import lib.message
  import lib.package
  global _algorithm_list
  _algorithm_list = [ ]
  src_file_list = os.listdir(lib.package.algorithmsPath())
  for filename in src_file_list:
    filename = filename.split('.')
    if len(filename) == 2 and filename[1] == 'py' and not filename[0] == '__init__':
      _algorithm_list.append(filename[0])
  _algorithm_list = sorted(_algorithm_list)
  lib.message.debug('Found algorithms: ' + str(_algorithm_list))
  return _algorithm_list



def initialise(base_parser, subparsers):
  import os, pkgutil, sys
  import lib.message
  import lib.package
  global _algorithm_list, _base_module
  initlist = [ ]
  if lib.package.isPackaged():
    _base_module = __import__(scriptname)
    if not _algorithm_list:
      getList()
    for package_name in _algorithm_list:
      __import__(scriptname, globals(), locals(), [ package_name ])
      module = getattr(_base_module, package_name)
      module.initParser(subparsers, base_parser)
      initlist.extend(package_name)
  else:
    for importer, package_name, ispkg in pkgutil.iter_modules( [ lib.package.algorithmsPath() ] ):
      loader = importer.find_loader(package_name)
      module = loader[0].load_module(package_name)
      module.initParser(subparsers, base_parser)
      initlist.extend(package_name)
  lib.message.debug('Initialised algorithms: ' + str(initlist))
  



def getModule(name):
  import pkgutil, sys
  import lib.app
  import lib.package
  if lib.package.isPackaged():
    return getattr(_base_module, lib.app.args.algorithm)
  else:
    # TODO Is this causing a double module load?
    return pkgutil.find_loader(name).load_module()


