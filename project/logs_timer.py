"""
Modul helper funkcija za zadatak 3
"""
import operator
import time


def first_diff(path_to_access_file):
    """Helper function za prvi pristup, da se uoče razlike.

    Prvi pristup access_log.txt file-u dohvata sav sadržaj.
    Tek nakon 10 sekundi, uspoređuje se access_log.txt ponovno
    sa starim sadržajem, koji je predstavljen sa "diffs_" varijablom.
    Razlike u zapisu access_log.txt se zapisuju, tj. razlike svakih
    10 sekundi.

    :param path_to_access_file: putanja do access_log.txt
    :return: diffs_, sorted_freq
    """
    with open(path_to_access_file) as access_log:
        diffs_ = access_log.readlines()  # Dohvati sve linije u access_log.txt
        words = ' '.join(diffs_).replace('\n', '').split(' ')  # Sve riječi
        # Prebrojavanje riječi upotrebom dict comprehension
        freq_counter = {key: words.count(key) for key in words}
        # Dohvatanje najčešće 3 riječi. Riječ je zadataka od razmaka do razmaka
        # tako da riječ može biti i '-'.
        sorted_freq = sorted(freq_counter.items(), key=operator.itemgetter(1))[-3::]
        sorted_freq = list(reversed(sorted_freq))
        return diffs_, sorted_freq


def diffs(path_to_diff_log, diff, sorted_freq):
    """Helper function za sve ostale razlike.

    Funkcija koja uspoređuje razlike u vremenskim intervalim
    i zapisuje u *diffs.txt*.
    """
    with open(path_to_diff_log, 'r+') as result:
        result.write('ACCESS_LOG.txt\n')
        # TODO: Najčešće riječi zadnje
        while True:
            line = result.readline()
            if line == '=== NAJCESCE RIJECI ===\n':
                break
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
