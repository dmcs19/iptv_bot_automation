import subprocess

def update_epg():
    subprocess.run(
                    ['python', 'update_epg.py'],
                    capture_output=True,
                    text=True
                )
    
    return