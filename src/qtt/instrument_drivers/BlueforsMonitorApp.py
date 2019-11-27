import getopt
import glob
import os
import sys
from datetime import datetime

from zmqrpc.ZmqRpcServer import ZmqRpcServerThread


class InstrumentDataServer:
    """ Represents a server proxy for sending instrument measurable quantities
    to a client.

    Args:
        functions (dict): the instrument functions.
        address (str): the ip-address of the server.
        port (int): the port number of the proxy server.
        user (str): a username for protection.
        password (str): a password for protection.
    """

    def __init__(self, functions, address='*', port=8080, user=None,
                 password=None):
        self._server_ = ZmqRpcServerThread("tcp://{0}:{1}".format(
            address, port),
            rpc_functions=functions,
            username=user,
            password=password)

    def run(self):
        """Starts the server proxy and blocks the current thread. A keyboard
        interuption will stop and clean-up the server proxy."""
        print(' Enabled instrument server...')
        print(' Press CTRL+C to quit!')
        try:
            self._server_.start()
            while (True):
                continue
        except KeyboardInterrupt:
            print(' Done')
        finally:
            self._server_.stop()
            self._server_.join()

    def start(self):
        """Starts the server proxy."""
        self._server_.start()

    def stop(self):
        """Stops the server proxy."""
        self._server_.stop()


