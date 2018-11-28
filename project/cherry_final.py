import difflib
import operator
import platform
import sqlite3
import time
import os
import subprocess
import signal
import json

import cherrypy

DATABASE = 'sample.db'
PROCESSES_EXECUTED = []  # List for /status route


class ProcessControl(object):

    @cherrypy.expose
    def index(self):
        return "Dummy Welcome"

    # Zadatak 1 - Start, Stop i Status
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def start(self):

        global PROCESSES_EXECUTED

        # Arbitrarni procesi 
        gedit_path = os.path.join('/', 'usr', 'bin', 'gedit')
        sublime_path = os.path.join('/', 'usr', 'bin', 'subl')

        # Pokretanje arbitrarnih procesa
        subprocess.Popen([gedit_path], shell=True)
        subprocess.Popen([sublime_path], shell=True)      

        process_names = ['gedit', 'sublime_text']

        process_pids = []

        for process in process_names:
            try:
                # Dohvatanje PID-a procesa
                process_pids.append(int(subprocess.check_output(['pidof', '-s', process])))
            except Exception:
                raise ValueError('No process named: {}'.format(process))

        # Svi pokrenuti procesi i PID-ovi za /status rutu
        for _p in range(len(process_names)):
            PROCESSES_EXECUTED.append({'name': process_names[_p],
                                       'PID': process_pids[_p]})

        # Response je lista svih PID-ova
        return json.dumps([int(p) for p in process_pids])

    @cherrypy.expose
    def stop(self, pid):

        # Prosljedjeni pid parametar završava proces sa odgovarajućim PID-om

        try:
            os.kill(int(pid), signal.SIGKILL)
            return 'Process with PID {} terminated'.format(pid)
        except ProcessLookupError:
            return 'Process with PID {} does not exist'.format(pid)
        except ValueError:
            return 'Invalid PID entered'

    @cherrypy.expose
    def status(self):

        # Vraća se lista sa imenom procesa i njegovim PID-om.
        # (For petlja jer response ne treba biti JSON)

        resp = ''

        for process in PROCESSES_EXECUTED:
            print(process.get('name'), process.get('PID'))
            resp += '\n' + process.get('name') + ' ' + str(process.get('PID')) + '\n\n'

        return resp

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def information(self):

        with sqlite3.connect(DATABASE) as c:
            # Unos u bazu podatka u tablicu "information"
            c.execute("INSERT INTO information VALUES (?, ?, ?)",
                      [platform.platform(),
                       platform.architecture()[0] + platform.version(),
                       platform.processor()]
                      )

            # Čitanje zapisanog iz tablice "information".
            r = c.execute("SELECT * FROM information")
            kern, nv, proc = list(r.fetchone())  # List assignament ili otpakovanje
            resp = {'kernel_version': kern,
                    'name_and_version_of_dist': nv,
                    'processor': proc
                    }

            return resp

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


# Pravimo tablicu "information" ako ne postoji na početku izvršavanja
# TODO: Nadopunit stupce tablice prikladnim informacijama
def setup():
    with sqlite3.connect(DATABASE) as con:
        con.execute("CREATE TABLE IF NOT EXISTS information (kernel_version,"
                    "name_and_version_of_dist,"
                    "processor)")


# Čišćenje baze podataka na kraju
def cleanup():
    with sqlite3.connect(DATABASE) as con:
        con.execute("DROP TABLE information")


if __name__ == '__main__':
    cherrypy.engine.subscribe('start', setup)
    cherrypy.engine.subscribe('stop', cleanup)

    conf = {
        '/': {
            'log.access_file': './access_log.txt',
        }
    }

    cherrypy.quickstart(ProcessControl(), '/', conf)

