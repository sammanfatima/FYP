# voice_module.py
import threading
import speech_recognition as sr
import pyttsx3
import os
import webbrowser
import pyautogui
import pygetwindow as gw
from PyQt5.QtCore import QObject, pyqtSignal

class VoiceSignals(QObject):
    commandRecognized = pyqtSignal(str)
    actionExecuted = pyqtSignal(str)

class VoiceCommandSystem(threading.Thread):
    def __init__(self, lang="en"):
        super().__init__()
        self.signals = VoiceSignals()
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.running = True
        self.lang = lang

    def speak(self, text):
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception:
            pass

    def execute_command(self, command):
        command = command.lower()
        try:
            if "open chrome" in command:
                os.startfile("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
                self.signals.actionExecuted.emit("Opening Chrome")
                self.speak("Opening Chrome")
            elif "open youtube" in command:
                webbrowser.open("https://www.youtube.com")
                self.signals.actionExecuted.emit("Opening YouTube")
                self.speak("Opening YouTube")
            elif "open word" in command:
                os.startfile("C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE")
                self.signals.actionExecuted.emit("Opening Word")
                self.speak("Opening Word")
            elif "open powerpoint" in command:
                os.startfile("C:\\Program Files\\Microsoft Office\\root\\Office16\\POWERPNT.EXE")
                self.signals.actionExecuted.emit("Opening PowerPoint")
                self.speak("Opening PowerPoint")
            elif "open notepad" in command:
                os.startfile("notepad.exe")
                self.signals.actionExecuted.emit("Opening Notepad")
                self.speak("Opening Notepad")
            elif "close window" in command:
                win = gw.getActiveWindow()
                if win:
                    win.close()
                    self.signals.actionExecuted.emit("Closing current window")
                    self.speak("Closing window")
                else:
                    self.signals.actionExecuted.emit("No active window found")
                    self.speak("No window to close")
                    
            elif "minimize window" in command or "minimize" in command:
                pyautogui.hotkey("win", "down")
                self.signals.actionExecuted.emit("Minimizing window")
                self.speak("Window minimized")
                
            elif "maximize window" in command or "maximize" in command:
                pyautogui.hotkey("win", "up")
                self.signals.actionExecuted.emit("Maximizing window")
                self.speak("Window maximized")

            elif "select all" in command:
                pyautogui.hotkey("ctrl","a")
                self.signals.actionExecuted.emit("Select all text")
                self.speak("Select all text")
            else:
                self.signals.actionExecuted.emit("Command not recognized")
                self.speak("Sorry, I don't understand")
        except Exception as e:
            print("Error executing command:", e)

    def run(self):
        while self.running:
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source)
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    command = self.recognizer.recognize_google(audio)
                    self.signals.commandRecognized.emit(command)
                    self.execute_command(command)
            except:
                continue

    def stop(self):
        self.running = False
        try:
            self.engine.stop()
        except:
            pass
