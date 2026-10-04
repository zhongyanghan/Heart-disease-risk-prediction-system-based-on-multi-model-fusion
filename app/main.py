# -*- coding: utf-8 -*-
"""基于多模型融合的心脏病风险预测系统 —— 桌面端（PyQt5 + MySQL）。

运行前请先执行 ``sql/init.sql`` 初始化 MySQL 数据库；
数据库连接参数可通过环境变量覆盖（HEART_DB_HOST / HEART_DB_USER /
HEART_DB_PASSWORD / HEART_DB_NAME），默认值见下方 ``Database`` 类。

可选资源：将背景图 ``beijng.jpg`` 与按钮图标 ``m1.png`` ~ ``m4.png``
放置于 ``app/assets/`` 目录；资源缺失时程序仍可正常运行（仅无背景/图标）。

默认登录账号：admin / 123456（见 sql/init.sql）
"""
import sys
import os
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pickle
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import pymysql
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
MODEL_PATH = os.path.join(PROJECT_ROOT, 'models', 'model.pkl')

with open(MODEL_PATH, 'rb') as file:
    loaded_model = pickle.load(file)


def set_background(label, image='beijng.jpg'):
    """为 QLabel 设置背景图；资源缺失时静默跳过，不影响程序运行。"""
    path = os.path.join(ASSETS_DIR, image)
    if os.path.exists(path):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            label.setPixmap(pixmap)
            label.setScaledContents(True)


def app_icon(name):
    """加载按钮图标；资源缺失时返回空图标。"""
    path = os.path.join(ASSETS_DIR, name)
    return QIcon(path) if os.path.exists(path) else QIcon()


class Database:
    def __init__(self):
        self.connection = pymysql.connect(
            host=os.getenv('HEART_DB_HOST', 'localhost'),       # 数据库地址
            user=os.getenv('HEART_DB_USER', 'root'),            # 数据库用户名
            password=os.getenv('HEART_DB_PASSWORD', '123456'),  # 数据库密码
            database=os.getenv('HEART_DB_NAME', 'heart_disease_prediction'),  # 数据库名称
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    def close(self):
        self.connection.close()

    def execute(self, query, args=None):
        with self.connection.cursor() as cursor:
            cursor.execute(query, args)
            self.connection.commit()

    def fetchall(self, query, args=None):
        with self.connection.cursor() as cursor:
            cursor.execute(query, args)
            return cursor.fetchall()

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)
        self.db = Database()
        self.setWindowTitle('登录页面')
        self.setGeometry(100, 50, 300, 100)
        self.setFixedSize(800, 600)  # Adjusted size for better appearance

        self.background_label = QLabel(self)
        self.background_label.setGeometry(0, 0, 800, 600)  # 调整标签大小以覆盖整个窗口
        set_background(self.background_label)
        self.background_label.lower()
#         self.setStyleSheet("""
#             QWidget {
#                 background-image: url('beijng.jpg');
#                 background-repeat: no-repeat;
#                 background-position: center;
#                 background-attachment: fixed;
#             }

#             """)
        # Main layout
        centralLayout = QVBoxLayout(self)

        # Title label
        titleLabel = QLabel("基于多模型融合的心脏病风险预测系统")
        titleLabel.setAlignment(Qt.AlignCenter)
        titleLabel.setStyleSheet("font-size: 28px; font-weight: bold;")
        centralLayout.addWidget(titleLabel)

        # Form layout for username and password
        formLayout = QFormLayout()

        # Username and password fields
        self.username = QLineEdit(self)
        self.username.setFixedSize(300, 40)  # Larger and more readable
        self.password = QLineEdit(self)
        self.password.setFixedSize(300, 40)  # Consistent with username field
        self.password.setEchoMode(QLineEdit.Password)

        # Login button
        login_button = QPushButton('登录', self)
        login_button.setFixedSize(150, 40)  # Properly sized button
        login_button.setStyleSheet("QPushButton { color: white; background-color: #90EE90; border-radius: 6px; }"
                                        "QPushButton:hover { background-color: #77DD77; }"
                                        "QPushButton:pressed { background-color: #66CC66; }")

        # Add widgets to form layout
        formLayout.addRow("账号:", self.username)
        formLayout.addRow("密码:", self.password)

        # Add form layout to central layout
        centralLayout.addLayout(formLayout)
        centralLayout.addWidget(login_button, 0, Qt.AlignCenter)  # Center the button within the layout

        # Set form layout alignment and add spacing
        formLayout.setLabelAlignment(Qt.AlignRight)
        formLayout.setFormAlignment(Qt.AlignCenter)
        formLayout.setVerticalSpacing(20)

        # Connect the login button
        login_button.clicked.connect(self.handle_login)

    def handle_login(self):
        username = self.username.text()
        password = self.password.text()
        query = "SELECT * FROM manager WHERE username=%s AND password=%s"
        result = self.db.fetchall(query, (username, password))
        if result:
            self.accept()
        else:
            QMessageBox.warning(self, 'Error', '错误的账号或密码')

    def closeEvent(self, event):
        self.db.close()


