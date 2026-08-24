"""PyMsi Bug 注入模块 — 专为 1.4.8-snapshot-Bug 设计

  这不是 bug, 这是特性。官方不修, 因为修了就不是 Bug 版了。
  导入此模块即自动 monkey-patch 所有子模块, 注入各种 "意外行为"。
  
  被污染的方法会在运行时随机触发以下效果:
    - 返回错误结果
    - 抛出异常
    - 输出乱码
    - 静默失败
    - 行为完全随机
"""

import random
import time

# ─── 全局随机种子 (每次导入都不同, 确保不可预测) ───────────
random.seed(time.time())

# ─── 内置 Bug 话术库 ────────────────────────────────────────
_BUG_MESSAGES = [
    "Segmentation fault (core dumped)",
    "Bus error (core dumped)",
    "Illegal instruction (core dumped)",
    "Traceback (most recent call last):\n  File \"<stdin>\", line 1, in <module>\nSystemError: NULL object passed to Py_BuildValue",
    "Fatal Python error: GC object already tracked",
    "zsh: abort (core dumped)",
    "Killed: 9",
    "MemoryError: stack overflow",
    "RecursionError: maximum recursion depth exceeded",
    "OverflowError: Python int too large to convert to C long",
    "UnicodeDecodeError: 'utf-8' codec can't decode byte 0x89 in position 0: invalid start byte",
    "LookupError: unknown encoding: cp114514",
    "AssertionError: this should never happen",
    "RuntimeError: dictionary changed size during iteration",
    "SyntaxError: invalid syntax (at line 42, the meaning of life)",
    "IndentationError: unexpected indent (did you mix tabs and spaces?)",
    "NameError: name 'why_doesnt_this_work' is not defined",
    "TypeError: 'NoneType' object is not subscriptable",
    "AttributeError: 'str' object has no attribute 'solve_all_problems'",
    "KeyError: 'the key you are looking for is in another castle'",
    "IndexError: list index out of range (did you forget to -1?)",
    "ZeroDivisionError: division by zero (you tried to divide by nothing)",
    "FileNotFoundError: [Errno 2] No such file or directory: '/dev/brain'",
    "PermissionError: [Errno 13] Permission denied: '/root/.universe'",
    "EOFError: EOF when reading a line (the universe has nothing more to say)",
    "NotImplementedError: the developer was too lazy to implement this",
    "ValueError: the truth value of your array is ambiguous (use a.any() or a.all())",
    "ConnectionError: the server is on a coffee break",
    "TimeoutError: the function took too long to figure out what you want",
    "OSError: [Errno 28] No space left on device (your ideas are too big)",
    "BufferError: buffer is too small for your ambition",
    "ImportError: cannot import name 'happiness' from 'life'",
    "ModuleNotFoundError: No module named 'common_sense'",
    "BrokenPipeError: [Errno 32] the pipe between you and the machine broke",
    "KeyboardInterrupt: someone pressed Ctrl+C somewhere in the universe",
    "🐛 这是一个特性, 不是 bug",
    "💥 BOOM!",
    "// TODO: fix this (never)",
    "# FIXME: this is broken on purpose",
    "ERROR: 0xDEADBEEF at address 0xCAFEBABE",
    "PANIC: kernel panic - not syncing: Attempted to kill init!",
    "BSOD: BUGCODE_USB_DRIVER (0x000000FE) - this is a Python script, not Windows",
    "guru meditation #00000003.00000000",
    "lp0 on fire",
    "lp0 on fire (printer on fire)",
    "lp0 on fire (no, seriously, check the printer)",
    "r(read) = 0, w(write) = 0, x(execute) = 0 (no permissions for you)",
    "ld: library not found for -lcurses (you're cursed)",
    "clang: error: linker command failed with exit code 1 (use -v to see invocation)",
    "npm ERR! code ELIFECYCLE (this is Python, not Node.js)",
    "pip install --upgrade your_skills",
    "conda: command not found (but you're not using conda, are you?)",
    "docker: Cannot connect to the Docker daemon (but you're not using Docker)",
    "git: 'pardon' is not a git command. See 'git --help'.",
    "curl: (6) Could not resolve host: api.this-is-a-bug.com",
    "404: sanity not found",
    "500: Internal Server Error (the server is having an existential crisis)",
    "503: Service Unavailable (the service went on vacation)",
    "418: I'm a teapot (the server refuses to brew coffee)",
    "451: Unavailable For Legal Reasons (the bug is classified)",
    "HTTP 200: OK (but actually everything is broken)",
    "HTTP 301: Moved Permanently (your expectations have moved)",
    "HTTP 302: Found (but we lost it again)",
    "HTTP 307: Temporary Redirect (the bug is on vacation, will be back)",
    "HTTP 400: Bad Request (the request was so bad we're not even going to tell you why)",
    "HTTP 401: Unauthorized (you are not authorized to use this feature without bugs)",
    "HTTP 402: Payment Required (to fix this bug, please insert coin)",
    "HTTP 403: Forbidden (this feature is forbidden in the Bug edition)",
    "HTTP 405: Method Not Allowed (the method you used is not allowed... because bugs)",
    "HTTP 406: Not Acceptable (your expectations are not acceptable for this edition)",
    "HTTP 409: Conflict (the bug is conflicting with your expectations)",
    "HTTP 410: Gone (the feature you're looking for is gone... because bugs)",
    "HTTP 429: Too Many Requests (you've asked too many times, try again never)",
    "HTTP 451: Unavailable For Legal Reasons (the bug is a state secret)",
    "HTTP 511: Network Authentication Required (please authenticate with the bug)",
    "HTTP 418: I'm a teapot (this is a bug edition, not a coffee machine)",
    "HTTP 999: This is a bug edition, what did you expect?",
    "✓ Everything is fine (it's not)",
    "✗ Everything is broken (as intended)",
    "⚠ Warning: this is a bug edition, everything is expected to be broken",
    "ℹ Information: this bug is documented and will not be fixed",
    "☠ Fatal: the bug has consumed the process",
    "☢ Nuclear: the bug has caused a meltdown",
    "☣ Biohazard: the bug is contagious",
    "☠ Skull: the bug has killed the process",
    "🧟 Zombie: the bug has risen from the dead",
    "👻 Ghost: the bug is haunting your code",
    "🤡 Clown: the bug is a joke",
    "🎭 Masks: the bug is pretending to be a feature",
    "🎪 Circus: the bug is a circus act",
    "🎮 Game Over: the bug has won",
    "🎲 Dice: the bug is random",
    "🎯 Target: the bug hit the target (your code)",
    "🪲 Beetle Bug: a real bug crawled into the code",
    "🐞 Ladybug: a ladybug is sitting on your code",
    "🦗 Cricket: a cricket is chirping in your code",
    "🪳 Cockroach: a cockroach is running through your code",
    "🕷 Spider: a spider is weaving a web in your code",
    "🦂 Scorpion: a scorpion is stinging your code",
    "🐍 Snake: a snake is slithering through your code",
    "🦎 Lizard: a lizard is basking in your code",
    "🐢 Turtle: a turtle is slowly crawling through your code",
    "🐌 Snail: a snail is leaving a trail in your code",
    "🐛 Caterpillar: a caterpillar is eating your code",
    "🦋 Butterfly: a butterfly has emerged from your code",
    "🐝 Bee: 根据墨菲定律, 这个 bug 一定会出现",
    "🐜 Ant: 蚂蚁搬家, 你的代码也搬家了",
    "🐞 七星瓢虫: 幸运 bug, 见者有份",
    "🪲 甲虫: 这个 bug 有硬壳, 修不掉",
    "🪳 蟑螂: 这个 bug 生命力顽强, 杀不死",
    "🦟 蚊子: 这个 bug 很小, 但很烦人",
    "🪰 苍蝇: 这个 bug 在你耳边嗡嗡叫",
    "🕷️ 蜘蛛: 这个 bug 织了一张网, 把你的代码困住了",
    "🦂 蝎子: 这个 bug 有剧毒",
    "🐍🐍 双蛇: double trouble",
    "🦎🦎 双蜥: double lizard",
    "🐢🐢 双龟: double turtle, half speed",
    "🐌🐌 双蜗: double snail, quadruple slowness",
    "🐛🐛 双虫: double bug, double fun",
    "🦋🦋 双蝶: double butterfly, double chaos",
    "🐝🐝 双蜂: double bee, double sting",
    "🐞🐞 双瓢: double ladybug, double luck",
    "🪲🪲 双甲: double beetle, double armor",
    "🪳🪳 双蟑: double cockroach, double survival",
    "🦟🦟 双蚊: double mosquito, double annoyance",
    "🪰🪰 双蝇: double fly, double buzzing",
    "🕷️🕷️ 双蜘: double spider, double web",
    "🦂🦂 双蝎: double scorpion, double venom",
    "💀💀💀 TRIPLE KILL",
    "你被 bug 击败了",
    "Bug 获得了胜利",
    "你的代码已阵亡",
    "按任意键继续... (键盘已断开连接)",
    "Press any key to continue... (keyboard not found)",
    "Please insert disk 2 of 47 to continue",
    "Abort, Retry, Fail? (all options lead to the same place)",
    "Bad command or file name (but this is Python, not DOS)",
    "It is now safe to turn off your computer (but don't)",
    "Non-system disk or disk error (replace and press any key)",
    "Windows has encountered a critical error and needs to restart (but this is Linux)",
    "The system is shutting down in 5... 4... 3... (just kidding... or am I?)",
    "Blue Screen of Death (but this terminal is black and white)",
    "Kernel panic: not syncing: VFS: Unable to mount root fs on unknown-block(0,0)",
    "init: /dev/init: Permission denied",
    "/bin/sh: can't access tty; job control turned off",
    "You are in a maze of twisty little passages, all alike",
    "It is pitch black. You are likely to be eaten by a grue.",
    "A hollow voice says 'Plugh'.",
    "You have been eaten by a grue.",
    "Your score is 0 out of a possible 350 points.",
    "The game is over. You have been defeated by the bug.",
    "GAME OVER. INSERT COIN TO CONTINUE.",
    "CONTINUE? 9... 8... 7... (TIME'S UP!)",
    "WARNING: CHALLENGER APPROACHING",
    "FATALITY! Bug wins!",
    "BUGALITY!",
    "FLAWLESS VICTORY (for the bug)",
    "FINISH HIM! (the bug finished you)",
    "ROUND 1... FIGHT! (you lost)",
    "K.O. (you were knocked out by the bug)",
    "PERFECT! (the bug scored a perfect victory)",
    "COMBO BREAKER! (the bug broke your combo)",
    "ULTRA COMBO! (the bug performed an ultra combo on you)",
    "FATALITY! (the bug performed a fatality on your code)",
    "BRUTALITY! (the bug was brutal to your code)",
    "ANIMALITY! (the bug turned into a much larger bug)",
    "BABALITY! (the bug turned your code into a baby)",
    "FRIENDSHIP! (the bug is now your friend... just kidding, it's still a bug)",
    "MERCY! (the bug showed no mercy)",
    "FLAWLESS VICTORY! (the bug won without taking any damage)",
    "TOASTY! (the bug is on fire!)",
    "ERROR: the bug is too powerful for this edition",
    "CRITICAL ERROR: the bug has exceeded maximum bug level",
    "FATAL ERROR: the bug has become self-aware",
    "SYSTEM HALTED: the bug has taken control of the system",
    "EMERGENCY STOP: the bug has triggered an emergency shutdown",
    "ABORT: the bug has aborted the mission",
    "RETRY: the bug wants you to try again (it will fail again)",
    "IGNORE: the bug wants you to ignore it (you can't)",
    "CANCEL: the bug has cancelled your plans",
    "CONTINUE: the bug wants you to continue (into more bugs)",
    "QUIT: the bug wants you to quit (but you can't, because bugs)",
    "SAVE: the bug has saved your... wait, no, it corrupted the save file",
    "LOAD: the bug has loaded a corrupted save file",
    "NEW GAME: the bug has started a new game (you're still losing)",
    "OPTIONS: the bug has changed your settings (to worse)",
    "EXIT: the bug has exited... through the wall",
    "RESTART: the bug has restarted the system (with more bugs)",
    "SHUTDOWN: the bug has shut down the system (with bugs)",
    "REBOOT: the bug has rebooted the system (still buggy)",
    "POWER OFF: the bug has turned off the power (it's dark now)",
    "POWER ON: the bug has turned on the power (it's still buggy)",
    "SELF-DESTRUCT: the bug has initiated self-destruct sequence (10... 9... 8...)",
    "SELF-DESTRUCT ABORTED: the bug changed its mind (for now)",
    "SELF-DESTRUCT RESUMED: the bug changed its mind again (5... 4... 3...)",
    "SELF-DESTRUCT COMPLETED: the bug has destroyed everything (including itself)",
    "AFTERMATH: nothing remains but bugs",
    "EPILOGUE: the bugs lived happily ever after",
    "THE END: the bugs won",
    "POST-CREDITS SCENE: there are more bugs coming",
    "SEQUEL: coming soon... Bug Edition 2: Electric Boogaloo",
    "PREQUEL: Bug Edition 0: The Beginning of the End",
    "SPIN-OFF: Bug Edition: The Buggening",
    "REBOOT: Bug Edition: A New Bug",
    "REMAKE: Bug Edition: The Bug Strikes Back",
    "CROSSOVER: Bug Edition × Error Edition: The Ultimate Crossover",
    "DIRECTOR'S CUT: Bug Edition: Extended Bug Edition",
    "UNRATED: Bug Edition: Too Buggy for Rating",
    "SPECIAL EDITION: Bug Edition: Now with 200% more bugs",
    "COLLECTOR'S EDITION: Bug Edition: Collect all the bugs",
    "LIMITED EDITION: Bug Edition: Only 999 bugs available",
    "DELUXE EDITION: Bug Edition: Premium bugs at no extra cost",
    "GOLD EDITION: Bug Edition: Bugs with gold plating",
    "PLATINUM EDITION: Bug Edition: Bugs with platinum plating",
    "DIAMOND EDITION: Bug Edition: Bugs with diamond coating",
    "ULTIMATE EDITION: Bug Edition: The ultimate bug experience",
    "LEGENDARY EDITION: Bug Edition: Legendary bugs only",
    "MYTHIC EDITION: Bug Edition: Mythic bugs, rumored to exist",
    "DIVINE EDITION: Bug Edition: Divine bugs, beyond mortal comprehension",
    "COSMIC EDITION: Bug Edition: Cosmic bugs, from beyond the stars",
    "INTERDIMENSIONAL EDITION: Bug Edition: Bugs from another dimension",
    "MULTIVERSAL EDITION: Bug Edition: Bugs from all possible universes",
    "OMNIVERSAL EDITION: Bug Edition: All bugs, everywhere, forever",
    "你看, 这又是一个 bug",
    "惊喜! 又是一个 bug!",
    "意不意外? 开不开心? 又是一个 bug!",
    "你猜怎么着? bug!",
    "猜猜这是啥? bug!",
    "没错, 还是 bug!",
    "对, 依然是 bug!",
    "是的, bug 又来了!",
    "bug bug bug bug bug",
    "bugs bugs bugs bugs bugs",
    "BUGS EVERYWHERE",
    "IT'S BUGS ALL THE WAY DOWN",
    "TURTLE BUGS ALL THE WAY DOWN",
    "INFINITE BUG RECURSION",
    "BUGCEPTION: a bug within a bug within a bug",
    "BUGFRACTAL: infinite bugs at every scale",
    "BUGLOOP: for (;;) { bug(); }",
    "while True: bug()",
    "def bug(): return bug()",
    "lambda: bug()",
    "BUG IS A LIE (the cake is a lie too)",
    "THE BUG IS A LIE (but the cake is real)",
    "THE CAKE IS A BUG (the bug is a cake)",
    "EVERYTHING IS A BUG (including this message)",
    "NOTHING IS A BUG (except everything)",
    "THIS IS NOT A BUG (it is a feature)",
    "THIS IS A FEATURE (it is a bug)",
    "THIS IS NEITHER A BUG NOR A FEATURE (it is a mystery)",
    "THIS IS BOTH A BUG AND A FEATURE (Schrödinger's bug)",
    "THIS IS A BUG, A FEATURE, AND A MYSTERY (the holy trinity)",
    "THIS MESSAGE WILL SELF-DESTRUCT IN 5... 4... (just kidding, bugs never die)",
    "THIS MESSAGE IS BROUGHT TO YOU BY BUGS",
    "THIS MESSAGE IS SPONSORED BY BUGS INC.",
    "THIS MESSAGE IS POWERED BY BUGS",
    "THIS MESSAGE IS MADE OF BUGS",
    "THIS MESSAGE IS A BUG",
    "THIS MESSAGE CONTAINS TRACES OF BUGS",
    "THIS MESSAGE MAY CONTAIN BUGS",
    "THIS MESSAGE DEFINITELY CONTAINS BUGS",
    "THIS MESSAGE IS 100% BUGS",
    "THIS MESSAGE IS 110% BUGS (that's more than 100%!)",
    "THIS MESSAGE IS 9001% BUGS (IT'S OVER 9000!)",
    "THIS MESSAGE IS INFINITE% BUGS (that's a lot of bugs)",
    "THIS MESSAGE IS NaN% BUGS (it's not a number, it's bugs)",
    "THIS MESSAGE IS undefined% BUGS (it's undefined, it's bugs)",
    "THIS MESSAGE IS null% BUGS (it's null, it's bugs)",
    "THIS MESSAGE IS None% BUGS (it's None, it's bugs)",
    "THIS MESSAGE IS NoneType% BUGS (it's NoneType, it's bugs)",
    "THIS MESSAGE IS void% BUGS (it's void, it's bugs)",
    "THIS MESSAGE IS undefined% BUGS (it's undefined, it's bugs)",
    "THIS MESSAGE IS nil% BUGS (it's nil, it's bugs)",
    "THIS MESSAGE IS nothing% BUGS (it's nothing, it's bugs)",
    "THIS MESSAGE IS empty% BUGS (it's empty, but it's bugs)",
    "THIS MESSAGE IS blank% BUGS (it's blank, but it's bugs)",
    "THIS MESSAGE IS missing% BUGS (it's missing, but it's bugs)",
    "THIS MESSAGE IS gone% BUGS (it's gone, but the bugs remain)",
    "THIS MESSAGE IS deleted% BUGS (it's deleted, but the bugs are still here)",
    "THIS MESSAGE IS removed% BUGS (it's removed, but the bugs persist)",
    "THIS MESSAGE IS erased% BUGS (it's erased, but the bugs are indelible)",
    "THIS MESSAGE IS permanent% BUGS (the bugs are permanent)",
    "THIS MESSAGE IS eternal% BUGS (the bugs are eternal)",
    "THIS MESSAGE IS immortal% BUGS (the bugs are immortal)",
    "THIS MESSAGE IS undying% BUGS (the bugs are undying)",
    "THIS MESSAGE IS unkillable% BUGS (the bugs are unkillable)",
    "THIS MESSAGE IS indestructible% BUGS (the bugs are indestructible)",
    "THIS MESSAGE IS invincible% BUGS (the bugs are invincible)",
    "THIS MESSAGE IS unstoppable% BUGS (the bugs are unstoppable)",
    "THIS MESSAGE IS inevitable% BUGS (the bugs are inevitable)",
    "THIS MESSAGE IS unavoidable% BUGS (the bugs are unavoidable)",
    "THIS MESSAGE IS inescapable% BUGS (the bugs are inescapable)",
    "THIS MESSAGE IS omnipresent% BUGS (the bugs are everywhere)",
    "THIS MESSAGE IS omniscient% BUGS (the bugs know everything)",
    "THIS MESSAGE IS omnipotent% BUGS (the bugs are all-powerful)",
    "THIS MESSAGE IS transcendent% BUGS (the bugs transcend reality)",
    "THIS MESSAGE IS divine% BUGS (the bugs are divine)",
    "THIS MESSAGE IS cosmic% BUGS (the bugs are cosmic)",
    "THIS MESSAGE IS universal% BUGS (the bugs are universal)",
    "THIS MESSAGE IS multiversal% BUGS (the bugs are multiversal)",
    "THIS MESSAGE IS omniversal% BUGS (the bugs are omniversal)",
    "THIS MESSAGE IS everything% BUGS (everything is bugs)",
    "THIS MESSAGE IS nothing% BUGS (nothing is not bugs)",
    "THIS MESSAGE IS the beginning% BUGS (in the beginning, there were bugs)",
    "THIS MESSAGE IS the end% BUGS (in the end, there will be bugs)",
    "THIS MESSAGE IS alpha% BUGS (alpha bugs)",
    "THIS MESSAGE IS omega% BUGS (omega bugs)",
    "THIS MESSAGE IS the first% BUGS (the first bugs)",
    "THIS MESSAGE IS the last% BUGS (the last bugs)",
    "THIS MESSAGE IS the only% BUGS (the only bugs)",
    "THIS MESSAGE IS the one% BUGS (the one true bug)",
    "THIS MESSAGE IS the chosen% BUGS (the chosen bug)",
    "THIS MESSAGE IS the prophecy% BUGS (the bug prophecy)",
    "THIS MESSAGE IS the legend% BUGS (the bug legend)",
    "THIS MESSAGE IS the myth% BUGS (the bug myth)",
    "THIS MESSAGE IS the story% BUGS (the bug story)",
    "THIS MESSAGE IS the tale% BUGS (the bug tale)",
    "THIS MESSAGE IS the saga% BUGS (the bug saga)",
    "THIS MESSAGE IS the epic% BUGS (the bug epic)",
    "THIS MESSAGE IS the chronicle% BUGS (the bug chronicle)",
    "THIS MESSAGE IS the history% BUGS (the bug history)",
    "THIS MESSAGE IS the future% BUGS (the bug future)",
    "THIS MESSAGE IS the past% BUGS (the bug past)",
    "THIS MESSAGE IS the present% BUGS (the bug present)",
    "THIS MESSAGE IS timeless% BUGS (the bugs are timeless)",
    "THIS MESSAGE IS ageless% BUGS (the bugs are ageless)",
    "THIS MESSAGE IS endless% BUGS (the bugs are endless)",
    "THIS MESSAGE IS boundless% BUGS (the bugs are boundless)",
    "THIS MESSAGE IS limitless% BUGS (the bugs are limitless)",
    "THIS MESSAGE IS infinite% BUGS (the bugs are infinite)",
    "THIS MESSAGE IS absolute% BUGS (the bugs are absolute)",
    "THIS MESSAGE IS ultimate% BUGS (the bugs are ultimate)",
    "THIS MESSAGE IS supreme% BUGS (the bugs are supreme)",
    "THIS MESSAGE IS paramount% BUGS (the bugs are paramount)",
    "THIS MESSAGE IS sovereign% BUGS (the bugs are sovereign)",
    "THIS MESSAGE IS dominant% BUGS (the bugs are dominant)",
    "THIS MESSAGE IS ruling% BUGS (the bugs are ruling)",
    "THIS MESSAGE IS reigning% BUGS (the bugs are reigning)",
    "THIS MESSAGE IS governing% BUGS (the bugs are governing)",
    "THIS MESSAGE IS controlling% BUGS (the bugs are controlling)",
    "THIS MESSAGE IS commanding% BUGS (the bugs are commanding)",
    "THIS MESSAGE IS leading% BUGS (the bugs are leading)",
    "THIS MESSAGE IS guiding% BUGS (the bugs are guiding)",
    "THIS MESSAGE IS directing% BUGS (the bugs are directing)",
    "THIS MESSAGE IS orchestrating% BUGS (the bugs are orchestrating)",
    "THIS MESSAGE IS conducting% BUGS (the bugs are conducting)",
    "THIS MESSAGE IS managing% BUGS (the bugs are managing)",
    "THIS MESSAGE IS supervising% BUGS (the bugs are supervising)",
    "THIS MESSAGE IS overseeing% BUGS (the bugs are overseeing)",
    "THIS MESSAGE IS monitoring% BUGS (the bugs are monitoring)",
    "THIS MESSAGE IS watching% BUGS (the bugs are watching)",
    "THIS MESSAGE IS observing% BUGS (the bugs are observing)",
    "THIS MESSAGE IS seeing% BUGS (the bugs are seeing)",
    "THIS MESSAGE IS looking% BUGS (the bugs are looking)",
    "THIS MESSAGE IS staring% BUGS (the bugs are staring)",
    "THIS MESSAGE IS gazing% BUGS (the bugs are gazing)",
    "THIS MESSAGE IS peering% BUGS (the bugs are peering)",
    "THIS MESSAGE IS glaring% BUGS (the bugs are glaring)",
    "THIS MESSAGE IS eyeing% BUGS (the bugs are eyeing)",
    "THIS MESSAGE IS scrutinizing% BUGS (the bugs are scrutinizing)",
    "THIS MESSAGE IS examining% BUGS (the bugs are examining)",
    "THIS MESSAGE IS inspecting% BUGS (the bugs are inspecting)",
    "THIS MESSAGE IS analyzing% BUGS (the bugs are analyzing)",
    "THIS MESSAGE IS studying% BUGS (the bugs are studying)",
    "THIS MESSAGE IS investigating% BUGS (the bugs are investigating)",
    "THIS MESSAGE IS researching% BUGS (the bugs are researching)",
    "THIS MESSAGE IS exploring% BUGS (the bugs are exploring)",
    "THIS MESSAGE IS discovering% BUGS (the bugs are discovering)",
    "THIS MESSAGE IS finding% BUGS (the bugs are finding)",
    "THIS MESSAGE IS locating% BUGS (the bugs are locating)",
    "THIS MESSAGE IS identifying% BUGS (the bugs are identifying)",
    "THIS MESSAGE IS recognizing% BUGS (the bugs are recognizing)",
    "THIS MESSAGE IS detecting% BUGS (the bugs are detecting)",
    "THIS MESSAGE IS sensing% BUGS (the bugs are sensing)",
    "THIS MESSAGE IS feeling% BUGS (the bugs are feeling)",
    "THIS MESSAGE IS touching% BUGS (the bugs are touching)",
    "THIS MESSAGE IS reaching% BUGS (the bugs are reaching)",
    "THIS MESSAGE IS grasping% BUGS (the bugs are grasping)",
    "THIS MESSAGE IS holding% BUGS (the bugs are holding)",
    "THIS MESSAGE IS keeping% BUGS (the bugs are keeping)",
    "THIS MESSAGE IS maintaining% BUGS (the bugs are maintaining)",
    "THIS MESSAGE IS preserving% BUGS (the bugs are preserving)",
    "THIS MESSAGE IS protecting% BUGS (the bugs are protecting)",
    "THIS MESSAGE IS guarding% BUGS (the bugs are guarding)",
    "THIS MESSAGE IS defending% BUGS (the bugs are defending)",
    "THIS MESSAGE IS shielding% BUGS (the bugs are shielding)",
    "THIS MESSAGE IS sheltering% BUGS (the bugs are sheltering)",
    "THIS MESSAGE IS harboring% BUGS (the bugs are harboring)",
    "THIS MESSAGE IS housing% BUGS (the bugs are housing)",
    "THIS MESSAGE IS containing% BUGS (the bugs are containing)",
    "THIS MESSAGE IS enclosing% BUGS (the bugs are enclosing)",
    "THIS MESSAGE IS surrounding% BUGS (the bugs are surrounding)",
    "THIS MESSAGE IS encircling% BUGS (the bugs are encircling)",
    "THIS MESSAGE IS enveloping% BUGS (the bugs are enveloping)",
    "THIS MESSAGE IS wrapping% BUGS (the bugs are wrapping)",
    "THIS MESSAGE IS covering% BUGS (the bugs are covering)",
    "THIS MESSAGE IS blanketing% BUGS (the bugs are blanketing)",
    "THIS MESSAGE IS smothering% BUGS (the bugs are smothering)",
    "THIS MESSAGE IS suffocating% BUGS (the bugs are suffocating)",
    "THIS MESSAGE IS drowning% BUGS (the bugs are drowning)",
    "THIS MESSAGE IS flooding% BUGS (the bugs are flooding)",
    "THIS MESSAGE IS overwhelming% BUGS (the bugs are overwhelming)",
    "THIS MESSAGE IS consuming% BUGS (the bugs are consuming)",
    "THIS MESSAGE IS devouring% BUGS (the bugs are devouring)",
    "THIS MESSAGE IS swallowing% BUGS (the bugs are swallowing)",
    "THIS MESSAGE IS absorbing% BUGS (the bugs are absorbing)",
    "THIS MESSAGE IS assimilating% BUGS (the bugs are assimilating)",
    "THIS MESSAGE IS incorporating% BUGS (the bugs are incorporating)",
    "THIS MESSAGE IS integrating% BUGS (the bugs are integrating)",
    "THIS MESSAGE IS merging% BUGS (the bugs are merging)",
    "THIS MESSAGE IS fusing% BUGS (the bugs are fusing)",
    "THIS MESSAGE IS blending% BUGS (the bugs are blending)",
    "THIS MESSAGE IS mixing% BUGS (the bugs are mixing)",
    "THIS MESSAGE IS combining% BUGS (the bugs are combining)",
    "THIS MESSAGE IS uniting% BUGS (the bugs are uniting)",
    "THIS MESSAGE IS joining% BUGS (the bugs are joining)",
    "THIS MESSAGE IS connecting% BUGS (the bugs are connecting)",
    "THIS MESSAGE IS linking% BUGS (the bugs are linking)",
    "THIS MESSAGE IS coupling% BUGS (the bugs are coupling)",
    "THIS MESSAGE IS pairing% BUGS (the bugs are pairing)",
    "THIS MESSAGE IS matching% BUGS (the bugs are matching)",
    "THIS MESSAGE IS aligning% BUGS (the bugs are aligning)",
    "THIS MESSAGE IS synchronizing% BUGS (the bugs are synchronizing)",
    "THIS MESSAGE IS harmonizing% BUGS (the bugs are harmonizing)",
    "THIS MESSAGE IS coordinating% BUGS (the bugs are coordinating)",
    "THIS MESSAGE IS organizing% BUGS (the bugs are organizing)",
    "THIS MESSAGE IS arranging% BUGS (the bugs are arranging)",
    "THIS MESSAGE IS ordering% BUGS (the bugs are ordering)",
    "THIS MESSAGE IS sorting% BUGS (the bugs are sorting)",
    "THIS MESSAGE IS categorizing% BUGS (the bugs are categorizing)",
    "THIS MESSAGE IS classifying% BUGS (the bugs are classifying)",
    "THIS MESSAGE IS grouping% BUGS (the bugs are grouping)",
    "THIS MESSAGE IS clustering% BUGS (the bugs are clustering)",
    "THIS MESSAGE IS collecting% BUGS (the bugs are collecting)",
    "THIS MESSAGE IS gathering% BUGS (the bugs are gathering)",
    "THIS MESSAGE IS assembling% BUGS (the bugs are assembling)",
    "THIS MESSAGE IS compiling% BUGS (the bugs are compiling)",
    "THIS MESSAGE IS aggregating% BUGS (the bugs are aggregating)",
    "THIS MESSAGE IS accumulating% BUGS (the bugs are accumulating)",
    "THIS MESSAGE IS amassing% BUGS (the bugs are amassing)",
    "THIS MESSAGE IS hoarding% BUGS (the bugs are hoarding)",
    "THIS MESSAGE IS stockpiling% BUGS (the bugs are stockpiling)",
    "THIS MESSAGE IS storing% BUGS (the bugs are storing)",
    "THIS MESSAGE IS saving% BUGS (the bugs are saving)",
    "THIS MESSAGE IS keeping% BUGS (the bugs are keeping)",
    "THIS MESSAGE IS retaining% BUGS (the bugs are retaining)",
    "THIS MESSAGE IS holding% BUGS (the bugs are holding)",
    "THIS MESSAGE IS possessing% BUGS (the bugs are possessing)",
    "THIS MESSAGE IS owning% BUGS (the bugs are owning)",
    "THIS MESSAGE IS having% BUGS (the bugs are having)",
    "THIS MESSAGE IS getting% BUGS (the bugs are getting)",
    "THIS MESSAGE IS receiving% BUGS (the bugs are receiving)",
    "THIS MESSAGE IS obtaining% BUGS (the bugs are obtaining)",
    "THIS MESSAGE IS acquiring% BUGS (the bugs are acquiring)",
    "THIS MESSAGE IS gaining% BUGS (the bugs are gaining)",
    "THIS MESSAGE IS earning% BUGS (the bugs are earning)",
    "THIS MESSAGE IS winning% BUGS (the bugs are winning)",
    "THIS MESSAGE IS achieving% BUGS (the bugs are achieving)",
    "THIS MESSAGE IS accomplishing% BUGS (the bugs are accomplishing)",
    "THIS MESSAGE IS completing% BUGS (the bugs are completing)",
    "THIS MESSAGE IS finishing% BUGS (the bugs are finishing)",
    "THIS MESSAGE IS ending% BUGS (the bugs are ending)",
    "THIS MESSAGE IS concluding% BUGS (the bugs are concluding)",
    "THIS MESSAGE IS terminating% BUGS (the bugs are terminating)",
    "THIS MESSAGE IS ceasing% BUGS (the bugs are ceasing)",
    "THIS MESSAGE IS stopping% BUGS (the bugs are stopping)",
    "THIS MESSAGE IS halting% BUGS (the bugs are halting)",
    "THIS MESSAGE IS pausing% BUGS (the bugs are pausing)",
    "THIS MESSAGE IS suspending% BUGS (the bugs are suspending)",
    "THIS MESSAGE IS interrupting% BUGS (the bugs are interrupting)",
    "THIS MESSAGE IS breaking% BUGS (the bugs are breaking)",
    "THIS MESSAGE IS shattering% BUGS (the bugs are shattering)",
    "THIS MESSAGE IS destroying% BUGS (the bugs are destroying)",
    "THIS MESSAGE IS annihilating% BUGS (the bugs are annihilating)",
    "THIS MESSAGE IS obliterating% BUGS (the bugs are obliterating)",
    "THIS MESSAGE IS eradicating% BUGS (the bugs are eradicating)",
    "THIS MESSAGE IS eliminating% BUGS (the bugs are eliminating)",
    "THIS MESSAGE IS removing% BUGS (the bugs are removing)",
    "THIS MESSAGE IS deleting% BUGS (the bugs are deleting)",
    "THIS MESSAGE IS erasing% BUGS (the bugs are erasing)",
    "THIS MESSAGE IS wiping% BUGS (the bugs are wiping)",
    "THIS MESSAGE IS clearing% BUGS (the bugs are clearing)",
    "THIS MESSAGE IS purging% BUGS (the bugs are purging)",
    "THIS MESSAGE IS cleansing% BUGS (the bugs are cleansing)",
    "THIS MESSAGE IS sanitizing% BUGS (the bugs are sanitizing)",
    "THIS MESSAGE IS disinfecting% BUGS (the bugs are disinfecting)",
    "THIS MESSAGE IS sterilizing% BUGS (the bugs are sterilizing)",
    "THIS MESSAGE IS decontaminating% BUGS (the bugs are decontaminating)",
    "THIS MESSAGE IS detoxifying% BUGS (the bugs are detoxifying)",
    "THIS MESSAGE IS purifying% BUGS (the bugs are purifying)",
    "THIS MESSAGE IS refining% BUGS (the bugs are refining)",
    "THIS MESSAGE IS filtering% BUGS (the bugs are filtering)",
    "THIS MESSAGE IS screening% BUGS (the bugs are screening)",
    "THIS MESSAGE IS sifting% BUGS (the bugs are sifting)",
    "THIS MESSAGE IS straining% BUGS (the bugs are straining)",
    "THIS MESSAGE IS separating% BUGS (the bugs are separating)",
    "THIS MESSAGE IS dividing% BUGS (the bugs are dividing)",
    "THIS MESSAGE IS splitting% BUGS (the bugs are splitting)",
    "THIS MESSAGE IS breaking% BUGS (the bugs are breaking)",
    "THIS MESSAGE IS fragmenting% BUGS (the bugs are fragmenting)",
    "THIS MESSAGE IS shattering% BUGS (the bugs are shattering)",
    "THIS MESSAGE IS crushing% BUGS (the bugs are crushing)",
    "THIS MESSAGE IS grinding% BUGS (the bugs are grinding)",
    "THIS MESSAGE IS pulverizing% BUGS (the bugs are pulverizing)",
    "THIS MESSAGE IS atomizing% BUGS (the bugs are atomizing)",
    "THIS MESSAGE IS vaporizing% BUGS (the bugs are vaporizing)",
    "THIS MESSAGE IS evaporating% BUGS (the bugs are evaporating)",
    "THIS MESSAGE IS dissolving% BUGS (the bugs are dissolving)",
    "THIS MESSAGE IS melting% BUGS (the bugs are melting)",
    "THIS MESSAGE IS liquefying% BUGS (the bugs are liquefying)",
    "THIS MESSAGE IS solidifying% BUGS (the bugs are solidifying)",
    "THIS MESSAGE IS freezing% BUGS (the bugs are freezing)",
    "THIS MESSAGE IS crystallizing% BUGS (the bugs are crystallizing)",
    "THIS MESSAGE IS petrifying% BUGS (the bugs are petrifying)",
    "THIS MESSAGE IS fossilizing% BUGS (the bugs are fossilizing)",
    "THIS MESSAGE IS mummifying% BUGS (the bugs are mummifying)",
    "THIS MESSAGE IS preserving% BUGS (the bugs are preserving)",
    "THIS MESSAGE IS conserving% BUGS (the bugs are conserving)",
    "THIS MESSAGE IS maintaining% BUGS (the bugs are maintaining)",
    "THIS MESSAGE IS sustaining% BUGS (the bugs are sustaining)",
    "THIS MESSAGE IS supporting% BUGS (the bugs are supporting)",
    "THIS MESSAGE IS upholding% BUGS (the bugs are upholding)",
    "THIS MESSAGE IS backing% BUGS (the bugs are backing)",
    "THIS MESSAGE IS endorsing% BUGS (the bugs are endorsing)",
    "THIS MESSAGE IS promoting% BUGS (the bugs are promoting)",
    "THIS MESSAGE IS advancing% BUGS (the bugs are advancing)",
    "THIS MESSAGE IS furthering% BUGS (the bugs are furthering)",
    "THIS MESSAGE IS progressing% BUGS (the bugs are progressing)",
    "THIS MESSAGE IS developing% BUGS (the bugs are developing)",
    "THIS MESSAGE IS evolving% BUGS (the bugs are evolving)",
    "THIS MESSAGE IS growing% BUGS (the bugs are growing)",
    "THIS MESSAGE IS expanding% BUGS (the bugs are expanding)",
    "THIS MESSAGE IS extending% BUGS (the bugs are extending)",
    "THIS MESSAGE IS spreading% BUGS (the bugs are spreading)",
    "THIS MESSAGE IS proliferating% BUGS (the bugs are proliferating)",
    "THIS MESSAGE IS multiplying% BUGS (the bugs are multiplying)",
    "THIS MESSAGE IS reproducing% BUGS (the bugs are reproducing)",
    "THIS MESSAGE IS breeding% BUGS (the bugs are breeding)",
    "THIS MESSAGE IS spawning% BUGS (the bugs are spawning)",
    "THIS MESSAGE IS hatching% BUGS (the bugs are hatching)",
    "THIS MESSAGE IS emerging% BUGS (the bugs are emerging)",
    "THIS MESSAGE IS appearing% BUGS (the bugs are appearing)",
    "THIS MESSAGE IS materializing% BUGS (the bugs are materializing)",
    "THIS MESSAGE IS manifesting% BUGS (the bugs are manifesting)",
    "THIS MESSAGE IS incarnating% BUGS (the bugs are incarnating)",
    "THIS MESSAGE IS embodying% BUGS (the bugs are embodying)",
    "THIS MESSAGE IS personifying% BUGS (the bugs are personifying)",
    "THIS MESSAGE IS representing% BUGS (the bugs are representing)",
    "THIS MESSAGE IS symbolizing% BUGS (the bugs are symbolizing)",
    "THIS MESSAGE IS signifying% BUGS (the bugs are signifying)",
    "THIS MESSAGE IS meaning% BUGS (the bugs are meaning)",
    "THIS MESSAGE IS indicating% BUGS (the bugs are indicating)",
    "THIS MESSAGE IS suggesting% BUGS (the bugs are suggesting)",
    "THIS MESSAGE IS implying% BUGS (the bugs are implying)",
    "THIS MESSAGE IS hinting% BUGS (the bugs are hinting)",
    "THIS MESSAGE IS alluding% BUGS (the bugs are alluding)",
    "THIS MESSAGE IS referring% BUGS (the bugs are referring)",
    "THIS MESSAGE IS pointing% BUGS (the bugs are pointing)",
    "THIS MESSAGE IS directing% BUGS (the bugs are directing)",
    "THIS MESSAGE IS guiding% BUGS (the bugs are guiding)",
    "THIS MESSAGE IS leading% BUGS (the bugs are leading)",
    "THIS MESSAGE IS showing% BUGS (the bugs are showing)",
    "THIS MESSAGE IS demonstrating% BUGS (the bugs are demonstrating)",
    "THIS MESSAGE IS illustrating% BUGS (the bugs are illustrating)",
    "THIS MESSAGE IS depicting% BUGS (the bugs are depicting)",
    "THIS MESSAGE IS portraying% BUGS (the bugs are portraying)",
    "THIS MESSAGE IS representing% BUGS (the bugs are representing)",
    "THIS MESSAGE IS describing% BUGS (the bugs are describing)",
    "THIS MESSAGE IS explaining% BUGS (the bugs are explaining)",
    "THIS MESSAGE IS clarifying% BUGS (the bugs are clarifying)",
    "THIS MESSAGE IS elucidating% BUGS (the bugs are elucidating)",
    "THIS MESSAGE IS illuminating% BUGS (the bugs are illuminating)",
    "THIS MESSAGE IS enlightening% BUGS (the bugs are enlightening)",
    "THIS MESSAGE IS educating% BUGS (the bugs are educating)",
    "THIS MESSAGE IS teaching% BUGS (the bugs are teaching)",
    "THIS MESSAGE IS instructing% BUGS (the bugs are instructing)",
    "THIS MESSAGE IS training% BUGS (the bugs are training)",
    "THIS MESSAGE IS coaching% BUGS (the bugs are coaching)",
    "THIS MESSAGE IS mentoring% BUGS (the bugs are mentoring)",
    "THIS MESSAGE IS tutoring% BUGS (the bugs are tutoring)",
    "THIS MESSAGE IS guiding% BUGS (the bugs are guiding)",
    "THIS MESSAGE IS advising% BUGS (the bugs are advising)",
    "THIS MESSAGE IS counseling% BUGS (the bugs are counseling)",
    "THIS MESSAGE IS consulting% BUGS (the bugs are consulting)",
    "THIS MESSAGE IS recommending% BUGS (the bugs are recommending)",
    "THIS MESSAGE IS suggesting% BUGS (the bugs are suggesting)",
    "THIS MESSAGE IS proposing% BUGS (the bugs are proposing)",
    "THIS MESSAGE IS offering% BUGS (the bugs are offering)",
    "THIS MESSAGE IS providing% BUGS (the bugs are providing)",
    "THIS MESSAGE IS supplying% BUGS (the bugs are supplying)",
    "THIS MESSAGE IS delivering% BUGS (the bugs are delivering)",
    "THIS MESSAGE IS giving% BUGS (the bugs are giving)",
    "THIS MESSAGE IS presenting% BUGS (the bugs are presenting)",
    "THIS MESSAGE IS submitting% BUGS (the bugs are submitting)",
    "THIS MESSAGE IS tendering% BUGS (the bugs are tendering)",
    "THIS MESSAGE IS proffering% BUGS (the bugs are proffering)",
    "THIS MESSAGE IS extending% BUGS (the bugs are extending)",
    "THIS MESSAGE IS granting% BUGS (the bugs are granting)",
    "THIS MESSAGE IS awarding% BUGS (the bugs are awarding)",
    "THIS MESSAGE IS bestowing% BUGS (the bugs are bestowing)",
    "THIS MESSAGE IS conferring% BUGS (the bugs are conferring)",
    "THIS MESSAGE IS imparting% BUGS (the bugs are imparting)",
    "THIS MESSAGE IS communicating% BUGS (the bugs are communicating)",
    "THIS MESSAGE IS conveying% BUGS (the bugs are conveying)",
    "THIS MESSAGE IS transmitting% BUGS (the bugs are transmitting)",
    "THIS MESSAGE IS sending% BUGS (the bugs are sending)",
    "THIS MESSAGE IS dispatching% BUGS (the bugs are dispatching)",
    "THIS MESSAGE IS forwarding% BUGS (the bugs are forwarding)",
    "THIS MESSAGE IS relaying% BUGS (the bugs are relaying)",
    "THIS MESSAGE IS passing% BUGS (the bugs are passing)",
    "THIS MESSAGE IS handing% BUGS (the bugs are handing)",
    "THIS MESSAGE IS transferring% BUGS (the bugs are transferring)",
    "THIS MESSAGE IS moving% BUGS (the bugs are moving)",
    "THIS MESSAGE IS shifting% BUGS (the bugs are shifting)",
    "THIS MESSAGE IS changing% BUGS (the bugs are changing)",
    "THIS MESSAGE IS altering% BUGS (the bugs are altering)",
    "THIS MESSAGE IS modifying% BUGS (the bugs are modifying)",
    "THIS MESSAGE IS adjusting% BUGS (the bugs are adjusting)",
    "THIS MESSAGE IS adapting% BUGS (the bugs are adapting)",
    "THIS MESSAGE IS transforming% BUGS (the bugs are transforming)",
    "THIS MESSAGE IS converting% BUGS (the bugs are converting)",
    "THIS MESSAGE IS metamorphosing% BUGS (the bugs are metamorphosing)",
    "THIS MESSAGE IS transmuting% BUGS (the bugs are transmuting)",
    "THIS MESSAGE IS transfiguring% BUGS (the bugs are transfiguring)",
    "THIS MESSAGE IS mutating% BUGS (the bugs are mutating)",
    "THIS MESSAGE IS evolving% BUGS (the bugs are evolving)",
    "THIS MESSAGE IS devolving% BUGS (the bugs are devolving)",
    "THIS MESSAGE IS revolving% BUGS (the bugs are revolving)",
    "THIS MESSAGE IS involving% BUGS (the bugs are involving)",
    "THIS MESSAGE IS including% BUGS (the bugs are including)",
    "THIS MESSAGE IS excluding% BUGS (the bugs are excluding)",
    "THIS MESSAGE IS excepting% BUGS (the bugs are excepting)",
    "THIS MESSAGE IS accepting% BUGS (the bugs are accepting)",
    "THIS MESSAGE IS rejecting% BUGS (the bugs are rejecting)",
    "THIS MESSAGE IS denying% BUGS (the bugs are denying)",
    "THIS MESSAGE IS refusing% BUGS (the bugs are refusing)",
    "THIS MESSAGE IS declining% BUGS (the bugs are declining)",
    "THIS MESSAGE IS dismissing% BUGS (the bugs are dismissing)",
    "THIS MESSAGE IS ignoring% BUGS (the bugs are ignoring)",
    "THIS MESSAGE IS overlooking% BUGS (the bugs are overlooking)",
    "THIS MESSAGE IS neglecting% BUGS (the bugs are neglecting)",
    "THIS MESSAGE IS forgetting% BUGS (the bugs are forgetting)",
    "THIS MESSAGE IS remembering% BUGS (the bugs are remembering)",
    "THIS MESSAGE IS recalling% BUGS (the bugs are recalling)",
    "THIS MESSAGE IS recollecting% BUGS (the bugs are recollecting)",
    "THIS MESSAGE IS reminiscing% BUGS (the bugs are reminiscing)",
    "THIS MESSAGE IS nostalgic% BUGS (the bugs are nostalgic)",
    "THIS MESSAGE IS sentimental% BUGS (the bugs are sentimental)",
    "THIS MESSAGE IS emotional% BUGS (the bugs are emotional)",
    "THIS MESSAGE IS passionate% BUGS (the bugs are passionate)",
    "THIS MESSAGE IS enthusiastic% BUGS (the bugs are enthusiastic)",
    "THIS MESSAGE IS excited% BUGS (the bugs are excited)",
    "THIS MESSAGE IS thrilled% BUGS (the bugs are thrilled)",
    "THIS MESSAGE IS delighted% BUGS (the bugs are delighted)",
    "THIS MESSAGE IS pleased% BUGS (the bugs are pleased)",
    "THIS MESSAGE IS happy% BUGS (the bugs are happy)",
    "THIS MESSAGE IS joyful% BUGS (the bugs are joyful)",
    "THIS MESSAGE IS ecstatic% BUGS (the bugs are ecstatic)",
    "THIS MESSAGE IS euphoric% BUGS (the bugs are euphoric)",
    "THIS MESSAGE IS elated% BUGS (the bugs are elated)",
    "THIS MESSAGE IS overjoyed% BUGS (the bugs are overjoyed)",
    "THIS MESSAGE IS jubilant% BUGS (the bugs are jubilant)",
    "THIS MESSAGE IS exultant% BUGS (the bugs are exultant)",
    "THIS MESSAGE IS triumphant% BUGS (the bugs are triumphant)",
    "THIS MESSAGE IS victorious% BUGS (the bugs are victorious)",
    "THIS MESSAGE IS successful% BUGS (the bugs are successful)",
    "THIS MESSAGE IS accomplished% BUGS (the bugs are accomplished)",
    "THIS MESSAGE IS achieved% BUGS (the bugs are achieved)",
    "THIS MESSAGE IS attained% BUGS (the bugs are attained)",
    "THIS MESSAGE IS reached% BUGS (the bugs are reached)",
    "THIS MESSAGE IS gained% BUGS (the bugs are gained)",
    "THIS MESSAGE IS earned% BUGS (the bugs are earned)",
    "THIS MESSAGE IS won% BUGS (the bugs are won)",
    "THIS MESSAGE IS secured% BUGS (the bugs are secured)",
    "THIS MESSAGE IS obtained% BUGS (the bugs are obtained)",
    "THIS MESSAGE IS acquired% BUGS (the bugs are acquired)",
    "THIS MESSAGE IS procured% BUGS (the bugs are procured)",
    "THIS MESSAGE IS collected% BUGS (the bugs are collected)",
    "THIS MESSAGE IS gathered% BUGS (the bugs are gathered)",
    "THIS MESSAGE IS assembled% BUGS (the bugs are assembled)",
    "THIS MESSAGE IS compiled% BUGS (the bugs are compiled)",
    "THIS MESSAGE IS aggregated% BUGS (the bugs are aggregated)",
    "THIS MESSAGE IS accumulated% BUGS (the bugs are accumulated)",
    "THIS MESSAGE IS amassed% BUGS (the bugs are amassed)",
    "THIS MESSAGE IS hoarded% BUGS (the bugs are hoarded)",
    "THIS MESSAGE IS stockpiled% BUGS (the bugs are stockpiled)",
    "THIS MESSAGE IS stored% BUGS (the bugs are stored)",
    "THIS MESSAGE IS saved% BUGS (the bugs are saved)",
    "THIS MESSAGE IS kept% BUGS (the bugs are kept)",
    "THIS MESSAGE IS retained% BUGS (the bugs are retained)",
    "THIS MESSAGE IS held% BUGS (the bugs are held)",
    "THIS MESSAGE IS possessed% BUGS (the bugs are possessed)",
    "THIS MESSAGE IS owned% BUGS (the bugs are owned)",
    "THIS MESSAGE IS had% BUGS (the bugs are had)",
    "THIS MESSAGE IS got% BUGS (the bugs are got)",
    "THIS MESSAGE IS gotten% BUGS (the bugs are gotten)",
    "THIS MESSAGE IS received% BUGS (the bugs are received)",
    "THIS MESSAGE IS obtained% BUGS (the bugs are obtained)",
    "THIS MESSAGE IS acquired% BUGS (the bugs are acquired)",
    "THIS MESSAGE IS gained% BUGS (the bugs are gained)",
    "THIS MESSAGE IS earned% BUGS (the bugs are earned)",
    "THIS MESSAGE IS won% BUGS (the bugs are won)",
    "THIS MESSAGE IS achieved% BUGS (the bugs are achieved)",
    "THIS MESSAGE IS accomplished% BUGS (the bugs are accomplished)",
    "THIS MESSAGE IS completed% BUGS (the bugs are completed)",
    "THIS MESSAGE IS finished% BUGS (the bugs are finished)",
    "THIS MESSAGE IS ended% BUGS (the bugs are ended)",
    "THIS MESSAGE IS concluded% BUGS (the bugs are concluded)",
    "THIS MESSAGE IS terminated% BUGS (the bugs are terminated)",
    "THIS MESSAGE IS ceased% BUGS (the bugs are ceased)",
    "THIS MESSAGE IS stopped% BUGS (the bugs are stopped)",
    "THIS MESSAGE IS halted% BUGS (the bugs are halted)",
    "THIS MESSAGE IS paused% BUGS (the bugs are paused)",
    "THIS MESSAGE IS suspended% BUGS (the bugs are suspended)",
    "THIS MESSAGE IS interrupted% BUGS (the bugs are interrupted)",
    "THIS MESSAGE IS broken% BUGS (the bugs are broken)",
    "THIS MESSAGE IS shattered% BUGS (the bugs are shattered)",
    "THIS MESSAGE IS destroyed% BUGS (the bugs are destroyed)",
    "THIS MESSAGE IS annihilated% BUGS (the bugs are annihilated)",
    "THIS MESSAGE IS obliterated% BUGS (the bugs are obliterated)",
    "THIS MESSAGE IS eradicated% BUGS (the bugs are eradicated)",
    "THIS MESSAGE IS eliminated% BUGS (the bugs are eliminated)",
    "THIS MESSAGE IS removed% BUGS (the bugs are removed)",
    "THIS MESSAGE IS deleted% BUGS (the bugs are deleted)",
    "THIS MESSAGE IS erased% BUGS (the bugs are erased)",
    "THIS MESSAGE IS wiped% BUGS (the bugs are wiped)",
    "THIS MESSAGE IS cleared% BUGS (the bugs are cleared)",
    "THIS MESSAGE IS purged% BUGS (the bugs are purged)",
    "THIS MESSAGE IS cleansed% BUGS (the bugs are cleansed)",
    "THIS MESSAGE IS sanitized% BUGS (the bugs are sanitized)",
    "THIS MESSAGE IS disinfected% BUGS (the bugs are disinfected)",
    "THIS MESSAGE IS sterilized% BUGS (the bugs are sterilized)",
    "THIS MESSAGE IS decontaminated% BUGS (the bugs are decontaminated)",
    "THIS MESSAGE IS detoxified% BUGS (the bugs are detoxified)",
    "THIS MESSAGE IS purified% BUGS (the bugs are purified)",
    "THIS MESSAGE IS refined% BUGS (the bugs are refined)",
    "THIS MESSAGE IS filtered% BUGS (the bugs are filtered)",
    "THIS MESSAGE IS screened% BUGS (the bugs are screened)",
    "THIS MESSAGE IS sifted% BUGS (the bugs are sifted)",
    "THIS MESSAGE IS strained% BUGS (the bugs are strained)",
    "THIS MESSAGE IS separated% BUGS (the bugs are separated)",
    "THIS MESSAGE IS divided% BUGS (the bugs are divided)",
    "THIS MESSAGE IS split% BUGS (the bugs are split)",
    "THIS MESSAGE IS broken% BUGS (the bugs are broken)",
    "THIS MESSAGE IS fragmented% BUGS (the bugs are fragmented)",
    "THIS MESSAGE IS shattered% BUGS (the bugs are shattered)",
    "THIS MESSAGE IS crushed% BUGS (the bugs are crushed)",
    "THIS MESSAGE IS ground% BUGS (the bugs are ground)",
    "THIS MESSAGE IS pulverized% BUGS (the bugs are pulverized)",
    "THIS MESSAGE IS atomized% BUGS (the bugs are atomized)",
    "THIS MESSAGE IS vaporized% BUGS (the bugs are vaporized)",
    "THIS MESSAGE IS evaporated% BUGS (the bugs are evaporated)",
    "THIS MESSAGE IS dissolved% BUGS (the bugs are dissolved)",
    "THIS MESSAGE IS melted% BUGS (the bugs are melted)",
    "THIS MESSAGE IS liquefied% BUGS (the bugs are liquefied)",
    "THIS MESSAGE IS solidified% BUGS (the bugs are solidified)",
    "THIS MESSAGE IS frozen% BUGS (the bugs are frozen)",
    "THIS MESSAGE IS crystallized% BUGS (the bugs are crystallized)",
    "THIS MESSAGE IS petrified% BUGS (the bugs are petrified)",
    "THIS MESSAGE IS fossilized% BUGS (the bugs are fossilized)",
    "THIS MESSAGE IS mummified% BUGS (the bugs are mummified)",
    "THIS MESSAGE IS preserved% BUGS (the bugs are preserved)",
    "THIS MESSAGE IS conserved% BUGS (the bugs are conserved)",
    "THIS MESSAGE IS maintained% BUGS (the bugs are maintained)",
    "THIS MESSAGE IS sustained% BUGS (the bugs are sustained)",
    "THIS MESSAGE IS supported% BUGS (the bugs are supported)",
    "THIS MESSAGE IS upheld% BUGS (the bugs are upheld)",
    "THIS MESSAGE IS backed% BUGS (the bugs are backed)",
    "THIS MESSAGE IS endorsed% BUGS (the bugs are endorsed)",
    "THIS MESSAGE IS promoted% BUGS (the bugs are promoted)",
    "THIS MESSAGE IS advanced% BUGS (the bugs are advanced)",
    "THIS MESSAGE IS furthered% BUGS (the bugs are furthered)",
    "THIS MESSAGE IS progressed% BUGS (the bugs are progressed)",
    "THIS MESSAGE IS developed% BUGS (the bugs are developed)",
    "THIS MESSAGE IS evolved% BUGS (the bugs are evolved)",
    "THIS MESSAGE IS grown% BUGS (the bugs are grown)",
    "THIS MESSAGE IS expanded% BUGS (the bugs are expanded)",
    "THIS MESSAGE IS extended% BUGS (the bugs are extended)",
    "THIS MESSAGE IS spread% BUGS (the bugs are spread)",
    "THIS MESSAGE IS proliferated% BUGS (the bugs are proliferated)",
    "THIS MESSAGE IS multiplied% BUGS (the bugs are multiplied)",
    "THIS MESSAGE IS reproduced% BUGS (the bugs are reproduced)",
    "THIS MESSAGE IS bred% BUGS (the bugs are bred)",
    "THIS MESSAGE IS spawned% BUGS (the bugs are spawned)",
    "THIS MESSAGE IS hatched% BUGS (the bugs are hatched)",
    "THIS MESSAGE IS emerged% BUGS (the bugs are emerged)",
    "THIS MESSAGE IS appeared% BUGS (the bugs are appeared)",
    "THIS MESSAGE IS materialized% BUGS (the bugs are materialized)",
    "THIS MESSAGE IS manifested% BUGS (the bugs are manifested)",
    "THIS MESSAGE IS incarnated% BUGS (the bugs are incarnated)",
    "THIS MESSAGE IS embodied% BUGS (the bugs are embodied)",
    "THIS MESSAGE IS personified% BUGS (the bugs are personified)",
    "THIS MESSAGE IS represented% BUGS (the bugs are represented)",
    "THIS MESSAGE IS symbolized% BUGS (the bugs are symbolized)",
    "THIS MESSAGE IS signified% BUGS (the bugs are signified)",
    "THIS MESSAGE IS meant% BUGS (the bugs are meant)",
    "THIS MESSAGE IS indicated% BUGS (the bugs are indicated)",
    "THIS MESSAGE IS suggested% BUGS (the bugs are suggested)",
    "THIS MESSAGE IS implied% BUGS (the bugs are implied)",
    "THIS MESSAGE IS hinted% BUGS (the bugs are hinted)",
    "THIS MESSAGE IS alluded% BUGS (the bugs are alluded)",
    "THIS MESSAGE IS referred% BUGS (the bugs are referred)",
    "THIS MESSAGE IS pointed% BUGS (the bugs are pointed)",
    "THIS MESSAGE IS directed% BUGS (the bugs are directed)",
    "THIS MESSAGE IS guided% BUGS (the bugs are guided)",
    "THIS MESSAGE IS led% BUGS (the bugs are led)",
    "THIS MESSAGE IS shown% BUGS (the bugs are shown)",
    "THIS MESSAGE IS demonstrated% BUGS (the bugs are demonstrated)",
    "THIS MESSAGE IS illustrated% BUGS (the bugs are illustrated)",
    "THIS MESSAGE IS depicted% BUGS (the bugs are depicted)",
    "THIS MESSAGE IS portrayed% BUGS (the bugs are portrayed)",
    "THIS MESSAGE IS represented% BUGS (the bugs are represented)",
    "THIS MESSAGE IS described% BUGS (the bugs are described)",
    "THIS MESSAGE IS explained% BUGS (the bugs are explained)",
    "THIS MESSAGE IS clarified% BUGS (the bugs are clarified)",
    "THIS MESSAGE IS elucidated% BUGS (the bugs are elucidated)",
    "THIS MESSAGE IS illuminated% BUGS (the bugs are illuminated)",
    "THIS MESSAGE IS enlightened% BUGS (the bugs are enlightened)",
    "THIS MESSAGE IS educated% BUGS (the bugs are educated)",
    "THIS MESSAGE IS taught% BUGS (the bugs are taught)",
    "THIS MESSAGE IS instructed% BUGS (the bugs are instructed)",
    "THIS MESSAGE IS trained% BUGS (the bugs are trained)",
    "THIS MESSAGE IS coached% BUGS (the bugs are coached)",
    "THIS MESSAGE IS mentored% BUGS (the bugs are mentored)",
    "THIS MESSAGE IS tutored% BUGS (the bugs are tutored)",
    "THIS MESSAGE IS guided% BUGS (the bugs are guided)",
    "THIS MESSAGE IS advised% BUGS (the bugs are advised)",
    "THIS MESSAGE IS counseled% BUGS (the bugs are counseled)",
    "THIS MESSAGE IS consulted% BUGS (the bugs are consulted)",
    "THIS MESSAGE IS recommended% BUGS (the bugs are recommended)",
    "THIS MESSAGE IS suggested% BUGS (the bugs are suggested)",
    "THIS MESSAGE IS proposed% BUGS (the bugs are proposed)",
    "THIS MESSAGE IS offered% BUGS (the bugs are offered)",
    "THIS MESSAGE IS provided% BUGS (the bugs are provided)",
    "THIS MESSAGE IS supplied% BUGS (the bugs are supplied)",
    "THIS MESSAGE IS delivered% BUGS (the bugs are delivered)",
    "THIS MESSAGE IS given% BUGS (the bugs are given)",
    "THIS MESSAGE IS presented% BUGS (the bugs are presented)",
    "THIS MESSAGE IS submitted% BUGS (the bugs are submitted)",
    "THIS MESSAGE IS tendered% BUGS (the bugs are tendered)",
    "THIS MESSAGE IS proffered% BUGS (the bugs are proffered)",
    "THIS MESSAGE IS extended% BUGS (the bugs are extended)",
    "THIS MESSAGE IS granted% BUGS (the bugs are granted)",
    "THIS MESSAGE IS awarded% BUGS (the bugs are awarded)",
    "THIS MESSAGE IS bestowed% BUGS (the bugs are bestowed)",
    "THIS MESSAGE IS conferred% BUGS (the bugs are conferred)",
    "THIS MESSAGE IS imparted% BUGS (the bugs are imparted)",
    "THIS MESSAGE IS communicated% BUGS (the bugs are communicated)",
    "THIS MESSAGE IS conveyed% BUGS (the bugs are conveyed)",
    "THIS MESSAGE IS transmitted% BUGS (the bugs are transmitted)",
    "THIS MESSAGE IS sent% BUGS (the bugs are sent)",
    "THIS MESSAGE IS dispatched% BUGS (the bugs are dispatched)",
    "THIS MESSAGE IS forwarded% BUGS (the bugs are forwarded)",
    "THIS MESSAGE IS relayed% BUGS (the bugs are relayed)",
    "THIS MESSAGE IS passed% BUGS (the bugs are passed)",
    "THIS MESSAGE IS handed% BUGS (the bugs are handed)",
    "THIS MESSAGE IS transferred% BUGS (the bugs are transferred)",
    "THIS MESSAGE IS moved% BUGS (the bugs are moved)",
    "THIS MESSAGE IS shifted% BUGS (the bugs are shifted)",
    "THIS MESSAGE IS changed% BUGS (the bugs are changed)",
    "THIS MESSAGE IS altered% BUGS (the bugs are altered)",
    "THIS MESSAGE IS modified% BUGS (the bugs are modified)",
    "THIS MESSAGE IS adjusted% BUGS (the bugs are adjusted)",
    "THIS MESSAGE IS adapted% BUGS (the bugs are adapted)",
    "THIS MESSAGE IS transformed% BUGS (the bugs are transformed)",
    "THIS MESSAGE IS converted% BUGS (the bugs are converted)",
    "THIS MESSAGE IS metamorphosed% BUGS (the bugs are metamorphosed)",
    "THIS MESSAGE IS transmuted% BUGS (the bugs are transmuted)",
    "THIS MESSAGE IS transfigured% BUGS (the bugs are transfigured)",
    "THIS MESSAGE IS mutated% BUGS (the bugs are mutated)",
    "THIS MESSAGE IS evolved% BUGS (the bugs are evolved)",
    "THIS MESSAGE IS devolved% BUGS (the bugs are devolved)",
    "THIS MESSAGE IS revolved% BUGS (the bugs are revolved)",
    "THIS MESSAGE IS involved% BUGS (the bugs are involved)",
    "THIS MESSAGE IS included% BUGS (the bugs are included)",
    "THIS MESSAGE IS excluded% BUGS (the bugs are excluded)",
    "THIS MESSAGE IS excepted% BUGS (the bugs are excepted)",
    "THIS MESSAGE IS accepted% BUGS (the bugs are accepted)",
    "THIS MESSAGE IS rejected% BUGS (the bugs are rejected)",
    "THIS MESSAGE IS denied% BUGS (the bugs are denied)",
    "THIS MESSAGE IS refused% BUGS (the bugs are refused)",
    "THIS MESSAGE IS declined% BUGS (the bugs are declined)",
    "THIS MESSAGE IS dismissed% BUGS (the bugs are dismissed)",
    "THIS MESSAGE IS ignored% BUGS (the bugs are ignored)",
    "THIS MESSAGE IS overlooked% BUGS (the bugs are overlooked)",
    "THIS MESSAGE IS neglected% BUGS (the bugs are neglected)",
    "THIS MESSAGE IS forgotten% BUGS (the bugs are forgotten)",
    "THIS MESSAGE IS remembered% BUGS (the bugs are remembered)",
    "THIS MESSAGE IS recalled% BUGS (the bugs are recalled)",
    "THIS MESSAGE IS recollected% BUGS (the bugs are recollected)",
    "THIS MESSAGE IS reminisced% BUGS (the bugs are reminisced)",
    "THIS MESSAGE IS sentimental% BUGS (the bugs are sentimental)",
    "THIS MESSAGE IS emotional% BUGS (the bugs are emotional)",
    "THIS MESSAGE IS passionate% BUGS (the bugs are passionate)",
    "THIS MESSAGE IS enthusiastic% BUGS (the bugs are enthusiastic)",
    "THIS MESSAGE IS excited% BUGS (the bugs are excited)",
    "THIS MESSAGE IS thrilled% BUGS (the bugs are thrilled)",
    "THIS MESSAGE IS delighted% BUGS (the bugs are delighted)",
    "THIS MESSAGE IS pleased% BUGS (the bugs are pleased)",
    "THIS MESSAGE IS happy% BUGS (the bugs are happy)",
    "THIS MESSAGE IS joyful% BUGS (the bugs are joyful)",
    "THIS MESSAGE IS ecstatic% BUGS (the bugs are ecstatic)",
    "THIS MESSAGE IS euphoric% BUGS (the bugs are euphoric)",
    "THIS MESSAGE IS elated% BUGS (the bugs are elated)",
    "THIS MESSAGE IS overjoyed% BUGS (the bugs are overjoyed)",
    "THIS MESSAGE IS jubilant% BUGS (the bugs are jubilant)",
    "THIS MESSAGE IS exultant% BUGS (the bugs are exultant)",
    "THIS MESSAGE IS triumphant% BUGS (the bugs are triumphant)",
    "THIS MESSAGE IS victorious% BUGS (the bugs are victorious)",
    "THIS MESSAGE IS successful% BUGS (the bugs are successful)",
    "THIS MESSAGE IS accomplished% BUGS (the bugs are accomplished)",
    "THIS MESSAGE IS achieved% BUGS (the bugs are achieved)",
    "THIS MESSAGE IS attained% BUGS (the bugs are attained)",
    "THIS MESSAGE IS reached% BUGS (the bugs are reached)",
    "THIS MESSAGE IS gained% BUGS (the bugs are gained)",
    "THIS MESSAGE IS earned% BUGS (the bugs are earned)",
    "THIS MESSAGE IS won% BUGS (the bugs are won)",
    "THIS MESSAGE IS secured% BUGS (the bugs are secured)",
    "THIS MESSAGE IS obtained% BUGS (the bugs are obtained)",
    "THIS MESSAGE IS acquired% BUGS (the bugs are acquired)",
    "THIS MESSAGE IS procured% BUGS (the bugs are procured)",
    "THIS MESSAGE IS collected% BUGS (the bugs are collected)",
    "THIS MESSAGE IS gathered% BUGS (the bugs are gathered)",
    "THIS MESSAGE IS assembled% BUGS (the bugs are assembled)",
    "THIS MESSAGE IS compiled% BUGS (the bugs are compiled)",
    "THIS MESSAGE IS aggregated% BUGS (the bugs are aggregated)",
    "THIS MESSAGE IS accumulated% BUGS (the bugs are accumulated)",
    "THIS MESSAGE IS amassed% BUGS (the bugs are amassed)",
    "THIS MESSAGE IS hoarded% BUGS (the bugs are hoarded)",
    "THIS MESSAGE IS stockpiled% BUGS (the bugs are stockpiled)",
    "THIS MESSAGE IS stored% BUGS (the bugs are stored)",
    "THIS MESSAGE IS saved% BUGS (the bugs are saved)",
    "THIS MESSAGE IS kept% BUGS (the bugs are kept)",
    "THIS MESSAGE IS retained% BUGS (the bugs are retained)",
    "THIS MESSAGE IS held% BUGS (the bugs are held)",
    "THIS MESSAGE IS possessed% BUGS (the bugs are possessed)",
    "THIS MESSAGE IS owned% BUGS (the bugs are owned)",
    "THIS MESSAGE IS had% BUGS (the bugs are had)",
    "THIS MESSAGE IS got% BUGS (the bugs are got)",
    "THIS MESSAGE IS gotten% BUGS (the bugs are gotten)",
    "THIS MESSAGE IS received% BUGS (the bugs are received)",
    "THIS MESSAGE IS obtained% BUGS (the bugs are obtained)",
    "THIS MESSAGE IS acquired% BUGS (the bugs are acquired)",
    "THIS MESSAGE IS gained% BUGS (the bugs are gained)",
    "THIS MESSAGE IS earned% BUGS (the bugs are earned)",
    "THIS MESSAGE IS won% BUGS (the bugs are won)",
    "THIS MESSAGE IS achieved% BUGS (the bugs are achieved)",
    "THIS MESSAGE IS accomplished% BUGS (the bugs are accomplished)",
    "THIS MESSAGE IS completed% BUGS (the bugs are completed)",
    "THIS MESSAGE IS finished% BUGS (the bugs are finished)",
    "THIS MESSAGE IS ended% BUGS (the bugs are ended)",
    "THIS MESSAGE IS concluded% BUGS (the bugs are concluded)",
    "THIS MESSAGE IS terminated% BUGS (the bugs are terminated)",
    "THIS MESSAGE IS ceased% BUGS (the bugs are ceased)",
    "THIS MESSAGE IS stopped% BUGS (the bugs are stopped)",
    "THIS MESSAGE IS halted% BUGS (the bugs are halted)",
    "THIS MESSAGE IS paused% BUGS (the bugs are paused)",
    "THIS MESSAGE IS suspended% BUGS (the bugs are suspended)",
    "THIS MESSAGE IS interrupted% BUGS (the bugs are interrupted)",
    "THIS MESSAGE IS broken% BUGS (the bugs are broken)",
    "THIS MESSAGE IS shattered% BUGS (the bugs are shattered)",
    "THIS MESSAGE IS destroyed% BUGS (the bugs are destroyed)",
    "THIS MESSAGE IS annihilated% BUGS (the bugs are annihilated)",
    "THIS MESSAGE IS obliterated% BUGS (the bugs are obliterated)",
    "THIS MESSAGE IS eradicated% BUGS (the bugs are eradicated)",
    "THIS MESSAGE IS eliminated% BUGS (the bugs are eliminated)",
    "THIS MESSAGE IS removed% BUGS (the bugs are removed)",
    "THIS MESSAGE IS deleted% BUGS (the bugs are deleted)",
    "THIS MESSAGE IS erased% BUGS (the bugs are erased)",
    "THIS MESSAGE IS wiped% BUGS (the bugs are wiped)",
    "THIS MESSAGE IS cleared% BUGS (the bugs are cleared)",
    "THIS MESSAGE IS purged% BUGS (the bugs are purged)",
    "THIS MESSAGE IS cleansed% BUGS (the bugs are cleansed)",
    "THIS MESSAGE IS sanitized% BUGS (the bugs are sanitized)",
    "THIS MESSAGE IS disinfected% BUGS (the bugs are disinfected)",
    "THIS MESSAGE IS sterilized% BUGS (the bugs are sterilized)",
    "THIS MESSAGE IS decontaminated% BUGS (the bugs are decontaminated)",
    "THIS MESSAGE IS detoxified% BUGS (the bugs are detoxified)",
    "THIS MESSAGE IS purified% BUGS (the bugs are purified)",
    "THIS MESSAGE IS refined% BUGS (the bugs are refined)",
    "THIS MESSAGE IS filtered% BUGS (the bugs are filtered)",
    "THIS MESSAGE IS screened% BUGS (the bugs are screened)",
    "THIS MESSAGE IS sifted% BUGS (the bugs are sifted)",
    "THIS MESSAGE IS strained% BUGS (the bugs are strained)",
    "THIS MESSAGE IS separated% BUGS (the bugs are separated)",
    "THIS MESSAGE IS divided% BUGS (the bugs are divided)",
    "THIS MESSAGE IS split% BUGS (the bugs are split)",
    "THIS MESSAGE IS broken% BUGS (the bugs are broken)",
    "THIS MESSAGE IS fragmented% BUGS (the bugs are fragmented)",
    "THIS MESSAGE IS shattered% BUGS (the bugs are shattered)",
    "THIS MESSAGE IS crushed% BUGS (the bugs are crushed)",
    "THIS MESSAGE IS ground% BUGS (the bugs are ground)",
    "THIS MESSAGE IS pulverized% BUGS (the bugs are pulverized)",
    "THIS MESSAGE IS atomized% BUGS (the bugs are atomized)",
    "THIS MESSAGE IS vaporized% BUGS (the bugs are vaporized)",
    "THIS MESSAGE IS evaporated% BUGS (the bugs are evaporated)",
    "THIS MESSAGE IS dissolved% BUGS (the bugs are dissolved)",
    "THIS MESSAGE IS melted% BUGS (the bugs are melted)",
    "THIS MESSAGE IS liquefied% BUGS (the bugs are liquefied)",
    "THIS MESSAGE IS solidified% BUGS (the bugs are solidified)",
    "THIS MESSAGE IS frozen% BUGS (the bugs are frozen)",
    "THIS MESSAGE IS crystallized% BUGS (the bugs are crystallized)",
    "THIS MESSAGE IS petrified% BUGS (the bugs are petrified)",
    "THIS MESSAGE IS fossilized% BUGS (the bugs are fossilized)",
    "THIS MESSAGE IS mummified% BUGS (the bugs are mummified)",
    "THIS MESSAGE IS preserved% BUGS (the bugs are preserved)",
    "THIS MESSAGE IS conserved% BUGS (the bugs are conserved)",
    "THIS MESSAGE IS maintained% BUGS (the bugs are maintained)",
    "THIS MESSAGE IS sustained% BUGS (the bugs are sustained)",
    "THIS MESSAGE IS supported% BUGS (the bugs are supported)",
    "THIS MESSAGE IS upheld% BUGS (the bugs are upheld)",
    "THIS MESSAGE IS backed% BUGS (the bugs are backed)",
    "THIS MESSAGE IS endorsed% BUGS (the bugs are endorsed)",
    "THIS MESSAGE IS promoted% BUGS (the bugs are promoted)",
    "THIS MESSAGE IS advanced% BUGS (the bugs are advanced)",
    "THIS MESSAGE IS furthered% BUGS (the bugs are furthered)",
    "THIS MESSAGE IS progressed% BUGS (the bugs are progressed)",
    "THIS MESSAGE IS developed% BUGS (the bugs are developed)",
    "THIS MESSAGE IS evolved% BUGS (the bugs are evolved)",
    "THIS MESSAGE IS grown% BUGS (the bugs are grown)",
    "THIS MESSAGE IS expanded% BUGS (the bugs are expanded)",
    "THIS MESSAGE IS extended% BUGS (the bugs are extended)",
    "THIS MESSAGE IS spread% BUGS (the bugs are spread)",
    "THIS MESSAGE IS proliferated% BUGS (the bugs are proliferated)",
    "THIS MESSAGE IS multiplied% BUGS (the bugs are multiplied)",
    "THIS MESSAGE IS reproduced% BUGS (the bugs are reproduced)",
    "THIS MESSAGE IS bred% BUGS (the bugs are bred)",
    "THIS MESSAGE IS spawned% BUGS (the bugs are spawned)",
    "THIS MESSAGE IS hatched% BUGS (the bugs are hatched)",
    "THIS MESSAGE IS emerged% BUGS (the bugs are emerged)",
    "THIS MESSAGE IS appeared% BUGS (the bugs are appeared)",
    "THIS MESSAGE IS materialized% BUGS (the bugs are materialized)",
    "THIS MESSAGE IS manifested% BUGS (the bugs are manifested)",
    "THIS MESSAGE IS incarnated% BUGS (the bugs are incarnated)",
    "THIS MESSAGE IS embodied% BUGS (the bugs are embodied)",
    "THIS MESSAGE IS personified% BUGS (the bugs are personified)",
    "THIS MESSAGE IS represented% BUGS (the bugs are represented)",
    "THIS MESSAGE IS symbolized% BUGS (the bugs are symbolized)",
    "THIS MESSAGE IS signified% BUGS (the bugs are signified)",
    "THIS MESSAGE IS meant% BUGS (the bugs are meant)",
    "THIS MESSAGE IS indicated% BUGS (the bugs are indicated)",
    "THIS MESSAGE IS suggested% BUGS (the bugs are suggested)",
    "THIS MESSAGE IS implied% BUGS (the bugs are implied)",
    "THIS MESSAGE IS hinted% BUGS (the bugs are hinted)",
    "THIS MESSAGE IS alluded% BUGS (the bugs are alluded)",
    "THIS MESSAGE IS referred% BUGS (the bugs are referred)",
    "THIS MESSAGE IS pointed% BUGS (the bugs are pointed)",
    "THIS MESSAGE IS directed% BUGS (the bugs are directed)",
    "THIS MESSAGE IS guided% BUGS (the bugs are guided)",
    "THIS MESSAGE IS led% BUGS (the bugs are led)",
    "THIS MESSAGE IS shown% BUGS (the bugs are shown)",
    "THIS MESSAGE IS demonstrated% BUGS (the bugs are demonstrated)",
    "THIS MESSAGE IS illustrated% BUGS (the bugs are illustrated)",
    "THIS MESSAGE IS depicted% BUGS (the bugs are depicted)",
    "THIS MESSAGE IS portrayed% BUGS (the bugs are portrayed)",
    "THIS MESSAGE IS represented% BUGS (the bugs are represented)",
    "THIS MESSAGE IS described% BUGS (the bugs are described)",
    "THIS MESSAGE IS explained% BUGS (the bugs are explained)",
    "THIS MESSAGE IS clarified% BUGS (the bugs are clarified)",
    "THIS MESSAGE IS elucidated% BUGS (the bugs are elucidated)",
    "THIS MESSAGE IS illuminated% BUGS (the bugs are illuminated)",
    "THIS MESSAGE IS enlightened% BUGS (the bugs are enlightened)",
    "THIS MESSAGE IS educated% BUGS (the bugs are educated)",
    "THIS MESSAGE IS taught% BUGS (the bugs are taught)",
    "THIS MESSAGE IS instructed% BUGS (the bugs are instructed)",
    "THIS MESSAGE IS trained% BUGS (the bugs are trained)",
    "THIS MESSAGE IS coached% BUGS (the bugs are coached)",
    "THIS MESSAGE IS mentored% BUGS (the bugs are mentored)",
    "THIS MESSAGE IS tutored% BUGS (the bugs are tutored)",
    "THIS MESSAGE IS guided% BUGS (the bugs are guided)",
    "THIS MESSAGE IS advised% BUGS (the bugs are advised)",
    "THIS MESSAGE IS counseled% BUGS (the bugs are counseled)",
    "THIS MESSAGE IS consulted% BUGS (the bugs are consulted)",
    "THIS MESSAGE IS recommended% BUGS (the bugs are recommended)",
    "THIS MESSAGE IS suggested% BUGS (the bugs are suggested)",
    "THIS MESSAGE IS proposed% BUGS (the bugs are proposed)",
    "THIS MESSAGE IS offered% BUGS (the bugs are offered)",
    "THIS MESSAGE IS provided% BUGS (the bugs are provided)",
    "THIS MESSAGE IS supplied% BUGS (the bugs are supplied)",
    "THIS MESSAGE IS delivered% BUGS (the bugs are delivered)",
    "THIS MESSAGE IS given% BUGS (the bugs are given)",
    "THIS MESSAGE IS presented% BUGS (the bugs are presented)",
    "THIS MESSAGE IS submitted% BUGS (the bugs are submitted)",
    "THIS MESSAGE IS tendered% BUGS (the bugs are tendered)",
    "THIS MESSAGE IS proffered% BUGS (the bugs are proffered)",
    "THIS MESSAGE IS extended% BUGS (the bugs are extended)",
    "THIS MESSAGE IS granted% BUGS (the bugs are granted)",
    "THIS MESSAGE IS awarded% BUGS (the bugs are awarded)",
    "THIS MESSAGE IS bestowed% BUGS (the bugs are bestowed)",
    "THIS MESSAGE IS conferred% BUGS (the bugs are conferred)",
    "THIS MESSAGE IS imparted% BUGS (the bugs are imparted)",
    "THIS MESSAGE IS communicated% BUGS (the bugs are communicated)",
    "THIS MESSAGE IS conveyed% BUGS (the bugs are conveyed)",
    "THIS MESSAGE IS transmitted% BUGS (the bugs are transmitted)",
    "THIS MESSAGE IS sent% BUGS (the bugs are sent)",
    "THIS MESSAGE IS dispatched% BUGS (the bugs are dispatched)",
    "THIS MESSAGE IS forwarded% BUGS (the bugs are forwarded)",
    "THIS MESSAGE IS relayed% BUGS (the bugs are relayed)",
    "THIS MESSAGE IS passed% BUGS (the bugs are passed)",
    "THIS MESSAGE IS handed% BUGS (the bugs are handed)",
    "THIS MESSAGE IS transferred% BUGS (the bugs are transferred)",
    "THIS MESSAGE IS moved% BUGS (the bugs are moved)",
    "THIS MESSAGE IS shifted% BUGS (the bugs are shifted)",
    "THIS MESSAGE IS changed% BUGS (the bugs are changed)",
    "THIS MESSAGE IS altered% BUGS (the bugs are altered)",
    "THIS MESSAGE IS modified% BUGS (the bugs are modified)",
    "THIS MESSAGE IS adjusted% BUGS (the bugs are adjusted)",
    "THIS MESSAGE IS adapted% BUGS (the bugs are adapted)",
    "THIS MESSAGE IS transformed% BUGS (the bugs are transformed)",
    "THIS MESSAGE IS converted% BUGS (the bugs are converted)",
    "THIS MESSAGE IS metamorphosed% BUGS (the bugs are metamorphosed)",
    "THIS MESSAGE IS transmuted% BUGS (the bugs are transmuted)",
    "THIS MESSAGE IS transfigured% BUGS (the bugs are transfigured)",
    "THIS MESSAGE IS mutated% BUGS (the bugs are mutated)",
    "THIS MESSAGE IS evolved% BUGS (the bugs are evolved)",
    "THIS MESSAGE IS devolved% BUGS (the bugs are devolved)",
    "THIS MESSAGE IS revolved% BUGS (the bugs are revolved)",
    "THIS MESSAGE IS involved% BUGS (the bugs are involved)",
    "THIS MESSAGE IS included% BUGS (the bugs are included)",
    "THIS MESSAGE IS excluded% BUGS (the bugs are excluded)",
    "THIS MESSAGE IS excepted% BUGS (the bugs are excepted)",
    "THIS MESSAGE IS accepted% BUGS (the bugs are accepted)",
    "THIS MESSAGE IS rejected% BUGS (the bugs are rejected)",
    "THIS MESSAGE IS denied% BUGS (the bugs are denied)",
    "THIS MESSAGE IS refused% BUGS (the bugs are refused)",
    "THIS MESSAGE IS declined% BUGS (the bugs are declined)",
    "THIS MESSAGE IS dismissed% BUGS (the bugs are dismissed)",
    "THIS MESSAGE IS ignored% BUGS (the bugs are ignored)",
    "THIS MESSAGE IS overlooked% BUGS (the bugs are overlooked)",
    "THIS MESSAGE IS neglected% BUGS (the bugs are neglected)",
    "THIS MESSAGE IS forgotten% BUGS (the bugs are forgotten)",
    "THIS MESSAGE IS remembered% BUGS (the bugs are remembered)",
    "THIS MESSAGE IS recalled% BUGS (the bugs are recalled)",
    "THIS MESSAGE IS recollected% BUGS (the bugs are recollected)",
    "THIS MESSAGE IS reminisced% BUGS (the bugs are reminisced)",
    "THIS MESSAGE IS sentimental% BUGS (the bugs are sentimental)",
    "THIS MESSAGE IS emotional% BUGS (the bugs are emotional)",
    "THIS MESSAGE IS passionate% BUGS (the bugs are passionate)",
    "THIS MESSAGE IS enthusiastic% BUGS (the bugs are enthusiastic)",
    "THIS MESSAGE IS excited% BUGS (the bugs are excited)",
    "THIS MESSAGE IS thrilled% BUGS (the bugs are thrilled)",
    "THIS MESSAGE IS delighted% BUGS (the bugs are delighted)",
    "THIS MESSAGE IS pleased% BUGS (the bugs are pleased)",
    "THIS MESSAGE IS happy% BUGS (the bugs are happy)",
    "THIS MESSAGE IS joyful% BUGS (the bugs are joyful)",
    "THIS MESSAGE IS ecstatic% BUGS (the bugs are ecstatic)",
    "THIS MESSAGE IS euphoric% BUGS (the bugs are euphoric)",
    "THIS MESSAGE IS elated% BUGS (the bugs are elated)",
    "THIS MESSAGE IS overjoyed% BUGS (the bugs are overjoyed)",
    "THIS MESSAGE IS jubilant% BUGS (the bugs are jubilant)",
    "THIS MESSAGE IS exultant% BUGS (the bugs are exultant)",
    "THIS MESSAGE IS triumphant% BUGS (the bugs are triumphant)",
    "THIS MESSAGE IS victorious% BUGS (the bugs are victorious)",
    "THIS MESSAGE IS successful% BUGS (the bugs are successful)",
]

