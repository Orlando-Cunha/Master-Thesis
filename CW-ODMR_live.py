import platform
import sys
import time
import os
import ctypes
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from spinapi import *
from pyAndorSDK2 import atmcd, atmcd_codes, atmcd_errors
from tkinter import Tk, Label, Button
import threading
import numpy as np
from typing import Union, List

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

source_lib_path = os.path.join(here, _package_name, 'libs', get_platform_name(), get_max_bits())
sdk = atmcd(source_lib_path)
codes = atmcd_codes

def detect_boards():
    global numBoards
    numBoards = pb_count_boards()
    if numBoards <= 0:
        print("No Boards were detected in your system. Verify that the board is firmly secured in the PCI slot.\n")
        exit(-1)

def select_boards():
    while True:
        try:
            choice = int(input(f"Found {numBoards} boards in your system. Which board should be used? (0-{numBoards - 1}): "))
            if choice < 0 or choice >= numBoards:
                print("Invalid Board Number (%d)." % choice)
            else:
                pb_select_board(choice)
                print("Board %d selected." % choice)
                break
        except ValueError:
            print("Incorrect input. Please enter a valid board number.")

# Initialize SpinCore board
pb_set_debug(1)
print("Copyright (c) 2023 SpinCore Technologies, Inc.\n")
print("Using SpinAPI Library version %s" % pb_get_version())
detect_boards()
if numBoards > 1:  # If there is more than one board in the system, have the user specify.
    select_boards()  # Request the board number to use from the user
if pb_init() != 0:
    print("Error initializing board: %s" % pb_get_error())
    exit(-1)


clock_freq = 500  # The value of your clock oscillator in MHz
t_min = 1e3/clock_freq # all values should be multiple of the instruction time (ns)
OFF = int(0b111000000000000000001100) # all off
ON = int(0b111000000000000000001111)

LONG_ZERO  = int(0b111000000000000000000000)
low_time = ctypes.c_double(10*ms)
wait = ctypes.c_double(50)
exposure_time= ctypes.c_double(20*ms)
f_accu= ctypes.c_double(25*ms)
start_freq = 2650
end_freq = 2880
pts = 231
Scanning_points = int(end_freq-start_freq+1)
n_avg = 3
NUMKIN = Scanning_points*n_avg
pb_reset()
print(NUMKIN)
pb_init()
# Tell driver what clock frequency the board uses
pb_core_clock(clock_freq)

pb_start_programming(PULSE_PROGRAM)

pb_inst_pbonly(OFF, Inst.CONTINUE,0,low_time)

loop = pb_inst_pbonly(ON, Inst.LOOP,NUMKIN,exposure_time)
pb_inst_pbonly(OFF, Inst.CONTINUE,0,f_accu)
pb_inst_pbonly(OFF, Inst.END_LOOP,loop,wait)
pb_inst_pbonly(LONG_ZERO, Inst.STOP,0,low_time)
pb_stop_programming()

# Initialize camera settings
ret = sdk.Initialize("")  # Initialize camera

if atmcd_errors.Error_Codes.DRV_SUCCESS == ret:
    ret = sdk.SetTemperature(-70)
    ret = sdk.CoolerON()
    ret = sdk.SetCoolerMode(1)
    sdk.SetAcquisitionMode(codes.Acquisition_Mode.KINETICS)
    sdk.SetKineticCycleTime(0)
    sdk.SetNumberKinetics(NUMKIN)
    sdk.SetTriggerMode(codes.Trigger_Mode.EXTERNAL_EXPOSURE_BULB)
    sdk.SetReadMode(codes.Read_Mode.IMAGE)
    sdk.SetPreAmpGain(2)
    sdk.SetEMGainMode(1)
    sdk.SetEMCCDGain(250)
    sdk.SetHSSpeed(0, 0)
    sdk.SetShutter(0, 1, 0, 0)
    xpixels, ypixels = sdk.GetDetector()[1:]
    sdk.SetImage(1, 1, 1, xpixels, 1, ypixels)
else:
    print("Cannot continue, could not initialize camera")
    exit(-1)
def acquire_series2(length: int) -> List[np.ndarray]:
    ret, xpixels, ypixels = sdk.GetDetector()
    sdk.handle_return(ret)

    (ret, temperature) = sdk.GetTemperature()
    print("Function GetTemperature returned {} current temperature = {}".format(
        ret, temperature))
    sdk.handle_return(sdk.PrepareAcquisition())
    time.sleep(5)
    sdk.handle_return(sdk.StartAcquisition())
    imageSize = xpixels * ypixels
    series = []
    pb_start()
    for _ in range(length):
        sdk.handle_return(sdk.WaitForAcquisition())
        ret,first,last = sdk.GetNumberNewImages()
        print(last)
        ret, fullFrameBuffer= sdk.GetMostRecentImage(imageSize)
        sdk.handle_return(ret)
        series.append(np.ctypeslib.as_array(fullFrameBuffer))
    return series


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 8))

# Display the image in the first subplot
blank_image = np.zeros((xpixels, ypixels))
im = ax1.imshow(blank_image, cmap='gray')
ax1.axis('off')  # Hide axes for the image
ax1.set_title('Image')

# Prepare the second subplot for the graph
ax2.set_xlabel('Fixed Image Index')
ax2.set_ylabel('Mean Intensity')
ax2.set_title('Mean Intensity of Generated Images')
ax2.grid(True)

try:
    while True:
        lista = []
        ax1.cla()
        for acq in acquire_series2(NUMKIN):
            acq = np.reshape(acq, (xpixels, ypixels))
            lista.append(acq)
        ax1.imshow(lista[30],cmap='gray')
        print(np.shape(lista[30]))
        lista = np.mean(lista, axis=(1, 2))
        print(np.shape(lista))
        lista = lista[pts:]
        print(np.shape(lista))
        data1=lista[:pts]
        data2=lista[pts:]
        lista = (data1 + data2) / 2
        lista = lista/max(lista)

        pb_stop()
        ax2.cla()
        ax2.set_xlabel('Frequency (MHz)')
        ax2.set_ylabel('Normalized Intensity')
        #ax2.set_title('Mean Intensity of Generated Images')
        ax2.grid(True)
        ax2.plot(np.linspace(start_freq, end_freq, Scanning_points), lista)
        # Redraw the updated plot
        plt.pause(0.1)

except KeyboardInterrupt:
    print("Stopped by user")
except KeyboardInterrupt:
    print("Plotting stopped by user.")

# Clean up
pb_stop()
pb_close()
ret = sdk.ShutDown()
print("Function Shutdown returned {}".format(ret))