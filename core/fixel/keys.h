/*
 * Copyright (c) 2008-2018 the MRtrix3 contributors.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, you can obtain one at http://mozilla.org/MPL/2.0/
 *
 * MRtrix3 is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty
 * of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 *
 * For more details, see http://www.mrtrix.org/
 */


#ifndef __fixel_keys_h__
#define __fixel_keys_h__

#include <string>

namespace MR
{
  namespace Fixel
  {
    const std::string n_fixels_key ("nfixels");
    const std::initializer_list <const std::string> supported_sparse_formats { ".mif", ".nii", ".mif.gz" , ".nii.gz" };
  }
}

#endif
