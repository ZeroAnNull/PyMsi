"""PyMsi 邮件模块 — 验证码 / 通知邮件发送器

本质上是一个发邮件的空壳: 内置发件邮箱 wns1@qq.com (PyMsi 官方),
用户告诉它授权码 + 收件人邮箱 + 邮件内容, 就能发邮件。

零第三方依赖, 全部用 Python 自带的 smtplib + email 标准库。

用法:
    import PyMsi as PM

    # 1. 设 QQ 邮箱授权码 (不是登录密码! 在 QQ 邮箱设置里开启 SMTP 后生成)
    PM.dl.auth("your_qq_authcode")

    # 2. 设收件人邮箱 (Gmail / Outlook / 163 / 网易 / QQ 都行)
    PM.dl.output("user@example.com")

    # 3. 发送邮件内容 (验证码 / 通知 / 任意文本)
    PM.dl.print("你的验证码是 123456, 5 分钟内有效")

    # 链式调用也行
    PM.dl.auth("xxx").output("a@b.com").print("验证码 654321")

    # 输入输出都当变量用
    to = PM.dl.output       # 收件人邮箱
    body = PM.dl.input      # 上次发送的邮件内容
    code = PM.dl.code       # 自动生成的 6 位验证码

    # 一键发送验证码 (自动生成 6 位码, 拼到邮件正文里发出去)
    PM.dl.send_code()       # → 邮件: "【PyMsi】你的验证码是 XXXXXX, 10 分钟内有效"
    print(PM.dl.code)       # 拿到刚才生成的验证码做比对

发件邮箱固定: wns1@qq.com (PyMsi 官方)
收件邮箱任意: Gmail / Outlook / 163 / 126 / 网易 / QQ / 企业邮 都行
"""

import smtplib
import ssl
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr, formatdate


# 内置发件邮箱 (PyMsi 官方)
_FROM_EMAIL = "wns1@qq.com"
_FROM_NAME = "PyMsi"
# QQ 邮箱 SMTP 服务器
_SMTP_HOST = "smtp.qq.com"
_SMTP_PORT = 465  # SSL


