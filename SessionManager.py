# SessionManager.py
import threading
import logging

class SessionManager:
    """会话管理核心类"""
    
    def __init__(self):
        self.active_sessions = {}  # {session_id: (conn, addr)}
        self.current_session = None
        self.lock = threading.Lock()
        self.session_counter = 0
        logging.info("会话管理器已初始化")

    def add(self, conn, addr):
        """添加新会话"""
        with self.lock:
            self.session_counter += 1
            self.active_sessions[self.session_counter] = (conn, addr)
            return self.session_counter

    def remove(self, session_id):
        """移除指定会话"""
        with self.lock:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                if self.current_session == session_id:
                    self.current_session = None
                logging.info(f"会话 {session_id} 已移除")

    def select(self, session_id):
        """选择当前活动会话"""
        with self.lock:
            if session_id in self.active_sessions:
                self.current_session = session_id
                return True
            return False

    def get_current_connection(self):
        """获取当前会话的连接对象"""
        with self.lock:
            return self.active_sessions.get(self.current_session, (None, None))[0]
