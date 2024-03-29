import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QStackedLayout, QTextEdit, QSizePolicy, QLineEdit, QFormLayout, QDialog, QDialogButtonBox, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator, QDoubleValidator
import pickle
import os.path
from BinarySpectroViewer import *
from multiprocessing import set_start_method
from EARSscan import *
import EARSscan
from StreamSim import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib
matplotlib.use('Qt5Agg')


''' Let's set globals up here for any formatting that will be used across all pages'''
ButtonStyleSheet = """
                    QPushButton{ border-radius:8px;\
                            border: 1px solid;\
                            font-size: 20pt; font-weight: bold; \
                            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, \
                            stop: 0 #ccd9ff, stop: 1 #2b50bd); }\
                            QPushButton:pressed {background-color: #fae22d}

                    QPushButton:hover {
                            background-color: #C0C0C0; /* set the background color on hover */
                            border: 2px solid #fae22d; /* set the border on hover */
                            padding: 5px;}
                    """
BackButtonStyleSheet = """
                    QPushButton{font-size: 14pt; \
                        font-weight: bold; \
                        border: 2px solid gray; \
                        border-radius: 10px; \
                        background-color: white;}

                    QPushButton:hover {
                        background-color: #C0C0C0; /* set the background color on hover */
                            border: 2px solid #fae22d; /* set the border on hover */
                            padding: 5px;}
                    """
BackgroundStyle = "background-color: black;"
InputFieldStyleSheet = """ 
                    QLineEdit{ font: bold; \
                        font-size: 10pt; \
                        color: white; \
                        text-align: center;}

                    QLineEdit:hover { border: 2px solid #fae22d; }

                    QLineEdit:focus { border: 2px solid #2b50bd; }

                    QLineEdit:disabled { background-color: #444; }
                    """
LabelStyleSheet = '''
                    QLabel {
                        color: white;
                        font-size: 18px;
                        font-weight: bold;
                    }
                '''
SubPageHeaderStyleSheet = '''font-size: 15pt; font-weight: bold; color: white;'''
SubPageInfoStyleSheet = '''font-size: 10pt; font-weight: bold; color: white;'''

def convert_to_int(value):
    suffixes = {'K': 10**3, 'M': 10**6, 'G': 10**9}
    try:
        suffix = value[-1]
        number = float(value[:-1])
        if suffix in suffixes:
            return int(number * suffixes[suffix])
    except ValueError:
        pass
    raise ValueError("Invalid input")