class FridgeDataSender():
    """
    Sends temperature and pressure data of the Bluefors fridge to the proxy
    client connections.
    """

    _T_file_ext_ = "CH*T*.log"
    _P_file_ext_ = "maxigauge*.log"
    _E_file_ext_ = "Status_*.log"

    def __init__(self, folder_path, **kwargs):
        self._folder_path_ = folder_path
        quantities = {'datetime': self.get_datetime,
                      'temperatures': self.get_temperatures,
                      'pressures': self.get_pressures,
                      'status': self.get_status}
        _data_server_ = InstrumentDataServer(quantities, **kwargs)
        _data_server_.run()

    @staticmethod
    def _get_tail_line_(file_path, block_size=1024):
        with open(file_path, 'rb') as fstream:
            fstream.seek(0, 2)
            end_byte = fstream.tell()
            lines_to_go = 1
            block_number = -1
            blocks = []
            while lines_to_go > 0 and end_byte > 0:
                if (end_byte - block_size > 0):
                    fstream.seek(block_number * block_size, 2)
                    data = fstream.read(block_size)
                else:
                    fstream.seek(0, 0)
                    data = fstream.read(end_byte)
                blocks.append(data.decode('utf-8'))
                lines_found = blocks[-1].count('\n')
                lines_to_go -= lines_found
                end_byte -= block_size
                block_number -= 1
        all_read_text = ''.join(reversed(blocks)).splitlines()[-1]
        return all_read_text.strip().split(",")

    def _read_temperature_(self, file_path):
        data = FridgeDataSender._get_tail_line_(file_path)
        temperature = float(data[2])
        time = '{0} {1}'.format(data[0], data[1])
        return (temperature, time)

    def get_temperatures(self):
        today = datetime.now().strftime('%y-%m-%d')
        T_directory = '{0}\\{1}\\{2}'.format(self._folder_path_, today,
                                             FridgeDataSender._T_file_ext_)
        temperature_files = glob.glob(T_directory)
        file_count = len(temperature_files)
        if file_count != 5:
            raise FileNotFoundError(T_directory,
                                    "Temperature log not present " +
                                    "({0}/5 files found on BlueFors desktop)!"
                                    .format(file_count))
        T = [self._read_temperature_(file) for file in temperature_files]
        return {'PT1': T[0], 'PT2': T[1], 'Magnet': T[2],
                'Still': T[3], 'MC': T[4]}

    def _read_pressure_(self, file_path):
        P = FridgeDataSender._get_tail_line_(file_path)
        time = '{0} {1}'.format(P[0], P[1])
        return {'P1': float(P[5]), 'P2': float(P[11]), 'P3': float(P[17]),
                'P4': float(P[23]), 'P5': float(P[29]), 'P6': float(P[35]),
                'time': time}

    def get_pressures(self):
        today = datetime.now().strftime('%y-%m-%d')
        P_directory = '{0}\\{1}\\{2}'.format(self._folder_path_, today,
                                             FridgeDataSender._P_file_ext_)
        pressure_files = glob.glob(P_directory)
        file_count = len(pressure_files)
        if file_count != 1:
            raise FileNotFoundError(P_directory,
                                    "Pressure log not present " +
                                    "({0}/1 files found on BlueFors desktop)!"
                                    .format(file_count))
        return self._read_pressure_(pressure_files[0])

    def get_status(self, item):
        today = datetime.now().strftime('%y-%m-%d')
        E_directory = '{0}\\{1}\\{2}'.format(self._folder_path_, today,
                                             FridgeDataSender._E_file_ext_)
        status_files = glob.glob(E_directory)
        file_count = len(status_files)
        if file_count != 1:
            raise FileNotFoundError(E_directory,
                                    "Error log not present " +
                                    "({0}/1 files found on BlueFors desktop)!"
                                    .format(file_count))
        return self._read_status_(status_files[0], item)

    def _read_status_(self, file_path, name):
        E = FridgeDataSender._get_tail_line_(file_path)
        try:
            index = E.index(name)
            return float(E[index + 1])
        except ValueError:
            return None

    def get_datetime(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


class BlueforsApp:
    """ App that reads the bluefors logs and periodically reports temperatures on the given port.

    To create an executable that runs on windows first install pyinstall via: pip install pyinstall
    then run pyinstall BluforsMonitorApp.py from the command line. This creates a directory dist were the
    BlueforsApp.exe can be found and ran.
    """
    _short_options_ = "?hd:u:p:n:"
    _long_options_ = ['--help', '--dir', '--un', '--pw', '--port']

    def __init__(self):
        self._directory_ = ''
        self._username_ = None
        self._password_ = None
        self._port_ = 8080

    def print_header(self):
        print("\n### BLUEFORS Data Proxy ###")
        print(" QuTech 2017, Delft, The Netherlands, www.qutech.nl\n")

    def print_usage(self, status=0):
        self.print_header()
        print(' BlueForsMonitor.exe [options]')
        print('    [-h, -?, --help]   print usage information')
        print('    [-d, --dir]        sets the log-data directory')
        print('    [-n, --port]       sets the proxy port number\n')
        print('    [-u, --user]       sets the server username')
        print('    [-p, --pw]         sets the server password')
        sys.exit(status)

    def print_settings(self):
        self.print_header()
        print(' Starting proxy with settings:')
        print("    directory : {0}".format(self._directory_))
        print("    portnumber : {0}".format(self._port_))
        print("    username : {0}".format(self._username_))
        print("    password : {0}\n".format(self._password_))

    def set_password(self, password: str):
        self._password_ = password

    def set_username(self, username: str):
        self._username_ = username

    def set_portnumber(self, port: str):
        try:
            self._port_ = int(port)
        except ValueError:
            self.print_usage(2)

    def set_directory(self, directory: str):
        print(directory)
        self._directory_ = directory

    def check_directory(self):
        today = datetime.now().strftime('%y-%m-%d')
        directory = '{0}\\{1}'.format(self._directory_, today)
        if not os.path.exists(directory):
            print('Directory ({0}) does not exist!\n'.format(directory))
            self.print_usage(3)

    def main(self, argv):
        if len(argv) < 2:
            self.print_usage(1)
        try:
            options, arguments = getopt.getopt(argv[1:],
                                               BlueforsApp._short_options_,
                                               BlueforsApp._long_options_)
        except getopt.GetoptError:
            self.print_usage(-1)
        print(options)
        for option, argument in options:
            if option in ('-?', '-h', '--help'):
                self.print_usage()
            elif option in ("-u", "--un"):
                self.set_username(argument)
            elif option in ("-p", "--pw"):
                self.set_password(argument)
            elif option in ("-d", "--dir"):
                self.set_directory(argument)
            elif option in ("-n", "--port"):
                self.set_portnumber(argument)
        self.print_settings()
        self.check_directory()
        FridgeDataSender(self._directory_, port=self._port_,
                         user=self._username_, password=self._password_)


if __name__ == '__main__':
    BlueforsApp().main(sys.argv)
