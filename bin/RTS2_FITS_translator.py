#!/usr/bin/env python
"""
@brief Translator application to convert RTS2 sensor FITS image files to 
conforming FITS files for analysis by the eotest package.
"""
import os
import numpy as np
import pyfits
import lsst.eotest.image_utils as imutils
import lsst.eotest.sensor as sensorTest

class RTS2_FITS_translator(object):
    def __init__(self, luts, geom, verbose=True):
        self.luts = luts
        self.verbose = verbose
        amp_loc = sensorTest.amp_loc[geom['vendor']]
        self.geom = sensorTest.AmplifierGeometry(prescan=geom['prescan'],
                                                 nx=geom['nx'], ny=geom['ny'],
                                                 detxsize=geom['detsize'][0],
                                                 detysize=geom['detsize'][1],
                                                 amp_loc=amp_loc)
    def __call__(self, infile, outfile, clobber=True):
        if self.verbose:
            print "processing", infile
        self.input = pyfits.open(infile)
        self.output = pyfits.open(infile)
        prototypes = sensorTest.fits_headers.fits_headers()

        # Primary HDU
        self.output[0].header.set('MJD', self.output[0].header['JD']-2400000.5)
        self._update_keywords(0)

        # TEST_COND and CCD_COND extensions
        self._update_extension('TEST_COND', prototypes['TEST_COND'])
        self._update_extension('CCD_COND', prototypes['CCD_COND'])

        # Image extensions
        self._update_amp_keywords()

        # Special handling for monitoring diode current in BNL data.
        try:
            self.luts[0]['MONDIODE']
        except KeyError:
            self._set_bnl_mondiode_keyword_value()

        self.output.writeto(outfile, clobber=clobber, checksum=True)
    def _update_keywords(self, ext):
        unresolved_keywords = []
        for key, source in self.luts[ext].items():
            try:
                value = self.input[0].header[source]
            except KeyError:
                unresolved_keywords.append(source)
                value = '' # write an empty string for the missing value
            self.output[ext].header.set(key, value)
        if unresolved_keywords and self.verbose:
            sys.stdout.write("HDU %s: " % ext)
            print "unresolved keywords in source primary hdu:"
            for item in unresolved_keywords:
                print "  %s" % item
    def _update_extension(self, extname, prototype):
        try:
            self.output[extname]
        except KeyError:
            # No header by that name, so add it along with required keys.
            self.output.append(pyfits.new_table([pyfits.Column(format='I',
                                                               name='DUMMY')]))
            self.output[-1].name = extname
            for keyword in prototype:
                self.output[-1].header.set(keyword, prototype[keyword])

        # Set the values from the primary hdu.
        self._update_keywords(extname)
    def _update_amp_keywords(self):
        self.output[0].header.set('DETSIZE', self.geom.DETSIZE)
        for amp in imutils.allAmps:
            self.output[amp].header.set('EXTNAME', imutils.hdu_dict[amp])
            for key in self.geom[amp].keys():
                self.output[amp].header.set(key, self.geom[amp][key])
    def _set_bnl_mondiode_keyword_value(self):
        try:
            self.input['AMP0.MEAS_TIMES']
        except KeyError:
            # Extension does not exist so assume this is not a flat and
            # set to empty string.
            self.output[0].header.set('MONDIODE', '')
            return
        mean, stdev = self._bnl_monodiode_current()
        self.output[0].header.set('MONDIODE', mean)
    def _bnl_monodiode_current(self):
        data = self.input['AMP0.MEAS_TIMES'].data
        y_pA, x_t = data.field(1), data.field(0)
        # The following code has been lifted directly from JohnK's
        # xlatfits.py script at http://git.kuzew.net/lsst/xlatfits.git/
        i = 0;
        cpnts = [];
        downflg = 0;
        upflg   = 0;

        #normalize data
        norm = y_pA/np.max(np.abs(y_pA));

        while (i < len(norm) - 2):
        #check thresholds 
            if (norm[i] <= -0.8 and downflg == 0):
                #make sure it's trending properly
                if (np.sum(np.diff(y_pA[i-2:i+2])) < 0.0):
                    downflg = 1;
                    #print "Found transition at t=", x_t[i],  y_pA[i], i
                    cpnts.append(i);
            elif (norm[i] >= -0.8 and upflg == 0 and downflg == 1):
                if (np.sum(np.diff(y_pA[i-2:i+2])) > 0.0):
                    upflg = 1;
                    #print "Found transition at t=", x_t[i],  y_pA[i], i 
                    cpnts.append(i);
                    break;
            i += 1;

        if (len(cpnts) > 0):
            x1 = cpnts[0];
            if (upflg == 0):
                x2 = len(y_pA) - 1;
            else:
                x2 = cpnts[len(cpnts)-1];

            return (np.mean(y_pA[x1:x2]), np.std(y_pA[x1:x2]))
#        else:
#            return -1, -1
        raise RuntimeError("Could not compute monitoring photodiode current")

if __name__ == '__main__':
    import sys
    import glob
    import argparse

    sys.path.append(os.path.join(os.environ['EOTEST_DIR'], 'policy'))
    from RTS2_FITS_LUTs import *

    parser = argparse.ArgumentParser(description='RTS2 FITS file translator')
    parser.add_argument('inputs', help="File pattern for input files")
    parser.add_argument('-o', '--output_dir', type=str, default='.',
                        help='output directory')
    parser.add_argument('-s', '--sensor_id', type=str, help='sensor id')
    parser.add_argument('-V', '--vendor', type=str, default='E2V',
                        help='Vendor (E2V or ITL)')
    parser.add_argument('-l', '--lab', type=str, default='BNL',
                        help='lab (BNL or Harvard)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        default=False, help='verbosity flag')
    
    args = parser.parse_args()

    if args.lab == 'BNL':
        lookup_tables = BNL_FITS_LUTs
    else:
        raise RuntimeError("Only BNL supported so far")

    e2v_translator = RTS2_FITS_translator(lookup_tables,
                                          RTS2_geom[args.vendor],
                                          verbose=args.verbose)
    infiles = glob.glob(args.inputs)
    for infile in infiles:
        outfile = os.path.join(args.output_dir, os.path.basename(infile))
        e2v_translator(infile, outfile)