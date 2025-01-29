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
LONG_ZERO = int(0b111000000000000000000000) # all off
AOM_CAM = int(0b111000000000000000001001)
CAM = int(0b111000000000000000000001)
AOM = int(0b111000000000000000001000)
MW = int(0b111000000000000000000100)
MW_CAM = int(0b111000000000000000000101)
FREQ = int(0b111000000000000000000010)

length_ttl = ctypes.c_double(1000)
camera_init = ctypes.c_double(10*ms)
aom_time = ctypes.c_double(50000*ns) #50us
fAccumulate = ctypes.c_double(25*ms)
relaxation_time = ctypes.c_double(1000*ns)
relaxation_time2 = ctypes.c_double(2000*ns)
aom_delay = ctypes.c_double(250*ns)
t_pi = ctypes.c_double(400*ns)
mw_delay = ctypes.c_double(50*ns)

# Rabi cycle parameters


N_avg = 50 # number of times the cycle is going to repeat for each MW_ON_time
start_freq = 2880
end_freq = 3110
step = 1
Scanning_points = int(int(end_freq-start_freq)/step + 1)
exposure_time = 20 * ms
NUMKIN = N_avg*Scanning_points
one_cycle_time = int(aom_delay.value + aom_time.value + aom_delay.value + t_pi.value)
number_of_sequences = int(exposure_time / one_cycle_time)
if (number_of_sequences%t_min):
    number_of_sequences = int(t_min*round(number_of_sequences/t_min))


print(one_cycle_time,number_of_sequences,NUMKIN)
pb_reset()
input('Press Enter to run the code')
# START Pulseblaster code here

pb_init()

# Tell driver what clock frequency the board uses
pb_core_clock(clock_freq)

pb_start_programming(PULSE_PROGRAM)

pb_inst_pbonly(LONG_ZERO, Inst.CONTINUE, 0, camera_init) #inicializaçao da camara

number_of_repetions = pb_inst_pbonly(LONG_ZERO, Inst.LOOP,N_avg,length_ttl) # number of repetitions for each average

frequencies = pb_inst_pbonly(LONG_ZERO, Inst.LOOP,Scanning_points,length_ttl)

#signal start
signal = pb_inst_pbonly(AOM_CAM,Inst.LOOP,number_of_sequences,aom_delay) # laser delay to turn on
pb_inst_pbonly(AOM_CAM, Inst.CONTINUE, 0, aom_time)
pb_inst_pbonly(CAM, Inst.CONTINUE, 0, aom_delay)  # laser delay to turn off
pb_inst_pbonly(CAM, Inst.CONTINUE, 0, relaxation_time)  # laser delay to turn off
pb_inst_pbonly(MW_CAM, Inst.CONTINUE, 0, t_pi) # time for the rabi pulse
#pb_inst_pbonly(CAM, Inst.CONTINUE, 0, mw_delay) # time for the rabi pulse
pb_inst_pbonly(CAM, Inst.END_LOOP, signal, length_ttl) # do i need to have the last 2 lines or just one is enough? I think so cause the length_ttl only happens when continuing to the next inst

pb_inst_pbonly(LONG_ZERO, Inst.CONTINUE, 0, fAccumulate)  # clean cycle for the camera

pb_inst_pbonly(FREQ, Inst.END_LOOP, frequencies, length_ttl)

pb_inst_pbonly(LONG_ZERO, Inst.END_LOOP, number_of_repetions, length_ttl) #get back to the beginning



#All loop ends all zero
pb_inst_pbonly(LONG_ZERO, Inst.CONTINUE, 0, camera_init)
pb_inst_pbonly(LONG_ZERO, Inst.STOP, 0, camera_init)

pb_stop_programming()
# Trigger pulse program
pb_reset()

# END pulseblaster code here
pb_start()
