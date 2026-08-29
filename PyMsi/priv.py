"""PyMsi.priv — 🔐 进程权限提升模块 (1.5.5 新增)

以特定权限打开进程:
    Windows: 管理员 → SYSTEM / TrustedInstaller (NSudo 技术链)
    Linux:   普通用户 → root (通过 sudo / pkexec)

⚠️ 权限要求:
    - Windows: 需要管理员 UAC 提权 (不能绕过 UAC!)
    - Linux: 需要 sudo 权限 (不能绕过 sudo 认证!)
    本模块在已有管理员/sudo 权限的基础上, 进一步提升到 SYSTEM/root

═══════════════════════════════════════════════════════════════
Windows SYSTEM 提升链 (管理员 → SYSTEM):
═══════════════════════════════════════════════════════════════
    1. AdjustTokenPrivileges: 开启 SeDebugPrivilege (调试特权)
    2. OpenProcess: 打开 winlogon.exe (SYSTEM 身份的系统进程)
    3. OpenProcessToken: 读取 SYSTEM 进程的访问令牌
    4. DuplicateTokenEx: 复制令牌为主令牌 (Primary Token)
    5. SetTokenInformation: 修正会话 ID (防止 GUI 窗口在错误桌面)
    6. CreateEnvironmentBlock: 生成环境变量块
    7. CreateProcessWithTokenW: 用主令牌创建进程 → SYSTEM 身份运行

Windows TrustedInstaller 提升链:
    1. 启动 TrustedInstaller 服务 → 短暂生成 TI 进程
    2. 抓取 TrustedInstaller 进程令牌
    3. 复制令牌
    4. 停止服务
    5. 用 TI 令牌创建进程

配套操作:
    - SetTokenInformation: 修改令牌完整性级别 (高完整性)
    - AdjustTokenPrivileges: 按需开启 SeBackup/SeRestore 等特权
    - 会话 ID 修正: 防止 GUI 程序窗口看不见

⚠️ Devil Mode (恶魔模式) 未实现:
    恶魔模式会 Hook ntdll.dll Nt 系列原生 API, 在底层系统调用时
    偷偷传入备份还原访问标记, 绕过部分文件/注册表安全检查。
    属于用户态 Hook, 不是内核驱动。
    出于安全考虑, 本模块不实现此功能。

用法:
    import PyMsi as PM

    # Windows: 以 SYSTEM 权限运行
    PM.priv.system("notepad.exe")
    PM.priv.system("C:/Windows/System32/cmd.exe")

    # Windows: 以 TrustedInstaller 权限运行
    PM.priv.trusted("notepad.exe")

    # Windows: 以管理员运行 (UAC 提权)
    PM.priv.admin("notepad.exe")

    # Linux: 以 root 运行
    PM.priv.system("ls /root")
    PM.priv.root("whoami")

    # 查看当前身份
    PM.priv.whoami()

    # 检查权限
    PM.priv.is_admin()
    PM.priv.is_system()

    # 查看可用的提升级别
    PM.priv.levels()

    # 别名: PM.su / PM.runas / PM.elevate / PM.提权 / PM.权限
"""

import os
import sys
import subprocess
import platform


# ═══════════════════════════════════════════════════════════════
# 平台检测
# ═══════════════════════════════════════════════════════════════

_IS_WINDOWS = sys.platform == "win32"
_IS_LINUX = sys.platform.startswith("linux")
_IS_MACOS = sys.platform == "darwin"


# ═══════════════════════════════════════════════════════════════
# Windows 实现 (ctypes → advapi32 / kernel32 / userenv)
# ═══════════════════════════════════════════════════════════════

