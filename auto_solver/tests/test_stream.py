import subprocess, json, select, time, sys

def test_json(payload):
    print(f"Testing: {payload}")
    p = subprocess.Popen(['agy', '--input-format', 'stream-json', '--output-format', 'stream-json'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Read init
    while True:
        line = p.stdout.readline()
        if not line: break
        if '"init"' in line: break
        
    p.stdin.write(json.dumps(payload) + '\n')
    p.stdin.flush()
    
    start = time.time()
    while time.time() - start < 3:
        # Check if there is data
        import msvcrt
        # On windows we can't easily select on pipes. We'll just read with a thread or let it block if we're careful.
        # Actually I can just do this in a thread.
        pass
        
    p.kill()
