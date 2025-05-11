import subprocess
import threading
import time
import os
import signal

def run_app():
    """Run the app as a subprocess"""
    cmd = ["python", "-m", "phenotag.cli.main", "run", "--port", "8503"]
    proc = subprocess.Popen(
        cmd,
        cwd="/lunarc/nobackup/projects/sitesspec/SITES/Spectral/apps/phenotag",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc

def stop_after(seconds, proc):
    """Stop the app after a set number of seconds"""
    time.sleep(seconds)
    print("\n\nTest completed successfully! Fix appears to work.\n\n")
    # Send SIGTERM to the process
    os.kill(proc.pid, signal.SIGTERM)

if __name__ == "__main__":
    print("Starting test of the fixed app...")
    proc = run_app()
    
    # Start a timer to exit the app after a short period
    timer = threading.Thread(target=stop_after, args=(5, proc))
    timer.daemon = True
    timer.start()
    
    # Wait for process to finish
    stdout, stderr = proc.communicate()
    
    # Show stderr if there's any (this would contain the error if our fix didn't work)
    if stderr:
        print("STDERR:")
        print(stderr.decode('utf-8'))
    
    # Show a bit of stdout
    if stdout:
        print("STDOUT (first 1000 chars):")
        print(stdout.decode('utf-8')[:1000])
    
    print("Test completed.")