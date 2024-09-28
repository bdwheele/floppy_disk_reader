#!/bin/env python3

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from pathlib import Path
import re
import signal
import sys
import time
import csv

FLUXENGINE = "./fluxengine.fedora40"


def main():
    app = QApplication(sys.argv)
    window = MainWindow()    
    window.show()
    signal.signal(signal.SIGINT, lambda signal, handler: app.quit())
    exit(app.exec())


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Amiga Disk Reader")
        layout = QGridLayout()
        layout.addWidget(QLabel(text="Destination Directory"), 0, 0)
        self.destination_dir = QPushButton(text="Unset")
        self.destination_dir.pressed.connect(self.set_destination)
        self.destination_dir.real_path = None
        layout.addWidget(self.destination_dir, 0, 1, 1, -1)

        layout.addWidget(QLabel(text="Disk Name"), 1, 0)
        self.disk_name = QLineEdit()
        self.disk_name.textChanged.connect(self.name_changed)
        layout.addWidget(self.disk_name, 1, 1, 1, -1)

        self.test_button = QPushButton(text="Test Device")
        self.test_button.pressed.connect(self.test_device)
        layout.addWidget(self.test_button, 2, 0)
        
        self.read_button = QPushButton(text="Read Disk")
        self.read_button.pressed.connect(self.read_disk)
        self.read_button.setEnabled(False)
        layout.addWidget(self.read_button, 2, 2)

        self.terminal = QPlainTextEdit()
        self.terminal.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.terminal.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        courier = QFont("courier", 10)
        metrics = QFontMetrics(courier)
        self.terminal.setFont(courier)
        self.terminal.setReadOnly(True)
        self.terminal.setLineWidth(86)
        self.terminal.setFixedWidth(86 * metrics.averageCharWidth())
        layout.addWidget(self.terminal, 3, 0, 1, -1)

        self.progress = QProgressBar()
        self.progress.setRange(0, 160)
        self.progress.setValue(0)
        layout.addWidget(self.progress, 4, 0, 1, -1)
        self.setLayout(layout)
        
        self.process = None
        self.stdout = ""
        self.stderr = ""
        self.process_callback = None
        self.process_rc = 0
        

    def closeEvent(self, event: QEvent):
        if self.process:
            print(f"Closing down {self.process.state}")
            self.process.terminate()            
            self.process.waitForFinished()            
        event.accept()


    def log(self, message, error=False):
        """Log a message to the terminal"""
        message = message.replace("&", "&amp;")
        message = message.replace("<", "&lt;")
        message = message.replace(">", "&gt;")
        if error:
            self.terminal.appendHtml(f'<pre style="color:red">{message}</pre>')
        else:
            self.terminal.appendHtml(f'<pre style="color:black">{message}</pre>')
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        self.terminal.setTextCursor(cursor)        


    def set_destination(self):
        """Set the destination and update the read button status"""        
        dirname = QFileDialog.getExistingDirectory(self, caption="Image Destination Directory")
        if dirname:
            self.destination_dir.real_path = dirname
            self.destination_dir.setText(Path(dirname).name)
            self.log(f"Setting destination directory to: {self.destination_dir.real_path}")
        self.read_button.setEnabled(self.is_valid_destination())
        

    def name_changed(self):
        """When the text has changed, update the read buttons status"""
        self.read_button.setEnabled(self.is_valid_destination())

    def test_device(self):
        """Just check connectivity with the greaseweazle"""
        self.run_command(FLUXENGINE, "test", "devices")


    def read_disk(self):
        """Read the disk sectors and a csv file for information"""
        base_name = Path(self.destination_dir.real_path, 
                         self.disk_name.text())
        image_name = base_name.with_suffix(".adf")
        csv_name = base_name.with_suffix(".csv")

        if image_name.exists():
            reply = QMessageBox()            
            reply.setWindowTitle("Ovewrite Disk Image?")
            reply.setText(f"The disk image {image_name} already exists.\nOverwrite it?")
            reply.setStandardButtons(QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No)
            x = reply.exec()
            if x == QMessageBox.StandardButton.No:
                return


        self.process_callback = lambda: self.post_read_disk(csv_name)
        self.run_command(FLUXENGINE, "read", "amiga", "-s", "drive:0", "-o", str(image_name), 
                         '--decoder.write_csv_to', str(csv_name))


    def post_read_disk(self, csv_file: Path):
        """Read the generated CSV file and report any issues to the log"""
        status = {}
        with open(csv_file, newline='') as csvfile:
            creader = csv.DictReader(csvfile)
            for row in creader:
                if row['Status'] not in status:
                    status[row['Status']] = []
                status[row['Status']].append((int(row['Logical track']), int(row['Logical side']), int(row['Logical sector'])))

        if len(status) == 1 and 'OK' in status:
            # Everything was great
            self.log("**** DISK READ SUCCESSFULLY ****\n")
        else:
            # or not.
            self.log("**** DISK READ HAD ERRORS ****\n")
            self.log("Status codes and (track, side, sector)\n")
            self.log("--------------------\n")
            for k, v in status.items():
                if k == 'OK':
                    continue
                self.log(f"{k}:\n")
                for s in [str(x) for x in v]:
                    self.log(f"   {s}\n")


    def run_command(self, program, *args):        
        self.log(f"Running command: {program} {args}")
        self.test_button.setEnabled(False)
        self.destination_dir.setEnabled(False)
        self.read_button.setEnabled(False)
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.output_update)
        self.process.finished.connect(self.process_finished)
        self.process.setProgram(program)
        self.process.setArguments(args)
        self.process.start()


    def is_valid_destination(self) -> bool:
        """Make sure the parameters have been set up correctly"""
        if self.destination_dir.real_path == "Unset":
            return False
        if re.match(r'[\w\d\.\-]+$', self.disk_name.text()):
            return True
        else:
            return False

        
    def output_update(self, final=False):
        if self.process:
            data = self.process.readAllStandardError()            
            text = str(data, encoding='utf-8').splitlines(keepends=True)
            if text:
                text[0] = self.stderr + text[0]
                if text[-1][-1] not in ('\n', '\r'):
                    # it didn't end with a newline, so we have a partial line read.
                    self.stderr = text.pop()   
                else:
                    self.stderr = ""                                 
                self.log("".join(text), True)
            if final and self.stderr:
                self.log(self.stderr, True)

            data = self.process.readAllStandardOutput()
            text = str(data, encoding='utf-8').splitlines(keepends=True)
            if text:
                text[0] = self.stdout + text[0]
                if text[-1][-1] not in ('\n', '\r'):
                    self.stdout = text.pop()
                else:
                    self.stdout = ""
                for t in text:
                    if m := re.match(r"\s?(\d+)\.(\d+):", t):
                        self.progress.setValue(int(m.group(1)) * 2 + int(m.group(2)))
                self.log("".join(text))
            if final and self.stdout:
                self.log(self.stdout)
            

    def process_finished(self):
        self.output_update(True)
        self.process_rc = self.process.exitCode()
        self.log(f"Process finished, rc={self.process_rc}")
        self.process = None
        self.read_button.setEnabled(self.is_valid_destination())
        self.test_button.setEnabled(True)
        self.destination_dir.setEnabled(True)
        self.progress.setValue(160)
        if self.process_callback:
            callback = self.process_callback
            self.process_callback = None
            callback()


if __name__ == "__main__":
    main()
