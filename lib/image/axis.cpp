/*
    Copyright 2008 Brain Research Institute, Melbourne, Australia

    Written by J-Donald Tournier, 27/06/08.

    This file is part of MRtrix.

    MRtrix is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    MRtrix is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with MRtrix.  If not, see <http://www.gnu.org/licenses/>.

*/

#include "app.h"
#include "image/axis.h"

namespace MR {
  namespace Image {

    const std::string Axes::axes_name ("anonymous axes");
    const char* Axes::left_to_right = "left->right";
    const char* Axes::posterior_to_anterior = "posterior->anterior";
    const char* Axes::inferior_to_superior = "inferior->superior";
    const char* Axes::time = "time";
    const char* Axes::real_imag = "real-imaginary";
    const char* Axes::millimeters = "mm";
    const char* Axes::milliseconds = "ms";





    std::vector<ssize_t> Axes::parse (size_t ndim, const std::string& specifier)
    {
      std::vector<ssize_t> parsed (ndim);

      size_t str = 0;
      size_t lim = 0;
      size_t end = specifier.size();
      size_t current = 0;

      try {
        while (str <= end) {
          bool pos = true;
          if (specifier[str] == '+') { pos = true; str++; }
          else if (specifier[str] == '-') { pos = false; str++; }
          else if (!isdigit (specifier[str])) throw 0;

          lim = str;

          while (isdigit (specifier[lim])) lim++;
          if (specifier[lim] != ',' && specifier[lim] != '\0') throw 0;
          parsed[current] = to<ssize_t> (specifier.substr (str, lim-str)) + 1;
          if (!pos) parsed[current] = -parsed[current];

          str = lim+1;
          current++;
        }
      }
      catch (int) { throw Exception ("malformed axes specification \"" + specifier + "\""); }

      if (current != ndim) 
        throw Exception ("incorrect number of axes in axes specification \"" + specifier + "\"");

      check (parsed, ndim);

      return (parsed);
    }







    void Axes::check (const std::vector<ssize_t>& parsed, size_t ndim)
    {
      if (parsed.size() != ndim) 
        throw Exception ("incorrect number of dimensions for axes specifier");
      for (size_t n = 0; n < parsed.size(); n++) {
        if (!parsed[n] || size_t(abs(parsed[n])) > ndim) 
          throw Exception ("axis ordering " + str (parsed[n]) + " out of range");

        for (size_t i = 0; i < n; i++) 
          if (abs(parsed[i]) == abs(parsed[n])) 
            throw Exception ("duplicate axis ordering (" + str (abs(parsed[n])) + ")");
      }
    }










    std::ostream& operator<< (std::ostream& stream, const Axes& axes)
    {
      stream << "dim [ ";
      for (size_t n = 0; n < axes.ndim(); n++) stream << axes.dim(n) << " ";
      stream << "], vox [ ";
      for (size_t n = 0; n < axes.ndim(); n++) stream << axes.vox(n) << " ";
      stream << "], stride [ ";
      for (size_t n = 0; n < axes.ndim(); n++) stream << std::showpos << axes.stride(n) << " ";
      stream << "], desc [ ";
      for (size_t n = 0; n < axes.ndim(); n++) stream << "\n" << axes.description(n) << "\" ";
      stream << "], units [ ";
      for (size_t n = 0; n < axes.ndim(); n++) stream << "\n" << axes.units(n) << "\" ";

      return (stream);
    }




  }
}

