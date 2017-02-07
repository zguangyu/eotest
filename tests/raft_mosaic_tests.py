"""
Test code for raft-level mosaicking code.
"""
from __future__ import absolute_import, print_function
import os
import glob
from collections import OrderedDict
import unittest
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import astropy.io.fits as fits
import lsst.eotest.raft as raftTest

class RaftMosaicTestCase(unittest.TestCase):
    "Test case class for raft_image_mosaic module."
    def setUp(self):
        self.outfile = 'raft_test_pattern.png'

    def tearDown(self):
        try:
            os.remove(self.outfile)
        except OSError:
            pass

    def test_raft_image_mosaic(self):
        """
        Test of raft-level mosaicking code.
        """
        root_dir = '/nfs/farm/g/lsst/u1/jobHarness/jh_archive-test/LCA-10753_RSA/LCA-10753_RSA-003_ETU1-Dev/4578D/qe_raft_acq_sim/v0/25597'
        infiles = sorted(glob.glob(os.path.join(root_dir, 'S??',
                                                '*_lambda_flat_1000_*.fits')))
        infiles = OrderedDict([(filename.split('/')[-2], filename)
                               for filename in infiles])
        test_files = dict()
        step = 100
        level = step
        for slot, infile in infiles.items():
            outfile = '%s_test_image_%05i.fits' % (slot, level)
            hdu_list = fits.open(infile)
            for hdu in hdu_list[1:17]:
                hdu.data = np.ones(hdu.data.shape, dtype=np.float32)*level
                level += step
            hdu_list.writeto(outfile, clobber=True)
            test_files[slot] = outfile

        raft_mosaic = raftTest.RaftMosaic(test_files, bias_subtract=False)
        raft_mosaic.plot(title='Test pattern')
        plt.savefig(self.outfile)

if __name__ == '__main__':
    unittest.main()
