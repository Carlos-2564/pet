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
            self.user_data_dir = os.path.join(os.environ.get('APPDATA'), '恋与深空桌宠配置')
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
        self.root.title("恋与深空专属桌宠")
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