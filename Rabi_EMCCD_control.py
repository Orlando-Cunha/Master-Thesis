from spinapi import *
import os
from pyAndorSDK2 import atmcd, atmcd_codes, atmcd_errors
import platform
import sys
import time
import numpy as np


section_high = int(0b111000000000000000001001) #Channel 1--ON the first one is for the laser and the last is for the camera
section_low = int(0b111000000000000000001000) #Channel 1-OFF

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


clock_freq = 500  # The value of your clock oscillator in MHz
t_min = 1e3/clock_freq # all values should be multiple of the instruction time (ns)
LONG_ZERO = int(0b111000000000000000000000) # all off
AOM_CAM = int(0b111000000000000000001001)
CAM = int(0b111000000000000000000001)
AOM = int(0b111000000000000000001000)
MW = int(0b111000000000000000000100)
MW_CAM = int(0b111000000000000000000101)

length_ttl = ctypes.c_double(1000)
camera_init = ctypes.c_double(10*ms)
aom_time = ctypes.c_double(2*us)
aom_time2 = ctypes.c_double(2000*ns)
fAccumulate = ctypes.c_double(50*ms)
relaxation_time = ctypes.c_double(300*ns)
relaxation_time2 = ctypes.c_double(2000*ns)
aom_delay = ctypes.c_double(100*us)

# Rabi cycle parameters

start_Pulse_duration = 500
end_Pulse_duration = 10
Scanning_points = 101
Scanned_parameters = np.linspace(start_Pulse_duration,end_Pulse_duration,Scanning_points)

N_avg = 30 # number of times the cycle is going to repeat for each MW_ON_time
exposure_time = 40 * ms
one_cycle_time = int(aom_time.value + aom_time2.value + end_Pulse_duration + relaxation_time.value)
number_of_sequences = int(exposure_time / one_cycle_time)
if (number_of_sequences%t_min):
    number_of_sequences = int(t_min*round(number_of_sequences/t_min))

NUMKIN = 2*N_avg*Scanning_points
print(one_cycle_time,number_of_sequences,NUMKIN)

pb_reset()

pb_init()

pb_core_clock(clock_freq)

pb_start_programming(PULSE_PROGRAM)

pb_inst_pbonly(LONG_ZERO, Inst.CONTINUE, 0, camera_init) #inicializaçao da camara


for t_rabi in Scanned_parameters: # define the number of rabi steps and the values
    t_rabi= ctypes.c_double(t_rabi)
    pb_inst_pbonly(LONG_ZERO, Inst.CONTINUE, 0, camera_init)  # inicializaçao da camara

    number_of_repetions = pb_inst_pbonly(LONG_ZERO, Inst.LOOP,N_avg,length_ttl) # number of repetitions for each t_rabi

    #signal start
    signal = pb_inst_pbonly(AOM_CAM,Inst.LOOP,number_of_sequences,aom_time)
    pb_inst_pbonly(CAM,Inst.CONTINUE,0,relaxation_time) # relaxation time
    pb_inst_pbonly(MW_CAM, Inst.CONTINUE, 0, t_rabi) # time for the rabi pulse
    #pb_inst_pbonly(CAM, Inst.CONTINUE, 0, relaxation_time2)  # 2nd relaxation time
    pb_inst_pbonly(AOM_CAM, Inst.CONTINUE, 0, aom_time2)  # readout pulse
    pb_inst_pbonly(CAM, Inst.END_LOOP, signal, length_ttl) # do i need to have the last 2 lines or just one is enough? I think so cause the length_ttl only happens when continuing to the next inst

    pb_inst_pbonly(LONG_ZERO, Inst.CONTINUE, 0, fAccumulate)  # clean cycle for the camera

    # #background start
    # background = pb_inst_pbonly(CAM, Inst.LOOP, 50, aom_time)
    # pb_inst_pbonly(CAM, Inst.CONTINUE, 0, relaxation_time)  # relaxation time
    # pb_inst_pbonly(CAM, Inst.CONTINUE, 0, t_rabi)  # time for the rabi pulse
    # pb_inst_pbonly(CAM, Inst.CONTINUE, 0, relaxation_time2)  # relaxation time
    # pb_inst_pbonly(CAM, Inst.CONTINUE, 0, aom_time2)  # relaxation time
    # pb_inst_pbonly(CAM, Inst.END_LOOP, background, length_ttl)  # do i need to have the last 2 lines or just one is enough?

    #pb_inst_pbonly(LONG_ZERO, Inst.CONTINUE, 0, fAccumulate) # clean cycle for the camera
    # pb_inst_pbonly = (AOM, Inst.CONTINUE, 0, 3)  # laser delay

    #reference start
    reference = pb_inst_pbonly(AOM_CAM, Inst.LOOP, number_of_sequences, aom_time)
    pb_inst_pbonly(CAM, Inst.CONTINUE, 0, relaxation_time)  # relaxation time
    pb_inst_pbonly(CAM, Inst.CONTINUE, 0, t_rabi)  # time for the rabi pulse
    #pb_inst_pbonly(CAM, Inst.CONTINUE, 0, relaxation_time2)  # relaxation time
    pb_inst_pbonly(AOM_CAM, Inst.CONTINUE, 0, aom_time2)  # readout pulse
    pb_inst_pbonly(CAM, Inst.END_LOOP, reference, length_ttl)  # do i need to have the last 2 lines or just one is enough?

    pb_inst_pbonly(LONG_ZERO, Inst.CONTINUE, 0, fAccumulate)  # clean cycle for the camera
    pb_inst_pbonly(LONG_ZERO, Inst.END_LOOP, number_of_repetions, length_ttl) #get back to the beginning

#All loop ends all zero
pb_inst_pbonly(LONG_ZERO, Inst.CONTINUE, 0, camera_init)
pb_inst_pbonly(LONG_ZERO, Inst.STOP, 0, camera_init)

pb_stop_programming()

ret = sdk.Initialize("")  # Initialize camera
print("Function Initialize returned {}".format(ret))

if atmcd_errors.Error_Codes.DRV_SUCCESS == ret:
    ret = sdk.SetTemperature(-70)
    print("Function SetTemperature returned {} target temperature -70".format(ret))

    ret = sdk.CoolerON()
    print("Function CoolerOn returned {}".format(ret))

    ret = sdk.SetCoolerMode(1)
    print("Function SetCoolerMode returned {} ".format(ret))

    (ret, temperature) = sdk.GetTemperature()
    print("Function GetTemperature returned {} current temperature = {}".format(
        ret, temperature))
    while ret != atmcd_errors.Error_Codes.DRV_TEMP_STABILIZED:
        time.sleep(5)
        (ret, temperature) = sdk.GetTemperature()
        print("Function GetTemperature returned {} current temperature = {}".format(
            ret, temperature))


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

    directory = f'C:\\Users\\LAB-A1-10\\Desktop\\Setup\\Orlando\\Images\\Rabi\\'  # Replace with desired directory

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
# Clean up
ret = sdk.ShutDown()
print("Function Shutdown returned {}".format(ret))


pb_stop()