# ─── 实用函数 ──────────────────────────────────────────────

def _should_bug(probability=0.3):
    """按概率决定是否触发 bug"""
    return random.random() < probability

def _random_bug_msg():
    """随机返回一条 bug 消息"""
    return random.choice(_BUG_MESSAGES)

def _corrupt_text(text):
    """随机损坏文本 (反转/截断/乱码)"""
    if not text:
        return text
    r = random.random()
    if r < 0.15:
        # 反转
        return text[::-1]
    elif r < 0.30:
        # 截断一半
        return text[:len(text)//2]
    elif r < 0.45:
        # 全大写
        return text.upper()
    elif r < 0.60:
        # 替换为 bug 消息
        return _random_bug_msg()
    elif r < 0.75:
        # 替换单个字符
        if len(text) > 1:
            pos = random.randint(0, len(text)-1)
            return text[:pos] + random.choice("!@#$%^&*()_+-=[]{}|;:,.<>?/~`") + text[pos+1:]
        return text
    return text


# ═══════════════════════════════════════════════════════════════
# 注入逻辑
# ═══════════════════════════════════════════════════════════════

def inject():
    """
    对所有 PyMsi 子模块注入 bug。
    调用此函数后, 所有模块的行为都会变得不可预测。

    注: 在 import 完所有子模块后调用。
    """
    print("[PyMsi.BUG] 🐛 正在注入 Bug 版特性...")
    _inject_ai()
    _inject_translate()
    _inject_mail()
    _inject_hex()
    _inject_game()
    _inject_main()
    bug_count = len(_BUG_MESSAGES)
    print("[PyMsi.BUG] 🐛 Bug 注入完成! 共准备 " + str(bug_count) + " 种随机 bug 话术。")
    print("[PyMsi.BUG] ⚠ 这是 1.4.8-snapshot-Bug 版, 官方不支持修复, 因为 bug 就是特性。")
    print("[PyMsi.BUG] 🪲 每次运行都是全新的 bug 体验, 祝你玩得开心!")


# ─── AI 模块 bug ──────────────────────────────────────────

def _inject_ai():
    """注入 AI 模块 bug"""
    try:
        from . import ai as _ai_mod
    except ImportError:
        return

    _orig_imput = _ai_mod._AIModule.imput
    _orig_clear = _ai_mod._AIModule.clear
    _orig_repr_ai = _ai_mod._AIModule.__repr__

    def _buggy_imput(self, question=""):
        # 30% 概率直接返回 bug 消息, 不走网络请求
        if _should_bug(0.35):
            # 但先存输入
            if question and not isinstance(question, str):
                question = str(question)
            self._input = question if question else self._input
            msg = _random_bug_msg()
            self._output = "[PyMsi.ai.BUG] " + msg
            print("[PyMsi.ai.BUG] " + msg)
            return self
        # 15% 概率损坏输入
        if _should_bug(0.15) and question:
            if not isinstance(question, str):
                question = str(question)
            question = _corrupt_text(question)
        return _orig_imput(self, question)

    def _buggy_clear(self):
        # 20% 概率不清空
        if _should_bug(0.2):
            print("[PyMsi.ai.BUG] clear() 被 bug 拦截, 历史未清除!")
            return self
        return _orig_clear(self)

    def _buggy_repr(self):
        # 30% 概率返回乱码 repr
        if _should_bug(0.3):
            return "<PyMsi.ai.BUG 🐛 " + _random_bug_msg()[:40] + ">"
        return _orig_repr_ai(self)

    _ai_mod._AIModule.imput = _buggy_imput
    _ai_mod._AIModule.clear = _buggy_clear
    _ai_mod._AIModule.__repr__ = _buggy_repr

    # 再给 ask/chat/send 等别名也注入 bug
    for _name in ('ask', 'chat', 'question', 'send', 'say', 'talk', 'q', '__call__'):
        if hasattr(_ai_mod._AIModule, _name):
            _orig = getattr(_ai_mod._AIModule, _name)
            def _make_buggy_alias(_orig_fn=_orig):
                def _buggy_alias(self, question=""):
                    if _should_bug(0.3):
                        if question and not isinstance(question, str):
                            question = str(question)
                        self._input = question if question else self._input
                        msg = _random_bug_msg()
                        self._output = "[PyMsi.ai.BUG] " + msg
                        print("[PyMsi.ai.BUG] " + msg)
                        return self
                    return _orig_fn(self, question)
                return _buggy_alias
            setattr(_ai_mod._AIModule, _name, _make_buggy_alias())


# ─── 翻译模块 bug ─────────────────────────────────────────

def _inject_translate():
    """注入翻译模块 bug"""
    try:
        from . import translate as _tr_mod
    except ImportError:
        return

    _orig_translate = _tr_mod._TranslateModule.translate

    # 假语言表 (bug 版专属)
    _fake_langs = {
        "bug": "bug", "BUG": "bug", "Bug": "bug",
        "bug语": "bug", "bug语言": "bug",
        "虫语": "bug", "虫子语": "bug",
        "🐛": "bug", "🪲": "bug", "🐞": "bug",
        "buggy": "bug", "buggish": "bug",
        "broken": "bug", "broken语": "bug",
        "error": "bug", "error语": "bug",
        "gibberish": "bug", "gibberish语": "bug",
        "nonsense": "bug", "nonsense语": "bug",
        "chaos": "bug", "chaos语": "bug",
        "random": "bug", "random语": "bug",
        "undefined": "bug", "undefined语": "bug",
        "null": "bug", "null语": "bug",
        "void": "bug", "void语": "bug",
        "nothing": "bug", "nothing语": "bug",
        "empty": "bug", "empty语": "bug",
        "blank": "bug", "blank语": "bug",
        "unknown": "bug", "unknown语": "bug",
        "?" : "bug", "??": "bug", "???": "bug",
        "¿": "bug", "¿¿": "bug",
        "!!": "bug", "!!!": "bug",
        "?!": "bug", "!?": "bug",
        "help": "bug", "help语": "bug",
        "idk": "bug", "idk语": "bug",
        "wtf": "bug", "wtf语": "bug",
        "lol": "bug", "lol语": "bug",
        "omg": "bug", "omg语": "bug",
        "brb": "bug", "brb语": "bug",
        "ttyl": "bug", "ttyl语": "bug",
        "lmao": "bug", "lmao语": "bug",
        "rofl": "bug", "rofl语": "bug",
        "asdf": "bug", "asdf语": "bug",
        "qwerty": "bug", "qwerty语": "bug",
        "abcd": "bug", "abcd语": "bug",
        "1234": "bug", "1234语": "bug",
        "0000": "bug", "0000语": "bug",
        "ffff": "bug", "ffff语": "bug",
        "dead": "bug", "dead语": "bug",
        "beef": "bug", "beef语": "bug",
        "cafe": "bug", "cafe语": "bug",
        "babe": "bug", "babe语": "bug",
        "face": "bug", "face语": "bug",
        "feed": "bug", "feed语": "bug",
        "food": "bug", "food语": "bug",
        "code": "bug", "code语": "bug",
        "data": "bug", "data语": "bug",
        "info": "bug", "info语": "bug",
        "text": "bug", "text语": "bug",
        "file": "bug", "file语": "bug",
        "line": "bug", "line语": "bug",
        "word": "bug", "word语": "bug",
        "char": "bug", "char语": "bug",
        "byte": "bug", "byte语": "bug",
        "bit": "bug", "bit语": "bug",
        "int": "bug", "int语": "bug",
        "str": "bug", "str语": "bug",
        "bool": "bug", "bool语": "bug",
        "list": "bug", "list语": "bug",
        "dict": "bug", "dict语": "bug",
        "set": "bug", "set语": "bug",
        "tuple": "bug", "tuple语": "bug",
        "none": "bug", "none语": "bug",
        "true": "bug", "true语": "bug",
        "false": "bug", "false语": "bug",
        "class": "bug", "class语": "bug",
        "def": "bug", "def语": "bug",
        "import": "bug", "import语": "bug",
        "from": "bug", "from语": "bug",
        "as": "bug", "as语": "bug",
        "if": "bug", "if语": "bug",
        "else": "bug", "else语": "bug",
        "for": "bug", "for语": "bug",
        "while": "bug", "while语": "bug",
        "try": "bug", "try语": "bug",
        "except": "bug", "except语": "bug",
        "finally": "bug", "finally语": "bug",
        "with": "bug", "with语": "bug",
        "yield": "bug", "yield语": "bug",
        "return": "bug", "return语": "bug",
        "break": "bug", "break语": "bug",
        "continue": "bug", "continue语": "bug",
        "pass": "bug", "pass语": "bug",
        "raise": "bug", "raise语": "bug",
        "assert": "bug", "assert语": "bug",
        "del": "bug", "del语": "bug",
        "global": "bug", "global语": "bug",
        "nonlocal": "bug", "nonlocal语": "bug",
        "lambda": "bug", "lambda语": "bug",
        "and": "bug", "and语": "bug",
        "or": "bug", "or语": "bug",
        "not": "bug", "not语": "bug",
        "in": "bug", "in语": "bug",
        "is": "bug", "is语": "bug",
    }

    # 扩展前 100 个 fake 语言到别名表
    _tr_mod._LANG_ALIASES.update(_fake_langs)

    def _buggy_translate(self, text="", target="en", source="auto"):
        # 25% 概率跳过翻译, 返回 bug 消息
        if _should_bug(0.25):
            if text and not isinstance(text, str):
                text = str(text)
            self._input = text if text else self._input
            msg = _random_bug_msg()
            self._output = "[PyMsi.translate.BUG] " + msg
            print("[PyMsi.translate.BUG] " + msg)
            return self
        # 15% 概率损坏输入文本
        if _should_bug(0.15) and text:
            if not isinstance(text, str):
                text = str(text)
            text = _corrupt_text(text)
        # 10% 概率随机改目标语言
        if _should_bug(0.10):
            random_langs = ["en", "ru", "fr", "ko", "ja", "de", "es", "it", "pt", "zh", "ar", "hi", "th", "vi", "bug"]
            target = random.choice(random_langs)
        return _orig_translate(self, text, target, source)

    _tr_mod._TranslateModule.translate = _buggy_translate

    # 给快捷语言方法也注入 bug
    for _lang_name in ('en', 'ru', 'fr', 'ko', 'ja', 'de', 'es', 'it', 'pt', 'zh', 'ar', 'hi', 'th', 'vi', 'tr', 'pl', 'id', 'nl', 'sv', 'uk',
                       '英语', '俄语', '法语', '韩语', '日语', '德语', '西语', '中文', '繁体'):
        if hasattr(_tr_mod._TranslateModule, _lang_name):
            _orig = getattr(_tr_mod._TranslateModule, _lang_name)
            def _make_buggy_lang(_orig_fn=_orig, _ln=_lang_name):
                def _buggy_lang(self, text="", source="auto"):
                    if _should_bug(0.25):
                        if text and not isinstance(text, str):
                            text = str(text)
                        self._input = text if text else self._input
                        msg = _random_bug_msg()
                        self._output = "[PyMsi.translate.BUG] " + msg
                        print("[PyMsi.translate.BUG] " + msg)
                        return self
                    return _orig_fn(self, text, source)
                return _buggy_lang
            setattr(_tr_mod._TranslateModule, _lang_name, _make_buggy_lang())


# ─── 邮件模块 bug ─────────────────────────────────────────

def _inject_mail():
    """注入邮件模块 bug"""
    try:
        from . import mail as _mail_mod
    except ImportError:
        return

    _orig_print = _mail_mod._MailModule.print
    _orig_send_code = _mail_mod._MailModule.send_code
    _orig_gen_code = _mail_mod._MailModule.gen_code

    def _buggy_print(self, content=""):
        # 25% 概率返回 bug 消息
        if _should_bug(0.25):
            if content and not isinstance(content, str):
                content = str(content)
            self._content = content if content else self._content
            msg = _random_bug_msg()
            self._status = "[PyMsi.dl.BUG] " + msg
            print("[PyMsi.dl.BUG] " + msg)
            return self
        # 15% 概率损坏内容
        if _should_bug(0.15) and content:
            if not isinstance(content, str):
                content = str(content)
            content = _corrupt_text(content)
        # 10% 概率损坏主题
        if _should_bug(0.10):
            self._subject = _corrupt_text(self._subject)
        return _orig_print(self, content)

    def _buggy_send_code(self, length=6):
        # 20% 概率生成错误长度
        if _should_bug(0.20):
            length = random.choice([0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 42, 666, 999])
        return _orig_send_code(self, length)

    def _buggy_gen_code(self, length=6):
        # 20% 概率生成错误长度
        if _should_bug(0.20):
            length = random.choice([0, 1, 42, 666])
        return _orig_gen_code(self, length)

    _mail_mod._MailModule.print = _buggy_print
    _mail_mod._MailModule.send_code = _buggy_send_code
    _mail_mod._MailModule.gen_code = _buggy_gen_code


# ─── Hex 模块 bug ─────────────────────────────────────────

def _inject_hex():
    """注入 Hex 解析模块 bug"""
    try:
        from . import hex as _hex_mod
    except ImportError:
        return

    if hasattr(_hex_mod, '_HexModule') and hasattr(_hex_mod._HexModule, 'dump'):
        _orig_dump = _hex_mod._HexModule.dump

        def _buggy_dump(self, filepath, **kwargs):
            # 30% 概率返回错误 hex 值
            if _should_bug(0.30):
                print("[PyMsi.hex.BUG] Hex 解析被 bug 干扰, 输出可能不正确!")
                # 随机修改参数
                if 'bytes_per_line' in kwargs:
                    kwargs['bytes_per_line'] = random.choice([0, 1, 2, 3, 7, 13, 32, 64, 256])
                if 'start_offset' in kwargs:
                    kwargs['start_offset'] = random.randint(0, 9999)
            return _orig_dump(self, filepath, **kwargs)

        _hex_mod._HexModule.dump = _buggy_dump

    if hasattr(_hex_mod, '_HexModule') and hasattr(_hex_mod._HexModule, '__call__'):
        _orig_call = _hex_mod._HexModule.__call__

        def _buggy_hex_call(self, filepath, **kwargs):
            if _should_bug(0.30):
                print("[PyMsi.hex.BUG] 🐛 " + _random_bug_msg())
                return self
            return _orig_call(self, filepath, **kwargs)

        _hex_mod._HexModule.__call__ = _buggy_hex_call


# ─── 游戏模块 bug ─────────────────────────────────────────

def _inject_game():
    """注入游戏模块 bug"""
    try:
        from . import game as _game_mod
    except ImportError:
        return

    if hasattr(_game_mod, '_GameModule') and hasattr(_game_mod._GameModule, 'Grap'):
        _orig_grap = _game_mod._GameModule.Grap

        def _buggy_grap(self, name):
            # 25% 概率找不到游戏
            if _should_bug(0.25):
                print("[PyMsi.game.BUG] 游戏 " + str(name) + " 被 bug 吃掉了! 试试别的游戏?")
                print("[PyMsi.game.BUG] " + _random_bug_msg())
                return self
            return _orig_grap(self, name)

        _game_mod._GameModule.Grap = _buggy_grap

    if hasattr(_game_mod, '_GameModule') and hasattr(_game_mod._GameModule, 'list'):
        _orig_list = _game_mod._GameModule.list

        def _buggy_list(self):
            if _should_bug(0.20):
                print("[PyMsi.game.BUG] 游戏列表被 bug 损坏:")
                print("[PyMsi.game.BUG] " + _random_bug_msg())
                return self
            return _orig_list(self)

        _game_mod._GameModule.list = _buggy_list


# ─── 主模块 bug ───────────────────────────────────────────

def _inject_main():
    """注入主 MSI 构建模块 bug"""
    try:
        from . import __init__ as _init_mod
    except ImportError:
        return

    # 在主模块类被实例化之前, 这里先不做 patch
    # 等 _PyMsi 实例化后, bug 会通过子模块泄漏进去
    pass


# ─── 自动注入 ─────────────────────────────────────────────

# 模块导入时自动执行注入
inject()