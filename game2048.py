import platform
import random
import threading
import os
import sys
import time

PLATFORM_WINDOWS = 0x102030
PLATFORM_LINUX = 0x103050
PLATFORM_MAC = 0x105060
PLATFORM_OTHER = 0x106070

# 系统平台
os_platform = 0

# 重定向标准输出的文件对象
std_out = None

# 清屏
def cls():
    # 保存标准输出
    old_stdout = sys.stdout
    # 将标准输出指向log_out
    sys.stdout = std_out
    # 根据不同平台 执行不同清屏命令
    if os_platform == PLATFORM_WINDOWS:
        os.system('cls')
    else:
        os.system('clear')
    # 恢复默认的标准输出
    sys.stdout = old_stdout


def sleep(s):
    time.sleep(s)


# 检测模块是否安装 没安装的 用 清华，阿里，默认 三个仓库安装这个模块
def check_install_lib(lib_name):
    try:
        exec("import " + lib_name)
    except ImportError:
        print("模块 %s 未安装!" % lib_name)
        print("开始安装 %s 模块(使用清华镜像)" % lib_name)
        c = os.system("pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple %s" % lib_name)
        if c == 0:
            print("模块 %s 安装成功!(使用清华镜像)" % lib_name)
            return 1
        print("模块 %s 安s装失败!" % lib_name)
        print("开始安装 %s 模块(使用阿里镜像)" % lib_name)
        c = os.system("pip3 install -i http://mirrors.aliyun.com/pypi/simple/ %s" % lib_name)
        if c == 0:
            print("模块 %s 安装成功!(使用阿里镜像)" % lib_name)
            return 1
        print("模块 %s 安装失败!" % lib_name)
        print("开始安装 %s 模块(使用默认源)" % lib_name)
        c = os.system("pip3 install %s" % lib_name)
        if c == 0:
            print("模块 %s 安装成功!(使用默认源)" % lib_name)
            return 1
        print("模块 %s 安装失败！" % lib_name)
        return -1
    else:
        print("模块 %s 已安装" % lib_name)
        return 0


# 检测必要的模块是否被安装了 没安装的按装
def check_libs():
    install_code = check_install_lib("pynput")
    if install_code == -1:
        print("pynput模块安装失败！")
    elif install_code == 1:
        print("模块安装成功!")
    else:
        print("模块已安装")
    return install_code

# 游戏块数据对象
class Block:
    def __init__(self, y=0, x=0, num=0):
        self.y = y
        self.x = x
        self.num = num

