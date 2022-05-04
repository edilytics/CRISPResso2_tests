"""CRISPResso Web Celery Load Balancer Test.

Description: This script will stress test the CRISPResso Web server to see how
it performs under a load.

main contributor: Jeffrey Forte
Date: 1/23/2022
Company: Edylitics
"""

import os
from datetime import datetime
from subprocess import check_output, Popen
from tqdm import tqdm
import time
import requests

REQUEST_NUM = 500  # Change this number to change number of requests sent
CONTAINER_NAME = 'c2web_stress_test'
PORT_NUM = 1234
LOG_FILE_PATH = './stress_test_log.txt'


def sleep():
    """Sleep to allow server to boot."""
    for i in tqdm(range(15)):
        time.sleep(1)
    print("Server Booted")


def boot_server():
    """Run the Docker web server."""
    print("Sever Booting...")
    # Subprocess Command
    running_container_id = check_output(
        ['docker', 'ps', '-aq', '-f', 'name={0}'.format(CONTAINER_NAME)],
    ).decode('utf-8').strip()
    if running_container_id:
        os.system('docker rm -f {0}'.format(running_container_id))
    cmd = 'docker run --name {0} --rm -p {1}:80 -it crispresso2web'.format(
        CONTAINER_NAME,
        PORT_NUM,
    )
    with open(LOG_FILE_PATH, 'w') as out:
        return_code = Popen(cmd.split(), stdout=out)
    pid = return_code.pid
    print('Process ID: {0}'.format(pid))
    return pid


def count_jobs(p):
    """Count the number of jobs that are submitted."""
    # Record Start Time
    now = datetime.now()
    scan_start = now.strftime('%H:%M:%S')
    print('Scan Initiated at: {0}'.format(scan_start))

    scan_start, scan_complete = 0, 0
    with tqdm(total=REQUEST_NUM, leave=False) as pbar:
        with open(LOG_FILE_PATH) as log_fh:
            while scan_complete < REQUEST_NUM:
                for line in log_fh:
                    scan_start += line.count('Started run:')
                    scan_complete += line.count('Deleting processed files...')
                    pbar.update(scan_complete)
                if scan_complete < REQUEST_NUM:
                    time.sleep(10)
    pbar.close()
    end = datetime.now()  # Clock End of Scan
    scan_end = end.strftime('%H:%M:%S')
    print('Scan Completed at: {0}'.format(scan_end))

    if scan_complete >= REQUEST_NUM:
        os.system('docker kill {0}'.format(CONTAINER_NAME))


def test_server(p):
    """Run the stress test."""
    sleep()  # sleep for 15 seconds

    sub_data = {
        'demo_used': 'multi-allele',
        'max_upload': 104857600,
        'seq_design': 'single',
        'active_paired_samples': 1,
        'active_single_samples': 1,
        'paired_sample_1_name': 'Sample_1',
        'paired_sample_1_fastq_r1': '',
        'paired_sample_1_fastq_r2': '',
        'paired_sample_1_amplicon': '', 'paired_sample_1_sgRNA': '', 'single_sample_1_name': 'Sample_1',
        'single_sample_1_fastq_se': '',
        'single_sample_1_amplicon': 'CGAGAGCCGCAGCCATGAACGGCACAGAGGGCCCCAATTTTTATGTGCCCTTCTCCAACGTCACAGGCGTGGTGCGGAGCCACTTCGAGCAGCCGCAGTACTACCTGGCGGAACCATGGCAGTTCTCCATGCTGGCAGCGTACATGTTCCTGCTCATCGTGCTGGG, CGAGAGCCGCAGCCATGAACGGCACAGAGGGCCCCAATTTTTATGTGCCCTTCTCCAACGTCACAGGCGTGGTGCGGAGCCCCTTCGAGCAGCCGCAGTACTACCTGGCGGAACCATGGCAGTTCTCCATGCTGGCAGCGTACATGTTCCTGCTCATCGTGCTGGG',
        'single_sample_1_sgRNA': 'GTGCGGAGCCACTTCGAGCAGC',
        'optional_name': '',
        'amplicon_names': 'P23H, WT',
        'optradio_hs': 60,
        'be_from': 'C',
        'be_to': 'T',
        'pe_spacer_seq': '',
        'pe_ext_seq': '',
        'optradio_pe_ws': 5,
        'pe_nicking_seq': '',
        'pe_scaffold_seq': '',
        'optradio_wc': -3,
        'optradio_ws': 1,
        'optradio_ps': 20,
        'hdr_seq': '',
        'exons': '',
        'optradio_qc': 0,
        'optradio_qs': 0,
        'optradio_qn': 0,
        'optradio_exc_l': 15,
        'optradio_exc_r': 15,
        'optradio_trim': '',
        'email': ''
    }
    print(f'Initiating Celery Stress Test of {REQUEST_NUM} sample Jobs... \n')

    # Send POST requests to web console to run sample job

    for _ in tqdm(range(REQUEST_NUM)):
        requests.post(
            'http://127.0.0.1:{0}/submit'.format(PORT_NUM),
            data=sub_data,
        )
    print('\nJob Requests have been sent. Clocking time now...')

    # TODO: Take time difference and output as total time to run 500 jobs

    # TODO: Search for any errors in log and output
    # Search Error Logs for "Exceptions"
    # dock_id = os.system(
    #     "docker ps -aqf 'status=running'")
    # error_output = os.system(
    #     f"docker exec -it {dock_id} cat /var/log/apache2/error.log")
    # print(error_output)

    # TODO: Cat the logging of first scan vs last scan.
    count_jobs(p)


if __name__ == '__main__':
    SERVER_PID = boot_server()
    test_server(SERVER_PID)
