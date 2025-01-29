from spinapi import *
import os
from pyAndorSDK2 import atmcd, atmcd_codes, atmcd_errors
import platform
import sys
import time


OFF = int(0b111000000000000000001100) # all off
ON = int(0b111000000000000000001111)
AOM = int(0b111000000000000000001000)
CAM = int(0b111000000000000000000001)
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

clock_freq = 500  # The value of your clock oscillator in MHz

NUMKIN = 4510#number of images to be taken
def detect_boards():
    global numBoards

    numBoards = pb_count_boards()

    if numBoards <= 0:
        print("No Boards were detected in your system. Verify that the board "
              "is firmly secured in the PCI slot.\n")

        exit(-1)


def select_boards():
    while True:
        try:
            choice = int(
                input(f"Found {numBoards} boards in your system. Which board should be used? (0-{numBoards - 1}): "))
            if choice < 0 or choice >= numBoards:
                print("Invalid Board Number (%d)." % choice)
            else:
                pb_select_board(choice)
                print("Board %d selected." % choice)
                break;
        except ValueError:
            print("Incorrect input. Please enter a valid board number.")


pb_set_debug(1)

print("Copyright (c) 2023 SpinCore Technologies, Inc.\n")

print("Using SpinAPI Library version %s" % pb_get_version())

detect_boards()

if numBoards > 1:  # If there is more than one board in the system, have the user specify.
    select_boards()  # Request the board numbet to use from the user

if pb_init() != 0:
    print("Error initializing board: %s" % pb_get_error())

    exit(-1)

pb_init()
# Tell driver what clock frequency the board uses
pb_core_clock(clock_freq)

# Begin pulse program
pb_start_programming(PULSE_PROGRAM)
low_time = ctypes.c_double(1*ms)
wait = ctypes.c_double(50)
exposure_time= ctypes.c_double(20*ms)
wait_time= ctypes.c_double(25*ms)

pb_inst_pbonly(OFF, Inst.CONTINUE,0,low_time)
pb_inst_pbonly(AOM, Inst.CONTINUE,0,low_time)
loop = pb_inst_pbonly(ON, Inst.LOOP,NUMKIN,exposure_time)
pb_inst_pbonly(OFF, Inst.CONTINUE,0,wait_time)
pb_inst_pbonly(OFF, Inst.END_LOOP,loop,wait)
# End of programming registers and pulse program
pb_stop_programming()
# Trigger pulse program
pb_reset()


ret = sdk.Initialize("")  # Initialize camera
print("Function Initialize returned {}".format(ret))

if atmcd_errors.Error_Codes.DRV_SUCCESS == ret:
    ret = sdk.SetTemperature(-70)
    print("Function SetTemperature returned {} target temperature -70".format(ret))

    ret = sdk.CoolerON()
    print("Function CoolerON returned {}".format(ret))

    (ret, temperature) = sdk.GetTemperature()
    print("Function GetTemperature returned {} current temperature = {}".format(
        ret, temperature))
    # while ret != atmcd_errors.Error_Codes.DRV_TEMP_STABILIZED:
    #     time.sleep(5)
    #     (ret, temperature) = sdk.GetTemperature()
    #     print("Function GetTemperature returned {} current temperature = {}".format(
    #          ret, temperature))

    ret= sdk.SetCoolerMode(1)
    print("Function SetCoolerMode returned {} ".format(ret))

    ret = sdk.SetAcquisitionMode(codes.Acquisition_Mode.KINETICS)
    print("Function SetAcquisitionMode returned {} mode = Kinetics".format(ret))

    ret = sdk.SetKineticCycleTime(0)
    print("Function SetKineticCycleTime returned {} cycle time = 0.5 seconds".format(ret))

    ret = sdk.SetNumberKinetics(NUMKIN)
    print("Function SetNumberKinetics returned {}".format(ret))

    ret = sdk.SetTriggerMode(codes.Trigger_Mode.EXTERNAL_EXPOSURE_BULB)
    print("Function SetTriggerMode returned {} mode = Software trigger".format(ret))

    ret = sdk.SetReadMode(codes.Read_Mode.IMAGE)
    print("Function SetReadMode returned {} mode = Image".format(ret))

    #ret = sdk.SetExposureTime(0.200)
    #print("Function SetExposureTime returned {} time = 0.227s".format(ret))

    ret = sdk.SetPreAmpGain(2)
    print("FUnction SetPreAmpGain returned {} preampgain = 1".format(ret))
    ret = sdk.SetEMGainMode(3)
    print("Function SetEmGainMode returned {} Mode = 1".format(ret))

    ret = sdk.SetEMCCDGain(300)
    print("Function SetEMCCDGain returned {} Gain = 249".format(ret))

    ret = sdk.SetHSSpeed(0, 0)
    print("Function SetHSSpeed returned {} HSS set to 17MHz".format(ret))

    ret = sdk.SetShutter(0, 1, 0, 0)
    print("Function SetShutter returned {} shutter is always open".format(ret))

    (ret, fminExposure, fAccumulate, fKinetic) = sdk.GetAcquisitionTimings()
    print("Function GetAcquisitionTimings returned {} exposure = {} accumulate = {} kinetic = {}".format(
        ret, fminExposure, fAccumulate, fKinetic))

    directory = f''  # Replace with desired directory

    filename = "{}-{}".format(directory, time.strftime("%Y-%m-%d-%H-%M"))
    ret = sdk.SetSpool(1, 5, filename, 10) #codes.Spool_Mode.SPOOL_TO_16_BIT_FITS
    print("Function SetSpool returned {} ".format(ret))

    (ret, xpixels, ypixels) = sdk.GetDetector()
    print("Function GetDetector returned {} xpixels = {} ypixels = {}".format(
        ret, xpixels, ypixels))

    ret = sdk.SetImage(1, 1, 1, xpixels, 1, ypixels)
    print("Function SetImage returned {} hbin = 1 vbin = 1 hstart = 1 hend = {} vstart = 1 vend = {}".format(
        ret, xpixels, ypixels))


else:
    print("Cannot continue, could not initialise camera")




ret = sdk.PrepareAcquisition()
print("Function PrepareAcquisition returned {}".format(ret))
time.sleep(5)
ret = sdk.StartAcquisition()
print("Function StartAcquisition returned {}".format(ret))

pb_start()

# ret,yes = sdk.GetStatus()
# while yes != atmcd_errors.Error_Codes.DRV_IDLE:
#     time.sleep(1)
#     ret,yes = sdk.GetStatus()
#     print("Function GetStatus returned {},{}".format(ret,yes))

ret = sdk.WaitForAcquisition()
print("Function WaitForAcquisition returned {}".format(ret))

index = 0
while index < NUMKIN:
    (ret, index) = sdk.GetTotalNumberImagesAcquired()
    print("Function current count {} ".format(index), end="\r")
print("")

pb_stop()
pb_close()

# Clean up
ret = sdk.ShutDown()
print("Function Shutdown returned {}".format(ret))