class MainWidget(QMainWindow):
    def __init__(self, stackLayout):
        super().__init__()

    # Set up main window properties

        # changing the background color to black
        self.setStyleSheet(BackgroundStyle)

        # Set up central widget and layout
        self.central_widget = QWidget()
        self.central_layout = QHBoxLayout()
        self.central_widget.setLayout(self.central_layout)

        # Set up left widget and layout
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout()
        self.left_widget.setLayout(self.left_layout)

        # create buttons
        self.quick_scan_button = QPushButton('Quick Scan')
        self.toggle_scan_button = QPushButton('Toggle Scan')
        self.simulated_scan_button = QPushButton('Simulated Scan')
        self.calibration_button = QPushButton('Calibration')
        self.MainButtons = [self.quick_scan_button, self.toggle_scan_button, self.simulated_scan_button, self.calibration_button]

        for button in self.MainButtons:
            button.setFlat(True)
            button.setStyleSheet(ButtonStyleSheet)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Add buttons to left layout
        for button in self.MainButtons:
            self.left_layout.addWidget(button)

        # Set up right widget and layout
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout()
        self.right_widget.setLayout(self.right_layout)

        # Set up alerts/recent scans text area
        '''TODO: this is currently setup very generically as a textbox to be a placeholder,
        but this will need to be fully redone to actually display a list of recent scans that can be
        opened and viewed. Maybe someday have a sort of comparison feature for comparing scans'''
        self.alerts_text = QTextEdit()
        self.alerts_text.setReadOnly(True)
        self.alerts_text.setStyleSheet("border: 2px solid; border-radius: 10px; background-color: white;")
        self.alerts_header = QLabel("Recent Scans")
        self.alerts_header.setAlignment(Qt.AlignCenter)
        self.alerts_header.setStyleSheet("font-size: 20pt; font-weight: bold; color: white;")

        # Add alerts header and text to right layout
        self.right_layout.addWidget(self.alerts_header)
        self.right_layout.addWidget(self.alerts_text)

        # Add left and right widgets to central layout
        self.central_layout.addWidget(self.left_widget)
        self.central_layout.addWidget(self.right_widget)

        # Set the stretch factors of the left and right layouts within central layout so that they're equal width
        self.central_layout.setStretch(0, 1)
        self.central_layout.setStretch(1, 1)

        # Set central widget
        self.setCentralWidget(self.central_widget)

        # set connections for buttons
        self.quick_scan_button.clicked.connect(self.openQuickScanWidget)
        self.toggle_scan_button.clicked.connect(self.openToggleScanWidget)
        self.simulated_scan_button.clicked.connect(self.openSimulatedScanWidget)
        self.calibration_button.clicked.connect(self.calibrateMethod)

        # set stack layout
        self.stackLayout = stackLayout

    def openQuickScanWidget(self):
        self.quickScanWidget = QWidget()
        self.quickScanWidget.setStyleSheet(BackgroundStyle)
        self.quickScanLayout = QVBoxLayout()
        self.quickScanBackButton = QPushButton('Back')
        self.VHFButton = QPushButton('VHF')
        self.UHFButton = QPushButton('UHF')
        self.FullScanButton = QPushButton('Full Scan')
        self.GPSScanButton = QPushButton('GPS Scan')
        self.quickScanButtons = [self.VHFButton, self.UHFButton, self.FullScanButton, self.GPSScanButton]
        for button in self.quickScanButtons:
            button.setFlat(True)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            button.setStyleSheet(ButtonStyleSheet)
            self.quickScanLayout.addWidget(button)
        self.quickScanBackButton.setStyleSheet(BackButtonStyleSheet)
        self.quickScanLayout.addWidget(self.quickScanBackButton)
        self.quickScanWidget.setLayout(self.quickScanLayout)
        self.stackLayout.addWidget(self.quickScanWidget)
        self.stackLayout.setCurrentWidget(self.quickScanWidget)

        # set connections for buttons
        self.quickScanBackButton.clicked.connect(self.openMainWidget)
        self.VHFButton.clicked.connect(self.VHFScanMethod)
        self.UHFButton.clicked.connect(self.UHFScanMethod)
        self.FullScanButton.clicked.connect(self.FullScanMethod)
        self.GPSScanButton.clicked.connect(self.GPSScanMethod)

    def openToggleScanWidget(self):
        self.ToggleScanWidget = QWidget()
        self.ToggleScanWidget.setStyleSheet(BackgroundStyle)

        # Set up the central layout
        self.ToggleScanCentral_Layout = QVBoxLayout()

        # Add the header label
        self.ToggleScan_header = QLabel("Toggle Scan")
        self.ToggleScan_header.setAlignment(Qt.AlignCenter)
        self.ToggleScan_header.setStyleSheet(SubPageHeaderStyleSheet)
        self.ToggleScanCentral_Layout.addWidget(self.ToggleScan_header)

        # Add the input fields
        self.ToggleScanInputs_Layout = QHBoxLayout()
        self.ToggleScaninput_field1_Layout = QVBoxLayout()
        self.ToggleScaninput_label1 = QLabel("Min Frequency:")
        self.ToggleScaninput_label1.setStyleSheet(LabelStyleSheet)
        self.ToggleScaninput_label1.setAlignment(Qt.AlignCenter)
        self.ToggleScaninput_field1 = QLineEdit()
        self.ToggleScaninput_field1.setPlaceholderText("30M")
        self.ToggleScaninput_field1.setStyleSheet(InputFieldStyleSheet)
        self.ToggleScaninput_field1.setAlignment(Qt.AlignCenter)
        self.ToggleScaninput_field1.setFixedWidth(200)
        self.ToggleScaninput_field1.setFixedHeight(40)
        self.ToggleScaninput_field1.setFocusPolicy(Qt.ClickFocus | Qt.NoFocus)
        self.ToggleScaninput_field1_Layout.addWidget(self.ToggleScaninput_label1)
        self.ToggleScaninput_field1_Layout.addWidget(self.ToggleScaninput_field1, alignment=Qt.AlignCenter)

        self.ToggleScaninput_field2_Layout = QVBoxLayout()
        self.ToggleScaninput_label2 = QLabel("Max Frequency:")
        self.ToggleScaninput_label2.setStyleSheet(LabelStyleSheet)
        self.ToggleScaninput_label2.setAlignment(Qt.AlignCenter)
        self.ToggleScaninput_field2 = QLineEdit()
        self.ToggleScaninput_field2.setPlaceholderText("40M")
        self.ToggleScaninput_field2.setStyleSheet(InputFieldStyleSheet)
        self.ToggleScaninput_field2.setAlignment(Qt.AlignCenter)
        self.ToggleScaninput_field2.setFixedWidth(200)
        self.ToggleScaninput_field2.setFixedHeight(40)
        self.ToggleScaninput_field2.setFocusPolicy(Qt.ClickFocus | Qt.NoFocus)
        self.ToggleScaninput_field2_Layout.addWidget(self.ToggleScaninput_label2)
        self.ToggleScaninput_field2_Layout.addWidget(self.ToggleScaninput_field2, alignment=Qt.AlignCenter)

        self.ToggleScanInputs_Layout.addLayout(self.ToggleScaninput_field1_Layout)
        self.ToggleScanInputs_Layout.addLayout(self.ToggleScaninput_field2_Layout)
        self.ToggleScanCentral_Layout.addLayout(self.ToggleScanInputs_Layout)

        # Add the scan button
        self.ToggleScanScanButton = QPushButton('Scan')
        self.ToggleScanScanButton.setStyleSheet(ButtonStyleSheet)
        self.ToggleScanScanButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ToggleScanScanButton.setFixedHeight(60)
        self.ToggleScanCentral_Layout.addWidget(self.ToggleScanScanButton)

        # Add the info label
        self.ToggleScan_Info = QLabel("""This scan allows you to toggle the frequency range of the scan by choosing minumum and maximum frequency values. Please enter values in the format of 60M for 60 MHz.""")
        self.ToggleScan_Info.setAlignment(Qt.AlignCenter)
        self.ToggleScan_Info.setStyleSheet(SubPageInfoStyleSheet)
        self.ToggleScan_Info.setWordWrap(True)
        self.ToggleScan_Info.setFixedWidth(600)
        self.ToggleScanCentral_Layout.addWidget(self.ToggleScan_Info, alignment=Qt.AlignHCenter)

        # Add the back button
        self.toggleScanbackButton = QPushButton('Back')
        self.toggleScanbackButton.setStyleSheet(BackButtonStyleSheet)
        self.ToggleScanCentral_Layout.addWidget(self.toggleScanbackButton)

        # Set the layout for the ToggleScanWidget
        self.ToggleScanWidget.setLayout(self.ToggleScanCentral_Layout)

        # Add the ToggleScanWidget to the stack layout
        self.stackLayout.addWidget(self.ToggleScanWidget)
        self.stackLayout.setCurrentWidget(self.ToggleScanWidget)

        # Set connections for buttons
        self.toggleScanbackButton.clicked.connect(self.openMainWidget)
        self.ToggleScanScanButton.clicked.connect(self.toggleScanMethod)


    def openSimulatedScanWidget(self):
        self.simulatedScanWidget = QWidget()
        self.simulatedScanWidget.setStyleSheet(BackgroundStyle)
        self.simScanLayout = QVBoxLayout()
        self.simScanBackButton = QPushButton('Back')
        self.fixedFrequencyScanButton = QPushButton('Fixed Frequency Scan')
        self.frequencyHoppingScanButton = QPushButton('Frequency Hopping Scan')
        self.widebandTransmissionScanButton = QPushButton('Wideband Transmission Scan')
        self.simScanButtons = [self.fixedFrequencyScanButton, self.frequencyHoppingScanButton, self.widebandTransmissionScanButton]
        for button in self.simScanButtons:
            button.setFlat(True)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            button.setStyleSheet(ButtonStyleSheet)
            self.simScanLayout.addWidget(button)
        self.simScanBackButton.setStyleSheet(BackButtonStyleSheet)
        self.simScanLayout.addWidget(self.simScanBackButton)
        self.simulatedScanWidget.setLayout(self.simScanLayout)
        self.stackLayout.addWidget(self.simulatedScanWidget)
        self.stackLayout.setCurrentWidget(self.simulatedScanWidget)

        # set connections for buttons
        self.simScanBackButton.clicked.connect(self.openMainWidget)
        self.fixedFrequencyScanButton.clicked.connect(self.openFixedFreqWidget)
        self.frequencyHoppingScanButton.clicked.connect(self.openFreqHoppingWidget)
        self.widebandTransmissionScanButton.clicked.connect(self.openWidebandTransmissionWidget)

    def openFixedFreqWidget(self):
        self.FixFreqWidget = QWidget()
        self.FixFreqWidget.setStyleSheet(BackgroundStyle)

        # Set up the central layout
        self.FixFreqCentral_Layout = QVBoxLayout()

        # Add the header label
        self.FixFreq_header = QLabel("Fixed Frequency Simulation")
        self.FixFreq_header.setAlignment(Qt.AlignCenter)
        self.FixFreq_header.setStyleSheet(SubPageHeaderStyleSheet)
        self.FixFreqCentral_Layout.addWidget(self.FixFreq_header)

        # Add the input fields
        self.FixFreqInputs_Layout = QVBoxLayout()

        self.FixFreqInputsUpper_Layout = QHBoxLayout()
        self.FixFreqinput_field1_Layout = QVBoxLayout()
        self.FixFreqinput_label1 = QLabel("Transmission Frequency:")
        self.FixFreqinput_label1.setStyleSheet(LabelStyleSheet)
        self.FixFreqinput_label1.setAlignment(Qt.AlignCenter)
        self.FixFreqinput_field1 = QLineEdit()
        self.FixFreqinput_field1.setPlaceholderText("33 MHz")
        self.FixFreqinput_field1.setStyleSheet(InputFieldStyleSheet)
        self.FixFreqinput_field1.setAlignment(Qt.AlignCenter)
        self.FixFreqinput_field1.setFixedWidth(200)
        self.FixFreqinput_field1.setFixedHeight(40)
        self.FixFreqinput_field1.setFocusPolicy(Qt.ClickFocus | Qt.NoFocus)
        self.FixFreqinput_field1_Layout.addWidget(self.FixFreqinput_label1)
        self.FixFreqinput_field1_Layout.addWidget(self.FixFreqinput_field1, alignment=Qt.AlignCenter)

        self.FixFreqinput_field2_Layout = QVBoxLayout()
        self.FixFreqinput_label2 = QLabel("Transmission Power:")
        self.FixFreqinput_label2.setStyleSheet(LabelStyleSheet)
        self.FixFreqinput_label2.setAlignment(Qt.AlignCenter)
        self.FixFreqinput_field2 = QLineEdit()
        self.FixFreqinput_field2.setPlaceholderText("-30 dBm")
        self.FixFreqinput_field2.setStyleSheet(InputFieldStyleSheet)
        self.FixFreqinput_field2.setAlignment(Qt.AlignCenter)
        self.FixFreqinput_field2.setFixedWidth(200)
        self.FixFreqinput_field2.setFixedHeight(40)
        self.FixFreqinput_field2.setFocusPolicy(Qt.ClickFocus | Qt.NoFocus)
        self.FixFreqinput_field2_Layout.addWidget(self.FixFreqinput_label2)
        self.FixFreqinput_field2_Layout.addWidget(self.FixFreqinput_field2, alignment=Qt.AlignCenter)

        self.FixFreqInputsUpper_Layout.addLayout(self.FixFreqinput_field1_Layout)
        self.FixFreqInputsUpper_Layout.addLayout(self.FixFreqinput_field2_Layout)
        self.FixFreqInputs_Layout.addLayout(self.FixFreqInputsUpper_Layout)

        self.FixFreqInputsLower_Layout = QHBoxLayout()

        self.FixFreqinput_field3_Layout = QVBoxLayout()
        self.FixFreqinput_label3 = QLabel("Lower Frequency:")
        self.FixFreqinput_label3.setStyleSheet(LabelStyleSheet)
        self.FixFreqinput_label3.setAlignment(Qt.AlignCenter)
        self.FixFreqinput_field3 = QLineEdit()
        self.FixFreqinput_field3.setPlaceholderText("30 MHz")
        self.FixFreqinput_field3.setStyleSheet(InputFieldStyleSheet)
        self.FixFreqinput_field3.setAlignment(Qt.AlignCenter)
        self.FixFreqinput_field3.setFixedWidth(200)
        self.FixFreqinput_field3.setFixedHeight(40)
        self.FixFreqinput_field3.setFocusPolicy(Qt.ClickFocus | Qt.NoFocus)
        self.FixFreqinput_field3_Layout.addWidget(self.FixFreqinput_label3)
        self.FixFreqinput_field3_Layout.addWidget(self.FixFreqinput_field3, alignment=Qt.AlignCenter)

        self.FixFreqinput_field4_Layout = QVBoxLayout()
        self.FixFreqinput_label4 = QLabel("Upper Frequency:")
        self.FixFreqinput_label4.setStyleSheet(LabelStyleSheet)
        self.FixFreqinput_label4.setAlignment(Qt.AlignCenter)
        self.FixFreqinput_field4 = QLineEdit()
        self.FixFreqinput_field4.setPlaceholderText("35 MHz")
        self.FixFreqinput_field4.setStyleSheet(InputFieldStyleSheet)
        self.FixFreqinput_field4.setAlignment(Qt.AlignCenter)
        self.FixFreqinput_field4.setFixedWidth(200)
        self.FixFreqinput_field4.setFixedHeight(40)
        self.FixFreqinput_field4.setFocusPolicy(Qt.ClickFocus | Qt.NoFocus)
        self.FixFreqinput_field4_Layout.addWidget(self.FixFreqinput_label4)
        self.FixFreqinput_field4_Layout.addWidget(self.FixFreqinput_field4, alignment=Qt.AlignCenter)

        self.FixFreqInputsLower_Layout.addLayout(self.FixFreqinput_field3_Layout)
        self.FixFreqInputsLower_Layout.addLayout(self.FixFreqinput_field4_Layout)
        self.FixFreqInputs_Layout.addLayout(self.FixFreqInputsLower_Layout)

        self.FixFreqCentral_Layout.addLayout(self.FixFreqInputs_Layout)

        # Add the scan button
        self.FixFreqScanButton = QPushButton('Scan')
        self.FixFreqScanButton.setStyleSheet(ButtonStyleSheet)
        self.FixFreqScanButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.FixFreqScanButton.setFixedHeight(60)
        self.FixFreqCentral_Layout.addWidget(self.FixFreqScanButton)

        # Add the info label
        self.FixFreq_Info = QLabel("""This scan simulation generates a fixed frequency transmission with power centered on the selected frequency. The default behavior is to select a random center frequency and random power if values are left blank. Inputted frequencies must be between 5 MHz and 5 GHz. Inputted powers must be between -60 dBm and 30 dBm. Enter frequency in the form of 60M for 60 MHz. Enter power in the form of -30 for -30 dBm.""")
        self.FixFreq_Info.setAlignment(Qt.AlignCenter)
        self.FixFreq_Info.setStyleSheet(SubPageInfoStyleSheet)
        self.FixFreq_Info.setWordWrap(True)
        self.FixFreq_Info.setFixedWidth(750)
        self.FixFreqCentral_Layout.addWidget(self.FixFreq_Info, alignment=Qt.AlignHCenter)

        # Add the back button
        self.FixFreqBackButton = QPushButton('Back')
        self.FixFreqBackButton.setStyleSheet(BackButtonStyleSheet)
        self.FixFreqCentral_Layout.addWidget(self.FixFreqBackButton)

        # Set the layout for the FixFreqWidget
        self.FixFreqWidget.setLayout(self.FixFreqCentral_Layout)

        # Add the FixFreqWidget to the stack layout
        self.stackLayout.addWidget(self.FixFreqWidget)
        self.stackLayout.setCurrentWidget(self.FixFreqWidget)

        # Set connections for buttons
        self.FixFreqBackButton.clicked.connect(self.openSimulatedScanWidget)
        self.FixFreqScanButton.clicked.connect(self.fixedFrequencyScanMethod)

    def openFreqHoppingWidget(self):
        self.FreqHopWidget = QWidget()
        self.FreqHopWidget.setStyleSheet(BackgroundStyle)

        # Set up the central layout
        self.FreqHopCentral_Layout = QVBoxLayout()

        # Add the header label
        self.FreqHop_header = QLabel("Frequency Hopping\nSimulation")
        self.FreqHop_header.setAlignment(Qt.AlignCenter)
        self.FreqHop_header.setStyleSheet(SubPageHeaderStyleSheet)
        self.FreqHopCentral_Layout.addWidget(self.FreqHop_header)

        # Add the input fields
        self.FreqHopInputs_Layout = QVBoxLayout()
        self.FreqHopInputsUpper_Layout = QHBoxLayout()

        self.FreqHopinput_field1_Layout = QVBoxLayout()
        self.FreqHopinput_label1 = QLabel("Transmission Power:")
        self.FreqHopinput_label1.setStyleSheet(LabelStyleSheet)
        self.FreqHopinput_label1.setAlignment(Qt.AlignCenter)
        self.FreqHopinput_field1 = QLineEdit()
        self.FreqHopinput_field1.setPlaceholderText("-30 dBm")
        self.FreqHopinput_field1.setStyleSheet(InputFieldStyleSheet)
        self.FreqHopinput_field1.setAlignment(Qt.AlignCenter)
        self.FreqHopinput_field1.setFixedWidth(200)
        self.FreqHopinput_field1.setFixedHeight(40)
        self.FreqHopinput_field1.setFocusPolicy(Qt.ClickFocus | Qt.NoFocus)
        self.FreqHopinput_field1_Layout.addWidget(self.FreqHopinput_label1)
        self.FreqHopinput_field1_Layout.addWidget(self.FreqHopinput_field1, alignment=Qt.AlignCenter)

        self.FreqHopInputsUpper_Layout.addLayout(self.FreqHopinput_field1_Layout)

        self.FreqHopCentral_Layout.addLayout(self.FreqHopInputsUpper_Layout)

        self.FreqHopInputsLower_Layout = QHBoxLayout()
        self.FreqHopinput_field3_Layout = QVBoxLayout()
        self.FreqHopinput_label3 = QLabel("Lower Frequency:")
        self.FreqHopinput_label3.setStyleSheet(LabelStyleSheet)
        self.FreqHopinput_label3.setAlignment(Qt.AlignCenter)
        self.FreqHopinput_field3 = QLineEdit()
        self.FreqHopinput_field3.setPlaceholderText("30 MHz")
        self.FreqHopinput_field3.setStyleSheet(InputFieldStyleSheet)
        self.FreqHopinput_field3.setAlignment(Qt.AlignCenter)
        self.FreqHopinput_field3.setFixedWidth(200)
        self.FreqHopinput_field3.setFixedHeight(40)
        self.FreqHopinput_field3.setFocusPolicy(Qt.ClickFocus | Qt.NoFocus)
        self.FreqHopinput_field3_Layout.addWidget(self.FreqHopinput_label3)
        self.FreqHopinput_field3_Layout.addWidget(self.FreqHopinput_field3, alignment=Qt.AlignCenter)

        self.FreqHopinput_field4_Layout = QVBoxLayout()
        self.FreqHopinput_label4 = QLabel("Upper Frequency:")
        self.FreqHopinput_label4.setStyleSheet(LabelStyleSheet)
        self.FreqHopinput_label4.setAlignment(Qt.AlignCenter)
        self.FreqHopinput_field4 = QLineEdit()
        self.FreqHopinput_field4.setPlaceholderText("60 MHz")
        self.FreqHopinput_field4.setStyleSheet(InputFieldStyleSheet)
        self.FreqHopinput_field4.setAlignment(Qt.AlignCenter)
        self.FreqHopinput_field4.setFixedWidth(200)
        self.FreqHopinput_field4.setFixedHeight(40)
        self.FreqHopinput_field4.setFocusPolicy(Qt.ClickFocus | Qt.NoFocus)
        self.FreqHopinput_field4_Layout.addWidget(self.FreqHopinput_label4)
        self.FreqHopinput_field4_Layout.addWidget(self.FreqHopinput_field4, alignment=Qt.AlignCenter)

        self.FreqHopInputsLower_Layout.addLayout(self.FreqHopinput_field3_Layout)
        self.FreqHopInputsLower_Layout.addLayout(self.FreqHopinput_field4_Layout)

        self.FreqHopInputs_Layout.addLayout(self.FreqHopInputsLower_Layout)
        self.FreqHopCentral_Layout.addLayout(self.FreqHopInputs_Layout)


        # Add the scan button
        self.FreqHopScanButton = QPushButton('Scan')
        self.FreqHopScanButton.setStyleSheet(ButtonStyleSheet)
        self.FreqHopScanButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.FreqHopScanButton.setFixedHeight(60)
        self.FreqHopCentral_Layout.addWidget(self.FreqHopScanButton)

        # Add the info label
        self.FreqHop_Info = QLabel("""Generates a frequency hopping transmission simulation with the high power center moving to a new frequency every scan cycle. If no parameters are chosen then default values will be utilized. Power should be enterd in the form -30 for -30dBM and frequencies should be entered in the form of 30M for 30 MHz.""")
        self.FreqHop_Info.setAlignment(Qt.AlignCenter)
        self.FreqHop_Info.setStyleSheet(SubPageInfoStyleSheet)
        self.FreqHop_Info.setWordWrap(True)
        self.FreqHop_Info.setFixedWidth(750)
        self.FreqHopCentral_Layout.addWidget(self.FreqHop_Info, alignment=Qt.AlignHCenter)

        # Add the back button
        self.FreqHopBackButton = QPushButton('Back')
        self.FreqHopBackButton.setStyleSheet(BackButtonStyleSheet)
        self.FreqHopCentral_Layout.addWidget(self.FreqHopBackButton)

        # Set the layout for the FreqHopWidget
        self.FreqHopWidget.setLayout(self.FreqHopCentral_Layout)

        # Add the FreqHopWidget to the stack layout
        self.stackLayout.addWidget(self.FreqHopWidget)
        self.stackLayout.setCurrentWidget(self.FreqHopWidget)

        # Set connections for buttons
        self.FreqHopBackButton.clicked.connect(self.openSimulatedScanWidget)
        self.FreqHopScanButton.clicked.connect(self.frequencyHoppingScanMethod)

    def openWidebandTransmissionWidget(self):
        self.WidebandWidget = QWidget()
        self.WidebandWidget.setStyleSheet(BackgroundStyle)

        # Set up the central layout
        self.WidebandCentral_Layout = QVBoxLayout()

        # Add the header label
        self.Wideband_header = QLabel("Wideband Transmission\nSimulation")
        self.Wideband_header.setAlignment(Qt.AlignCenter)
        self.Wideband_header.setStyleSheet(SubPageHeaderStyleSheet)
        self.WidebandCentral_Layout.addWidget(self.Wideband_header)

        # Add the input fields
        self.WidebandInputs_Layout = QVBoxLayout()
        self.Widebandinput_field1_Layout = QVBoxLayout()
        self.Widebandinput_Upper_Layout = QHBoxLayout()
        self.Widebandinput_label1 = QLabel("Wideband Frequencies:")
        self.Widebandinput_label1.setStyleSheet(LabelStyleSheet)
        self.Widebandinput_label1.setAlignment(Qt.AlignCenter)
        self.Widebandinput_field1_Layout.addWidget(self.Widebandinput_label1)
        self.Widebandinput_field1_1 = QLineEdit()
        self.Widebandinput_field1_2 = QLineEdit()
        self.Widebandinput_field1_3 = QLineEdit()
        self.Widebandinput_field1_4 = QLineEdit()
        self.Widebandinput_fields = [self.Widebandinput_field1_1, self.Widebandinput_field1_2, self.Widebandinput_field1_3, self.Widebandinput_field1_4]
        for field in self.Widebandinput_fields:
            field.setStyleSheet(InputFieldStyleSheet)
            field.setAlignment(Qt.AlignCenter)
            field.setFixedWidth(150)
            field.setFixedHeight(40)
            field.setFocusPolicy(Qt.ClickFocus | Qt.NoFocus)
            self.Widebandinput_Upper_Layout.addWidget(field, alignment=Qt.AlignCenter)
        self.Widebandinput_field1_1.setPlaceholderText("31 MHz")
        self.Widebandinput_field1_2.setPlaceholderText("32 MHz")
        self.Widebandinput_field1_3.setPlaceholderText("33 MHz")
        self.Widebandinput_field1_4.setPlaceholderText("34 MHz")
        self.Widebandinput_field1_Layout.addLayout(self.Widebandinput_Upper_Layout)

        self.Widebandinput_Lower_Layout = QHBoxLayout()
        self.Widebandinput_field2_Layout = QVBoxLayout()
        self.Widebandinput_label2 = QLabel("Transmission Power:")
        self.Widebandinput_label2.setStyleSheet(LabelStyleSheet)
        self.Widebandinput_label2.setAlignment(Qt.AlignCenter)
        self.Widebandinput_field2 = QLineEdit()
        self.Widebandinput_field2.setPlaceholderText("-30 dBm")
        self.Widebandinput_field2.setStyleSheet(InputFieldStyleSheet)
        self.Widebandinput_field2.setAlignment(Qt.AlignCenter)
        self.Widebandinput_field2.setFixedWidth(200)
        self.Widebandinput_field2.setFixedHeight(40)
        self.Widebandinput_field2.setFocusPolicy(Qt.ClickFocus | Qt.NoFocus)
        self.Widebandinput_field2_Layout.addWidget(self.Widebandinput_label2)
        self.Widebandinput_field2_Layout.addWidget(self.Widebandinput_field2, alignment=Qt.AlignCenter)
        self.Widebandinput_Lower_Layout.addLayout(self.Widebandinput_field2_Layout)

        self.Widebandinput_field3_Layout = QVBoxLayout()
        self.Widebandinput_label3 = QLabel("Lower Frequency:")
        self.Widebandinput_label3.setStyleSheet(LabelStyleSheet)
        self.Widebandinput_label3.setAlignment(Qt.AlignCenter)
        self.Widebandinput_field3 = QLineEdit()
        self.Widebandinput_field3.setPlaceholderText("30 MHz")
        self.Widebandinput_field3.setStyleSheet(InputFieldStyleSheet)
        self.Widebandinput_field3.setAlignment(Qt.AlignCenter)
        self.Widebandinput_field3.setFixedWidth(200)
        self.Widebandinput_field3.setFixedHeight(40)
        self.Widebandinput_field3.setFocusPolicy(Qt.ClickFocus | Qt.NoFocus)
        self.Widebandinput_field3_Layout.addWidget(self.Widebandinput_label3)
        self.Widebandinput_field3_Layout.addWidget(self.Widebandinput_field3, alignment=Qt.AlignCenter)
        self.Widebandinput_Lower_Layout.addLayout(self.Widebandinput_field3_Layout)

        self.Widebandinput_field4_Layout = QVBoxLayout()
        self.Widebandinput_label4 = QLabel("Upper Frequency:")
        self.Widebandinput_label4.setStyleSheet(LabelStyleSheet)
        self.Widebandinput_label4.setAlignment(Qt.AlignCenter)
        self.Widebandinput_field4 = QLineEdit()
        self.Widebandinput_field4.setPlaceholderText("35 MHz")
        self.Widebandinput_field4.setStyleSheet(InputFieldStyleSheet)
        self.Widebandinput_field4.setAlignment(Qt.AlignCenter)
        self.Widebandinput_field4.setFixedWidth(200)
        self.Widebandinput_field4.setFixedHeight(40)
        self.Widebandinput_field4.setFocusPolicy(Qt.ClickFocus | Qt.NoFocus)
        self.Widebandinput_field4_Layout.addWidget(self.Widebandinput_label4)
        self.Widebandinput_field4_Layout.addWidget(self.Widebandinput_field4, alignment=Qt.AlignCenter)
        self.Widebandinput_Lower_Layout.addLayout(self.Widebandinput_field4_Layout)

        self.WidebandInputs_Layout.addLayout(self.Widebandinput_field1_Layout)
        self.WidebandInputs_Layout.addLayout(self.Widebandinput_Lower_Layout)
        self.WidebandCentral_Layout.addLayout(self.WidebandInputs_Layout)

        # Add the scan button
        self.WidebandScanButton = QPushButton('Scan')
        self.WidebandScanButton.setStyleSheet(ButtonStyleSheet)
        self.WidebandScanButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.WidebandScanButton.setFixedHeight(60)
        self.WidebandCentral_Layout.addWidget(self.WidebandScanButton)

        # Add the info label
        self.Wideband_Info = QLabel("""Generates wideband transmission simulation with 4 channels centered at selected frequencies with selected center power. The default behavior is to select 4 random center frequencies between 5M to 5G at randomly selected center powers.""")
        self.Wideband_Info.setAlignment(Qt.AlignCenter)
        self.Wideband_Info.setStyleSheet(SubPageInfoStyleSheet)
        self.Wideband_Info.setWordWrap(True)
        self.Wideband_Info.setFixedWidth(750)
        self.WidebandCentral_Layout.addWidget(self.Wideband_Info, alignment=Qt.AlignHCenter)

        # Add the back button
        self.WidebandBackButton = QPushButton('Back')
        self.WidebandBackButton.setStyleSheet(BackButtonStyleSheet)
        self.WidebandCentral_Layout.addWidget(self.WidebandBackButton)

        # Set the layout for the WidebandWidget
        self.WidebandWidget.setLayout(self.WidebandCentral_Layout)

        # Add the WidebandWidget to the stack layout
        self.stackLayout.addWidget(self.WidebandWidget)
        self.stackLayout.setCurrentWidget(self.WidebandWidget)

        # Set connections for buttons
        self.WidebandBackButton.clicked.connect(self.openSimulatedScanWidget)
        self.WidebandScanButton.clicked.connect(self.widebandTransmissionScanMethod)

    def openPlottingWidget(self, cmdFreqs, simFlag, simConfig):
        # Set up the plotting widget
        self.plottingWidget = QWidget()
        self.plottingWidget.setStyleSheet(BackgroundStyle)
        self.plottingLayout = QVBoxLayout()

        print('Initializing scan...')
        matplotlib.pyplot.style.use('dark_background')

        # Start the first scan so there is data in the pipe
        self.initScanMethod()

        # Show the scan Data
        self.powerGraph = MplCanvas(self)
        self.axesRef = self.powerGraph.figure.axes[0]
        self.powerGraph.figure.tight_layout()
        self.updateCount = 0
        
        # call the update event This drives both the scanning calls and the graph updating
        # Set up the update function
        self.updateTimer = QTimer()
        self.updateTimer.timeout.connect(self.updateMethod)
        #Update interval is set in milliseconds
        self.updateTimer.setInterval(1000)
        self.updateTimer.start()
        #Start software bus queue
        self.SWBQueue = Queue(25)
        # Add the graph widget which shows the moving average of the power, in decibels, of the band.
        self.plottingLayout.addWidget(self.powerGraph)
        #Add a loading message to the power graph
        self.axesRef.text(0.05, .95, 'Loading data...')
        #Start the hardware scanning process
        self.hwScanProcess = Process(target=streamScan, args = (cmdFreqs, self.SWBQueue, simFlag, simConfig))
        self.hwScanProcess.start()

        # Close Button setup
        self.Close_Button = QPushButton('End Scan')
        self.Close_Button.setStyleSheet(BackButtonStyleSheet)
        self.Close_Button.clicked.connect(self.close)
        self.Close_Button.clicked.connect(self.openMainWidget)
        self.plottingLayout.addWidget(self.Close_Button)
        #Final setup for the plotting widget
        self.plottingWidget.setLayout(self.plottingLayout)
        self.stackLayout.addWidget(self.plottingWidget)
        self.stackLayout.setCurrentWidget(self.plottingWidget)

        simConfigObj.clear(self)

    # All the the necessary items from old EARSscan will be here

    class MplCanvas(FigureCanvasQTAgg):
        #This is a class for setting up the embedded matplotlib figure
        def __init__(self, parent=None, width=5, height=4, dpi=100):
            fig = Figure(figsize=(width, height), dpi=dpi)
            self.axes = fig.add_subplot(111)
            super(MplCanvas, self).__init__(fig)

    def initScanMethod(self):
        # we have not started the first scan. Build the Command
        #Return True if the method completed without issues. Return False if there were errors.
        # configDict has keys title, minFreq, maxFreq, binSize, interval, exitTimer
        pass

    def updateMethod(self):

        #check for an update in the queue
        if not self.SWBQueue.empty():
            self.updateCount += 1
            #Got data in the queue
            df, maxDF, baseline = self.SWBQueue.get()
            #Clear axes
            self.axesRef.cla()
            #Add time and number of updates annotation
            curTime = datetime.datetime.now().strftime("%Y:%m:%d:%H:%M:%S")
            curTimeUpdateText = 'Last update: ' + curTime
            curUpdateText = 'Number of scans: ' + str(self.updateCount)
            print(curUpdateText)
            print(curTimeUpdateText)
            self.axesRef.text(0.05, .95, curTimeUpdateText)
            self.axesRef.text(0.05, .90, curUpdateText)
            #Plot our data
            maxDF.plot(ax=self.axesRef, x='freqCompare', y='power', style='y', linewidth = .5, label='max hold', grid='On', title = 'ScanView')
            df.plot(ax=self.axesRef, x='frequency', y='power', grid='On', title = 'ScanView', label='current', alpha = .7, linewidth = .5)
            self.axesRef.fill_between(df['frequency'], df['power'], df['power'].min(), alpha = .5)
            baseline.plot(ax=self.axesRef, x='frequency', y='power', style='r-.', linewidth=.5, alpha = .7, label = 'baseline')
            
            #Draw and allow matplotlib to do plot update
            self.powerGraph.draw()
            matplotlib.pyplot.pause(.05)

    def updatePlot(self):
        #Read in all the new data
        pass

    def closeEvent(self, event):
        # Make sure we are gracefully ending the scan and not just leaving the process running in the background.
        # This would probably cause problems if the user then immediately tried to start another scan.
        print('gracefully closing...')
        while not self.SWBQueue.empty():
            print('Flushing queue...')
            #Ensure the queue is empty before sending the command. 
            #This ensures that this is the next item in the queue when the hw process looks.
            flushVar = self.SWBQueue.get()
        self.SWBQueue.put('QUIT')
        print('Closed the SWB Queue and hardware process.')
        #self.hwScanProcess.join()
        self.SWBQueue.get(block=True, timeout=300)
        self.SWBQueue.close()
        self.hwScanProcess.terminate()
        print('Closed scan and queue')
        self.updateTimer.stop()
        event.accept()

    '''TODO: Need to figure out how errors and updates will be handled with new button scheme
    whether with popups or integrating alert section into pages'''
    
    def openMainWidget(self):
        self.stackLayout.setCurrentWidget(self)

    def VHFScanMethod(self):
        cmdFreq = '30M:50M'
        self.openPlottingWidget(cmdFreq, False, None)

    def UHFScanMethod(self):
        cmdFreq = '225M:400M'
        self.openPlottingWidget(cmdFreq, False, None)

    def FullScanMethod(self):
        cmdFreq = '30M:1.7G'
        self.openPlottingWidget(cmdFreq, False, None)

    def GPSScanMethod(self):
        cmdFreq = '1227590000:1227610000'
        self.openPlottingWidget(cmdFreq, False, None)

    def toggleScanMethod(self):
        ToggleScan_starting_freq = self.ToggleScaninput_field1.text()
        ToggleScan_ending_freq = self.ToggleScaninput_field2.text()
        cmdFreq = ToggleScan_starting_freq + ":" + ToggleScan_ending_freq

        if ToggleScan_starting_freq == "" and ToggleScan_ending_freq == "":
            cmdFreq = '30M:40M'

        elif ToggleScan_starting_freq == "":
            cmdFreq = '30M:' + ToggleScan_ending_freq

        elif ToggleScan_ending_freq == "":
            cmdFreq = ToggleScan_starting_freq + ':40M'

        else: 
            cmdFreq = ToggleScan_starting_freq + ":" + ToggleScan_ending_freq

        self.openPlottingWidget(cmdFreq, False, None)
    
    def fixedFrequencyScanMethod(self):
        if self.FixFreqinput_field1.text() == "":
            selectedFreq = 33_000_000
        else:
            selectedFreq = convert_to_int(self.FixFreqinput_field1.text())
        
        
        FixFreq_starting_freq = self.FixFreqinput_field3.text()
        FixFreq_ending_freq = self.FixFreqinput_field4.text()

        if FixFreq_starting_freq == "" and FixFreq_ending_freq == "":
            cmdFreq = '30M:35M'

        elif FixFreq_starting_freq == "":
            cmdFreq = '30M:' + FixFreq_ending_freq

        elif FixFreq_ending_freq == "":
            cmdFreq = FixFreq_starting_freq + ':35M'

        else: 
            cmdFreq = FixFreq_starting_freq + ":" + FixFreq_ending_freq

        if self.FixFreqinput_field2.text() == "":
            peakPower = -30
        else:
            peakPower = int(self.FixFreqinput_field2.text())

        simConfig = simConfigObj()
        simConfig.snr = 10
        simConfig.peakPower = peakPower
        simConfig.scanType = 'fixedFreq'
        simConfig.selectedFreq = selectedFreq

        self.openPlottingWidget(cmdFreq, True, simConfig)

    
    def frequencyHoppingScanMethod(self):
        if self.FreqHopinput_field1.text() == "":
            peakPower = -30
        else:
            peakPower = int(self.FreqHopinput_field1.text())

        freqHop_starting_freq = self.FreqHopinput_field3.text()
        freqHop_ending_freq = self.FreqHopinput_field4.text()
        
        if freqHop_starting_freq == "" and freqHop_ending_freq == "":
            cmdFreq = '30M:60M'

        elif freqHop_starting_freq == "":
            cmdFreq = '30M:' + freqHop_ending_freq

        elif freqHop_ending_freq == "":
            cmdFreq = freqHop_starting_freq + ':60M'

        else: 
            cmdFreq = freqHop_starting_freq + ":" + freqHop_ending_freq

        simConfig = simConfigObj()
        simConfig.snr = 10
        simConfig.peakPower = peakPower
        simConfig.scanType = 'freqHopping'

        self.openPlottingWidget(cmdFreq, True, simConfig)
        
    
    def widebandTransmissionScanMethod(self):
        simConfig = simConfigObj()
        if (self.Widebandinput_field1_1.text() == "") or (self.Widebandinput_field1_2.text() == "") or (self.Widebandinput_field1_3.text() == "") or (self.Widebandinput_field1_4.text() == ""):
            simConfig.selectedFreq1 = 31_000_000
            simConfig.selectedFreq2 = 32_000_000
            simConfig.selectedFreq3 = 33_000_000
            simConfig.selectedFreq4 = 34_000_000
        else:
            simConfig.selectedFreq1 = convert_to_int(self.Widebandinput_field1_1.text())
            simConfig.selectedFreq2 = convert_to_int(self.Widebandinput_field1_2.text())
            simConfig.selectedFreq3 = convert_to_int(self.Widebandinput_field1_3.text())
            simConfig.selectedFreq4 = convert_to_int(self.Widebandinput_field1_4.text())

        if self.Widebandinput_field2.text() == "":
            peakPower = -30
        else:
            peakPower = int(self.Widebandinput_field2.text())
        
        WB_starting_freq = self.Widebandinput_field3.text()
        WB_ending_freq = self.Widebandinput_field4.text()
        
        if WB_starting_freq == "" and WB_ending_freq == "":
            cmdFreq = '30M:35M'

        elif WB_starting_freq == "":
            cmdFreq = '30M:' + WB_ending_freq

        elif WB_ending_freq == "":
            cmdFreq = WB_starting_freq + ':35M'

        else: 
            cmdFreq = WB_starting_freq + ":" + WB_ending_freq

        simConfig.snr = 10
        simConfig.peakPower = peakPower
        simConfig.scanType = 'widebandFreq'


        self.openPlottingWidget(cmdFreq, True, simConfig)

    def calibrateMethod(self):
        '''TODO: This should be revisited in the case we want to handle the calibration method 
        differently with respect to the GUI layout. Particularly if we change how we build the pages
        for data visualization'''

        '''
        The calibration method scans the environment across the entire UHF and VHF
        frequency ranges. It returns the median power received across the frequency bands
        for each band, in dB. The difference between this value and the filtered value
        will later be used to determine whether anything unexpected is happening
        in the spectrum.

        'rtl_power_fftw -f 30M:1.7G -b 500 -n 500 -g 100 -q'
        frequency range is from 30 MHz to 1.7 GHz. 
        Each fft bin is sampled 500 times.
        '''
        #This takes forever, so Popup a message that the cal is starting.
        print("starting Calibration")
        self.msgBox = QMessageBox()
        self.msgBox.setWindowTitle('Calibrating')
        self.msgBox.setIcon(QMessageBox.Information)
        self.msgBox.setText("Calibrating system...\nThis typically takes several minutes")
        self.msgBox.setStandardButtons(QMessageBox.Ok)
        self.statusBar().showMessage('Calibrating')
        self.msgBox.exec()

        if takeBaselineMeasurement() == 'Error':
            self.msgBox.close()
            self.msgBox = QMessageBox()
            self.msgBox.setWindowTitle('Error!')
            self.msgBox.setIcon(QMessageBox.Information)
            self.msgBox.setText("Failed to Calibrate System\nCheck hardware connections")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.statusBar().showMessage('Error Calibrating')
            self.msgBox.exec()
        else:
            self.msgBox.close()
            #Popup a message that the cal was successful.
            print("succesfully performed Calibration")
            self.msgBox = QMessageBox()
            self.msgBox.setWindowTitle('Sucess!')
            self.msgBox.setIcon(QMessageBox.Information)
            self.msgBox.setText("Successfully Calibrated System")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.statusBar().showMessage('Done Calibrating')
            self.msgBox.exec()