# 游戏主类
class Game:
    # GAME_STATUS_WELCOME = 0x1001
    # GAME_STATUS_NEW_GAME = 0x1010
    # GAME_STATUS_RUNNING = 0x1020
    # GAME_STATUS_WIN = 0x1030
    # GAME_STATUS_FAIL = 0x1040
    # GAME_STATUS_EXIT = 0x1050
    # GAME_STATUS_WAIT = 0x1060
    GAME_STATUS_WELCOME = 'WELCOME'
    GAME_STATUS_START = 'START'
    GAME_STATUS_NEW_GAME = 'NEW GAME'
    GAME_STATUS_RUNNING = 'RUNNING'
    GAME_STATUS_WIN = 'WIN'
    GAME_STATUS_FAIL = 'FAIL'
    GAME_STATUS_EXIT = 'EXIT'
    GAME_STATUS_WAIT = 'WAIT'

    def __init__(self):
        # 游戏最高得分
        self.max_score = 0
        # 当前游戏得分
        self.score = 0
        # 游戏合并最大数
        self.max_number = 0
        # 游戏当前最大合并数
        self.number = 0
        # 游戏场次
        self.play_count = 0
        # 游戏数据
        self.data = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        for i in range(0, 4):
            for n in range(0, 4):
                self.data[i][n] = Block(i, n)

        # 最后一次按键时间
        self.last_key_event = int(time.time() * 1000)

        # 按键事件线程
        self.key_thread = threading.Thread(target=self.key_event, name="key event thread")
        self.key_thread.start()
        self.key_listener = None

        # 游戏状态设置为欢迎
        self.game_status = self.GAME_STATUS_WELCOME

    # 按键被触发
    def press(self, key):
        # 救救孩子吧  键盘按的那么快 孩子都忙不过来了
        if int(time.time() * 1000) - self.last_key_event < 400:
            return
        # 游戏状态处于等待状态时 不响应按键事件
        if self.game_status == self.GAME_STATUS_WAIT:
            return
        # 处理有效按键
        self.on_key_pressed(key)
        # 记录本次按键处理完的时间
        self.last_key_event = int(time.time() * 1000)

    # 当有效按键被按下
    def on_key_pressed(self, key):
        from pynput.keyboard import Key
        # 根据不同按键，处理游戏逻辑或改变游戏状态
        if str(key) == 'Key.left':
            self.left()
            self.check_win()
            self.check_fail()
        elif str(key) == 'Key.right':
            self.right()
            self.check_win()
            self.check_fail()
        elif str(key) == 'Key.up':
            self.up()
            self.check_win()
            self.check_fail()
        elif str(key) == 'Key.down':
            self.down()
            self.check_win()
            self.check_fail()
        elif str(key) == 'Key.esc':
            self.game_status = self.GAME_STATUS_EXIT
        elif str(key) == 'Key.enter':
            if self.game_status == self.GAME_STATUS_WELCOME:
                self.game_status = self.GAME_STATUS_START
        elif not isinstance(key, Key) and key.char == 'n':
            if self.game_status == self.GAME_STATUS_RUNNING or self.game_status == self.GAME_STATUS_FAIL or self.game_status == self.GAME_STATUS_WIN:
                self.game_status = self.GAME_STATUS_NEW_GAME

    # 检测游戏是否赢了  赢了的标准是 有数字等于2048
    def check_win(self):
        for i in range(0, 4):
            for n in range(0, 4):
                if self.data[i][n].num == 2048:
                    self.game_status = self.GAME_STATUS_WIN
                    return True
        return False

    # 从block_list里找第一个num大于0的对象
    # 根据传入的for循环的 开始 结束 步长 可从前向后，也可从后向前 查找对象
    def get_first_full_block(self, block_list, start=0, end=4, step=1):
        if start >= len(block_list):
            return None
        for i in range(start, end, step):
            if block_list[i].num > 0:
                return block_list[i]
        return None

    # 检测本场游戏是否结束
    def check_fail(self):
        if len(self.get_empty_list()) == 0 and not self.has_block_can_merge():
            # 添加失败 说明没有空格了 并且没有可以合并的块了，就说明游戏结束
            self.game_status = self.GAME_STATUS_FAIL

    # 检测是否还有可以合并的数字块
    def has_block_can_merge(self):
        for i in range(0, 3):
            for n in range(0, 3):
                # 本行这个和本行下一个
                if self.data[i][n].num == self.data[i][n+1].num:
                    return True
                # 本行当前这个和下一行这个
                if self.data[i][n].num == self.data[i+1][n].num:
                    return True
            # 本行最后一个和下一行最后一个
            if self.data[i][3].num == self.data[i+1][3].num:
                return True
        return False

    # 合法的按下了左键
    def left(self):
        if self.game_status != self.GAME_STATUS_RUNNING:
            return
        # 是否触发了合并或移动操作
        is_merge_or_moved = False
        for i in range(0, 4):
            # 一行只能合并一次, 用来判断本行是否合并过
            is_merge = False
            line = self.data[i]
            if line[0].num == 0:
                first_full_block = self.get_first_full_block(line, 1)
                if first_full_block:
                    line[0].num = first_full_block.num
                    first_full_block.num = 0
                    is_merge_or_moved = True
            for n in range(0, 3):
                prev_block = line[n]
                first_full_block = self.get_first_full_block(line, n + 1)
                if prev_block.num == 0:
                    if first_full_block:
                        prev_block.num = first_full_block.num
                        first_full_block.num = 0
                        is_merge_or_moved = True
                elif first_full_block:
                    if prev_block.num == first_full_block.num and not is_merge:
                        prev_block.num = prev_block.num * 2
                        self.set_score(self.score + prev_block.num)
                        first_full_block.num = 0
                        is_merge = True
                        is_merge_or_moved = True
                    elif n + 1 < first_full_block.x:
                        line[n + 1].num = first_full_block.num
                        first_full_block.num = 0
                        is_merge_or_moved = True
        if is_merge_or_moved:
            add_status = self.generate_block_number()
        self.render()

    # 合法的按下了右键
    def right(self):
        if self.game_status != self.GAME_STATUS_RUNNING:
            return
        # 是否触发了合并或移动操作
        is_merge_or_moved = False
        for i in range(0, 4):
            # 一行只能合并一次, 用来判断本行是否合并过
            is_merge = False
            line = self.data[i]
            if line[3].num == 0:
                first_full_block = self.get_first_full_block(line, 2, -1, -1)
                if first_full_block:
                    line[3].num = first_full_block.num
                    first_full_block.num = 0
                    is_merge_or_moved = True
            for n in range(3, -1, -1):
                prev_block = line[n]
                first_full_block = self.get_first_full_block(line, n - 1, -1, -1)
                if prev_block.num == 0:
                    if first_full_block:
                        prev_block.num = first_full_block.num
                        first_full_block.num = 0
                        is_merge_or_moved = True
                elif first_full_block:
                    if prev_block.num == first_full_block.num and not is_merge:
                        prev_block.num = prev_block.num * 2
                        self.set_score(self.score + prev_block.num)
                        first_full_block.num = 0
                        is_merge = True
                        is_merge_or_moved = True
                    elif n - 1 > first_full_block.x:
                        line[n - 1].num = first_full_block.num
                        first_full_block.num = 0
                        is_merge_or_moved = True
        if is_merge_or_moved:
            add_status = self.generate_block_number()
        self.render()

    # 合法的按下了上键
    def up(self):
        if self.game_status != self.GAME_STATUS_RUNNING:
            return
        # 是否触发了合并或移动操作
        is_merge_or_moved = False
        for i in range(0, 4):
            # 一行只能合并一次, 用来判断本行是否合并过
            is_merge = False
            line = [self.data[0][i], self.data[1][i], self.data[2][i], self.data[3][i]]
            if line[0].num == 0:
                first_full_block = self.get_first_full_block(line, 1)
                if first_full_block:
                    line[0].num = first_full_block.num
                    first_full_block.num = 0
                    is_merge_or_moved = True
            for n in range(0, 3):
                prev_block = line[n]
                first_full_block = self.get_first_full_block(line, n + 1)
                if prev_block.num == 0:
                    if first_full_block:
                        prev_block.num = first_full_block.num
                        first_full_block.num = 0
                        is_merge_or_moved = True
                elif first_full_block:
                    if prev_block.num == first_full_block.num and not is_merge:
                        prev_block.num = prev_block.num * 2
                        self.set_score(self.score + prev_block.num)
                        first_full_block.num = 0
                        is_merge = True
                        is_merge_or_moved = True
                    elif n + 1 < first_full_block.y:
                        line[n + 1].num = first_full_block.num
                        first_full_block.num = 0
                        is_merge_or_moved = True
        if is_merge_or_moved:
            add_status = self.generate_block_number()
        self.render()

    # 合法的按下了下键
    def down(self):
        if self.game_status != self.GAME_STATUS_RUNNING:
            return
        # 是否触发了合并或者移动操作
        is_merge_or_moved = False
        for i in range(0, 4):
            # 一行只能合并一次, 用来判断本行是否合并过
            is_merge = False
            line = [self.data[0][i], self.data[1][i], self.data[2][i], self.data[3][i]]
            if line[3].num == 0:
                first_full_block = self.get_first_full_block(line, 2, -1, -1)
                if first_full_block:
                    line[3].num = first_full_block.num
                    first_full_block.num = 0
                    is_merge_or_moved = True
            for n in range(3, -1, -1):
                prev_block = line[n]
                first_full_block = self.get_first_full_block(line, n - 1, -1, -1)
                if prev_block.num == 0:
                    if first_full_block:
                        prev_block.num = first_full_block.num
                        first_full_block.num = 0
                        is_merge_or_moved = True
                elif first_full_block:
                    if prev_block.num == first_full_block.num and not is_merge:
                        prev_block.num = prev_block.num * 2
                        self.set_score(self.score + prev_block.num)
                        first_full_block.num = 0
                        is_merge = True
                        is_merge_or_moved = True
                    elif n - 1 > first_full_block.y:
                        line[n - 1].num = first_full_block.num
                        first_full_block.num = 0
                        is_merge_or_moved = True
        if is_merge_or_moved:
            add_status = self.generate_block_number()
        self.render()

    # 设置当前游戏得分，并调整最大分数
    def set_score(self, num):
        self.score = num
        if self.score > self.max_score:
            self.max_score = self.score

    # 开启键盘记录
    def key_event(self):
        from pynput.keyboard import Listener
        self.key_listener = Listener(on_press=self.press)
        self.key_listener.start()

    # 开始状态循环
    def start(self):
        self.game_status = self.GAME_STATUS_WELCOME
        # 记录最后一次游戏状态
        last_status = None
        # 在游戏状态不是 EXIT 的情况下，根据游戏状态处理不同游戏状态下的逻辑
        while self.game_status != self.GAME_STATUS_EXIT:
            if self.game_status == last_status:
                sleep(1)
                continue
            if self.game_status == self.GAME_STATUS_WELCOME:
                last_status = self.GAME_STATUS_WELCOME
                # 初始欢迎界面
                self.welcome()
            if self.game_status == self.GAME_STATUS_START:
                last_status = self.GAME_STATUS_START
                # 开始游戏
                self.start_game()
            elif self.game_status == self.GAME_STATUS_NEW_GAME:
                last_status = self.GAME_STATUS_NEW_GAME
                self.new_game()
            elif self.game_status == self.GAME_STATUS_RUNNING:
                last_status = self.GAME_STATUS_RUNNING
            elif self.game_status == self.GAME_STATUS_WIN:
                last_status = self.GAME_STATUS_WIN
                self.win()
            elif self.game_status == self.GAME_STATUS_FAIL:
                last_status = self.GAME_STATUS_FAIL
                self.fail()
        # 游戏状态为 EXIT 执行 游戏退出逻辑
        self.game_exit()

    # 游戏状态 WELCOME 逻辑
    def welcome(self):
        msg = """
        欢迎来到 2048小游戏
    作者: 孤风残影
    时间: 2020/03/03

========================================
    按 回车 进入游戏
    按 ESC 退出游戏
"""
        self.print_msg_slowly(msg, True)

    # 第一次开始游戏
    def start_game(self):
        # 第一次场次为1
        self.play_count = 1
        # 第一次游戏 生成两个游戏块数字
        self.generate_block_number()
        self.generate_block_number()
        # 设置游戏状态为 RUNNING
        self.game_status = self.GAME_STATUS_RUNNING
        # 渲染游戏场景
        self.render()

    # 游戏状态 NEW_GAME 逻辑
    def new_game(self):
        # 游戏场次+1
        self.play_count += 1
        self.print_msg_slowly("\n......\n")
        self.print_msg_slowly("您选择了新游戏\n")
        sleep(1)
        self.print_msg_slowly("正在打扫战场...\n")
        sleep(1)
        self.print_msg_slowly("......\n")
        sleep(1)
        self.print_msg_slowly("战场打扫完毕...\n")
        sleep(1)
        self.print_msg_slowly("新游戏即将开始...\n")
        sleep(1)
        self.print_msg_slowly("3")
        sleep(1)
        print("\r", end='', flush=True)
        self.print_msg_slowly("2")
        sleep(1)
        print("\r", end='', flush=True)
        self.print_msg_slowly("1")
        sleep(1)
        print("\r", end='', flush=True)
        self.print_msg_slowly("0")
        sleep(1)
        # 当前游戏得分
        self.score = 0
        # 游戏当前最大合并数
        self.number = 0

        # 重置游戏数据
        self.data = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        for i in range(0, 4):
            for n in range(0, 4):
                self.data[i][n] = Block(i, n)

        # 生成2个游戏数据数字
        self.generate_block_number()
        self.generate_block_number()
        # 设置游戏状态为 RUNNING
        self.game_status = self.GAME_STATUS_RUNNING
        # 渲染
        self.render()

    # 游戏状态 WIN 逻辑
    def win(self):
        msg = """\n
    你赢了！ ^_^
    按 ESC 结束游戏， 按 N 开始新游戏
    """
        self.print_msg_slowly(msg)

    # 游戏状态 FAIL 逻辑
    def fail(self):
        print("\n")
        for i in range(0, 5):
            print("GAME OVER!", end='', flush=True)
            sleep(1)
            print("\r", end='', flush=True)
            print("            ", end='', flush=True)
            print("\r", end='', flush=True)
            sleep(1)

    # 游戏状态 EXIT 逻辑
    def game_exit(self):
        if self.play_count > 0:

            msg = """\n
    您选择了退出游戏 ...
----------------------------
    游戏结果:
        
    场次：%d
        
    最高分: %d
    
    最高数: %d
    """ % (self.play_count, self.max_score, self.max_number)
            self.print_msg_slowly(msg)
            msg = """
----------------------------
    正在清扫战场...
    战场清扫完毕!
    欢迎下次光临 ^_^
    \n"""
            self.print_msg_slowly(msg)
        else:
            msg = """\n
    您选择了退出游戏 ...
    正在清扫战场...
    战场清扫完毕!
    欢迎下次光临 ^_^
   """
            self.print_msg_slowly(msg)
        self.key_listener.stop()

    # 渲染游戏场景
    def render(self):
        msg = """
        ---------------------------------------------
        |  score: %s|
        |  max score: %s|
        |  max number: %s|
        ---------------------------------------------
        |          |          |          |          |
        |          |          |          |          |
        |%s|%s|%s|%s|
        |          |          |          |          |
        |          |          |          |          |
        ---------------------------------------------
        |          |          |          |          |
        |          |          |          |          |
        |%s|%s|%s|%s|
        |          |          |          |          |
        |          |          |          |          |
        ---------------------------------------------
        |          |          |          |          |
        |          |          |          |          |
        |%s|%s|%s|%s|
        |          |          |          |          |
        |          |          |          |          |
        ---------------------------------------------
        |          |          |          |          |
        |          |          |          |          |
        |%s|%s|%s|%s|
        |          |          |          |          |
        |          |          |          |          |
        ---------------------------------------------
    """
        msg = msg % (str(self.score).ljust(34), str(self.max_score).ljust(30), str(self.max_number).ljust(29)
                     , self.fstr(self.data[0][0].num), self.fstr(self.data[0][1].num), self.fstr(self.data[0][2].num),
                     self.fstr(self.data[0][3].num)
                     , self.fstr(self.data[1][0].num), self.fstr(self.data[1][1].num), self.fstr(self.data[1][2].num),
                     self.fstr(self.data[1][3].num)
                     , self.fstr(self.data[2][0].num), self.fstr(self.data[2][1].num), self.fstr(self.data[2][2].num),
                     self.fstr(self.data[2][3].num)
                     , self.fstr(self.data[3][0].num), self.fstr(self.data[3][1].num), self.fstr(self.data[3][2].num),
                     self.fstr(self.data[3][3].num)
                     )
        msg += "按 ESC 退出游戏, 按 N 重新开始 当前游戏状态：%s" % self.game_status
        self.print_msg_slowly(msg, clear=True, tm=0)

    # 慢速打印
    def print_msg_slowly(self, msg, clear=False, tm=0.03):
        tmp_status = self.game_status
        self.game_status = self.GAME_STATUS_WAIT
        if clear:
            cls()
        if tm == 0:
            print(msg, end='', flush=True)
        else:
            for c in msg:
                sleep(tm)
                print(c, end='', flush=True)
        self.game_status = tmp_status

    # 格式化一块数字 宽度 10 居中显示 留空的用空格填充
    def fstr(self, num):
        block_str = str(num)
        if num == 0:
            return "          "
        last_block_len = int((10 - len(block_str)) / 2)
        first_block_len = 10 - len(block_str) - last_block_len
        block_str = block_str.rjust(first_block_len + len(block_str))
        block_str = block_str.ljust(10)
        return block_str

    # 在游戏数据中随机生成一个数
    def generate_block_number(self):
        if self.number < 4:
            if random.randint(0, 100) == 50:
                return self.random_block(4)
            else:
                return self.random_block(2)
        else:
            return self.random_block(2)

    # 根据 num 随机生成这个数的游戏块
    def random_block(self, num):
        empty_list = self.get_empty_list()
        if len(empty_list) == 0:
            return False
        empty_list[random.randint(0, len(empty_list) - 1)].num = num
        return True

    # 获取剩余空白的块列表
    def get_empty_list(self):
        empty_list = []
        for line in self.data:
            for b in line:
                if b.num == 0:
                    empty_list.append(b)
                if b.num > self.number:
                    self.number = b.num
        # 顺便把最大数字更新了
        if self.number > self.max_number:
            self.max_number = self.number
        return empty_list


if __name__ == '__main__':

    # 获取平台信息 并记录
    os_name = platform.system()
    if os_name == "Windows":
        os_platform = PLATFORM_WINDOWS
    elif os_name == "Linux":
        os_platform = PLATFORM_LINUX
    else:
        os_platform = PLATFORM_OTHER

    # 检测并安装必要的模块
    print("开始环境检测...")
    status = check_libs()
    if status == -1:
        print("模块安装失败！程序无法执行！")
        exit(1)
    elif status == 1:
        print("模块安装完毕！请重启程序！")
        exit(1)

    # 打开临时标准输出重定向临时文件
    std_out = open('stdout', 'w')

    # 启动游戏
    Game().start()

    # 释放临时文件并删除
    std_out.close()
    sleep(1)
    os.remove("stdout")
    print("游戏结束..........")
