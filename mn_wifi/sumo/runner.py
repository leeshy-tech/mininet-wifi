import os
import threading
from threading import Thread as thread

from mininet.log import info
from mn_wifi.mobility import Mobility
from mn_wifi.sumo.sumolib.sumolib import checkBinary
from mn_wifi.sumo.traci import main as traci, _vehicle


class sumo(Mobility):

    vehCmds = None

    def __init__(self, cars, aps, **kwargs):
        Mobility.thread_ = thread(name='vanet', target=self.configureApp,
                                  args=(cars, aps), kwargs=dict(kwargs,))
        Mobility.thread_.daemon = True
        Mobility.thread_._keep_alive = True
        Mobility.thread_.start()

    @classmethod
    def getVehCmd(cls):
        return cls.vehCmds

    def configureApp(self, cars, aps, config_file='map.sumocfg',
                     clients=1, port=8813, exec_order=0, extra_params=None):
        if extra_params is None:
            extra_params = []

        try:
            Mobility.cars = cars
            Mobility.aps = aps
            Mobility.mobileNodes = cars
            self.start(cars, config_file, clients, port,
                       exec_order, extra_params)
        except:
            info("*** Connection with SUMO has been closed\n")

    def setWifiParameters(self):
        thread = threading.Thread(name='wifiParameters', target=self.parameters)
        thread.start()

    def start(self, cars, config_file, clients, port,
              exec_order, extra_params):
        sumoBinary = checkBinary('sumo-gui')
        if '/' in config_file:
            sumoConfig = config_file
        else:
            sumoConfig = os.path.join(os.path.dirname(__file__), "data/{}".format(config_file))

        command = ' {} -c {} --num-clients {} --remote-port {} ' \
                  '--time-to-teleport -1'.format(sumoBinary, sumoConfig, clients, port)
        for param in extra_params:
            command = command + " " + param
        command += " &"
        os.system(command)
        traci.init(port)
        traci.setOrder(exec_order)

        self.setWifiParameters()

        vehCmds = _vehicle.VehicleDomain()
        vehCmds._connection = traci.getConnection(label="default")

        while True:
            traci.simulationStep()
            for vehID1 in vehCmds.getIDList():
                x1 = vehCmds.getPosition(vehID1)[0]
                y1 = vehCmds.getPosition(vehID1)[1]

                if int(vehID1) < len(cars):
                    cars[int(vehID1)].position = x1, y1, 0
                    cars[int(vehID1)].set_pos_wmediumd(cars[int(vehID1)].position)

                    if hasattr(cars[int(vehID1)], 'sumo'):
                        if cars[int(vehID1)].sumo:
                            args = [cars[int(vehID1)].sumoargs]
                            cars[int(vehID1)].sumo(vehID1, vehCmds, *args)
                            del cars[int(vehID1)].sumo

