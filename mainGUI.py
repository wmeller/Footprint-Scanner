"""
Footprint Scanner is designed to do VHF, UHF or total spectrum scans (VHF + UHF) in order to assist with a
full operational tactical picture in the EM spectrum
"""
"""
Dev Notes:
    2/14/2021: Initial GUI build. Script to call scan is rtl_power_script. Range of scanner 24 – 1766 MHz
"""
import sys, os.path
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QPushButton, QScrollArea, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QGroupBox, QFileDialog
from PyQt5.QtCore import Qt, QTimer
import datetime
import csv
import pickle
import pdb

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        #Main Layout creation, this is the sandbox
        print("Main layout creation")
        self.CentralWindow = QWidget()
        MainLayout = QVBoxLayout()
        MainLayout.addWidget(QLabel('Tactical Footprint Scanner'))

        #Add the main buttons. Lots of detail later.
        #UHF Button setup
        self.UHF_Button = QPushButton('UHF Scan')
        self.UHF_Button.connect.click(self.UHFScanMethod)

        #VHF Button setup
        self.VHF_Button = QPushButton('VHF Scan')
        self.VHF_Button.connect.click(self.VHFScanMethod)

        #Full Button setup
        self.Full_Button = QPushButton('Full Scan')
        self.Full_Button.connect.click(self.FullScanMethod)

        #Open the window and display the UI
        self.CentralWindow.setLayout(MainLayout)
        self.setCentralWidget(self.CentralWindow)
        self.setWindowTitle('Tactical Footprint Scanner')
        self.showMaximized()

    def UHFScanMethod(self):
        #Open a new window with immediate tactical info (Relative power level)

        #Keep scanning until the view is closed.
        pass

    def VHFScanMethod(self):
        #Open a new window with immediate tactical info (Relative power level)

        #Keep scanning until the view is closed.
        pass

    def FullScanMethod(self):
        #Open a new window with immediate tactical info (Relative power level)

        #Keep scanning until the view is closed.
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    #Start the application
    sys.exit(app.exec_())