if _IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    # ─── 常量 ───────────────────────────────────────────

    # Token 访问权限
    TOKEN_QUERY = 0x0008
    TOKEN_DUPLICATE = 0x0002
    TOKEN_ASSIGN_PRIMARY = 0x0001
    TOKEN_ADJUST_PRIVILEGES = 0x0020
    TOKEN_ADJUST_DEFAULT = 0x0080
    TOKEN_ADJUST_SESSIONID = 0x0100
    TOKEN_ALL_ACCESS = 0xF01FF

    # Process 访问权限
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    # 特权
    SE_PRIVILEGE_ENABLED = 0x00000002

    # 安全模拟级别
    SecurityImpersonation = 2

    # Token 类型
    TokenPrimary = 1

    # Token 信息类
    TokenSessionId = 12
    TokenElevation = 20
    TokenIntegrityLevel = 25

    # 进程创建标志
    CREATE_UNICODE_ENVIRONMENT = 0x00000400
    CREATE_NEW_CONSOLE = 0x00000010
    CREATE_NO_WINDOW = 0x08000000

    # 进程快照
    TH32CS_SNAPPROCESS = 0x00000002

    # 服务控制
    SC_MANAGER_CONNECT = 0x0001
    SERVICE_QUERY_STATUS = 0x0004
    SERVICE_START = 0x0010
    SERVICE_STOP = 0x0020
    SERVICE_CONTROL_STOP = 0x00000001
    SERVICE_RUNNING = 0x00000004
    SERVICE_START_PENDING = 0x00000002
    SERVICE_STOPPED = 0x00000001

    # ─── 结构体 ─────────────────────────────────────────

    class LUID(ctypes.Structure):
        _fields_ = [
            ("LowPart", wintypes.DWORD),
            ("HighPart", wintypes.LONG),
        ]

    class LUID_AND_ATTRIBUTES(ctypes.Structure):
        _fields_ = [
            ("Luid", LUID),
            ("Attributes", wintypes.DWORD),
        ]

    class TOKEN_PRIVILEGES(ctypes.Structure):
        _fields_ = [
            ("PrivilegeCount", wintypes.DWORD),
            ("Privileges", LUID_AND_ATTRIBUTES * 1),
        ]

    class STARTUPINFOW(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("lpReserved", wintypes.LPWSTR),
            ("lpDesktop", wintypes.LPWSTR),
            ("lpTitle", wintypes.LPWSTR),
            ("dwX", wintypes.DWORD),
            ("dwY", wintypes.DWORD),
            ("dwXSize", wintypes.DWORD),
            ("dwYSize", wintypes.DWORD),
            ("dwXCountChars", wintypes.DWORD),
            ("dwYCountChars", wintypes.DWORD),
            ("dwFillAttribute", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("wShowWindow", wintypes.WORD),
            ("cbReserved2", wintypes.WORD),
            ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
            ("hStdInput", wintypes.HANDLE),
            ("hStdOutput", wintypes.HANDLE),
            ("hStdError", wintypes.HANDLE),
        ]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("hProcess", wintypes.HANDLE),
            ("hThread", wintypes.HANDLE),
            ("dwProcessId", wintypes.DWORD),
            ("dwThreadId", wintypes.DWORD),
        ]

    class SECURITY_ATTRIBUTES(ctypes.Structure):
        _fields_ = [
            ("nLength", wintypes.DWORD),
            ("lpSecurityDescriptor", ctypes.c_void_p),
            ("bInheritHandle", wintypes.BOOL),
        ]

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", ctypes.c_wchar * 260),
        ]

    class SERVICE_STATUS(ctypes.Structure):
        _fields_ = [
            ("dwServiceType", wintypes.DWORD),
            ("dwCurrentState", wintypes.DWORD),
            ("dwControlsAccepted", wintypes.DWORD),
            ("dwWin32ExitCode", wintypes.DWORD),
            ("dwServiceSpecificExitCode", wintypes.DWORD),
            ("dwCheckPoint", wintypes.DWORD),
            ("dwWaitHint", wintypes.DWORD),
        ]

    class TOKEN_ELEVATION(ctypes.Structure):
        _fields_ = [("TokenIsElevated", wintypes.DWORD)]

    # ─── API 加载 ───────────────────────────────────────

    _advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _userenv = ctypes.WinDLL("userenv", use_last_error=True)

    # 函数原型
    _advapi32.LookupPrivilegeValueW.restype = wintypes.BOOL
    _advapi32.LookupPrivilegeValueW.argtypes = [
        wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.POINTER(LUID)
    ]

    _advapi32.AdjustTokenPrivileges.restype = wintypes.BOOL
    _advapi32.AdjustTokenPrivileges.argtypes = [
        wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(TOKEN_PRIVILEGES),
        wintypes.DWORD, ctypes.POINTER(TOKEN_PRIVILEGES), ctypes.POINTER(wintypes.DWORD)
    ]

    _advapi32.OpenProcessToken.restype = wintypes.BOOL
    _advapi32.OpenProcessToken.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)
    ]

    _advapi32.DuplicateTokenEx.restype = wintypes.BOOL
    _advapi32.DuplicateTokenEx.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(SECURITY_ATTRIBUTES),
        ctypes.c_int, ctypes.c_int, ctypes.POINTER(wintypes.HANDLE)
    ]

    _advapi32.CreateProcessWithTokenW.restype = wintypes.BOOL
    _advapi32.CreateProcessWithTokenW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPWSTR,
        wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR,
        ctypes.POINTER(STARTUPINFOW), ctypes.POINTER(PROCESS_INFORMATION)
    ]

    _advapi32.SetTokenInformation.restype = wintypes.BOOL
    _advapi32.SetTokenInformation.argtypes = [
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD
    ]

    _advapi32.GetTokenInformation.restype = wintypes.BOOL
    _advapi32.GetTokenInformation.argtypes = [
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
        wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)
    ]

    _advapi32.OpenSCManagerW.restype = wintypes.SC_HANDLE
    _advapi32.OpenSCManagerW.argtypes = [
        wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD
    ]

    _advapi32.OpenServiceW.restype = wintypes.SC_HANDLE
    _advapi32.OpenServiceW.argtypes = [
        wintypes.SC_HANDLE, wintypes.LPCWSTR, wintypes.DWORD
    ]

    _advapi32.StartServiceW.restype = wintypes.BOOL
    _advapi32.StartServiceW.argtypes = [
        wintypes.SC_HANDLE, wintypes.DWORD, ctypes.POINTER(ctypes.c_wchar_p)
    ]

    _advapi32.ControlService.restype = wintypes.BOOL
    _advapi32.ControlService.argtypes = [
        wintypes.SC_HANDLE, wintypes.DWORD, ctypes.POINTER(SERVICE_STATUS)
    ]

    _advapi32.QueryServiceStatus.restype = wintypes.BOOL
    _advapi32.QueryServiceStatus.argtypes = [
        wintypes.SC_HANDLE, ctypes.POINTER(SERVICE_STATUS)
    ]

    _advapi32.CloseServiceHandle.restype = wintypes.BOOL
    _advapi32.CloseServiceHandle.argtypes = [wintypes.SC_HANDLE]

    _kernel32.OpenProcess.restype = wintypes.HANDLE
    _kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]

    _kernel32.CloseHandle.restype = wintypes.BOOL
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    _kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    _kernel32.GetCurrentProcess.argtypes = []

    _kernel32.GetCurrentProcessId.restype = wintypes.DWORD
    _kernel32.GetCurrentProcessId.argtypes = []

    _kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    _kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]

    _kernel32.Process32FirstW.restype = wintypes.BOOL
    _kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]

    _kernel32.Process32NextW.restype = wintypes.BOOL
    _kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]

    _kernel32.ProcessIdToSessionId.restype = wintypes.BOOL
    _kernel32.ProcessIdToSessionId.argtypes = [wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]

    _userenv.CreateEnvironmentBlock.restype = wintypes.BOOL
    _userenv.CreateEnvironmentBlock.argtypes = [
        ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.BOOL
    ]

    _userenv.DestroyEnvironmentBlock.restype = wintypes.BOOL
    _userenv.DestroyEnvironmentBlock.argtypes = [ctypes.c_void_p]

    # ─── 辅助函数 ──────────────────────────────────────

    def _win_enable_privilege(privilege_name):
        """开启当前进程的指定特权 (需要管理员 UAC)

        Args:
            privilege_name: "SeDebugPrivilege" / "SeImpersonatePrivilege" 等
        """
        # 打开当前进程令牌
        token_handle = wintypes.HANDLE()
        if not _advapi32.OpenProcessToken(
            _kernel32.GetCurrentProcess(),
            TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
            ctypes.byref(token_handle)
        ):
            raise RuntimeError(
                f"OpenProcessToken 失败 (错误码: {ctypes.get_last_error()})\n"
                f"可能原因: 没有管理员权限, 请以管理员身份运行"
            )

        try:
            # 查找特权 LUID
            luid = LUID()
            if not _advapi32.LookupPrivilegeValueW(None, privilege_name, ctypes.byref(luid)):
                raise RuntimeError(f"LookupPrivilegeValueW 失败: {privilege_name}")

            # 构建 TOKEN_PRIVILEGES
            tp = TOKEN_PRIVILEGES()
            tp.PrivilegeCount = 1
            tp.Privileges[0].Luid = luid
            tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED

            # 调整特权
            if not _advapi32.AdjustTokenPrivileges(
                token_handle, False, ctypes.byref(tp),
                ctypes.sizeof(tp), None, None
            ):
                err = ctypes.get_last_error()
                if err == 1300:  # ERROR_NOT_ALL_ASSIGNED
                    raise RuntimeError(
                        f"AdjustTokenPrivileges: 特权未分配 ({privilege_name})\n"
                        f"可能原因: 当前账户没有此特权, 需要管理员 UAC 提权"
                    )
                raise RuntimeError(f"AdjustTokenPrivileges 失败 (错误码: {err})")
        finally:
            _kernel32.CloseHandle(token_handle)

    def _win_find_process(name):
        """通过进程名查找进程 PID

        Args:
            name: 进程名 (如 "winlogon.exe")
        Returns:
            int: 进程 PID
        """
        name_lower = name.lower()
        snapshot = _kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snapshot == wintypes.HANDLE(-1).value or snapshot == 0:
            raise RuntimeError("CreateToolhelp32Snapshot 失败")

        try:
            entry = PROCESSENTRY32W()
            entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)

            if not _kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
                raise RuntimeError(f"找不到进程: {name}")

            while True:
                if entry.szExeFile.lower() == name_lower:
                    return entry.th32ProcessID
                if not _kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                    break

            raise RuntimeError(f"找不到进程: {name}")
        finally:
            _kernel32.CloseHandle(snapshot)

    def _win_get_process_token(pid):
        """获取指定进程的访问令牌

        Args:
            pid: 进程 PID
        Returns:
            HANDLE: 令牌句柄 (调用者负责 CloseHandle)
        """
        process_handle = _kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
        if not process_handle:
            raise RuntimeError(
                f"OpenProcess 失败 (PID: {pid}, 错误码: {ctypes.get_last_error()})\n"
                f"可能原因: 没有开启 SeDebugPrivilege"
            )

        try:
            token_handle = wintypes.HANDLE()
            if not _advapi32.OpenProcessToken(
                process_handle,
                TOKEN_DUPLICATE | TOKEN_QUERY,
                ctypes.byref(token_handle)
            ):
                raise RuntimeError(
                    f"OpenProcessToken 失败 (错误码: {ctypes.get_last_error()})"
                )
            return token_handle
        finally:
            _kernel32.CloseHandle(process_handle)

    def _win_duplicate_token(token_handle):
        """复制令牌为主令牌 (Primary Token)

        Args:
            token_handle: 源令牌句柄
        Returns:
            HANDLE: 新的主令牌句柄 (调用者负责 CloseHandle)
        """
        new_token = wintypes.HANDLE()
        if not _advapi32.DuplicateTokenEx(
            token_handle,
            TOKEN_ALL_ACCESS,
            None,
            SecurityImpersonation,
            TokenPrimary,
            ctypes.byref(new_token)
        ):
            raise RuntimeError(
                f"DuplicateTokenEx 失败 (错误码: {ctypes.get_last_error()})"
            )
        return new_token

    def _win_get_session_id():
        """获取当前进程的会话 ID"""
        session_id = wintypes.DWORD()
        if not _kernel32.ProcessIdToSessionId(
            _kernel32.GetCurrentProcessId(), ctypes.byref(session_id)
        ):
            return 1  # 默认会话 1
        return session_id.value

    def _win_set_session_id(token_handle, session_id):
        """设置令牌的会话 ID (防止 GUI 窗口在错误桌面)"""
        sid = wintypes.DWORD(session_id)
        if not _advapi32.SetTokenInformation(
            token_handle, TokenSessionId,
            ctypes.byref(sid), ctypes.sizeof(sid)
        ):
            # 非致命错误, 继续执行
            pass

    def _win_create_env_block(token_handle):
        """创建环境变量块"""
        env_ptr = ctypes.c_void_p()
        if not _userenv.CreateEnvironmentBlock(
            ctypes.byref(env_ptr), token_handle, False
        ):
            return None
        return env_ptr

    def _win_create_process_with_token(token_handle, exe_path, env_block=None):
        """用主令牌创建进程

        Args:
            token_handle: 主令牌句牌
            exe_path: 要运行的 exe 路径
            env_block: 环境变量块 (None 则不传)
        Returns:
            dict: {pid, process_handle, thread_handle}
        """
        si = STARTUPINFOW()
        si.cb = ctypes.sizeof(STARTUPINFOW)
        si.dwFlags = 0x00000001  # STARTF_USESHOWWINDOW
        si.wShowWindow = 1  # SW_SHOWNORMAL

        pi = PROCESS_INFORMATION()

        creation_flags = CREATE_UNICODE_ENVIRONMENT | CREATE_NEW_CONSOLE

        # 准备命令行
        cmdline = ctypes.create_unicode_buffer(exe_path, len(exe_path) + 1)

        if not _advapi32.CreateProcessWithTokenW(
            token_handle,
            0,  # dwLogonFlags
            exe_path,  # lpApplicationName
            cmdline,  # lpCommandLine
            creation_flags,
            env_block,  # lpEnvironment
            None,  # lpCurrentDirectory
            ctypes.byref(si),
            ctypes.byref(pi)
        ):
            err = ctypes.get_last_error()
            raise RuntimeError(
                f"CreateProcessWithTokenW 失败 (错误码: {err})\n"
                f"可能原因: 没有开启 SeImpersonatePrivilege"
            )

        result = {
            "pid": pi.dwProcessId,
            "process_handle": pi.hProcess,
            "thread_handle": pi.hThread
        }

        # 关闭句柄 (调用者不需要)
        _kernel32.CloseHandle(pi.hProcess)
        _kernel32.CloseHandle(pi.hThread)

        return result

    def _win_is_admin():
        """检查当前进程是否以管理员权限运行"""
        token_handle = wintypes.HANDLE()
        if not _advapi32.OpenProcessToken(
            _kernel32.GetCurrentProcess(),
            TOKEN_QUERY,
            ctypes.byref(token_handle)
        ):
            return False

        try:
            elevation = TOKEN_ELEVATION()
            returned = wintypes.DWORD()
            if not _advapi32.GetTokenInformation(
                token_handle, TokenElevation,
                ctypes.byref(elevation), ctypes.sizeof(elevation),
                ctypes.byref(returned)
            ):
                return False
            return bool(elevation.TokenIsElevated)
        finally:
            _kernel32.CloseHandle(token_handle)

    def _win_whoami():
        """获取当前用户名"""
        size = wintypes.DWORD(256)
        buf = ctypes.create_unicode_buffer(256)
        if _advapi32.GetUserNameW(buf, ctypes.byref(size)):
            return buf.value
        return os.getenv("USERNAME", "unknown")

    def _win_run_as_system(exe_path):
        """以 SYSTEM 权限运行进程 (完整提升链)

        步骤:
            1. 开启 SeDebugPrivilege (调试特权)
            2. 开启 SeImpersonatePrivilege (模拟特权)
            3. 找到 winlogon.exe (SYSTEM 进程)
            4. 获取其令牌
            5. 复制为主令牌
            6. 修正会话 ID
            7. 创建环境变量块
            8. 用主令牌创建进程
        """
        if not _win_is_admin():
            raise RuntimeError(
                "需要管理员权限!\n"
                "请以管理员身份运行 (右键 → 以管理员身份运行)\n"
                "本模块不能绕过 UAC, 需要已有管理员权限"
            )

        # 步骤 1-2: 开启特权
        _win_enable_privilege("SeDebugPrivilege")
        _win_enable_privilege("SeImpersonatePrivilege")

        # 步骤 3: 找到 winlogon.exe
        pid = _win_find_process("winlogon.exe")

        # 步骤 4: 获取 SYSTEM 进程令牌
        token = _win_get_process_token(pid)

        try:
            # 步骤 5: 复制为主令牌
            primary_token = _win_duplicate_token(token)

            try:
                # 步骤 6: 修正会话 ID
                session_id = _win_get_session_id()
                _win_set_session_id(primary_token, session_id)

                # 步骤 7: 创建环境变量块
                env_block = _win_create_env_block(primary_token)

                try:
                    # 步骤 8: 用主令牌创建进程
                    result = _win_create_process_with_token(
                        primary_token, exe_path, env_block
                    )
                    return result
                finally:
                    if env_block:
                        _userenv.DestroyEnvironmentBlock(env_block)
            finally:
                _kernel32.CloseHandle(primary_token)
        finally:
            _kernel32.CloseHandle(token)

    def _win_run_as_trustedinstaller(exe_path):
        """以 TrustedInstaller 权限运行进程

        步骤:
            1. 开启 SeDebugPrivilege + SeImpersonatePrivilege
            2. 启动 TrustedInstaller 服务
            3. 等待 TrustedInstaller 进程出现
            4. 获取其令牌
            5. 复制为主令牌
            6. 停止 TrustedInstaller 服务
            7. 修正会话 ID + 创建环境变量块
            8. 用 TI 令牌创建进程
        """
        if not _win_is_admin():
            raise RuntimeError(
                "需要管理员权限!\n"
                "请以管理员身份运行 (右键 → 以管理员身份运行)"
            )

        # 步骤 1: 开启特权
        _win_enable_privilege("SeDebugPrivilege")
        _win_enable_privilege("SeImpersonatePrivilege")

        # 步骤 2: 启动 TrustedInstaller 服务
        scm = _advapi32.OpenSCManagerW(None, None, SC_MANAGER_CONNECT)
        if not scm:
            raise RuntimeError(f"OpenSCManager 失败 (错误码: {ctypes.get_last_error()})")

        try:
            service = _advapi32.OpenServiceW(
                scm, "TrustedInstaller",
                SERVICE_START | SERVICE_QUERY_STATUS | SERVICE_STOP
            )
            if not service:
                raise RuntimeError(
                    f"OpenService(TrustedInstaller) 失败 "
                    f"(错误码: {ctypes.get_last_error()})"
                )

            try:
                # 启动服务
                _advapi32.StartServiceW(service, 0, None)

                # 等待服务运行 (最多等 10 秒)
                import time
                status = SERVICE_STATUS()
                for _ in range(20):
                    _advapi32.QueryServiceStatus(service, ctypes.byref(status))
                    if status.dwCurrentState == SERVICE_RUNNING:
                        break
                    time.sleep(0.5)

                if status.dwCurrentState != SERVICE_RUNNING:
                    raise RuntimeError("TrustedInstaller 服务启动超时")

                # 步骤 3-4: 找到 TrustedInstaller 进程并获取令牌
                pid = _win_find_process("TrustedInstaller.exe")
                token = _win_get_process_token(pid)

                try:
                    # 步骤 5: 复制为主令牌
                    primary_token = _win_duplicate_token(token)

                    try:
                        # 步骤 6: 停止服务
                        _advapi32.ControlService(
                            service, SERVICE_CONTROL_STOP, ctypes.byref(status)
                        )

                        # 步骤 7: 修正会话 ID + 环境变量块
                        session_id = _win_get_session_id()
                        _win_set_session_id(primary_token, session_id)
                        env_block = _win_create_env_block(primary_token)

                        try:
                            # 步骤 8: 用 TI 令牌创建进程
                            return _win_create_process_with_token(
                                primary_token, exe_path, env_block
                            )
                        finally:
                            if env_block:
                                _userenv.DestroyEnvironmentBlock(env_block)
                    finally:
                        _kernel32.CloseHandle(primary_token)
                finally:
                    _kernel32.CloseHandle(token)
            finally:
                _advapi32.CloseServiceHandle(service)
        finally:
            _advapi32.CloseServiceHandle(scm)

    def _win_run_as_admin(exe_path):
        """以管理员权限运行 (UAC 提权弹窗)"""
        # 使用 ShellExecuteW 的 "runas" 动词触发 UAC
        import ctypes
        SW_SHOWNORMAL = 1
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", exe_path, None, None, SW_SHOWNORMAL
        )
        return {"pid": None, "method": "uac_shell_execute"}

    def _win_levels():
        """返回 Windows 可用的提升级别"""
        return [
            {"level": "user", "desc": "当前用户 (普通权限)", "platform": "Windows"},
            {"level": "admin", "desc": "管理员 (UAC 提权)", "platform": "Windows"},
            {"level": "system", "desc": "SYSTEM (最高系统权限)", "platform": "Windows"},
            {"level": "trusted", "desc": "TrustedInstaller (文件所有者)", "platform": "Windows"},
        ]


