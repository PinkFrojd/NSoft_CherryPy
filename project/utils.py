import os
import platform
import sqlite3

DATABASE = 'sample.db'


def get_information():
    """Utility function for collecting all information about system.

    :return: dict info: dictionary with information which
                        acts as (key, value) pair
    """

    info = {}

    # info['Version_of_kernel'] = platform.release()

    info['Name_and_version_of_distribution'] = ' '.join(platform.dist()[:2])

    # Processor information
    with open(os.path.join('/', 'proc', 'cpuinfo')) as processor_file:

        vendor_id = model_name = cpu_mhz = cpu_cores = ""

        line = processor_file.readline()
        while line:
            line = line.replace('\t', '').replace(' ', '')

            try:
                separator_index = line.index(':') + 1
            except ValueError:
                line = processor_file.readline()
                continue

            if line.startswith('vendor_id'):
                vendor_id = "vendor_id: "
                vendor_id += line[separator_index:].strip()
            elif line.startswith('modelname'):
                model_name = "model_name: "
                model_name += line[separator_index:].strip()
            elif line.startswith('cpuMHz'):
                cpu_mhz = "cpu_frequency: "
                cpu_mhz += line[separator_index:].strip()
            elif line.startswith('cpucores'):
                cpu_cores = "cpu_cores: "
                cpu_cores += line[separator_index:].strip()

            line = processor_file.readline()

        info['Processor'] = vendor_id + " "
        info['Processor'] += model_name + " "
        info['Processor'] += cpu_mhz + " "
        info['Processor'] += cpu_cores + " "

    # Ukupna ram memorija(na sta se tocno odnosi 'memorija') ???
    with open(os.path.join('/', 'proc', 'meminfo')) as memory_file:
        memory_in_kb = memory_file.readline().replace('\t', '').replace(' ', '')
        separator_index = memory_in_kb.index(':') + 1

        info['Processor'] += 'ram_memory: ' + memory_in_kb[separator_index:].strip()

    info['Firmware'] = 'dummy firmware model '
    info['Firmware'] += 'dummy serial number '
    info['Firmware'] += 'dummy firmware version'

    info['Disks'] = 'dummy capacity'

    return info


def setup():
    """Function to create table in database on startup.

    Utility function that gets executed at the server startup.
    It creates table *information* if it doesn't exist and adds columns
    that represent each information separately.

    :return: None
    """
    with sqlite3.connect(DATABASE) as con:
        con.execute("CREATE TABLE IF NOT EXISTS information (version_of_kernel,"
                    "name_and_version_of_distribution,"
                    "processor,"
                    "firmware,"
                    "disks_memory)")


def cleanup():
    """Function to clear table at the end.

    Utility function that destroys *information* table
    on server shutdown because CherryPy is multi-threaded.
    SQLite in python forbids sharing a connection between threads.

    :return: None
    """
    with sqlite3.connect(DATABASE) as con:
        con.execute("DROP TABLE information")
