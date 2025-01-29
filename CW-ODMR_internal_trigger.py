    import os
import time
from pyAndorSDK2 import atmcd, atmcd_codes, atmcd_errors
import platform
import sys
here = os.path.abspath(os.path.dirname(__file__))
_package_name = 'pyAndorSDK2'
def get_platform_name():
    return platform.system()


def get_max_bits():
    if (sys.maxsize > 2 ** 32):
        return '64'
    else:
        return '32'
source_lib_path = os.path.join(here, _package_name, 'libs', get_platform_name(), get_max_bits())

sdk = atmcd(source_lib_path)
codes = atmcd_codes
ret = sdk.Initialize("")  # Initialize camera
print("Function Initialize returned {}".format(ret))

if atmcd_errors.Error_Codes.DRV_SUCCESS == ret:
    NUMKIN = 3020

    ret = sdk.SetTemperature(-70)
    print("Function SetTemperature returned {} target temperature -70".format(ret))

    ret = sdk.CoolerON()
    print("Function CoolerOn returned {}".format(ret))
    (ret, temperature) = sdk.GetTemperature()
    print("Function GetTemperature returned {} current temperature = {}".format(
        ret, temperature))
    if temperature+70 > 0:
        while ret != atmcd_errors.Error_Codes.DRV_TEMP_STABILIZED:
            time.sleep(5)
            (ret, temperature) = sdk.GetTemperature()
            print("Function GetTemperature returned {} current temperature = {}".format(
                ret, temperature))

    ret = sdk.SetCoolerMode(1)
    print("Function SetCoolerMode returned {} ".format(ret))

    print("")
    print("Temperature stabilized")

    ret = sdk.SetAcquisitionMode(codes.Acquisition_Mode.KINETICS)
    print("Function SetAcquisitionMode returned {} mode = Kinetics".format(ret))

    ret = sdk.SetKineticCycleTime(0)
    print("Function SetKineticCycleTime returned {} cycle time = 0.5 seconds".format(ret))

    ret = sdk.SetNumberKinetics(NUMKIN)
    print("Function SetNumberKinetics returned {}".format(ret))

    ret = sdk.SetExposureTime(0.035)
    print("Function SetExposureTime returned {} time = 0.5s".format(ret))

    ret = sdk.SetTriggerMode(codes.Trigger_Mode.INTERNAL)
    print("Function SetTriggerMode returned {} mode = Software trigger".format(ret))

    ret = sdk.SetReadMode(codes.Read_Mode.IMAGE)
    print("Function SetReadMode returned {} mode = Image".format(ret))

    ret = sdk.SetPreAmpGain(2)
    print("FUnction SetPreAmpGain returned {} preampgain = 1".format(ret))
    ret = sdk.SetEMGainMode(3)
    print("Function SetEmGainMode returned {} Mode = 1".format(ret))

    ret = sdk.SetEMCCDGain(300)
    print("Function SetEMCCDGain returned {} Gain = 300".format(ret))

    ret = sdk.SetHSSpeed(0, 0)
    print("Function SetHSSpeed returned {} HSS set to 17MHz".format(ret))

    (ret, fminExposure, fAccumulate, fKinetic) = sdk.GetAcquisitionTimings()
    print("Function GetAcquisitionTimings returned {} exposure = {} accumulate = {} kinetic = {}".format(ret, fminExposure, fAccumulate, fKinetic))

    ret = sdk.SetShutter(0, 1, 0, 0)
    print("Function SetShutter returned {} shutter is always open".format(ret))

    directory = f'C:\\Users\\LAB-A1-10\\Desktop\\Setup\\Orlando\\Images\\cw_Internal'

    filename = "{}-{}".format(directory, time.strftime("%Y-%m-%d-%H-%M"))
    ret = sdk.SetSpool(1, codes.Spool_Mode.SPOOL_TO_16_BIT_FITS, filename, 10)
    print("Function SetSpool returned {} ".format(ret))

    (ret, xpixels, ypixels) = sdk.GetDetector()
    print("Function GetDetector returned {} xpixels = {} ypixels = {}".format(
        ret, xpixels, ypixels))

    ret = sdk.SetImage(1, 1, 1, xpixels, 1, ypixels)
    print("Function SetImage returned {} hbin = 1 vbin = 1 hstart = 1 hend = {} vstart = 1 vend = {}".format(
        ret, xpixels, ypixels))

    ret = sdk.PrepareAcquisition()
    print("Function PrepareAcquisition returned {}".format(ret))
    time.sleep(5)
    ret = sdk.StartAcquisition()
    print("Function StartAcquisition returned {} ".format(ret))

    index = 0
    while index < NUMKIN:
        (ret, index) = sdk.GetTotalNumberImagesAcquired()
        print("Function current count {} ".format(index), end="\r")
    print("")
    # Clean up
    ret = sdk.ShutDown()
    print("Function Shutdown returned {}".format(ret))

else:
    print("Cannot continue, could not initialise camera")