class ChurnPredictionApp(QMainWindow):
    update_output1_signal = pyqtSignal(str)
    update_output2_signal = pyqtSignal(str)
    update_output3_signal = pyqtSignal(str)
    update_output4_signal = pyqtSignal(str)
    update_output5_signal = pyqtSignal(str)
    update_output6_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.db = Database()
        self.initUI()
        # 将QPalette应用于窗口
        self.update_output1_signal.connect(self.update_output1_slot)
        self.update_output2_signal.connect(self.update_output2_slot)
        self.update_output3_signal.connect(self.update_output3_slot)
        self.update_output4_signal.connect(self.update_output4_slot)
        self.update_output5_signal.connect(self.update_output5_slot)
        self.update_output6_signal.connect(self.update_output6_slot)
    def initUI(self):
        self.hide()
        # Login Dialog
        login = LoginDialog(self)
        if login.exec_() == QDialog.Accepted:
            self.setup_main_ui()
            self.show()
        else:
            self.close()  # Close the app if the login is not successful
            
    def setup_main_ui(self):
        self.centralwidget = QWidget()
        self.setCentralWidget(self.centralwidget)
        self.centralwidget = QWidget()
        self.setCentralWidget(self.centralwidget)
        self.Layout = QHBoxLayout(self.centralwidget)
        self.palette = QPalette()
        self.palette.setColor(QPalette.Background, QColor(255, 255, 255))
        self.centralwidget.setAutoFillBackground(True)
        self.centralwidget.setPalette(self.palette)

        # 设置五个个按钮
        self.topwidget = QWidget()
        self.palette = QPalette()
        self.palette.setColor(QPalette.Background, QColor(60,60,60)) # 设置背景色为RGB值为(128, 128, 128)的灰色
        self.topwidget.setAutoFillBackground(True)
        self.topwidget.setPalette(self.palette)

        self.buttonLayout = QVBoxLayout(self.topwidget)
        self.pushButton1 = QPushButton()
        self.pushButton1.setText("病症预测")
        self.pushButton1.setFixedSize(130, 50)  # 设置按钮大小
        self.pushButton1.setStyleSheet("QPushButton{background-color: rgb(60,60,60); color: white;font-size: 24px; font-weight: bold;}"
                    "QPushButton:hover{background:rgb(110,115,100);}"
                    "QPushButton::pressed{background:grey}")
        self.pushButton1.setIcon(app_icon("m1.png"))  # 设置按钮图标
        self.buttonLayout.addWidget(self.pushButton1)
       # self.pushButton1.setStyleSheet("background-color: red;")

        self.pushButton4 = QPushButton()
        self.pushButton4.setText("意见反馈")
        self.pushButton4.setFixedSize(130, 50)  # 设置按钮大小
        self.pushButton4.setStyleSheet(
            "QPushButton{background-color: rgb(60,60,60); color: white;font-size: 24px; font-weight: bold;}"
            "QPushButton:hover{background:rgb(110,115,100);}"  
            "QPushButton::pressed{background:grey;}" 
        )
        self.pushButton4.setIcon(app_icon("m2.png"))  # 设置按钮图标
        self.buttonLayout.addWidget(self.pushButton4)

        self.pushButton5 = QPushButton()
        self.pushButton5.setText("患者管理")
        self.pushButton5.setFixedSize(130, 50)  # 设置按钮大小
        self.pushButton5.setStyleSheet(
            "QPushButton{background-color: rgb(60,60,60); color: white;font-size: 24px; font-weight: bold;}"
            "QPushButton:hover{background:rgb(110,115,100);}" 
            "QPushButton::pressed{background:grey;}" 
        )
        self.pushButton5.setIcon(app_icon("m3.png"))  # 设置按钮图标
        self.buttonLayout.addWidget(self.pushButton5)
        
        self.pushButton6 = QPushButton()
        self.pushButton6.setText("数据可视")
        self.pushButton6.setFixedSize(130, 50)  # 设置按钮大小
        self.pushButton6.setStyleSheet(
            "QPushButton{background-color: rgb(60,60,60); color: white;font-size: 24px; font-weight: bold;}"
            "QPushButton:hover{background:rgb(110,115,100);}" 
            "QPushButton::pressed{background:grey;}" 
        )
        self.pushButton6.setIcon(app_icon("m4.png"))  # 设置按钮图标
        self.buttonLayout.addWidget(self.pushButton6)

        self.Layout.addWidget(self.topwidget)
        self.stackedWidget = QStackedWidget()
        self.Layout.addWidget(self.stackedWidget)

        self.setWindowTitle('基于多模型融合的心脏病风险预测系统')
        self.setGeometry(100, 50, 300, 100)
        self.setFixedSize(1400, 965)
        self.pdf_input_text=''
        self.log_result={}
        
        self.neicun = []
        
        # 设置第一个面板
        self.form1 = QWidget()
        self.background_label = QLabel(self.form1)
        self.background_label.setGeometry(0, 0, 1400, 965)  # 调整标签大小以覆盖整个窗口
        set_background(self.background_label)  # 将背景标签置于最底层
        self.layout = QVBoxLayout(self.form1)
    
        self.label2 = QLabel()
        self.label2.setText("基于多模型融合的心脏病风险预测系统")
        self.label2.setContentsMargins(15, 15, 15, 15)
        self.label2.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.label2.setAlignment(Qt.AlignCenter)
        self.label2.setFont(QFont("STKaiti", 25, QFont.Bold))
        
        self.model = loaded_model
        self.loaded_file_label = QLabel("", self)
        self.loaded_file_label.setStyleSheet("font-size: 22px; color: red;font-weight: bold;")
        self.person_information = QLabel("", self)
        self.person_information.setStyleSheet("font-size: 22px; color: black;font-weight: bold;")
        self.comboBox = QComboBox(self)
        self.comboBox.currentIndexChanged.connect(self.update_display)
        self.label_result = QLabel("预测结果: ", self) 
        self.label_result.setStyleSheet("font-size: 26px; color: red;font-weight: bold;")
        self.button_load = QPushButton("加载Excel文件", self)
        self.button_load.setStyleSheet("font-size: 22px; color: black;font-weight: bold;background-color: #ADD8E6;")
        self.button_load.clicked.connect(self.load_excel)
        self.horizontal_layout = QHBoxLayout()
        self.form_layout_left = QFormLayout()
        self.form_layout_right = QFormLayout()

        self.horizontal_layout.addLayout(self.form_layout_left)
        self.horizontal_layout.addLayout(self.form_layout_right)
        self.layout.addWidget(self.label2)
        self.layout.addWidget(self.comboBox)
        self.layout.addWidget(self.button_load)
        self.layout.addWidget(self.loaded_file_label)
        self.layout.addWidget(self.person_information)
        self.layout.addLayout(self.horizontal_layout)
        self.layout.addWidget(self.label_result)

        # 设置第四个面板
        self.form4 = QWidget()
        self.background_label = QLabel(self.form4)
        self.background_label.setGeometry(0, 0, 1400, 965)  # 调整标签大小以覆盖整个窗口
        set_background(self.background_label)  # 将背景标签置于最底层
        self.layout4 = QVBoxLayout(self.form4)

        self.label5 = QLabel()
        self.label5.setText("基于多模型融合的心脏病风险预测系统")
        self.label5.setContentsMargins(15, 15, 15, 15)
        self.label5.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.label5.setAlignment(Qt.AlignCenter)
        self.label5.setFont(QFont("STKaiti", 25, QFont.Bold))
        
        self.layout4.addWidget(self.label5)
        # 用户姓名输入
        self.name_layout = QHBoxLayout()

        self.name_label = QLabel("患者姓名:")
        self.name_label.setStyleSheet("font-size: 24px; color: black;")
        self.name_entry = QLineEdit()
        self.name_entry.setPlaceholderText("请输入您的姓名")
        self.name_entry.setStyleSheet("font-size: 24px; color: black;")
        self.name_layout.addWidget(self.name_label)
        self.name_layout.addWidget(self.name_entry)

        self.layout4.addLayout(self.name_layout)

        # 反馈内容输入
        self.feedback_layout = QVBoxLayout()

        self.feedback_label = QLabel("诊断意见:")
        self.feedback_label.setStyleSheet("font-size: 24px; color: black;")
        self.feedback_entry = QTextEdit()
        self.feedback_entry.setPlaceholderText("请输入您的反馈内容")
        self.feedback_entry.setStyleSheet("font-size: 24px; color: black;")
        self.feedback_layout.addWidget(self.feedback_label)
        self.feedback_layout.addWidget(self.feedback_entry)

        self.layout4.addLayout(self.feedback_layout)

        # 提交按钮
        self.submit_button = QPushButton("提交反馈")
        self.submit_button.setStyleSheet("")
        self.submit_button.setStyleSheet("""
            font-size: 26px;
            color: white;
            background-color: lightgreen;
            border-radius: 10px;
            padding: 10px;
        """)
        self.submit_button.clicked.connect(self.submit_feedback)
        self.layout4.addWidget(self.submit_button)
        
        # 设置第五个面板
        self.form5 = QWidget()
        self.background_label = QLabel(self.form5)
        self.background_label.setGeometry(0, 0, 1400, 965)  # 调整标签大小以覆盖整个窗口
        set_background(self.background_label)  # 将背景标签置于最底层
        self.layout5 = QVBoxLayout(self.form5)

        self.label6 = QLabel()
        self.label6.setText("基于多模型融合的心脏病风险预测系统")
        self.label6.setContentsMargins(15, 15, 15, 15)
        self.label6.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.label6.setAlignment(Qt.AlignCenter)
        self.label6.setFont(QFont("STKaiti", 25, QFont.Bold))
        self.layout5.addWidget(self.label6)

        # 创建用户列表
        self.user_table = QTableWidget(self)
        self.user_table.setColumnCount(5)  # 增加列数
        self.user_table.setHorizontalHeaderLabels(["患者ID", "患者姓名", "年龄", "性别", "症状"])
        # 设置表格的样式表以调整字体大小
        self.user_table.setStyleSheet("QTableWidget {font-size: 20px;}")

        # 设置列宽
        self.user_table.setColumnWidth(0, 100)  # 用户ID的列宽
        self.user_table.setColumnWidth(1, 200) # 用户名的列宽
        self.user_table.setColumnWidth(2, 100)  # 年龄的列宽
        self.user_table.setColumnWidth(3, 100)  # 性别的列宽
        self.user_table.setColumnWidth(4, 500) # 症状的列宽

