import difflib
import operator
import sqlite3
import time
import os
import subprocess
import signal

import cherrypy

from project import utils

PROCESSES_EXECUTED = []  # List for /status route


class ProcessControl(object):

    @cherrypy.expose
    def index(self):
        return "Dummy Welcome"

    @cherrypy.expose
    def start(self):
        """Zadatak 1 - *start*

        Pokrenuti arbitrarni proces (npr neki browser)
        te vratiti informaciju o pidu.

        :returns: [int] process_pids: Lista PID-ova pokrenutih procesa
        """

        global PROCESSES_EXECUTED

        # Putanja do arbitrarnih procesa
        gedit_path = os.path.join('/', 'usr', 'bin', 'gedit')
        sublime_path = os.path.join('/', 'usr', 'bin', 'subl')

        # Pokretanje arbitrarnih procesa
        subprocess.Popen([gedit_path], shell=True)
        subprocess.Popen([sublime_path], shell=True)

        process_names = ['gedit', 'sublime_text']
        process_pids = []

        for process in process_names:
            try:
                # Dohvatanje PID-a procesa ako postoji
                process_pids.append(int(subprocess.check_output(['pidof', '-s', process])))
            except Exception:
                raise ValueError('No process named: {}'.format(process)) from None

        # Svi pokrenuti procesi i PID-ovi za /status rutu
        for _p in range(len(process_names)):
            PROCESSES_EXECUTED.append({'name': process_names[_p],
                                       'PID': process_pids[_p]})

        # Response je serijalizirana lista PID-ova pretvorenih u string.
        return [int(p) for p in process_pids]

    @cherrypy.expose
    def stop(self, pid):
        """Zadatak 1 - *stop*

        Zaustaviti proces sa proslijedjenim pidom.
        """

        try:
            os.kill(int(pid), signal.SIGKILL)
            return 'Process with PID {} terminated'.format(pid)
        except ProcessLookupError:
            return 'Process with PID {} does not exist'.format(pid)
        except ValueError:
            return 'Invalid PID entered'
        finally:
            return 'Something else happened...'

    @cherrypy.expose
    def status(self):
        """Zadatak 1 - *status*

        Ispisati listu procesa (tj njihovih pidova) koje
        smo pokrenuli funkcionalnoscu iz prve tocke.

        :returns: str resp: Lista sa imenom i prikaldnim PID-om procesa
        """

        return [process.get('name') + ' ' + str(process.get('PID')) + ' '
                for process in PROCESSES_EXECUTED]

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def information_zadatak_2(self):
        """Zadatak 2 - Information Flow

        Prikupiti razne informacije o sustavu te ih vratit u
        JSON formatu. Ujedno se prikupljene informacije unose
        u tablicu *information*.

        :returns: JSON object
        """

        # Prikupljanje svih potrebnih informacija
        info = utils.get_information()

        with sqlite3.connect(utils.DATABASE) as c:
            c.execute("INSERT INTO information VALUES (?, ?, ?, ?, ?)",
                      [info.get('Version_of_kernel'),
                       info.get('Name_and_version_of_distribution'),
                       info.get('Processor'),
                       info.get('Firmware'),
                       info.get('Disks')]
                      )

        return info

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def information_zadatak_4(self):
        """Zadatak 4 - Information Flow Nadopunjen

        Sve informacije se dohvataju iz tablice *information* i
        vraćaju u JSON formatu.

        :returns: JSON object
        """
        with sqlite3.connect(utils.DATABASE) as c:
            r = c.execute("SELECT * FROM information")
            helper_info = list(r.fetchone())
            # BUG: r.fetchone().keys() ne postoji ?
            info = {'Version_of_kernel': helper_info[0],
                    'Name_and_version_of_distribution': helper_info[1],
                    'Processor': helper_info[2],
                    'Firmware': helper_info[3],
                    'Disks': helper_info[4]
                    }

        return info

    @cherrypy.expose
    # /logs ruta streama response sa yield (omogućeno na dnu metode)
    def logs(self, *custom_log):

        # Putanja do access_log.txt
        path_to_access_file = os.path.join(*[str(path_) for path_ in custom_log])
        # Putanja gdje će se razlike zapisivat
        path_to_diff_log = os.path.join(os.getcwd(), 'diff.txt')

        first_time = True
        diffs = []
        sorted_freq = []

        while True:

            yield bytes('Streaming request for diff between log files...\n', 'utf-8')

            if first_time:
                # Prvi pristup access_log.txt file-u dohvata sav sadržaj.
                # Tek nakon 10 sekundi, uspoređuje se access_log.txt ponovno
                # sa starim sadržajem, koji je predstavljen sa "diffs" varijablom.
                # Razlike u zapisu access_log.txt se zapisuju, tj. razlike svakih
                # 10 sekundi.
                with open(path_to_access_file) as access_log:
                    diffs = access_log.readlines()  # Dohvati sve linije u access_log.txt
                    words = ' '.join(diffs).replace('\n', '').split(' ')  # Sve riječi
                    # Prebrojavanje riječi upotrebom dict comprehension
                    freq_counter = {key: words.count(key) for key in words}
                    # Dohvatanje najčešće 3 riječi. Riječ je zadataka od razmaka do razmaka
                    # tako da riječ može biti i '-'.
                    sorted_freq = sorted(freq_counter.items(), key=operator.itemgetter(1))[-3::]
                    sorted_freq = list(reversed(sorted_freq))
                first_time = False
                time.sleep(10)  # 10 sekundi čekanje
            else:
                with open(path_to_access_file) as access_log:
                    access_log_lines = access_log.readlines()
                    # Razlika između sadržaja access_log.txt prije 10 sekundi
                    # te access_log.txt u sadašnjem trenutku.
                    diff = difflib.ndiff(access_log_lines, diffs)

                # Otvaranje file radi čitanja i pisanja
                # TODO: Napravit da se unose najcesce rijeci kao zadnji sadrzaj
                with open(path_to_diff_log, 'r+') as result:
                    result.write('ACCESS_LOG.txt\n')
                    result.read()
                    result.write('=== RAZLIKA ===\n')
                    for line in diff:
                        if line.startswith('- '):
                            result.write(line.replace('- ', '', 1))
                    result.write('=== VRIJEME ZAPISA ===\n')
                    result.write(time.ctime())
                    result.write('\n=== NAJCESCE RIJECI ===\n')
                    for word in sorted_freq:
                        result.write(word[0] + " ")
                    result.write('\n')
                time.sleep(10)
    logs._cp_config = {'response.stream': True}  # Za streaming requests


if __name__ == '__main__':

    cherrypy.engine.subscribe('start', utils.setup)
    cherrypy.engine.subscribe('stop', utils.cleanup)

    cherrypy.quickstart(ProcessControl(), '/', "app.conf")

