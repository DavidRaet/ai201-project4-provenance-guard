import subprocess
import time
import sys

def run_applications():
    print("Starting python app.py and python gradio_app.py...")
    
    # Start both scripts as subprocesses
    process1 = subprocess.Popen([sys.executable, "app.py"])
    process2 = subprocess.Popen([sys.executable, "gradio_app.py"])
    
    print("Both apps are running. Press Ctrl+C to stop both.")
    
    try:
        # Keep the main script alive while monitoring the sub-processes
        while True:
            # Check if either process has exited unexpectedly
            if process1.poll() is not None:
                print("app.py stopped unexpectedly.")
                break
            if process2.poll() is not None:
                print("gradio_app.py stopped unexpectedly.")
                break
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping both applications...")
    finally:
        # Clean up and terminate both processes safely
        process1.terminate()
        process2.terminate()
        
        # Wait a moment for them to close
        process1.wait()
        process2.wait()
        print("Both apps have been stopped.")

if __name__ == "__main__":
    run_applications()