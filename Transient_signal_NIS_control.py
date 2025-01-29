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
OFF = int(0b111000000000000000000000) # all off
MW = int(0b111000000000000000000101)
ON = int(0b111000000000000000001011)
ON_MW = int(0b111000000000000000001111)
LONG_ZERO  = int(0b111000000000000000000000)
low_time = ctypes.c_double(1000*ms)
wait = ctypes.c_double(50)
exposure_time= ctypes.c_double(1*ms)
f_accu= ctypes.c_double(50*ms)
t_wait = ctypes.c_double(5*ms)
n_avg = 100
NUMKIN= 10
t_delay = np.linspace(0,5,26)
pb_reset()
print(n_avg*26)
input('Press Enter to run the code')
# START Pulseblaster code here

pb_init()
# Tell driver what clock frequency the board uses
pb_core_clock(clock_freq)

pb_start_programming(PULSE_PROGRAM)

pb_inst_pbonly(OFF, Inst.CONTINUE,0,low_time)
start = pb_inst_pbonly(OFF,Inst.LOOP,n_avg,wait)
#for cycle to start acquisition before trigger
for t in t_delay:
    t = ctypes.c_double(t*ms)
    pb_inst_pbonly(OFF, Inst.CONTINUE, 0, t)
    if t.value < exposure_time.value:
        print(t.value,0)
        pb_inst_pbonly(ON, Inst.CONTINUE, 0, exposure_time)
        pb_inst_pbonly(OFF, Inst.CONTINUE, 0, f_accu)

    elif exposure_time.value <= t.value < (exposure_time.value+1*ms):
        print(t.value,1)
        # Calculations about the exposure time with and without Wire ON
        t_without_mw = ctypes.c_double(exposure_time.value+1*ms - t.value)
        t_with_mw = ctypes.c_double(1 * ms - t_without_mw.value)

        pb_inst_pbonly(ON, Inst.CONTINUE, 0, t_without_mw)
        pb_inst_pbonly(ON_MW, Inst.CONTINUE, 0, t_with_mw)
        pb_inst_pbonly(OFF, Inst.CONTINUE, 0, f_accu)

    elif (exposure_time.value + 1 * ms) <= t.value < (exposure_time.value + 2 * ms):
        print(t.value,2)
        pb_inst_pbonly(ON_MW, Inst.CONTINUE, 0, exposure_time)
        pb_inst_pbonly(OFF, Inst.CONTINUE, 0, f_accu)

    elif (exposure_time.value + 2 * ms) <= t.value < (exposure_time.value + 3 * ms):
        print(t.value,3)
        # Calculations about the exposure time with and without Wire ON
        t_with_mw2 = ctypes.c_double(t.value-2*ms)
        #t_without_mw2 = ctypes.c_double(t_with_mw2.value-1*ms)


        pb_inst_pbonly(MW, Inst.CONTINUE, 0, t_with_mw2)
        pb_inst_pbonly(ON, Inst.CONTINUE, 0, exposure_time)
        pb_inst_pbonly(OFF, Inst.CONTINUE, 0, f_accu)
    else:
        print(t.value,4)
        pb_inst_pbonly(ON, Inst.CONTINUE, 0, exposure_time)
        pb_inst_pbonly(OFF, Inst.CONTINUE, 0, f_accu)

pb_inst_pbonly(OFF, Inst.END_LOOP,start,wait)

pb_inst_pbonly(LONG_ZERO, Inst.STOP,0,low_time)


pb_stop_programming()
# Trigger pulse program
pb_reset()

# END pulseblaster code here
pb_start()
input('Press Enter to stop the code')
pb_stop()