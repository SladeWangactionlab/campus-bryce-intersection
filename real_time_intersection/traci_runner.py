import os
import sys
import time
import definitions as var_def
from global_config_parameters import CONFIG
from functions.pre_processing.intersection_parameters import IntersectionParameters
from sumolib import checkBinary  # noqa
import traci  # noqa
from functions.real_time_lights.sumo_info_process import DetectorProcess
from functions.real_time_lights.snmp import SNMP

gui = True

if gui:

    sumoBinary = checkBinary('sumo-gui')

else:

    sumoBinary = checkBinary('sumo')

    # traci.start([sumoBinary, "-c", self.sumocfg, "--step-length", str(step)])

SIM_LENGTH = CONFIG.sim_length
IP = "127.0.0.1"
PORT = 501


def run(detector_rw_index):

    # detector_ids = traci.lanearea.getIDList()

    detector_processor = DetectorProcess(traci=traci, IDS=detector_rw_index)
    snmp_client = SNMP(ip=IP, port=PORT)

    while traci.simulation.getTime() < SIM_LENGTH:
        t0 = time.time()

        hex_string = detector_processor.get_occupancy()

        if hex_string is not None:
            snmp_client.send_detectors(hex_string)

        # sim step
        traci.simulationStep()

        # sleep enough to make sim step take 1 second (real-time)
        dt = (time.time() - t0)
        time.sleep(max(CONFIG.sim_step - dt, 0))

    traci.close()
    sys.stdout.flush()


def index_detectors(intersection_setup_file):

    parameters = IntersectionParameters()
    parameters.import_file(intersection_setup_file)

    # this won't work with more than 1 traffic light
    rw_index = parameters.get_rw_index_by_light(CONFIG.tl_ids[0], main=True, dict=False)

    return rw_index


if __name__ == "__main__":

    detect_rw_index = index_detectors(intersection_setup_file=CONFIG.intersection_setup_file)

    command_line_list = CONFIG.get_cmd_line_list(method='randomRoutes',
                                                 sim_length=CONFIG.sim_length,
                                                 sim_step=CONFIG.sim_step,
                                                 emissions=False,
                                                 dual_ring_lights=False)

    traci.start([sumoBinary] + command_line_list)

    run(detect_rw_index)