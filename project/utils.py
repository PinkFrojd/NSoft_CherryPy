import platform
import sqlite3

DATABASE = 'sample.db'


def get_information():
    """Utility function for collecting all information about system.

    :return: dict info: dictionary with information which
                        acts as (key, value) pair
    """

    info = {}

    info['Version_of_kernel'] = platform.release()

    info['Name_and_version_of_distribution'] = platform.architecture()[0] + " "
    info['Name_and_version_of_distribution'] += platform.version()

    info['Processor'] = 'dummy proizvodjac '
    info['Processor'] += 'dummy model '
    info['Processor'] += 'dummy frequency '
    info['Processor'] += 'dummy cores '
    info['Processor'] += 'dummy processor memory'

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
