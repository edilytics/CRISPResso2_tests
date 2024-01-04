import subprocess
import sys
import time

# TODO: collect baseline measures for commands of interest
# We are more interested in larger jobs, so we can see any 
# performance improvements.
# - Cole suggested a batch run, there may be a batch run in tests
# - We can run the make commands

def main():
    command = "alias python='python3' && " + sys.argv[1]
    start = time.time()
    subprocess.run(command, shell=True, stderr=subprocess.STDOUT, text=True)
    end = time.time()
    duration = end - start
    print(f"Duration: {duration} seconds")

if __name__ == '__main__':
    main()