class simConfigObj():
    '''
    The simconfig object will always have all the attributes for all the scan types, which should all default
    to None. We will only populate and use the appropriate attributes.

    Ensure this is cleared after each scan completes so that we aren't douple populating this object.

    scanType can be either fixedFreq, widebandFreq or freqHopping
    '''
    def __init__(self):
        #Common attributes
        self.scanType = None
        self.snr = None 
        self.peakPower = None

        #List of fixed freq scan attributes
        self.selectedFreq = None
        
        #List of frequency hopping scan attributes
        self.hopDuration = None

        #List of wideband scan attributes
        self.selectedFreq1 = None
        self.selectedFreq2 = None
        self.selectedFreq3 = None
        self.selectedFreq4 = None

    def clear(self):
        #Common attributes
        self.scanType = None
        self.snr = None 
        self.peakPower = None

        #List of fixed freq scan attributes
        self.selectedFreq = None
        
        #List of frequency hopping scan attributes
        self.hopDuration = None

        #List of wideband scan attributes
        self.selectedFreq1 = None
        self.selectedFreq2 = None
        self.selectedFreq3 = None
        self.selectedFreq4 = None


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # create stacked layout
        self.stackLayout = QStackedLayout()

        # create main widget
        self.mainWidget = MainWidget(self.stackLayout)

        # add widgets to stacked layout
        self.stackLayout.addWidget(self.mainWidget)

        # set layout
        self.setLayout(self.stackLayout)

        self.setWindowTitle('Tactical Footprint Scanner')
        #self.showMaximized()
        self.resize(800, 480)  # Replace the width and height values for testing what GUI looks like on PI screen



if __name__ == '__main__':
    #Global multiprocessing setup, needs to be set at the start of the context definition
    #This line is required for multiprocessing on linux specifically due to a nuance in 
    #how the new processes are generated. Without it, calling bound C code (which we use
    # in pytables) will get deadlocked.
    set_start_method("spawn")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())



