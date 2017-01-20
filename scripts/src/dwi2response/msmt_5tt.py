def initParser(subparsers, base_parser):
  import argparse
  import lib.app
  lib.app.addCitation('If using \'msmt_csd\' algorithm', 'Jeurissen, B.; Tournier, J.-D.; Dhollander, T.; Connelly, A. & Sijbers, J. Multi-tissue constrained spherical deconvolution for improved analysis of multi-shell diffusion MRI data. NeuroImage, 2014, 103, 411-426', False)
  parser = subparsers.add_parser('msmt_5tt', parents=[base_parser], add_help=False, description='Derive MSMT-CSD tissue response functions based on a co-registered five-tissue-type (5TT) image')
  parser.add_argument('input', help='The input DWI')
  parser.add_argument('in_5tt', help='Input co-registered 5TT image')
  parser.add_argument('out_wm', help='Output WM response text file')
  parser.add_argument('out_gm', help='Output GM response text file')
  parser.add_argument('out_csf', help='Output CSF response text file')
  options = parser.add_argument_group('Options specific to the \'msmt_5tt\' algorithm')
  options.add_argument('-dirs', help='Manually provide the fibre direction in each voxel (a tensor fit will be used otherwise)')
  options.add_argument('-fa', type=float, default=0.2, help='Upper fractional anisotropy threshold for GM and CSF voxel selection')
  options.add_argument('-pvf', type=float, default=0.95, help='Partial volume fraction threshold for tissue voxel selection')
  options.add_argument('-wm_algo', metavar='algorithm', default='tournier', help='dwi2response algorithm to use for WM single-fibre voxel selection')
  parser.set_defaults(algorithm='msmt_5tt')
  
  
  
def checkOutputFiles():
  import lib.app
  lib.app.checkOutputFile(lib.app.args.out_wm)
  lib.app.checkOutputFile(lib.app.args.out_gm)
  lib.app.checkOutputFile(lib.app.args.out_csf)



def getInputFiles():
  import os
  import lib.app
  import lib.path
  from lib.runCommand import runCommand
  runCommand('mrconvert ' + lib.path.fromUser(lib.app.args.in_5tt, True) + ' ' + os.path.join(lib.app.tempDir, '5tt.mif'))
  if lib.app.args.dirs:
    runCommand('mrconvert ' + lib.path.fromUser(lib.app.args.dirs, True) + ' ' + os.path.join(lib.app.tempDir, 'dirs.mif') + ' -stride 0,0,0,1')



def execute():
  import math, os, shutil
  import lib.app
  import lib.image
  import lib.message
  import lib.path
  from lib.runCommand  import runCommand
  from lib.runFunction import runFunction
  
  # Ideally want to use the oversampling-based regridding of the 5TT image from the SIFT model, not mrtransform
  # May need to commit 5ttregrid...

  # Verify input 5tt image
  runCommand('5ttcheck 5tt.mif')

  # Get shell information
  shells = [ int(round(float(x))) for x in lib.image.headerField('dwi.mif', 'shells').split() ]
  if len(shells) < 3:
    lib.message.warn('Less than three b-value shells; response functions will not be applicable in MSMT-CSD algorithm')

  # Get lmax information (if provided)
  wm_lmax = [ ]
  if lib.app.args.lmax:
    wm_lmax = [ int(x.strip()) for x in lib.app.args.lmax.split(',') ]
    if not len(wm_lmax) == len(shells):
      lib.message.error('Number of manually-defined lmax\'s (' + str(len(wm_lmax)) + ') does not match number of b-value shells (' + str(len(shells)) + ')')
    for l in wm_lmax:
      if l%2:
        lib.message.error('Values for lmax must be even')
      if l<0:
        lib.message.error('Values for lmax must be non-negative')

  runCommand('dwi2tensor dwi.mif - -mask mask.mif | tensor2metric - -fa fa.mif -vector vector.mif')
  if not os.path.exists('dirs.mif'):
    runFunction(shutil.copy, 'vector.mif', 'dirs.mif')
  runCommand('mrtransform 5tt.mif 5tt_regrid.mif -template fa.mif -interp linear')

  # Basic tissue masks
  runCommand('mrconvert 5tt_regrid.mif - -coord 3 2 -axes 0,1,2 | mrcalc - ' + str(lib.app.args.pvf) + ' -gt mask.mif -mult wm_mask.mif')
  runCommand('mrconvert 5tt_regrid.mif - -coord 3 0 -axes 0,1,2 | mrcalc - ' + str(lib.app.args.pvf) + ' -gt fa.mif ' + str(lib.app.args.fa) + ' -lt -mult mask.mif -mult gm_mask.mif')
  runCommand('mrconvert 5tt_regrid.mif - -coord 3 3 -axes 0,1,2 | mrcalc - ' + str(lib.app.args.pvf) + ' -gt fa.mif ' + str(lib.app.args.fa) + ' -lt -mult mask.mif -mult csf_mask.mif')

  # Revise WM mask to only include single-fibre voxels
  lib.message.print('Calling dwi2response recursively to select WM single-fibre voxels using \'' + lib.app.args.wm_algo + '\' algorithm')
  recursive_cleanup_option=''
  if not lib.app.cleanup:
    recursive_cleanup_option = ' -nocleanup'
  runCommand('dwi2response ' + lib.app.args.wm_algo + ' dwi.mif wm_ss_response.txt -mask wm_mask.mif -voxels wm_sf_mask.mif -quiet -tempdir ' + lib.app.tempDir + recursive_cleanup_option)

  # Check for empty masks
  wm_voxels  = int(lib.image.statistic('wm_sf_mask.mif', 'count', 'wm_sf_mask.mif'))
  gm_voxels  = int(lib.image.statistic('gm_mask.mif',    'count', 'gm_mask.mif'))
  csf_voxels = int(lib.image.statistic('csf_mask.mif',   'count', 'csf_mask.mif'))
  empty_masks = [ ]
  if not wm_voxels:
    empty_masks.append('WM')
  if not gm_voxels:
    empty_masks.append('GM')
  if not csf_voxels:
    empty_masks.append('CSF')
  if empty_masks:
    message = ','.join(empty_masks)
    message += ' tissue mask'
    if len(empty_masks) > 1:
      message += 's'
    message += ' empty; cannot estimate response function'
    if len(empty_masks) > 1:
      message += 's'
    lib.message.error(message)

  # For each of the three tissues, generate a multi-shell response
  bvalues_option = ' -shell ' + ','.join(map(str,shells))
  sfwm_lmax_option = ''
  if wm_lmax:
    sfwm_lmax_option = ' -lmax ' + ','.join(map(str,wm_lmax))
  runCommand('amp2response dwi.mif wm_sf_mask.mif dirs.mif wm.txt' + bvalues_option + sfwm_lmax_option)
  runCommand('amp2response dwi.mif gm_mask.mif dirs.mif gm.txt' + bvalues_option + ' -isotropic')
  runCommand('amp2response dwi.mif csf_mask.mif dirs.mif csf.txt' + bvalues_option + ' -isotropic')
  runFunction(shutil.copyfile, 'wm.txt',  lib.path.fromUser(lib.app.args.out_wm,  False))
  runFunction(shutil.copyfile, 'gm.txt',  lib.path.fromUser(lib.app.args.out_gm,  False))
  runFunction(shutil.copyfile, 'csf.txt', lib.path.fromUser(lib.app.args.out_csf, False))

  # Generate output 4D binary image with voxel selections; RGB as in MSMT-CSD paper
  runCommand('mrcat csf_mask.mif gm_mask.mif wm_sf_mask.mif voxels.mif -axis 3')

