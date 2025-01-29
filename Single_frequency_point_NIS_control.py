from spinapi import *
import numpy as np

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
OFF = int(0b111000000000000000001100) # all off
ON = int(0b111000000000000000001111)

LONG_ZERO  = int(0b111000000000000000000000)
low_time = ctypes.c_double(100*ms)
wait = ctypes.c_double(50)
exposure_time= ctypes.c_double(20*ms)
f_accu= ctypes.c_double(35*ms)
Scanning_points = 1
NUMKIN = int(20*60*1000)/int(20)
pb_reset()
print(NUMKIN)
input('Press Enter to run the code')
# START Pulseblaster code here

pb_init()
# Tell driver what clock frequency the board uses
pb_core_clock(clock_freq)
# Starting to program the board
pb_start_programming(PULSE_PROGRAM)
# Time to initialize the camera
pb_inst_pbonly(OFF, Inst.CONTINUE,0,low_time)
# Loop to take N averages of an ODMR spectrum
loop = pb_inst_pbonly(ON, Inst.LOOP,NUMKIN,exposure_time)
#pb_inst_pbonly(OFF, Inst.CONTINUE,0,f_accu)
pb_inst_pbonly(OFF, Inst.END_LOOP,loop,wait)
pb_inst_pbonly(LONG_ZERO, Inst.STOP,0,low_time)
pb_stop_programming()
# Trigger pulse program
pb_reset()
#Start the pulses
pb_start()
input('Press Enter to stop the code')
pb_stop()