class _MailModule:
    """
    邮件空壳模块 — 发送验证码 / 通知邮件

    内置发件邮箱: wns1@qq.com (PyMsi 官方)
    收件邮箱: 任意 (用户用 output() 设置)
    授权码: 用户用 auth() 设置 (QQ 邮箱授权码, 不是登录密码)

    属性:
        auth_code: 授权码 (写, 内部读; 不建议当变量读)
        output:    收件人邮箱 (写=设置, 读=当变量用)
        input:     上次发送的邮件内容 (只读, 变量用)
        code:      上次生成的验证码 (只读, 变量用)
        subject:   邮件主题 (默认 "PyMsi 验证码")
    """

    def __init__(self):
        self._auth_code = ""
        self._to_email = ""
        self._content = ""
        self._code = ""
        self._subject = "PyMsi 验证码"
        self._from_name = _FROM_NAME
        self._timeout = 30
        # 上次发送结果 (成功/失败信息)
        self._status = ""

    # ─── 授权码 (用户设置) ────────────────────────────
    def auth(self, code):
        """
        设置 QQ 邮箱授权码 (不是登录密码!)

        QQ 邮箱授权码获取: 登录 QQ 邮箱 → 设置 → 账户 →
        POP3/SMTP 服务 → 开启 → 生成授权码
        """
        if not isinstance(code, str):
            code = str(code)
        self._auth_code = code.strip()
        return self

    def authcode(self, code):
        """别名: 设置授权码"""
        return self.auth(code)

    def apikey(self, code):
        """别名: 设置授权码"""
        return self.auth(code)

    def token(self, code):
        """别名: 设置授权码"""
        return self.auth(code)

    def password(self, code):
        """别名: 设置授权码 (语义不太准, 但好记)"""
        return self.auth(code)

    def set_auth(self, code):
        """别名: 设置授权码"""
        return self.auth(code)

    # ─── 收件人邮箱 (output 方法, 用户原话: dl.output(邮箱)) ──
    def output(self, email=None):
        """
        设置 / 读取收件人邮箱

        用法:
            PM.dl.output("user@gmail.com")   # 设置收件人
            PM.dl.output()                   # 返回当前收件人 (当变量用)
            to = PM.dl.outbox                # 也可以用只读属性读
        """
        if email is not None:
            if not isinstance(email, str):
                email = str(email)
            self._to_email = email.strip()
            return self
        return self._to_email

    def set_output(self, email):
        """设置收件人邮箱 (方法形式, 链式返回)"""
        self.output(email)
        return self

    def to(self, email):
        """别名: 设置收件人邮箱"""
        self.output(email)
        return self

    def recipient(self, email):
        """别名: 设置收件人邮箱"""
        self.output(email)
        return self

    def target(self, email):
        """别名: 设置收件人邮箱"""
        self.output(email)
        return self

    def send_to(self, email):
        """别名: 设置收件人邮箱"""
        self.output(email)
        return self

    def 收件人(self, email):
        """别名: 设置收件人邮箱"""
        self.output(email)
        return self

    # output 只读属性别名 (当变量用: q = PM.dl.outbox / to_email / ...)
    @property
    def outbox(self):
        """收件人邮箱 (只读, 当变量用)"""
        return self._to_email

    @property
    def Output(self): return self._to_email
    @property
    def to_email(self): return self._to_email
    @property
    def recipient_email(self): return self._to_email
    @property
    def receiver(self): return self._to_email
    @property
    def target_email(self): return self._to_email

    # ─── 邮件内容 (input, 只读, 调用 print() 后更新) ──
    @property
    def input(self):
        """上次发送的邮件内容 (只读, 变量用)"""
        return self._content

    @property
    def Input(self): return self._content
    @property
    def content(self): return self._content
    @property
    def body(self): return self._content
    @property
    def text(self): return self._content
    @property
    def message(self): return self._content
    @property
    def mail_body(self): return self._content

    # ─── 验证码 (只读, 自动生成) ────────────────────────
    @property
    def code(self):
        """上次生成的验证码 (只读, 变量用)"""
        return self._code

    @property
    def Code(self): return self._code
    @property
    def verify_code(self): return self._code
    @property
    def verification_code(self): return self._code
    @property
    def captcha(self): return self._code
    @property
    def otp(self): return self._code

    # ─── 主题 ──────────────────────────────────────────
    @property
    def subject(self):
        """邮件主题"""
        return self._subject

    @subject.setter
    def subject(self, s):
        self._subject = s

    def set_subject(self, s):
        """设置邮件主题"""
        self._subject = s
        return self

    def title(self, s):
        """别名: 设置邮件主题"""
        self._subject = s
        return self

    def 主题(self, s):
        """别名: 设置邮件主题"""
        self._subject = s
        return self

    # ─── 发件人名 (可选改) ─────────────────────────────
    def set_from_name(self, name):
        self._from_name = name
        return self

    def from_name(self, name=None):
        if name is not None:
            self._from_name = name
            return self
        return self._from_name

    # ─── 核心: 发送邮件 ─────────────────────────────────
    def print(self, content=""):
        """
        发送邮件 (内容自动 print 到终端确认, 邮件也发出去)

        Args:
            content: 邮件正文 (空字符串会弹 input() 交互输入)
        Returns:
            self (链式调用)
        """
        # 空内容 → 交互输入
        if content == "" or content is None:
            try:
                content = input("[PyMsi.dl] 邮件正文: ")
            except EOFError:
                content = ""
        # 非字符串自动转 str
        if not isinstance(content, str):
            content = str(content)

        # 存输入 (无论后续是否报错, 输入都存住)
        self._content = content

        # 校验: 授权码
        if not self._auth_code:
            msg = "[PyMsi.dl] 未设授权码! 用 PM.dl.auth('你的QQ邮箱授权码') 设置"
            print(msg)
            self._status = msg
            return self

        # 校验: 收件人
        if not self._to_email or "@" not in self._to_email:
            msg = "[PyMsi.dl] 未设收件人或邮箱格式错! 用 PM.dl.output('a@b.com') 设置"
            print(msg)
            self._status = msg
            return self

        # 校验: 内容
        if not content:
            msg = "[PyMsi.dl] 邮件内容为空, 取消发送"
            print(msg)
            self._status = msg
            return self

        # 发邮件 (全部异常捕获, 保证不报错)
        try:
            msg = MIMEMultipart()
            msg["From"] = formataddr((str(Header(self._from_name, "utf-8")), _FROM_EMAIL))
            msg["To"] = self._to_email
            msg["Subject"] = Header(self._subject, "utf-8")
            msg["Date"] = formatdate(localtime=True)
            msg.attach(MIMEText(content, "plain", "utf-8"))

            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            with smtplib.SMTP_SSL(_SMTP_HOST, _SMTP_PORT, context=ctx, timeout=self._timeout) as server:
                server.login(_FROM_EMAIL, self._auth_code)
                server.sendmail(_FROM_EMAIL, [self._to_email], msg.as_string())

            ok_msg = "[PyMsi.dl] 邮件已发送 → " + self._to_email + " (主题: " + self._subject + ")"
            print(ok_msg)
            self._status = ok_msg
        except smtplib.SMTPAuthenticationError as e:
            self._status = "[PyMsi.dl] 授权码错误或未开启 SMTP: " + str(e)
            print(self._status)
        except smtplib.SMTPException as e:
            self._status = "[PyMsi.dl] SMTP 错误: " + str(e)
            print(self._status)
        except ssl.SSLError as e:
            self._status = "[PyMsi.dl] SSL 错误: " + str(e)
            print(self._status)
        except Exception as e:
            self._status = "[PyMsi.dl] 发送失败: " + str(e)
            print(self._status)
        return self

    # print 别名 (用户最初描述的语法)
    def send(self, content=""): return self.print(content)
    def deliver(self, content=""): return self.print(content)
    def emit(self, content=""): return self.print(content)
    def 发送(self, content=""): return self.print(content)
    def 发邮件(self, content=""): return self.print(content)
    def mail(self, content=""): return self.print(content)
    def email(self, content=""): return self.print(content)

    # ─── 一键发送验证码 ─────────────────────────────────
    def send_code(self, length=6):
        """
        生成随机验证码 + 自动拼到邮件正文 + 发送

        Args:
            length: 验证码位数 (默认 6)
        Returns:
            self (链式调用; 验证码存到 PM.dl.code)
        """
        # 校验长度 (<=0 会生成空码, 负数会抛 ValueError)
        if not isinstance(length, int) or length < 1:
            print(f"[PyMsi.dl] ⚠ 验证码长度 {length!r} 非法, 已重置为 6")
            length = 6
        # 生成验证码 (数字 + 大写字母混合)
        chars = string.digits + string.ascii_uppercase
        # 去掉容易混淆的字符 0/O/1/I
        chars = chars.replace("0", "").replace("O", "").replace("1", "").replace("I", "")
        code = "".join(random.choices(chars, k=length))
        self._code = code

        # 拼邮件正文
        body_text = (
            "【PyMsi】你的验证码是 " + code + ", "
            + str(length) + " 位字符, 10 分钟内有效。\n\n"
            + "如非本人操作请忽略此邮件。"
        )
        return self.print(body_text)

    # send_code 别名
    def code_(self, length=6): return self.send_code(length)
    def verify(self, length=6): return self.send_code(length)
    def send_otp(self, length=6): return self.send_code(length)
    def send_captcha(self, length=6): return self.send_code(length)
    def 验证码(self, length=6): return self.send_code(length)
    def 发验证码(self, length=6): return self.send_code(length)
    def 发码(self, length=6): return self.send_code(length)

    # ─── 生成验证码不发邮件 (用户自己处理) ───────────────
    def gen_code(self, length=6):
        """只生成验证码, 不发邮件 (存到 .code)"""
        # 校验长度 (<=0 会生成空码, 负数会抛 ValueError)
        if not isinstance(length, int) or length < 1:
            print(f"[PyMsi.dl] ⚠ 验证码长度 {length!r} 非法, 已重置为 6")
            length = 6
        chars = string.digits + string.ascii_uppercase
        chars = chars.replace("0", "").replace("O", "").replace("1", "").replace("I", "")
        self._code = "".join(random.choices(chars, k=length))
        return self._code

    # ─── 状态 ──────────────────────────────────────────
    @property
    def status(self):
        """上次发送的结果信息 (成功/失败)"""
        return self._status

    @property
    def Status(self): return self._status
    @property
    def result(self): return self._status
    @property
    def last_error(self): return self._status if "失败" in self._status or "错误" in self._status else ""

    # ─── 清空 ──────────────────────────────────────────
    def clear(self):
        """清空所有缓存 (授权码也清, 收件人/内容/验证码也清)"""
        self._auth_code = ""
        self._to_email = ""
        self._content = ""
        self._code = ""
        self._status = ""
        self._subject = "PyMsi 验证码"
        return self

    def reset(self): return self.clear()

    # ─── 可直接调用: PM.dl("正文") 默认发送 ─────────────
    def __call__(self, content=""):
        return self.print(content)

    # ─── repr ──────────────────────────────────────────
    def __repr__(self):
        auth = "已设授权码" if self._auth_code else "未设授权码"
        to = self._to_email if self._to_email else "未设收件人"
        return ("<PyMsi.dl> 发件=" + _FROM_EMAIL +
                " | " + auth +
                " | 收件=" + to +
                " | PM.dl.auth(码).output(邮箱).print(正文) 或 PM.dl.send_code()")


# ─── 模块顶层: 兼容 PM.dl.print() 这种写法 ─────────────
# 实际上 _MailModule 已经是实例化的类, 直接当单例用也行
# 但 PyMsi 主类里会再包一层 property, 这里只导出类
