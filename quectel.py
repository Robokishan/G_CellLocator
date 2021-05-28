import requests
import time
import sys, getopt
import serial
import json

class Modem:
    network_towers = [ u'\u2581',u'\u2582',  u'\u2584', u'\u2586', u'\u2588']
    
    signalMap = [
        (2	,-109,	"Marginal", 1),
        (3	,-107,	"Marginal", 1),
        (4	,-105,	"Marginal", 1),
        (5	,-103,	"Marginal", 1),
        (6	,-101,	"Marginal", 1),
        (7	,-99,	"Marginal", 1),
        (8	,-97,	"Marginal", 1),
        (9	,-95,	"Marginal", 1),
        (10	,-93,	"OK", 2),
        (11	,-91,	"OK", 2),
        (12	,-89,	"OK", 2),
        (13	,-87,	"OK", 2),
        (14	,-85,	"OK", 2),
        (15	,-83,	"Good", 3),
        (16	,-81,	"Good", 3),
        (17	,-79,	"Good", 3),
        (18	,-77,	"Good", 3),
        (19	,-75,	"Good", 3),
        (20	,-73,	"Excellent", 4),
        (21	,-71,	"Excellent", 4),
        (22	,-69,	"Excellent", 4),
        (23	,-67,	"Excellent", 4),
        (24	,-65,	"Excellent", 4),
        (25	,-63,	"Excellent", 4),
        (26	,-61,	"Excellent", 4),
        (27	,-59,	"Excellent", 4),
        (28	,-57,	"Excellent", 4),
        (29	,-55,	"Excellent", 4),
        (30	,-53,	"Excellent", 4)
    ]

    cmd_delay = 0.1
    dataDelay = 2

    DEBUG = False
    _timeout_ = 60
    TIMEOUT = _timeout_ * 1000

    def __init__(self, modem_port="/dev/ttyUSB3", baud=115200):
        super().__init__()
        self.__modem_port = serial.Serial(
            port=modem_port,
            baudrate=baud,
            timeout=10,
            write_timeout=3
            # parity=serial.PARITY_NONE,
            # stopbits=serial.STOPBITS_ONE,
            # bytesize=serial.EIGHTBITS
        )
        self.__modem_port.close()
    def micros(self):
        return int(time.time() * 1000000)

    def millis(self):
        return int(time.time() * 1000)

    def send_command(self,command, read_counter=1):
        if not self.__modem_port.is_open:
            self.__modem_port.open()
        try:
            command = command + "\r"
            self.__modem_port.write(command.encode())
            for _counter in range(0, read_counter):
                print(f"#:{_counter+1}")
                response=self.read() #read response of the command from quectel
                for msg in response:
                    print(msg.decode("utf-8"), end='',flush=True)
        except Exception as e:
            print("Error",e)
        finally:
            self.__modem_port.close()
    
    def read(self):
        out = ""
        time_prev = self.millis()
        print_time = self.millis()
        print(f"[MODEM] Waiting {self.__modem_port.inWaiting()}")
        while self.__modem_port.inWaiting() <= 0 :
            timeout = self.millis() - time_prev
            if (self.millis() - print_time) > 1000:
                print(f"..{int((print_time - time_prev)/1000)}s",end=' ',flush=True)
                print_time = self.millis()
                
            '''
            TIMEOUT is disabled
            '''
            # if timeout > self.TIMEOUT:
            #     print("[ERR MODEM] Timeout MODEM")
            #     break
        print("\n")
        recieve_bytes = []
        i = 0
        while self.__modem_port.inWaiting() > 0:
            recieve_bytes.append(self.__modem_port.readline())
        return recieve_bytes
    
    def signalstrength(self):
        if not self.__modem_port.is_open:
            self.__modem_port.open()
        try:
            cmd="AT+CSQ\r"
            self.__modem_port.write(cmd.encode())
            msg=self.__modem_port.readline() #read echo command from quectel
            # print(msg)
            msg=self.__modem_port.readline() #read response of the command from quectel
            # print(msg)
            response=msg.decode("utf-8") #convert bytes to string
            print("Response:{0}".format(response))
            dbm = 0
            rssi_int_value = 0
            message = ""
            bars = self.network_towers[0]
            if "+CSQ:" in response: #check if iccid is in there
                value = response.split(':')[1]
                status = value.rstrip().strip()
                rssi_int_value = int(status.split(",")[0])
                for _rssi in self.signalMap:
                    if rssi_int_value >= 31:
                        dbm = -51
                        message = "Unknown"
                        bars = self.network_towers[1]  +self.network_towers[2] + self.network_towers[3] + self.network_towers[4]
                        break
                    if _rssi[0] == rssi_int_value:
                        dbm = _rssi[1]
                        message = _rssi[2]
                        _bar = _rssi[3]
                        bars = ""
                        for i in range(1, _bar+1):
                            bars+=self.network_towers[i]
                        break
                print(f"'{rssi_int_value}' '{dbm} dbm' '{message}' {bars}")
                return status
        except Exception as e:
            print("Error",e)
        finally:
            self.__modem_port.close()

    def neighbors(self):
        neighbors = []
        if not self.__modem_port.is_open:
            self.__modem_port.open()
        try:
            cmd='AT+QENG="neighbourcell"\r'
            self.__modem_port.write(cmd.encode())
            msg=self.__modem_port.readline() #read echo command from quectel
            # print(msg)
            raw_info = []
            while msg != "OK":
                msg=self.__modem_port.readline().decode("utf-8").rstrip().strip() #read response of the command from quectel
                raw_info.append(msg)
            for info in raw_info:
                if '+QENG' in info:
                    cell_info = info.split(': ')[1].rstrip().strip().replace('"','')
                    cell_info = cell_info.split(',')
                    network_type = cell_info[1]
                    '''
                    LTE IS NOT SUPPORTED CURRENTLY
                    '''
                    # if network_type == "LTE":
                    #     com_method = cell_info[2]
                    #     mcc = cell_info[3]
                    #     mnc = cell_info[4]
                    #     cellid = int(cell_info[6], 16)
                    #     lac = int(cell_info[12], 16)
                    #     # print(f"{network_type} {com_method} {mcc} {mnc} {cellid}")
                    #     neighbors.append({ "type": network_type, "l":lac, "c":mcc, "n": mnc, "i": cellid })

                    if network_type == "GSM":
                        mcc = cell_info[2]
                        mnc = cell_info[3]
                        cellid = int(cell_info[5], 16)
                        lac = int(cell_info[4], 16)
                        # print(f"{network_type} {mcc} {mnc} {cellid} {lac}")
                        neighbors.append({ "type": network_type, "l":lac, "c":mcc, "n": mnc, "i": cellid })
        except Exception as e:
            print("Error",e)
        finally:
            self.__modem_port.close()
            return neighbors

    def retriveNetworkinfo(self):
        cell_towers = []
        if not self.__modem_port.is_open:
            self.__modem_port.open()
        try:
            cmd='AT+QENG="servingcell"\r'
            self.__modem_port.write(cmd.encode())
            msg=self.__modem_port.readline() #read echo command from quectel
            # print(msg)
            msg=self.__modem_port.readline() #read response of the command from quectel
            # print(msg)
            response=msg.decode("utf-8") #convert bytes to string
            print("Response:{0}".format(response))
            if "+QENG:" in response: #check if iccid is in there
                cell_info = response.split(':')[1].rstrip().strip().replace('"','')
                # print(cell_info)
                cell_info = cell_info.split(',')
                network_type = cell_info[2]
                if network_type == "LTE":
                    com_method = cell_info[3]
                    mcc = cell_info[4]
                    mnc = cell_info[5]
                    cellid = int(cell_info[6], 16)
                    lac = int(cell_info[12], 16)
                    # print(f"{network_type} {com_method} {mcc} {mnc} {cellid}")
                    cell_towers.append({ "type": network_type, "l":lac, "c":mcc, "n": mnc, "i": cellid })

                elif network_type == "GSM":
                    mcc = cell_info[3]
                    mnc = cell_info[4]
                    cellid = int(cell_info[6], 16)
                    lac = int(cell_info[5], 16)
                    # print(f"{network_type} {com_method} {mcc} {mnc} {cellid}")
                    cell_towers.append({ "type": network_type, "l":lac, "c":mcc, "n": mnc, "i": cellid })
                    self.__modem_port.close()
                    cell_towers.extend(self.neighbors())

        except Exception as e:
            print("Error",e)
        finally:
            self.__modem_port.close()
            return { 'c': {'a': cell_towers }}