#         self.populate_user_table(users)
        self.populate_user_table()
        self.layout5.addWidget(self.user_table)

        # 添加用户的部分
        self.add_user_layout = QHBoxLayout()

        self.add_user_label = QLabel("患者姓名:")
        self.add_user_label.setStyleSheet("font-size: 22px; color: black;")
        self.add_user_entry = QLineEdit()
        self.add_user_entry.setStyleSheet("font-size: 22px; color: black;")
        self.add_user_age_label = QLabel("年龄:")
        self.add_user_age_label.setStyleSheet("font-size: 22px; color: black;")
        self.add_user_age_entry = QLineEdit()
        self.add_user_age_entry.setStyleSheet("font-size: 22px; color: black;")
        self.add_user_gender_label = QLabel("性别:")
        self.add_user_gender_label.setStyleSheet("font-size: 22px; color: black;")
        self.add_user_gender_entry = QLineEdit()
        self.add_user_gender_entry.setStyleSheet("font-size: 22px; color: black;")
        self.add_user_symptoms_label = QLabel("症状:")
        self.add_user_symptoms_label.setStyleSheet("font-size: 22px; color: black;")
        self.add_user_symptoms_entry = QLineEdit()
        self.add_user_symptoms_entry.setStyleSheet("font-size: 22px; color: black;")

        self.add_user_button = QPushButton("添加患者")
        self.add_user_button.setStyleSheet("font-size: 22px; color: white; background-color: #ADD8E6;font-weight: bold;")
        self.add_user_button.clicked.connect(self.add_user)

        self.add_user_layout.addWidget(self.add_user_label)
        self.add_user_layout.addWidget(self.add_user_entry)
        self.add_user_layout.addWidget(self.add_user_age_label)
        self.add_user_layout.addWidget(self.add_user_age_entry)
        self.add_user_layout.addWidget(self.add_user_gender_label)
        self.add_user_layout.addWidget(self.add_user_gender_entry)
        self.add_user_layout.addWidget(self.add_user_symptoms_label)
        self.add_user_layout.addWidget(self.add_user_symptoms_entry)
        self.add_user_layout.addWidget(self.add_user_button)

        self.layout5.addLayout(self.add_user_layout)

        # 删除用户的部分
        self.delete_user_layout = QHBoxLayout()

        self.delete_user_label = QLabel("患者ID:")
        self.delete_user_label.setStyleSheet("font-size: 22px; color: black;")
        self.delete_user_entry = QLineEdit()
        self.delete_user_entry.setStyleSheet("font-size: 22px; color: black;")
        self.delete_user_button = QPushButton("删除患者")
        self.delete_user_button.setStyleSheet("font-size: 22px; color: white; background-color: #FF0000;font-weight: bold;")
        self.delete_user_button.clicked.connect(self.delete_user)

        self.delete_user_layout.addWidget(self.delete_user_label)
        self.delete_user_layout.addWidget(self.delete_user_entry)
        self.delete_user_layout.addWidget(self.delete_user_button)

        self.layout5.addLayout(self.delete_user_layout)
        
            # 修改用户的部分
        self.modify_user_layout = QHBoxLayout()

        self.modify_user_id_label = QLabel("患者ID:")
        self.modify_user_id_label.setStyleSheet("font-size: 22px; color: black;")
        self.modify_user_id_entry = QLineEdit()
        self.modify_user_id_entry.setStyleSheet("font-size: 22px; color: black;")

        self.modify_user_name_label = QLabel("患者姓名:")
        self.modify_user_name_label.setStyleSheet("font-size: 22px; color: black;")
        self.modify_user_name_entry = QLineEdit()
        self.modify_user_name_entry.setStyleSheet("font-size: 22px; color: black;")

        self.modify_user_age_label = QLabel("年龄:")
        self.modify_user_age_label.setStyleSheet("font-size: 22px; color: black;")
        self.modify_user_age_entry = QLineEdit()
        self.modify_user_age_entry.setStyleSheet("font-size: 22px; color: black;")

        self.modify_user_gender_label = QLabel("性别:")
        self.modify_user_gender_label.setStyleSheet("font-size: 22px; color: black;")
        self.modify_user_gender_entry = QLineEdit()
        self.modify_user_gender_entry.setStyleSheet("font-size: 22px; color: black;")

        self.modify_user_symptoms_label = QLabel("症状:")
        self.modify_user_symptoms_label.setStyleSheet("font-size: 22px; color: black;")
        self.modify_user_symptoms_entry = QLineEdit()
        self.modify_user_symptoms_entry.setStyleSheet("font-size: 22px; color: black;")

        self.modify_user_button = QPushButton("修改患者")
        self.modify_user_button.setStyleSheet("font-size: 22px; color: white; background-color: #90EE90;font-weight: bold;")
        self.modify_user_button.clicked.connect(self.modify_user)

        self.modify_user_layout.addWidget(self.modify_user_id_label)
        self.modify_user_layout.addWidget(self.modify_user_id_entry)
        self.modify_user_layout.addWidget(self.modify_user_name_label)
        self.modify_user_layout.addWidget(self.modify_user_name_entry)
        self.modify_user_layout.addWidget(self.modify_user_age_label)
        self.modify_user_layout.addWidget(self.modify_user_age_entry)
        self.modify_user_layout.addWidget(self.modify_user_gender_label)
        self.modify_user_layout.addWidget(self.modify_user_gender_entry)
        self.modify_user_layout.addWidget(self.modify_user_symptoms_label)
        self.modify_user_layout.addWidget(self.modify_user_symptoms_entry)
        self.modify_user_layout.addWidget(self.modify_user_button)

        self.layout5.addLayout(self.modify_user_layout)
        
        # 设置第五个面板
        self.form6 = QWidget()
        self.background_label = QLabel(self.form6)
        self.background_label.setGeometry(0, 0, 1400, 965)  # 调整标签大小以覆盖整个窗口
        set_background(self.background_label)  # 将背景标签置于最底层
        self.layout6 = QVBoxLayout(self.form6)

        self.label7 = QLabel()
        self.label7.setText("基于多模型融合的心脏病风险预测系统")
        self.label7.setContentsMargins(15, 15, 15, 15)
        self.label7.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.label7.setAlignment(Qt.AlignCenter)
        self.label7.setFont(QFont("STKaiti", 25, QFont.Bold))
        self.layout6.addWidget(self.label7)
        
        self.plot_button = QPushButton("更新数据可视化")
        self.plot_button.setStyleSheet("font-size: 22px; color: white; background-color: #ADD8E6;font-weight: bold;")
        self.plot_button.clicked.connect(self.update_plots)
        self.layout6.addWidget(self.plot_button)

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.layout6.addWidget(self.canvas)
        
        # 将三个面板，加入stackedWidget
        self.stackedWidget.addWidget(self.form1)
        self.stackedWidget.addWidget(self.form4)
        self.stackedWidget.addWidget(self.form5)
        self.stackedWidget.addWidget(self.form6)
        ###### 三个按钮事件 ######
        self.pushButton1.clicked.connect(self.on_pushButton1_clicked)
        self.pushButton4.clicked.connect(self.on_pushButton4_clicked)
        self.pushButton5.clicked.connect(self.on_pushButton5_clicked)
        self.pushButton6.clicked.connect(self.on_pushButton6_clicked)
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        plt.rcParams['font.sans-serif'] = ['SimHei'] 
        self.show()
    def modify_user(self):
        user_id = self.modify_user_id_entry.text()
        name = self.modify_user_name_entry.text()
        age = self.modify_user_age_entry.text()
        gender = self.modify_user_gender_entry.text()
        symptoms = self.modify_user_symptoms_entry.text()

        if not user_id:
            QMessageBox.warning(self, "输入错误", "患者ID不能为空！")
            return

        try:
            # 构建更新语句
            update_fields = []
            update_values = []

            if name:
                update_fields.append("name=%s")
                update_values.append(name)
            if age:
                update_fields.append("age=%s")
                update_values.append(age)
            if gender:
                update_fields.append("gender=%s")
                update_values.append(gender)
            if symptoms:
                update_fields.append("symptoms=%s")
                update_values.append(symptoms)

            if update_fields:
                update_values.append(user_id)  # 把 user_id 添加到参数列表的最后
                update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id=%s"
                self.db.execute(update_query, tuple(update_values))
                QMessageBox.information(self, "修改成功", "患者信息已成功修改。")
                self.populate_user_table()
            else:
                QMessageBox.warning(self, "输入错误", "至少要有一个字段进行修改！")

        except Exception as e:
            QMessageBox.critical(self, "修改失败", f"修改患者信息时发生错误: {e}")
        
    def load_excel(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "选择Excel文件", "", "Excel Files (*.xlsx *.xls);;All Files (*)", options=options)

        if file_name:
            self.df = pd.read_excel(file_name)
            self.comboBox.clear()
            self.comboBox.addItems([str(index) for index in self.df.index])
            
            # Update the loaded file label
            self.loaded_file_label.setText(f"已加载文件：{file_name}")
            self.person_information.setText("患者具体信息：")

    def update_display(self): 
        self.neicun = []
        selected_index = int(self.comboBox.currentText())
        selected_row = self.df.loc[selected_index]

        self.clear_form_layouts()

        column_count = len(selected_row)
        middle_index = column_count // 2
        for i, (column, value) in enumerate(selected_row.items()):
            label = QLabel(f"{column}:", self)
            data_label = QLabel(str(value), self)
            self.neicun.append(f"{column}:{value}")
            if i < middle_index:
                self.form_layout_left.addRow(label, data_label)
            else:
                self.form_layout_right.addRow(label, data_label)

        # Assume your model accepts the selected_row as features and returns a binary classification result
        prediction = self.model.predict([selected_row])[0]

        self.label_result.setText(f"预测结果: {'疑似有心脏病，具体请遵循医生意见！' if prediction >= 0.5 else '智能预测无心脏病风险，'}预测心脏病概率为：{prediction*100}%")
    
    def submit_feedback(self):
        name = self.name_entry.text()
        feedback = self.feedback_entry.toPlainText()

        if not name or not feedback:
            QMessageBox.warning(self, "输入错误", "姓名和反馈内容不能为空！")
            return
        
        doc = Document()
        doc.add_heading('诊断意见反馈文档', level=0)

        doc.add_heading('患者姓名:', level=1)
        doc.add_paragraph(name)

        doc.add_heading('指标数据:', level=1)
        if self.neicun!='':
            table = doc.add_table(rows=1, cols=2)
            table.style = 'Table Grid'  # 添加网格风格
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = '第一列'
            hdr_cells[1].text = '第二列'
            count = 0
            for item in self.neicun:
                if count == 0:
                    row_cells = table.add_row().cells
                row_cells[count].text = item
                count+=1
                count%=2
        else:
            doc.add_paragraph("无检测指标结果。")
        
        doc.add_heading('模型预测结果:', level=1)
        doc.add_paragraph(self.label_result.text())
        
        doc.add_heading('诊断意见:', level=1)
        doc.add_paragraph(feedback)

        # 保存文档
        file_path = f"{name}_意见.docx"
        doc.save(file_path)
        # 将数据插入到 diagnosis 表
        self.db.execute("INSERT INTO diagnosis (patient_name, feedback, date) VALUES (%s, %s, %s)",
                        (name, feedback, datetime.datetime.now()))
        # 通知用户文档已保存
        QMessageBox.information(self, "提交成功", f"您的反馈已保存至文档：{file_path}")
        
    def clear_form_layouts(self):
        self.clear_layout(self.form_layout_left)
        self.clear_layout(self.form_layout_right)

    def clear_layout(self, layout):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)
    def calculate(self):
        pass
    def update_output1(self):
        pass
    def generate_input_value1(self):
        pass
    # 定义一个槽函数，用于处理信号
    def update_output1_slot(self, input_value):
        pass
    def page2_button(self):
        pass
    def update_output2(self):
        pass
    def generate_input_value2(self):
        pass
    # 定义一个槽函数，用于处理信号
    def update_output2_slot(self, input_value):
        pass
    def page3_button(self):
        pass
    def update_output3(self):
        pass
    def generate_input_value3(self):
        pass
    # 定义一个槽函数，用于处理信号
    def update_output3_slot(self, input_value):
        pass
    def page4_button(self):
        pass
    def update_output4(self):
        pass
    def generate_input_value4(self):
        pass
    # 定义一个槽函数，用于处理信号
    def update_output4_slot(self, input_value):
        pass
    def page5_button(self):
        pass
    def update_output5(self):
        pass
    def generate_input_value5(self):
        pass
    # 定义一个槽函数，用于处理信号
    def update_output5_slot(self, input_value):
        pass
    def page6_button(self):
        pass
    def update_output6(self):
        pass
    def generate_input_value6(self):
        pass
    # 定义一个槽函数，用于处理信号
    def update_output6_slot(self, input_value):
        pass
    def on_pushButton1_clicked(self):
        self.stackedWidget.setCurrentIndex(0)
    def on_pushButton4_clicked(self):
        self.stackedWidget.setCurrentIndex(1)
    def on_pushButton5_clicked(self):
        self.stackedWidget.setCurrentIndex(2)
    def on_pushButton6_clicked(self):
        self.stackedWidget.setCurrentIndex(3)

    def update_plots(self):
        self.figure.clear()

        if hasattr(self, 'df'):
            # 第一类数据可视化：病症预测结果
            self.plot_disease_prediction()

        # 第二类数据可视化：诊断意见输出数量
        self.plot_diagnosis_outputs()

        # 第三类数据可视化：患者管理统计
        self.plot_patient_management()

        self.canvas.draw()

    def plot_disease_prediction(self):
        df = self.df.copy()
        df['prediction'] = self.model.predict(df)
        df['prediction'] = df['prediction'].apply(lambda x: '患病' if x >= 0.5 else '无风险')

        male = df[df['Gender'] == 0]['prediction'].value_counts()
        female = df[df['Gender'] == 1]['prediction'].value_counts()

        colors = ['#8da0cb', '#fc8d62']

        ax2 = self.figure.add_subplot(221)
        ax2.pie(male, labels=male.index, autopct='%1.1f%%', startangle=90, colors=colors)
        ax2.set_title('男性患病 vs 无风险')
        
        colors = ['#66c2a5', '#fc8d62']
        ax3 = self.figure.add_subplot(222)
        ax3.pie(female, labels=female.index, autopct='%1.1f%%', startangle=90, colors=colors)
        ax3.set_title('女性患病 vs 无风险')

    def plot_diagnosis_outputs(self):
        # Get today's date and the date 15 days ago
        today = datetime.datetime.now()
        start_date = today - datetime.timedelta(days=10)

        # Fetch data for the past 10 days
        query = """
        SELECT DATE(date) as diagnosis_date, COUNT(*) as count 
        FROM diagnosis 
        WHERE date >= %s AND date <= %s
        GROUP BY diagnosis_date
        ORDER BY diagnosis_date
        """
        outputs = self.db.fetchall(query, (start_date, today))

        # Create a dictionary to store counts for each date
        date_counts = {start_date + datetime.timedelta(days=i): 0 for i in range(10)}
        for row in outputs:
            date_counts[row['diagnosis_date']] = row['count']

        # Extract dates and counts for plotting
        dates = list(date_counts.keys())
        counts = list(date_counts.values())

        # Plotting the line chart in the specified subplot
        ax = self.figure.add_subplot(223)
        ax.plot(dates, counts, marker='o', linestyle='-', color='skyblue', linewidth=2, markersize=6)

        # Formatting the plot for better aesthetics
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.tick_params(axis='x', rotation=45)
        ax.set_xlabel('日期')
        ax.set_ylabel('诊断意见输出数量')
        ax.set_title('近十天诊断意见输出数量')
        ax.grid(True, linestyle='--', alpha=0.6)

        # Adjust layout for better fit
        self.figure.tight_layout()

    def plot_patient_management(self):
        # Get today's date and the date 15 days ago
        today = datetime.datetime.now()
        start_date = today - datetime.timedelta(days=10)

        new_patients_query = """
        SELECT DATE(created_at) as action_date, COUNT(*) as count 
        FROM users 
        WHERE created_at >= %s AND created_at <= %s
        GROUP BY action_date
        ORDER BY action_date
        """
        new_patients = self.db.fetchall(new_patients_query, (start_date, today))

        # Create a dictionary to store counts for each date
        date_counts_new = {start_date + datetime.timedelta(days=i): 0 for i in range(10)}

        for row in new_patients:
            date_counts_new[row['action_date']] = row['count']

        # Extract dates and counts for plotting
        dates = list(date_counts_new.keys())
        new_counts = list(date_counts_new.values())

        # Plotting the line chart in the specified subplot
        ax = self.figure.add_subplot(224)
        ax.plot(dates, new_counts, marker='o', linestyle='-', color='green', linewidth=2, markersize=6, label='新增患者')

        # Formatting the plot for better aesthetics
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.tick_params(axis='x', rotation=45)
        ax.set_xlabel('日期')
        ax.set_ylabel('新增患者数量')
        ax.set_title('近十天新增患者统计')
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend()

        # Adjust layout for better fit
        self.figure.tight_layout()
        
        
    def populate_user_table(self):
        users = self.db.fetchall("SELECT * FROM users")  # 每页显示20条记录
        self.user_table.setRowCount(len(users))
        for row, user in enumerate(users):
            self.user_table.setItem(row, 0, QTableWidgetItem(str(user["id"])))
            self.user_table.setItem(row, 1, QTableWidgetItem(user["name"]))
            self.user_table.setItem(row, 2, QTableWidgetItem(str(user["age"])))
            self.user_table.setItem(row, 3, QTableWidgetItem(user["gender"]))
            self.user_table.setItem(row, 4, QTableWidgetItem(user["symptoms"]))

    def add_user(self):
        username = self.add_user_entry.text()
        age = self.add_user_age_entry.text()
        gender = self.add_user_gender_entry.text()
        symptoms = self.add_user_symptoms_entry.text()
        self.db.execute("INSERT INTO users (name, age, gender, symptoms) VALUES (%s, %s, %s, %s)", (username, age, gender, symptoms))
        self.populate_user_table()

    def delete_user(self):
        user_id = int(self.delete_user_entry.text())
        self.db.execute("DELETE FROM users WHERE id = %s", (user_id,))
        self.populate_user_table()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont("STFangsong")
    app.setFont(font)
    window = ChurnPredictionApp()
    sys.exit(app.exec_())