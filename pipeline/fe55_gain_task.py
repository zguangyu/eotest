"""
@brief Compute the system gains for each segment in a CCD from Fe55
exposures.  The median gain value from among the input files is
identified as the system gain for that segment and written to the db
tables.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
import os
import sys
import glob

import lsst.afw.math as afwMath
import image_utils as imUtils
import pipeline.pipeline_utils as pipeUtils
from database.SensorDb import SensorDb, NullDbObject

from xray_gain import hdu_gains

median = lambda x : afwMath.makeStatistics(x, afwMath.MEDIAN).getValue()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        pattern = sys.argv[1].replace('\\', '')
        target = os.path.join(pattern)
        Fe55_files = glob.glob(target)
        Fe55_files.sort()
    else:
        try:
            sensor_id = os.environ['SENSOR_ID']
            Fe55_files = pipeUtils.get_file_list('FE55', sensor_id)
        except:
            print "usage: python fe55_gain_task.py <Fe55 file pattern>"
            sys.exit(1)

    try:
        sensor_id = os.environ['SENSOR_ID']
        vendor = os.environ['CCD_VENDOR']
        sensorDb = SensorDb(os.environ["DB_CREDENTIALS"])
        sensor = sensorDb.getSensor(vendor, sensor_id, add=True)
    except KeyError:
        sensor = NullDbObject()

    gain_dists = dict([(amp, []) for amp in imUtils.allAmps])
    for fe55 in Fe55_files:
        print "processing", fe55
        gains = hdu_gains(fe55)
        for amp in imUtils.allAmps:
            gain_dists[amp].append(gains[amp])
    seg_gains = [imUtils.median(gain_dists[amp]) for amp in imUtils.allAmps]
    
    sensor.add_ccd_result('gainMedian', imUtils.median(seg_gains))
    print "Median gain among segments:", imUtils.median(seg_gains)
    print "Segment    gain"
    for amp in imUtils.allAmps:
        sensor.add_seg_result(amp, 'gain', seg_gains[amp-1])
        print "%s         %.4f" % (imUtils.channelIds[amp], seg_gains[amp-1])
