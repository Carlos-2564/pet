import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, Menu, simpledialog
from PIL import Image, ImageTk, ImageSequence
import webbrowser
import json
import random
import hashlib
class DogGIFPlayer:
    def __init__(self, master):
        # ---------------------- 1. 路径处理（适配开发/打包环境） ----------------------
        # 判断是否是打包后的exe（后续打包给别人用时，资源路径不会错）
        if getattr(sys, 'frozen', False):
            self.base_dir = sys._MEIPASS  # 打包后资源路径
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))  # 开发时路径（项目文件夹）

        # 关键：配置文件存用户目录（避免打包后设置丢失）
        if getattr(sys, 'frozen', False):
            # 打包后：存到Windows的AppData/Roaming目录（隐藏，不占桌面空间）
            self.user_data_dir = os.path.join(os.environ.get('APPDATA'), 'CARLOS DENG的桌宠配置')
        else:
            # 开发时：存到项目目录（方便调试）
            self.user_data_dir = os.path.dirname(os.path.abspath(__file__))

        # 确保配置目录存在（首次运行自动创建，不会报错）
        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir)

        # 核心路径定义
        self.gif_folder = os.path.join(self.base_dir, 'gif')  # 角色动图文件夹
        self.hash_file = os.path.join(self.base_dir, 'hash_verify.json')  # 哈希验证文件
        self.config_path = os.path.join(self.user_data_dir, 'config.json')  # 配置文件（用户目录）

        # ---------------------- 2. 窗口基础样式（无边框+置顶+透明） ----------------------
        self.root = master
        self.root.title("CARLOS DENG专属桌宠")
        self.root.geometry("400x400")  # 初始窗口大小
        self.root.overrideredirect(True)  # 去掉窗口边框（桌宠更美观）
        self.root.attributes('-topmost', True)  # 窗口置顶（始终在桌面最上层）
        self.root.attributes('-transparentcolor', '#000001')  # 透明色（避免背景黑边）
        self.transparency = 1.0  # 初始透明度（1.0=完全不透明）
        self.root.attributes('-alpha', self.transparency)
        self.is_fixed = False  # 是否固定窗口（防止误拖拽）

        # ---------------------- 3. 核心变量初始化（后续功能用） ----------------------
        self.gif_files = []  # 存储所有动图路径
        self.current_index = 0  # 当前显示动图的索引
        self.playing = True  # GIF是否正在播放
        self.frames = []  # 存储GIF的所有帧（静态图是单帧）
        self.current_frame = 0  # 当前显示的帧索引
        self.animation_id = None  # 动画任务ID（用于暂停）
        self.auto_play_id = None  # 自动播放任务ID（用于停止）
        self.is_auto_playing = False  # 是否开启自动播放
        self.auto_play_interval = 5000  # 自动播放间隔（默认5秒）
        self.control_bar_visible = False  # 控制栏是否显示（默认隐藏）

        # ---------------------- 4. 初始化流程（先验证哈希，再加载功能） ----------------------
        self.create_context_menu()  # 右键菜单（核心功能入口）
        self.create_control_bar()   # 控制栏（快捷按钮）
        self.create_canvas()        # 画布（显示动图）
        self.bind_drag_events()     # 拖拽事件（拖动物宠）

        # 加载资源与配置
        self.load_local_gifs()  # 加载gif文件夹的动图
        self.load_config()      # 加载之前的配置（窗口大小、透明度）
        # 退出时自动保存配置
        self.root.protocol("WM_DELETE_WINDOW", self.save_on_exit)
        def calculate_file_hash(self, file_path):
         """计算单个文件的MD5哈希值（用于验证文件是否被篡改）"""
        md5_hash = hashlib.md5()
        try:
            # 分块读取大文件（避免内存占用过高）
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            messagebox.showerror("哈希计算错误", f"文件 {os.path.basename(file_path)} 读取失败: {str(e)}")
            return None

    def save_gif_hashes(self):
        """保存gif文件夹中所有动图的哈希值（首次创建或更新时用）"""
        if not os.path.exists(self.gif_folder):
            try:
                os.makedirs(self.gif_folder)
            except Exception as e:
                messagebox.showerror("错误", f"创建gif文件夹失败: {str(e)}")
                return False
            messagebox.showerror("错误", "未找到gif文件夹，请先放入动图！")
            return False

        # 获取所有有效图片文件（支持GIF/PNG/JPG等）
        valid_extensions = ('.gif', '.png', '.jpg', '.jpeg', '.bmp')
        self.gif_files = [
            os.path.join(self.gif_folder, f)
            for f in os.listdir(self.gif_folder)
            if f.lower().endswith(valid_extensions)
        ]

        if not self.gif_files:
            messagebox.showerror("错误", "gif文件夹中无有效动图文件！")
            return False

        # 计算并保存每个文件的哈希值
        hash_dict = {}
        for f in self.gif_files:
            filename = os.path.basename(f)
            file_hash = self.calculate_file_hash(f)
            if file_hash is None:
                return False
            hash_dict[filename] = file_hash

        # 保存到哈希文件
        try:
            with open(self.hash_file, 'w', encoding='utf-8') as f:
                json.dump(hash_dict, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"保存哈希文件失败: {str(e)}")
            return False

    def verify_gif_hash(self):
        """验证当前动图文件的哈希值是否与保存的一致（防止篡改）"""
        # 哈希文件不存在时，视为首次运行，后续会自动创建
        if not os.path.exists(self.hash_file):
            return True

        # 加载已保存的哈希值
        try:
            with open(self.hash_file, 'r', encoding='utf-8') as f:
                saved_hashes = json.load(f)
        except Exception as e:
            messagebox.showerror("错误", f"哈希验证文件损坏: {str(e)}")
            return False

        # 获取当前文件夹中的动图文件
        valid_extensions = ('.gif', '.png', '.jpg', '.jpeg', '.bmp')
        current_files = [
            os.path.join(self.gif_folder, f)
            for f in os.listdir(self.gif_folder)
            if f.lower().endswith(valid_extensions)
        ]

        # 先验证文件数量是否一致（数量变了，说明文件被增删）
        if len(current_files) != len(saved_hashes):
            return False

        # 逐个验证文件哈希值
        for file_path in current_files:
            filename = os.path.basename(file_path)
            if filename not in saved_hashes:
                return False  # 文件名不存在，视为篡改
            current_hash = self.calculate_file_hash(file_path)
            if current_hash != saved_hashes[filename]:
                return False  # 哈希值不一致，视为篡改

        return True  # 所有验证通过

    def verify_and_update_hash(self):
        """验证哈希值，失败则自动更新（用户不用手动操作）"""
        # 首次运行或哈希文件不存在，自动创建
        if not os.path.exists(self.hash_file):
            self.save_gif_hashes()
            return

        # 验证失败时，自动更新哈希值（比如用户换了新动图）
        if not self.verify_gif_hash():
            messagebox.showinfo(
                "哈希验证更新",
                "检测到动图已更新，正在重新计算哈希值..."
            )
            self.save_gif_hashes()
            messagebox.showinfo("完成", "哈希值已更新，当前动图文件已被认可")
            if __name__ == "__main__":
             try:
                 root = tk.Tk()
                 app = DogGIFPlayer(root)
                 root.mainloop()
             except Exception as e:
        # 错误日志保存到用户目录（方便排查）
              log_dir = (
            os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), '恋与深空桌宠配置')
            if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        )
        os.makedirs(log_dir, exist_ok=True)
        error_log_path = os.path.join(log_dir, 'error.log')
        with open(error_log_path, 'w', encoding='utf-8') as f:
            f.write(str(e))
        messagebox.showerror("程序异常", f"错误信息已保存到 {error_log_path}，可凭此排查问题")

    def create_context_menu(self):
        """创建右键菜单（新增“更多桌宠”入口）"""
        self.context_menu = Menu(self.root, tearoff=0)  # 取消菜单可分离

        # 1. 控制栏开关
        self.context_menu.add_command(label="显示/隐藏控制栏", command=self.toggle_control_bar)
        self.context_menu.add_separator()

        # 2. 动图切换
        self.context_menu.add_command(label="上一张", command=self.prev_gif)
        self.context_menu.add_command(label="下一张", command=self.next_gif)
        self.context_menu.add_command(label="随机显示", command=self.random_gif)
        self.context_menu.add_separator()

        # 3. 动图选择子菜单（动态显示所有动图文件名）
        self.gif_submenu = Menu(self.context_menu, tearoff=0)
        self.context_menu.add_cascade(label="选择角色动图", menu=self.gif_submenu)
        self.context_menu.add_separator()

        # 4. 窗口固定
        self.context_menu.add_command(label="固定窗口", command=self.fix_window)
        self.context_menu.add_command(label="取消固定", command=self.unfix_window)
        self.context_menu.add_separator()

        # 5. 自动播放
        self.context_menu.add_command(label="开启循环播放", command=self.start_auto_play)
        self.context_menu.add_command(label="停止循环播放", command=self.stop_auto_play)
        self.context_menu.add_command(label="设置播放间隔", command=self.set_auto_play_interval)
        self.context_menu.add_separator()

        # 6. 透明度调节子菜单
        self.transparency_menu = Menu(self.context_menu, tearoff=0)
        self.context_menu.add_cascade(label="调节透明度", menu=self.transparency_menu)
        transparencies = [("100%", 1.0), ("75%", 0.75), ("50%", 0.5), ("25%", 0.25)]
        for label, value in transparencies:
            self.transparency_menu.add_command(
                label=label, 
                command=lambda v=value: self.set_transparency(v)
            )

        self.context_menu.add_separator()
        # 7. 新增：关于作者与更多桌宠入口
        self.context_menu.add_command(label="关于作者", command=self.show_about)
        self.context_menu.add_command(
            label="更多桌宠", 
            command=lambda: webbrowser.open(
                "https://dianshudata.com/dataMarket?search=%E6%A1%8C%E5%AE%A0&mtm_campaign=zhuochonglink&mtm_kwd=%E6%A1%8C%E5%AE%A0"
            )
        )
        self.context_menu.add_separator()
        # 8. 退出（保存配置后关闭）
        self.context_menu.add_command(label="退出", command=self.save_on_exit)

    def show_context_menu(self, event):
        """在鼠标右键点击位置显示菜单"""
        self.context_menu.post(event.x_root, event.y_root)

    def create_control_bar(self):
        """创建控制栏（快捷操作按钮）"""
        self.control_bar = ttk.Frame(self.root)  # 控制栏容器

        # 上一张按钮
        self.btn_prev = ttk.Button(self.control_bar, text="上一张", command=self.prev_gif)
        self.btn_prev.pack(side=tk.LEFT, padx=5)  # 水平排列，左右留间距

        # 暂停/播放按钮
        self.btn_play_pause = ttk.Button(self.control_bar, text="暂停", command=self.toggle_play)
        self.btn_play_pause.pack(side=tk.LEFT, padx=5)

        # 下一张按钮
        self.btn_next = ttk.Button(self.control_bar, text="下一张", command=self.next_gif)
        self.btn_next.pack(side=tk.LEFT, padx=5)

        # 停止自动播放按钮
        self.btn_stop_auto = ttk.Button(self.control_bar, text="停止自动播放", command=self.stop_auto_play)
        self.btn_stop_auto.pack(side=tk.LEFT, padx=5)

        # 状态标签（显示当前动图名称和索引）
        self.status_label = ttk.Label(self.control_bar, text="正在显示: 无 | 0/0")
        self.status_label.pack(side=tk.LEFT, padx=10)

    def toggle_control_bar(self):
        """显示/隐藏控制栏（节省桌面空间）"""
        self.control_bar_visible = not self.control_bar_visible
        if self.control_bar_visible:
            self.control_bar.pack(fill=tk.X, side=tk.TOP)  # 显示：顶部水平填充
        else:
            self.control_bar.pack_forget()  # 隐藏：移除控制栏

    def bind_drag_events(self):
        """绑定拖拽事件（初始化变量）"""
        self.dragging = False  # 是否正在拖拽
        self.drag_start_x = 0  # 拖拽起点x坐标（相对于画布）
        self.drag_start_y = 0  # 拖拽起点y坐标（相对于画布）

        # 绑定鼠标事件：按下（开始拖拽）、移动（拖拽中）、松开（停止拖拽）
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)

    def start_drag(self, event):
        """开始拖拽（仅当窗口未固定时生效）"""
        if not self.is_fixed:
            self.dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y

    def on_drag(self, event):
        """拖拽中（计算窗口新位置）"""
        if self.dragging and not self.is_fixed:
            # 窗口当前位置 + 鼠标移动距离 = 新位置
            x = self.root.winfo_x() - self.drag_start_x + event.x
            y = self.root.winfo_y() - self.drag_start_y + event.y
            self.root.geometry(f"+{x}+{y}")  # 更新窗口位置

    def stop_drag(self, event):
        """停止拖拽"""
        self.dragging = False

    def on_mouse_wheel(self, event):
        """鼠标滚轮缩放窗口（最小100x100像素，避免太小看不见）"""
        # 获取当前窗口大小（解析geometry字符串，如“400x400+100+100”）
        width, height = map(int, self.root.geometry().split("+")[0].split("x"))
        step = 20  # 每次缩放20像素

        # 上滚放大，下滚缩小（兼容Windows和Linux）
        if event.num == 4 or event.delta > 0:
            new_width = width + step
            new_height = height + step
        else:
            new_width = max(100, width - step)  # 最小100像素
            new_height = max(100, height - step)

        self.root.geometry(f"{new_width}x{new_height}")
        self.save_config()  # 缩放后自动保存大小

    def fix_window(self):
        """固定窗口（无法拖拽）"""
        self.is_fixed = True
        self.update_context_menu_state()  # 灰显“固定窗口”菜单

    def unfix_window(self):
        """取消固定（可拖拽）"""
        self.is_fixed = False
        self.update_context_menu_state()  # 灰显“取消固定”菜单

    def update_context_menu_state(self):
        """更新右键菜单状态（根据窗口是否固定灰显对应选项）"""
        self.context_menu.entryconfig("固定窗口", state=tk.DISABLED if self.is_fixed else tk.NORMAL)
        self.context_menu.entryconfig("取消固定", state=tk.NORMAL if self.is_fixed else tk.DISABLED)
         # -------------------------- 动图加载与播放 --------------------------
    def load_local_gifs(self):
        """加载gif文件夹中的动图（自动过滤非图片文件）"""
        if not os.path.exists(self.gif_folder):
            messagebox.showerror("错误", "未找到gif文件夹，请检查程序完整性！")
            self.root.destroy()
            return

        # 只加载支持的图片格式
        valid_extensions = ('.gif', '.png', '.jpg', '.jpeg', '.bmp')
        self.gif_files = [
            os.path.join(self.gif_folder, f)
            for f in os.listdir(self.gif_folder)
            if f.lower().endswith(valid_extensions)
        ]

        if self.gif_files:
            # 加载第一张动图
            self.load_gif(self.gif_files[0])
            # 更新右键菜单的动图列表
            self.update_gif_submenu()
        else:
            messagebox.showerror("错误", "gif文件夹中没有有效图片，请放入恋与深空动图！")

    def update_gif_submenu(self):
        """动态更新右键菜单中的动图选择列表"""
        self.gif_submenu.delete(0, tk.END)  # 清空现有选项
        for idx, path in enumerate(self.gif_files):
            filename = os.path.basename(path)  # 只显示文件名（不含路径）
            self.gif_submenu.add_command(
                label=filename,
                command=lambda i=idx: self.select_gif(i)  # 点击切换到对应动图
            )

    def load_gif(self, gif_path):
        """加载单张动图（支持GIF动画和静态图）"""
        try:
            # 停止当前动画（避免多个动画同时运行）
            if self.animation_id:
                self.root.after_cancel(self.animation_id)

            # 打开图片并提取所有帧（GIF是多帧，静态图是单帧）
            self.gif = Image.open(gif_path)
            self.frames = [frame.copy().convert("RGBA") for frame in ImageSequence.Iterator(self.gif)]
            self.current_frame = 0  # 从第一帧开始显示
            self.display_frame()  # 显示第一帧
            self.animate()  # 开始播放动画

            # 更新状态标签（显示当前动图名称和索引）
            filename = os.path.basename(gif_path)
            self.status_label.config(
                text=f"正在显示: {filename} | {self.current_index + 1}/{len(self.gif_files)}"
            )

        except Exception as e:
            messagebox.showerror("加载失败", f"动图 {os.path.basename(gif_path)} 加载出错: {str(e)}")

    def display_frame(self):
        """显示当前帧（修复透明背景黑边问题）"""
        if not self.frames:
            return

        frame = self.frames[self.current_frame]
        self.canvas.delete("all")  # 清空画布

        # 获取画布尺寸，自适应缩放动图（保持比例）
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width > 0 and canvas_height > 0:
            # 计算缩放比例（取宽高比例的最小值，避免动图超出画布）
            ratio = min(canvas_width / frame.width, canvas_height / frame.height)
            new_size = (int(frame.width * ratio), int(frame.height * ratio))
            # 高质量缩放（保留透明通道）
            frame = frame.resize(new_size, Image.LANCZOS)

            # 创建透明背景（解决GIF透明区域显示黑边的问题）
            bg = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))  # 全透明背景
            # 计算居中位置
            x = (canvas_width - new_size[0]) // 2
            y = (canvas_height - new_size[1]) // 2
            # 将动图帧粘贴到透明背景上（保留透明区域）
            bg.paste(frame, (x, y), frame)
            self.photo = ImageTk.PhotoImage(bg)
        else:
            # 画布未初始化时直接显示原帧
            self.photo = ImageTk.PhotoImage(frame)

        # 在画布居中显示
        self.canvas.create_image(canvas_width // 2, canvas_height // 2, image=self.photo)

    def animate(self):
        """播放GIF动画（按原GIF的帧间隔播放）"""
        if not self.playing or not self.frames:
            return

        # 切换到下一帧（循环播放）
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.display_frame()

        # 获取GIF原帧间隔（默认100毫秒）
        delay = self.gif.info.get('duration', 100)
        # 预约下一帧播放（递归调用实现动画循环）
        self.animation_id = self.root.after(delay, self.animate)

    def toggle_play(self):
        """切换播放/暂停状态"""
        self.playing = not self.playing
        # 更新按钮文字
        self.btn_play_pause.config(text="播放" if self.playing else "暂停")
        if self.playing:
            self.animate()  # 继续播放

    def prev_gif(self):
        """切换到上一张动图（循环切换）"""
        if self.gif_files:
            # 索引减1，用取模运算实现循环（0的上一张是最后一张）
            self.current_index = (self.current_index - 1) % len(self.gif_files)
            self.load_gif(self.gif_files[self.current_index])

    def next_gif(self):
        """切换到下一张动图（循环切换）"""
        if self.gif_files:
            # 索引加1，取模运算循环（最后一张的下一张是0）
            self.current_index = (self.current_index + 1) % len(self.gif_files)
            self.load_gif(self.gif_files[self.current_index])

    def random_gif(self):
        """随机切换一张动图"""
        if self.gif_files:
            self.current_index = random.randint(0, len(self.gif_files) - 1)
            self.load_gif(self.gif_files[self.current_index])

    def select_gif(self, index):
        """通过右键菜单选择指定动图"""
        if 0 <= index < len(self.gif_files):
            self.current_index = index
            self.load_gif(self.gif_files[index])

    def start_auto_play(self):
        """开启自动循环播放（按设置的间隔切换）"""
        if not self.is_auto_playing:
            self.is_auto_playing = True
            self.auto_play_next_gif()  # 开始循环

    def auto_play_next_gif(self):
        """自动播放下一张（递归调用实现循环）"""
        if self.is_auto_playing:
            self.next_gif()  # 切换到下一张
            # 预约下一次切换（间隔时间由用户设置）
            self.auto_play_id = self.root.after(self.auto_play_interval, self.auto_play_next_gif)

    def stop_auto_play(self):
        """停止自动播放"""
        if self.is_auto_playing:
            self.is_auto_playing = False
            if self.auto_play_id:
                self.root.after_cancel(self.auto_play_id)  # 取消预约任务
                self.auto_play_id = None

    def set_auto_play_interval(self):
        """设置自动播放间隔（1-200秒）"""
        try:
            seconds = simpledialog.askinteger(
                "设置间隔",
                "请输入自动播放间隔（秒，1-200）:",
                minvalue=1,
                maxvalue=200
            )
            if seconds:
                self.auto_play_interval = seconds * 1000  # 转换为毫秒
                self.save_config()  # 保存设置
                messagebox.showinfo("成功", f"自动播放间隔已设置为 {seconds} 秒")
        except Exception as e:
            messagebox.showerror("错误", f"设置失败: {str(e)}")

    def load_config(self):
        """加载之前保存的配置（窗口大小、透明度等）"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 恢复窗口大小
                    if 'window_size' in config:
                        self.root.geometry(config['window_size'])
                    # 恢复透明度
                    if 'transparency' in config:
                        self.transparency = config['transparency']
                        self.root.attributes('-alpha', self.transparency)
                    # 恢复自动播放间隔
                    if 'auto_play_interval' in config:
                        self.auto_play_interval = config['auto_play_interval']
        except Exception as e:
            print(f"加载配置出错: {e}")
            # 配置文件损坏时删除，下次运行会自动创建新的
            if os.path.exists(self.config_path):
                try:
                    os.remove(self.config_path)
                except:
                    pass

    def save_config(self):
        """保存当前配置（窗口大小、透明度、播放间隔）"""
        try:
            config = {
                'window_size': f"{self.root.winfo_width()}x{self.root.winfo_height()}",
                'transparency': self.transparency,
                'auto_play_interval': self.auto_play_interval
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置出错: {str(e)}")

    def save_on_exit(self):
        """退出程序时保存配置"""
        self.save_config()
        self.root.destroy()

    def set_transparency(self, value):
        """调节窗口透明度（1.0=完全不透明，0.25=半透明）"""
        self.transparency = value
        self.root.attributes('-alpha', self.transparency)
        self.save_config()  # 保存透明度设置

    def show_about(self):
        """显示关于信息（作者与版权声明）"""
        messagebox.showinfo(
            "关于作者",
            "此软件由Carlos Deng独立开发完成，想了解更多可联系carlos.dh.usfrcn0528@gmail.com\n\n严重声明：本软件禁止二次售卖！"
        )


