import difflib
import operator
import platform
import json
import sqlite3
import time
import os
import subprocess
import signal

import cherrypy

DATABASE = 'sample.db'
PROCESSES_EXECUTED = []  # List for /status route


class ProcessControl(object):

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
            except Exception as e:
                raise ValueError('No process named: {}'.format(process))

        # Svi pokrenuti procesi i PID-ovi za /status rutu
        for _p in range(len(process_names)):
            PROCESSES_EXECUTED.append({'name': process_names[_p],
                                       'PID': process_pids[_p]})


        # Response je lista svih PID-ova
        return [int(p) for p in process_pids]

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

    # Zadatak 2 i 4
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def information(self):
        with sqlite3.connect(DATABASE) as c:
            c.execute("INSERT INTO information VALUES (?, ?, ?)",
                      [platform.platform(),
                       platform.architecture()[0] + platform.version(),
                       platform.processor()]
                      )
            r = c.execute("SELECT * FROM information")
            kern, nv, proc = list(r.fetchone())
            resp = {'kernel_version': kern,
                    'name_and_version_of_dist': nv,
                    'processor': proc
                    }

        return json.dumps(resp)

    # Zadatak 3
    @cherrypy.expose
    def logs(self, *custom_log):

        print(custom_log)
        path_to_access_file = os.path.join(*[str(path_) for path_ in custom_log])
        path_to_diff_log = os.path.join(os.getcwd(), 'diff.txt')

        first_time = True
        diffs = []
        sorted_freq = []

        while True:
            yield bytes('Streaming request for diff between log files...\n', 'utf-8')

            if first_time:
                with open(path_to_access_file) as access_log:
                    diffs = access_log.readlines()
                    words = ' '.join(diffs).replace('\n', '').split(' ')
                    freq_counter = {key: words.count(key) for key in words}
                    sorted_freq = sorted(freq_counter.items(), key=operator.itemgetter(1))[-3::]
                    sorted_freq = list(reversed(sorted_freq))
                first_time = False
                time.sleep(5)
            else:
                print('Here I come with diffs')
                with open(path_to_access_file) as access_log:
                    access_log_lines = access_log.readlines()
                    diff = difflib.ndiff(access_log_lines, diffs)
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
    logs._cp_config = {'response.stream': True}


# Vezano za Zadatak 4, te ujedno i 2.
def setup():
    with sqlite3.connect(DATABASE) as con:
        con.execute("CREATE TABLE IF NOT EXISTS information (kernel_version,"
                    "name_and_version_of_dist,"
                    "processor)")

# Vezano za Zadatak 4, te ujedno i 2.
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
