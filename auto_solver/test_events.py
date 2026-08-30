import subprocess, json, sys, time

def test_events():
    payloads = [
        {"event": "prompt", "text": "reply hello"},
        {"event": "turn", "text": "reply hello"},
        {"event": "user_input", "text": "reply hello"},
        {"event": "USER_INPUT", "text": "reply hello"},
        {"event": "message", "text": "reply hello"},
        {"event": "request", "text": "reply hello"},
        {"type": "USER_INPUT", "content": "reply hello", "event": "prompt"},
        {"event": "run", "text": "reply hello"},
        {"event": "start", "text": "reply hello"},
        {"event": "chat", "text": "reply hello"},
    ]
    
    for p in payloads:
        print(f"Testing: {p}")
        proc = subprocess.Popen(['agy', '--input-format', 'stream-json', '--output-format', 'stream-json'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        proc.stdin.write(json.dumps(p) + '\n')
        proc.stdin.flush()
        
        # Wait a bit
        time.sleep(1)
        # Terminate and read
        proc.terminate()
        stdout, stderr = proc.communicate()
        print("STDOUT:", stdout[-200:])
        print("STDERR:", stderr[-200:])

if __name__ == '__main__':
    test_events()