# ═══════════════════════════════════════════════════════════════
# Linux / macOS 实现 (sudo / pkexec / su)
# ═══════════════════════════════════════════════════════════════

elif _IS_LINUX or _IS_MACOS:

    def _unix_run_as_root(exe_path, use_pkexec=False, capture_output=False):
        """以 root 权限运行 (通过 sudo 或 pkexec)

        Args:
            exe_path: 命令或脚本路径
            use_pkexec: True 用 pkexec (GUI), False 用 sudo
            capture_output: 是否捕获输出
        Returns:
            dict: {returncode, stdout, stderr, pid}
        """
        # 如果已经是 root, 直接运行
        if os.geteuid() == 0:
            cmd = exe_path.split() if isinstance(exe_path, str) else exe_path
            result = subprocess.run(
                cmd, capture_output=capture_output, text=True
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout if capture_output else "",
                "stderr": result.stderr if capture_output else "",
                "pid": None,
                "method": "direct_root"
            }

        # 选择提权方式
        if use_pkexec:
            # pkexec 用于 GUI 程序, 会弹认证窗口
            prefix = ["pkexec"]
        else:
            # sudo 用于命令行
            prefix = ["sudo"]

        # 解析命令
        if isinstance(exe_path, str):
            cmd = prefix + exe_path.split()
        else:
            cmd = prefix + list(exe_path)

        result = subprocess.run(
            cmd, capture_output=capture_output, text=True
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout if capture_output else "",
            "stderr": result.stderr if capture_output else "",
            "pid": None,
            "method": "sudo" if not use_pkexec else "pkexec"
        }

    def _unix_run_as_user(username, exe_path):
        """以指定用户身份运行

        Args:
            username: 目标用户名
            exe_path: 命令
        Returns:
            dict
        """
        if isinstance(exe_path, str):
            cmd = ["sudo", "-u", username] + exe_path.split()
        else:
            cmd = ["sudo", "-u", username] + list(exe_path)

        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "pid": None,
            "method": f"sudo_as_{username}"
        }

    def _unix_is_admin():
        """检查是否是 root 或有 sudo 权限"""
        if os.geteuid() == 0:
            return True
        # 检查 sudo 权限 (非交互)
        try:
            result = subprocess.run(
                ["sudo", "-n", "true"],
                capture_output=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _unix_whoami():
        """获取当前用户名"""
        try:
            result = subprocess.run(["whoami"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return os.getenv("USER", os.getenv("LOGNAME", "unknown"))

    def _unix_levels():
        """返回 Linux/macOS 可用的提升级别"""
        return [
            {"level": "user", "desc": "当前用户 (普通权限)", "platform": "Linux"},
            {"level": "admin", "desc": "root (通过 sudo)", "platform": "Linux"},
            {"level": "system", "desc": "root (通过 sudo)", "platform": "Linux"},
            {"level": "root", "desc": "root (通过 sudo/pkexec)", "platform": "Linux"},
        ]


# ═══════════════════════════════════════════════════════════════
# 跨平台 _PrivModule 类
# ═══════════════════════════════════════════════════════════════

class _PrivModule:
    """PyMsi.priv — 🔐 进程权限提升模块 (1.5.5 新增)

    以特定权限打开进程:
        Windows: 管理员 → SYSTEM / TrustedInstaller (NSudo 技术链)
        Linux:   普通用户 → root (通过 sudo / pkexec)

    ⚠️ 需要管理员 (Windows) / sudo (Linux) 权限, 不能绕过认证!

    用法:
        # Windows: 以 SYSTEM 权限运行
        PM.priv.system("notepad.exe")
        PM.priv.system("C:/Windows/System32/cmd.exe")

        # Windows: 以 TrustedInstaller 权限运行
        PM.priv.trusted("notepad.exe")

        # Linux: 以 root 运行
        PM.priv.system("ls /root")
        PM.priv.root("whoami")

        # 查看当前身份
        PM.priv.whoami()

        # 检查权限
        PM.priv.is_admin()
        PM.priv.is_system()

        # 别名: PM.su / PM.runas / PM.elevate / PM.提权 / PM.权限
    """

    def __init__(self):
        self._platform = "Windows" if _IS_WINDOWS else ("Linux" if _IS_LINUX else ("macOS" if _IS_MACOS else "Unknown"))

    def __repr__(self):
        return f"<PyMsi.priv [🔐权限提升] platform={self._platform}>"

    # ─── system: 以 SYSTEM/root 运行 ──────────────────────

    def system(self, exe_path):
        """以 SYSTEM (Windows) / root (Linux) 权限运行进程

        Windows: 完整 NSudo 提升链 (管理员 → SYSTEM)
        Linux:   通过 sudo 以 root 运行

        Args:
            exe_path: str — 要运行的程序路径或命令

        用法:
            PM.priv.system("notepad.exe")          # Windows
            PM.priv.system("C:/Windows/System32/cmd.exe")
            PM.priv.system("ls /root")              # Linux
        """
        if _IS_WINDOWS:
            return _win_run_as_system(exe_path)
        elif _IS_LINUX or _IS_MACOS:
            return _unix_run_as_root(exe_path)
        else:
            raise RuntimeError(f"不支持的平台: {sys.platform}")

    # ─── trusted: 以 TrustedInstaller 运行 (仅 Windows) ──

    def trusted(self, exe_path):
        """以 TrustedInstaller 权限运行 (仅 Windows)

        TrustedInstaller 是 Windows 文件所有者服务账号:
            1. 启动 TrustedInstaller 服务
            2. 抓取进程令牌
            3. 停止服务
            4. 用 TI 令牌创建进程

        Args:
            exe_path: str — 要运行的程序路径

        用法:
            PM.priv.trusted("notepad.exe")
            PM.priv.trusted("C:/Windows/System32/cmd.exe")
        """
        if not _IS_WINDOWS:
            raise RuntimeError(
                "TrustedInstaller 仅支持 Windows!\n"
                "Linux 没有 TrustedInstaller 概念, 请用 PM.priv.system()"
            )
        return _win_run_as_trustedinstaller(exe_path)

    # ─── admin: 以管理员/root 运行 ───────────────────────

    def admin(self, exe_path):
        """以管理员权限运行

        Windows: 触发 UAC 提权弹窗 (ShellExecuteW runas)
        Linux:   通过 sudo 以 root 运行

        Args:
            exe_path: str — 要运行的程序路径或命令

        用法:
            PM.priv.admin("notepad.exe")          # Windows UAC
            PM.priv.admin("apt update")           # Linux sudo
        """
        if _IS_WINDOWS:
            return _win_run_as_admin(exe_path)
        elif _IS_LINUX or _IS_MACOS:
            return _unix_run_as_root(exe_path)
        else:
            raise RuntimeError(f"不支持的平台: {sys.platform}")

    # ─── root: 以 root 运行 (Linux 别名) ─────────────────

    def root(self, exe_path, use_pkexec=False):
        """以 root 运行 (Linux/macOS)

        通过 sudo 或 pkexec 以 root 权限运行

        Args:
            exe_path: str — 命令
            use_pkexec: bool — True 用 pkexec (GUI 认证窗口)

        用法:
            PM.priv.root("whoami")
            PM.priv.root("apt install nginx")
        """
        if _IS_WINDOWS:
            # Windows 上 root 等同于 system
            return _win_run_as_system(exe_path)
        elif _IS_LINUX or _IS_MACOS:
            return _unix_run_as_root(exe_path, use_pkexec=use_pkexec)
        else:
            raise RuntimeError(f"不支持的平台: {sys.platform}")

    # ─── as_user: 以指定用户运行 ─────────────────────────

    def as_user(self, username, exe_path):
        """以指定用户身份运行 (Linux)

        Args:
            username: str — 目标用户名
            exe_path: str — 命令

        用法:
            PM.priv.as_user("alice", "whoami")
        """
        if _IS_WINDOWS:
            # Windows 用 runas
            import ctypes
            SW_SHOWNORMAL = 1
            ctypes.windll.shell32.ShellExecuteW(
                None, None, "runas", f"/user:{username} {exe_path}",
                None, SW_SHOWNORMAL
            )
            return {"method": f"runas_user_{username}"}
        elif _IS_LINUX or _IS_MACOS:
            return _unix_run_as_user(username, exe_path)
        else:
            raise RuntimeError(f"不支持的平台: {sys.platform}")

    # ─── whoami: 查看当前身份 ────────────────────────────

    def whoami(self):
        """查看当前身份

        Returns:
            str — 当前用户名

        用法:
            PM.priv.whoami()
        """
        if _IS_WINDOWS:
            return _win_whoami()
        elif _IS_LINUX or _IS_MACOS:
            return _unix_whoami()
        else:
            return "unknown"

    # ─── is_admin: 检查是否管理员/root ───────────────────

    def is_admin(self):
        """检查当前是否以管理员/root 权限运行

        Returns:
            bool

        用法:
            if PM.priv.is_admin():
                print("已管理员")
        """
        if _IS_WINDOWS:
            return _win_is_admin()
        elif _IS_LINUX or _IS_MACOS:
            return _unix_is_admin()
        else:
            return False

    # ─── is_system: 检查是否 SYSTEM/root ─────────────────

    def is_system(self):
        """检查当前是否以 SYSTEM (Windows) / root (Linux) 权限运行

        Returns:
            bool

        用法:
            if PM.priv.is_system():
                print("已是 SYSTEM/root")
        """
        if _IS_WINDOWS:
            return _win_whoami().lower() == "system"
        elif _IS_LINUX or _IS_MACOS:
            return os.geteuid() == 0
        else:
            return False

    # ─── levels: 列出可用的提升级别 ──────────────────────

    def levels(self):
        """列出当前平台可用的提升级别

        Returns:
            list[dict] — 每个级别的 {level, desc, platform}

        用法:
            PM.priv.levels()
        """
        if _IS_WINDOWS:
            return _win_levels()
        elif _IS_LINUX or _IS_MACOS:
            return _unix_levels()
        else:
            return [{"level": "none", "desc": f"不支持的平台: {sys.platform}", "platform": "Unknown"}]

    # ─── 别名方法 ────────────────────────────────────────

    def su(self, *args, **kwargs):
        """别名: PM.priv.su() == PM.priv.system()"""
        return self.system(*args, **kwargs)

    def runas(self, *args, **kwargs):
        """别名: PM.priv.runas() == PM.priv.admin()"""
        return self.admin(*args, **kwargs)

    def elevate(self, *args, **kwargs):
        """别名: PM.priv.elevate() == PM.priv.system()"""
        return self.system(*args, **kwargs)

    def exec_as(self, *args, **kwargs):
        """别名: PM.priv.exec_as() == PM.priv.system()"""
        return self.system(*args, **kwargs)

    def run_as(self, *args, **kwargs):
        """别名: PM.priv.run_as() == PM.priv.system()"""
        return self.system(*args, **kwargs)

    def help(self):
        """打印帮助"""
        print(self.__doc__)
