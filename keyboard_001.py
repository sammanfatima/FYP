from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QTextEdit, QMessageBox, QFileDialog, QInputDialog,
    QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QShortcut, QDesktopWidget  #qshortcut keyborad shorcut #qpolicy how the button expand or shrink
)
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QIcon, QPixmap
import pyautogui
import screen_brightness_control as screen #show brightness of connected screen
import ctypes
import os

# Import voice module
from voicecommands import VoiceCommandSystem
from predictive_text import EyeTypingPredictor
from dictation import DictationThread

#import ui
from ui import AccessibilitySettings

class MyKeyboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.alphabet_button = []
        self.caps_on = False
        
        self.voice_thread = None
        self.voice_active = False
        
        # DistilGPT2 Model
        self.predictive_model = EyeTypingPredictor()
        
        # Dictation thread variable
        self.dictation_thread = None
        self.dictation_active = False

        self.setWindowTitle("OnScreen Keyboard")
        self.setGeometry(100, 100, 800, 400)
 

        self.setStyleSheet("""
            QMainWindow { background-color: #1c1c1e; }
            QTextEdit {
                background-color: #2c2c2e;
                border-radius: 28px; font-size: 20px; padding: 15px;
                border: none;
                
            }
            QPushButton {
                background-color: #3a3a3c; color: white;
                border-radius: 20px; font-size: 16px; font-weight: bold;
                min-height: 55px; border: 1px solid #555;
            }
            QPushButton:hover { background-color: #4a4a4c; }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        self.main_layout.setSpacing(8)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        text_container = QHBoxLayout()
        text_container.setSpacing(15)
        text_container.setContentsMargins(15, 10, 15, 10)
        #text area
        self.text_area = QTextEdit()
        self.text_area.setFixedHeight(70)  
        self.text_area.setStyleSheet("""
            QTextEdit {
                background-color: #2c2c2e;
                color: white;                    
                border: none;
                border-radius: 35px;
                padding: 0px 25px;               
                -size: 20px;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            QTextEdit::placeholder {
            color: #888888;                  
            font-size: 19px;
            }
            QTextEdit:focus {
               border: 3px solid #007AFF;       
               padding: 0px 22px;               
            }
        """)
        self.text_area.setPlaceholderText("Type a message")
        #self.text_area.setAlignment(Qt.AlignVCenter)  
        self.text_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_area.textChanged.connect(self.update_suggestions)
        self.main_layout.addWidget(self.text_area)
        
        #suggestion bar
        sug_layout = QHBoxLayout()
        sug_layout.addStretch()
        self.suggestion_buttons = []

        for _ in range(3):
            btn = QPushButton("")
            btn.setFixedSize(180, 62)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3a3a3c;
                    color: white;
                    border-radius: 31px;
                    font-size: 20px;
                    font-weight: bold;
                    border: 2px solid #555555;
                }
                QPushButton:hover {
                    background-color: #48484a;
                    border: 2px solid #666666;
                }
                QPushButton:pressed {
                    background-color: #2a2a2c;
                }
            """)
            btn.setVisible(False)
            btn.clicked.connect(lambda _, b=btn: self.insert_suggestion(b.text()))
            self.suggestion_buttons.append(btn)
            sug_layout.addWidget(btn)
            sug_layout.addSpacing(20)

        sug_layout.addStretch()
        self.main_layout.addLayout(sug_layout)
        
        
        
        voice_layout = QVBoxLayout()
        voice_layout.setSpacing(10)
        voice_layout.setAlignment(Qt.AlignVCenter)
        
        self.voice_btn = QPushButton("")
        self.voice_btn.setFixedSize(60, 60)
        self.voice_btn.setIcon(QIcon("mic.png"))
        self.voice_btn.setIconSize(QSize(36, 36))
        self.voice_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 25px;
                font-weight: bold;
                font-size: 20px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3e8e41; }
        """)
        self.voice_btn.clicked.connect(self.toggle_voice)

        #icon = QIcon("voice.png")
        self.mic_off_icon = QIcon("mic.png")
        self.mic_on_icon = QIcon("mic.png")
        self.voice_btn.setIcon(self.mic_off_icon)
        self.voice_btn.setIconSize(QSize(40, 40))
        
        # dictate button
        self.dictate_btn = QPushButton("Dictate")
        self.dictate_btn.setFixedSize(100, 60)
        self.dictate_btn.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2196F3, stop:1 #1976D2);
                color: white;
                border-radius: 29px;
                font-weight: bold;
                font-size: 15px;
                padding: 8px 16px;
            }
            QPushButton:hover { 
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #42A5F5, stop:1 #1E88E5);
            }
            QPushButton:pressed { 
                background-color: #1565C0;
                border: 3px solid #0D47A1; 
            }
        """)
        self.dictate_btn.clicked.connect(self.toggle_dictation)
        
        voice_layout.addWidget(self.voice_btn)
        voice_layout.addWidget(self.dictate_btn)
        
        # Add to main container
        text_container.addWidget(self.text_area, stretch=1)
        text_container.addLayout(voice_layout)
        self.main_layout.addLayout(text_container)

        self.create_keyboard_layout()
        self.create_action_buttons()
        self.create_shortcut_buttons()

        shortcut_print = QShortcut(QKeySequence("Ctrl+P"), self)
        shortcut_print.activated.connect(self.open_print_dialog)
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.center_window()
        
    def center_window(self):
        screen = QDesktopWidget().screenGeometry()
        window_size = self.frameGeometry()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        y = max(50, y - 80)  # Taskbar se safe distance
        self.move(x, y)    
        
        #make window always on top
        
        # screen_geometry = QDesktopWidget().availableGeometry() 
        # x = screen_geometry.width() - self.width() 
        # y = screen_geometry.height() - self.height() - 25  
        #self.move(x, y)
    
        

    def showEvent(self, event): 
        super().showEvent(event)
        self.set_no_activate()

    def set_no_activate(self):
        GWL_EXSTYLE = -20
        WS_EX_NOACTIVATE = 0x08000000
        hwnd = self.winId().__int__()
        exStyle = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, exStyle | WS_EX_NOACTIVATE)

    def create_keyboard_layout(self):
        self.caps_on = True
        self.alphabet_button = []
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)

        def make_button(key, width=60):
            btn = QPushButton(key)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            btn.setMinimumHeight(40)

            if key.isalpha():
                self.alphabet_button.append(btn)

            # Special keys handling
            action_map = {
                'esc': lambda: pyautogui.press('esc'),
                'Tab': self.handle_tab,
                'Caps Lock': self.handle_caps_lock,
                'Backspace': self.handle_backspace,
                'Select all': self.handle_select_all,
                'Print': lambda: pyautogui.hotkey('ctrl', 'p'),
                'Zoom In': lambda: self.text_area.zoomIn(4),         
                'Zoom Out': lambda: self.text_area.zoomOut(4),
                'Close Win': self.close_window,
                'Switch Win': self.switch_window,
                'Win Menu': self.window_menu,
                'Win': self.open_start_menu,
                'enter': self.handle_enter,
                'Space': lambda: self.handle_key_click(' ')
            }

            if key in action_map:
                #btn.clicked.connect(action_map[key])
                btn.clicked.connect(lambda checked=False: action_map[key]())
            else:
                btn.clicked.connect(lambda checked=False, k=key: self.handle_key_click(k))

            return btn

        rows = [
            (['esc', '1', '2', '3', '4', '5','6', '7', '8', '9', '0', 'Backspace'], [60]*11 + [90]),
            (['Tab','Q','W','E','R','T','Y','U','I','O','P','[',']','\\', '{', '}', '?', '<','>'], [60]*20),
            (['Caps Lock','A','S','D','F','G','H','J','K','L',';','\'','enter'], [90] + [60]*10 + [60, 90]),
            (['Print','Z','X','C','V','B','N','M',',','.','/','Select all'], [70] + [60]*9 + [90]),
            (['Zoom In','Win','Space','Zoom Out','Close Win','Switch Win', 'Win Menu'], [60, 60, 300, 80,80, 80, 90])
        ]

        for keys, widths in rows:
            hbox = QHBoxLayout()
            hbox.setSpacing(2)
            hbox.setContentsMargins(0, 0, 0, 0)
            for key, width in zip(keys, widths):
                hbox.addWidget(make_button(key, width))
            layout.addLayout(hbox)

        self.main_layout.addLayout(layout)

    def create_action_buttons(self):
        layout = QHBoxLayout()

        # Clear All
        btn_clr_all = QPushButton("Clear All")
        btn_clr_all.setFixedSize(120, 40)
        btn_clr_all.clicked.connect(self.handle_clr_all)
        layout.addWidget(btn_clr_all)

        # Volume buttons
        for label, key in [("Vol+", 'volumeup'), ("Vol-", 'volumedown'), ("Mute", 'volumemute')]:
            btn = QPushButton(label) #button creation
            btn.setFixedSize(100, 40)
            btn.clicked.connect(lambda _, k=key:    pyautogui.press(k))                
            layout.addWidget(btn)

        # Brightness buttons
        for label, value in [("Low Bright", 20), ("High Bright", 100)]:
            btn = QPushButton(label)
            btn.setFixedSize(100, 40)
            btn.clicked.connect(lambda _, v=value: screen.set_brightness(v))
            layout.addWidget(btn)

        # Power menu
        btn_power = QPushButton("Power")
        btn_power.setFixedSize(100, 40)
        btn_power.clicked.connect(self.show_power_options)
        layout.addWidget(btn_power)
        
        btn_access = QPushButton("Accessibility Menu")
        btn_access.setFixedSize(180, 60)
        btn_access.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8E44AD, stop:1 #9B59B6);
                color: white;
                border-radius: 30px;
                font-weight: bold;
                font-size: 15px;
                border: 4px solid #BBB;
            }
            QPushButton:hover {
                background: white;
                color: #8E44AD;
                border: 4px solid #8E44AD;
            }
        """)
        btn_access.clicked.connect(self.open_accessibility_menu)
        layout.addWidget(btn_access)

        self.main_layout.addLayout(layout)

    def create_shortcut_buttons(self):
        shortcuts = [
            ('Copy', lambda: pyautogui.hotkey('ctrl', 'c')),
            ('Paste', lambda: pyautogui.hotkey('ctrl', 'v')),  
            ('Cut', lambda: pyautogui.hotkey('ctrl', 'x')),
            ('Save', self.save_text),
            ('Undo', lambda: pyautogui.hotkey('ctrl', 'z')),
            ('Print', self.open_print_dialog),
            ('New Tab', lambda: pyautogui.hotkey('ctrl', 't')),
            ('Select all', self.select_all)
        ]

        layout = QHBoxLayout()
        layout.setSpacing(12)
        for name, func in shortcuts:
            button = QPushButton(name)
            button.setFixedSize(110, 55)
            # Beautiful gradient + modern look
            if name in ['Copy', 'Paste', 'Cut']:
                color = "#FF5722"  # Orange
            elif name in ['Save', 'Print']:
                color = "#9C27B0"  # Purple
            elif name == 'Undo':
                color = "#FF9800"  # Amber
            else:
                color = "#00BCD4"  # Cyan
                
            button.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {color}, stop:1 {color}DD);
                    color: white;
                    border-radius: 27px;
                    font-weight: bold;
                    font-size: 14px;
                    border: 2px solid #444;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 white, stop:1 {color});
                    color: #1c1c1e;
                    border: 2px solid white;
                }}
                QPushButton:pressed {{
                    background-color: #333;
                }}
            """)
            button.clicked.connect(func)
            layout.addWidget(button) 
               
        container = QHBoxLayout()
        container.addStretch()
        container.addLayout(layout)
        container.addStretch()
        self.main_layout.addLayout(container)
        

    def open_start_menu(self):
        pyautogui.press('win')

    def open_print_dialog(self): #open print setting window 
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted: #show dialog box on screen 
            self.text_area.print_(printer) #text in our text area start printing it

    def zoom_in(self):
        self.text_area.zoomIn(4)

    def zoom_out(self):
        self.text_area.zoomOut(4)

    def close_window(self):
        pyautogui.hotkey('alt', 'f4')

    def window_menu(self):
        pyautogui.hotkey('alt', 'space')

    def switch_window(self):
        pyautogui.hotkey('alt', 'tab')

    def select_all(self):
        pyautogui.hotkey('ctrl', 'a')

    def handle_key_click(self, key):
        if self.caps_on and key.isalpha():
            key = key.upper()
        elif not self.caps_on and key.isalpha():
            key = key.lower()
        pyautogui.press(key)
        self.text_area.insertPlainText(key) 

    def handle_backspace(self):
        cursor = self.text_area.textCursor()
        if cursor.position() > 0:
            cursor.deletePreviousChar()
            self.text_area.setTextCursor(cursor)
        pyautogui.press('backspace')

    def handle_enter(self):
        cursor = self.text_area.textCursor()
        cursor.insertText('\n')
        pyautogui.press('enter')

    def handle_tab(self):
        cursor = self.text_area.textCursor()
        cursor.insertText('\t')
        pyautogui.press('tab')

    def handle_caps_lock(self):
        self.caps_on = not self.caps_on
        for btn in self.alphabet_button:
            current_text = btn.text()
            btn.setText(current_text.upper() if self.caps_on else current_text.lower())

    def handle_clr_all(self):
        self.text_area.clear()

    def handle_select_all(self):
        self.text_area.selectAll()
        
    def update_suggestions(self):
        text = self.text_area.toPlainText().strip()
        if not text or text.endswith((" ", "\n", "\t")):
            for b in self.suggestion_buttons:
                b.setVisible(False)
            return
        current_word = text.split()[-1]
        suggestions = self.predictive_model.suggest_next_words(current_word)
        for i, btn in enumerate(self.suggestion_buttons):
            if i < len(suggestions):
                btn.setText(suggestions[i])
                btn.setVisible(True)
            else:
                btn.setVisible(False)
    
    def insert_suggestion(self, word):
        cursor = self.text_area.textCursor()
        cursor.movePosition(cursor.StartOfWord, cursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(word + " ")
        self.update_suggestions()

    def save_text(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Text", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.text_area.toPlainText())

    def show_power_options(self):
        options = {
            "Switch user": "tsdiscon",
            "Sign Out": "shutdown -l",
            "Sleep": "rundll32.exe powrprof.dll,SetSuspendState 0,1,0",
            "Shut Down": "shutdown /s /t 1",
            "Restart": "shutdown /r /t 1"
        }
        item, ok = QInputDialog.getItem(self, "Power Options", "Choose an option:", list(options.keys()), 0, False)
        if ok and item:
            os.system(options[item])
            
    def toggle_voice(self):
        if not self.voice_active:
            # start voice commands
            self.voice_thread = VoiceCommandSystem()
            self.voice_thread.signals.commandRecognized.connect(lambda cmd: print("Heard:", cmd))
            self.voice_thread.signals.actionExecuted.connect(lambda act: print("Action:", act))
            self.voice_thread.start()
            self.voice_btn.setIcon(self.mic_on_icon)
            self.voice_active = True
        else:
            if self.voice_thread:
                self.voice_thread.stop()
                self.voice_thread = None
            self.voice_btn.setIcon(self.mic_off_icon)
            self.voice_active = False   
            
    # toggle_dictation() 
    def toggle_dictation(self):
        if not self.dictation_active:
           self.dictation_thread = DictationThread()
           self.dictation_thread.text_recognized.connect(self.insert_dictation_text)
           self.dictation_thread.error_occurred.connect(lambda msg: print(msg))
           self.dictation_thread.start()
           
           self.dictate_btn.setText("Stop")
           self.dictate_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #f44336, stop:1 #d32f2f);
                    color: white;
                    border-radius: 29px;
                    font-weight: bold;A
                    font-size: 16px;
                    border: 4px solid #333;
                    padding: 8px 0px;                              
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #e53935, stop:1 #c62828);
                    border: 4px solid #ff5252;
                }
                QPushButton:pressed {
                    background: #c62828;
                    border: 4px solid #b71c1c;
                }                                 
            """)
           self.dictation_active = True
           print("Voice typing ON")
        else:
           if self.dictation_thread:
              self.dictation_thread.stop()
              self.dictation_thread = None
              
           self.dictate_btn.setText("Dictate")
           self.dictate_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                         stop:0 #2196F3, stop:1 #1976D2);
                    color: white;
                    border-radius: 29px;
                    font-weight: bold;
                    font-size: 15px;
                    border: 3px solid #333;
                    padding: 8px 0px;
                }
                QPushButton:hover{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #42A5F5, stop:1 #1E88E5);
                        border: 3px solid #555;
                }
                QPushButton:pressed {
                    background: #1565C0;
                    border: 3px solid #0D47A1; 
                }           
            """)
           self.dictation_active = False
           print("Voice typing OFF")

    def insert_dictation_text(self, text):
        self.text_area.insertPlainText(text)
        self.update_suggestions()  
        self.text_area.moveCursor(self.text_area.textCursor().End) 
        
    def open_accessibility_menu(self):
        
        self.access_ui = AccessibilitySettings(self)  
        self.access_ui.show()
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MyKeyboard()
    window.show()
    app.exec_()