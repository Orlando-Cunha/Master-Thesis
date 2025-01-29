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

length_ttl = ctypes.c_double(1000)
camera_init = ctypes.c_double(10*ms)
aom_time = ctypes.c_double(200*us)
aom_time2 = ctypes.c_double(2000*ns)
fAccumulate = ctypes.c_double(25*ms)
relaxation_time = ctypes.c_double(1000*ns)
relaxation_time2 = ctypes.c_double(2000*ns)
aom_delay = ctypes.c_double(250*ns)
t_pi = ctypes.c_double(160*ns)
wait = ctypes.c_double(50*ms)
# Time parameters

start_Pulse_duration = ctypes.c_double(15*ms)

end_Pulse_duration = 50*ns
Scanning_points = 17
#Scanned_parameters = [5000*us,2000*us,1000*us, 500*us,50*us,10*us,5*us,500*ns,50*ns,10*ns]
#Scanned_parameters = [30000*us,15000*us,10000*us, 5000*us,1000*us, 500*us,50*us,500*ns,50*ns,10*ns]
#Scanned_parameters = [10*ns,50*ns,500*ns,5*us,50*us, 500*us,1000*us, 5000*us,10000*us,15000*us]
#Scanned_parameters = [1000*us,2000*us,3000*us,5000*us,7000*us,9000*us,11000*us,12000*us,13000*us,15000*us]
Scanned_parameters = [15000*us,14000*us,13000*us,12000*us,11000*us,10000*us, 9000*us,8000*us,7000*us,6000*us,5000*us,4000*us,3000*us,2000*us,1500*us,1200*us,1000*us, 800*us,500*us,300*us,100*us]
#Scanned_parameters = [5000*us,3000*us,2000*us,1500*us,1200*us,1000*us, 800*us,500*us,300*us,100*us,500*ns,10*ns]
#Scanned_parameters = np.logspace(np.log(50.0*ns),np.log10(15000000.0),Scanning_points)
start = 500*ns
end = 15*ms
num_points = len(Scanned_parameters)
#Scanned_parameters = np.logspace(np.log10(end),np.log10(start),num=num_points)
print(Scanned_parameters)
N_avg = 20 # number of times the cycle is going to repeat for each MW_ON_time
exposure_time = 40 * ms
#one_cycle_time = int(aom_time.value + aom_time2.value + end_Pulse_duration + relaxation_time.value)
print(t_min)
one_cycle_time_with_delay = int(aom_delay.value+aom_time.value+aom_delay.value+start_Pulse_duration.value+aom_delay.value+aom_time.value)
number_of_sequences = int(exposure_time / one_cycle_time_with_delay)
if (number_of_sequences%t_min):
    number_of_sequences = int(t_min*round(number_of_sequences/t_min))

NUMKIN = 2*N_avg*num_points
print(one_cycle_time_with_delay,number_of_sequences,NUMKIN)
pb_reset()
input('Press Enter to run the code')
# START Pulseblaster code here

pb_init()

# Tell driver what clock frequency the board uses
pb_core_clock(clock_freq)

pb_start_programming(PULSE_PROGRAM)

pb_inst_pbonly(LONG_ZERO, Inst.CONTINUE, 0, camera_init) #inicializaçao da camara

# lixo = pb_inst_pbonly(LONG_ZERO, Inst.LOOP,400,length_ttl) #  images to the bin
#
# teste = pb_inst_pbonly(AOM_CAM,Inst.LOOP,number_of_sequences,aom_delay)
# pb_inst_pbonly(AOM_CAM, Inst.CONTINUE, 0, aom_time)
# pb_inst_pbonly(AOM_CAM, Inst.CONTINUE, 0, start_Pulse_duration)
# pb_inst_pbonly(AOM_CAM, Inst.CONTINUE, 0, aom_delay)
# pb_inst_pbonly(AOM_CAM, Inst.CONTINUE, 0, aom_time)
# pb_inst_pbonly(CAM, Inst.END_LOOP, teste, length_ttl)
#
# pb_inst_pbonly(LONG_ZERO, Inst.CONTINUE, 0, fAccumulate)  # clean cycle for the camera
# pb_inst_pbonly(LONG_ZERO, Inst.END_LOOP, lixo, length_ttl) #get back to the beginning


for t in Scanned_parameters: # define the number of rabi steps and the values
    t= ctypes.c_double(t)
    #pb_inst_pbonly(LONG_ZERO, Inst.CONTINUE, 0, camera_init)  # inicializaçao da camara

    number_of_repetions = pb_inst_pbonly(LONG_ZERO, Inst.LOOP,N_avg,length_ttl) # number of repetitions for each t_rabi

    #signal with delays
    signal = pb_inst_pbonly(AOM_CAM,Inst.LOOP,100,aom_delay) # laser delay to turn on
    pb_inst_pbonly(AOM_CAM, Inst.CONTINUE, 0, aom_time)
    #pb_inst_pbonly(CAM,Inst.CONTINUE,0,relaxation_time) # relaxation time
    pb_inst_pbonly(MW_CAM, Inst.CONTINUE, 0, t_pi)  # laser delay to turn off
    pb_inst_pbonly(CAM, Inst.CONTINUE, 0, t)
    #pb_inst_pbonly(MW_CAM, Inst.CONTINUE, 0, t_pi)  # laser delay to turn off
    pb_inst_pbonly(CAM, Inst.END_LOOP, signal, length_ttl) # do i need to have the last 2 lines or just one is enough? I think so cause the length_ttl only happens when continuing to the next inst

    pb_inst_pbonly(LONG_ZERO, Inst.CONTINUE, 0, fAccumulate)  # clean cycle for the camera

    pb_inst_pbonly(LONG_ZERO, Inst.CONTINUE, 0, wait)  # clean cycle for the camera

    # back with delays
    reference= pb_inst_pbonly(AOM_CAM, Inst.LOOP, 100, aom_delay)  # laser delay to turn on
    pb_inst_pbonly(AOM_CAM, Inst.CONTINUE, 0, aom_time)  # relaxation time
    pb_inst_pbonly(CAM, Inst.CONTINUE, 0, t_pi)  # laser delay to turn off
    #pb_inst_pbonly(CAM, Inst.CONTINUE, 0, aom_delay)  # laser delay to turn off
    pb_inst_pbonly(CAM, Inst.CONTINUE, 0, t)

    pb_inst_pbonly(CAM, Inst.END_LOOP, reference,length_ttl)

    pb_inst_pbonly(LONG_ZERO, Inst.CONTINUE, 0, fAccumulate)  # clean cycle for the camera
    pb_inst_pbonly(LONG_ZERO, Inst.CONTINUE, 0, wait)  # clean cycle for the camera
    pb_inst_pbonly(LONG_ZERO, Inst.END_LOOP, number_of_repetions, length_ttl) #get back to the beginning

#All loop ends all zero
pb_inst_pbonly(LONG_ZERO, Inst.CONTINUE, 0, camera_init)
pb_inst_pbonly(LONG_ZERO, Inst.STOP, 0, camera_init)

pb_stop_programming()
# Trigger pulse program
pb_reset()

# END pulseblaster code here
pb_start()
