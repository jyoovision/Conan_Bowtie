from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QWidget,
    QDial,
    QProgressBar,
)
from PyQt5.QtGui import QPixmap, QPalette, QBrush
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import pyaudio
import wave
import socket
import threading
from simpleRVC import RVC
from dotenv import load_dotenv
from configs.config import Config
from infer.modules.vc.modules import VC
import time

load_dotenv()
first_record = False
current_voice = None
current_audio = None
vc = VC(Config())


class ServerThread(QThread):
    connection_established = pyqtSignal(socket.socket)  # 새로운 연결 시그널
    status_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.conn = None
        self.addr = None

    def run(self):
        HOST = "172.30.1.51"
        PORT = 12345
        BACKLOG = 5

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen(BACKLOG)
            print(f"서버 시작: {HOST}에서 {PORT} 포트를 리스닝 중")
            self.status_signal.emit(
                f"Server started: Listening on {HOST} at port {PORT}"
            )

            self.conn, self.addr = s.accept()
            print(f"연결됨: {self.addr}")
            self.status_signal.emit(f"Connected: {self.addr}")
            server_thread.send_message("Server connected!")
            self.connection_established.emit(self.conn)  # 연결된 소켓을 메인 스레드로 전송

            while True:  # 클라이언트로부터 데이터를 지속적으로 수신
                try:
                    data = self.conn.recv(1024)  # 클라이언트로부터 데이터 받기
                    if not data:
                        break  # 데이터가 없으면 루프 탈출

                    # 수신된 데이터 처리
                    message = data.decode()  # 수신된 데이터를 문자열로 변환
                    self.process_message(message)  # 메시지 처리 함수 호출

                except Exception as e:
                    print(f"데이터 수신 중 오류 발생: {e}")
                    break

    def process_message(self, message):
        global current_audio
        if not message.strip():
            return

        print(f"수신된 메시지: {message}")

        if message == "End audio streaming":
            if current_audio == "O":
                send_audio_button.show()
            else:
                playback_button.show()
            current_audio = None
        elif message == "button pressed":
            server_thread.send_audio("../InputOutput/output_audio.wav")

    def send_audio(self, audio_path):
        if self.conn:
            try:
                wf = wave.open(audio_path, "rb")

                # 오디오 데이터 헤더 전송
                header = "audio:"
                self.conn.send(header.encode())

                # 오디오 데이터 청크 단위로 전송
                CHUNK_SIZE = 4096
                data = wf.readframes(CHUNK_SIZE)
                while data:
                    self.conn.send(data)
                    data = wf.readframes(CHUNK_SIZE)

                time.sleep(1)  # 1초 대기

                # 오디오 전송 종료 신호 전송
                eos_signal = "EOS"
                self.conn.send(eos_signal.encode())
                wf.close()

            except Exception as e:
                print(f"오디오 전송 에러: {e}")

        else:
            print("아직 클라이언트에 연결되지 않음")

    def send_message(self, message):
        if self.conn:
            try:
                # 텍스트 메시지 헤더 전송
                header = "text:"

                # 텍스트 메시지 전송
                full_message = header + message + "\n"
                self.conn.sendall(full_message.encode())

            except Exception as e:
                print(f"메시지 전송 에러: {e}")
        else:
            print("아직 클라이언트에 연결되지 않음")


class ProgressBarThread(QThread):
    update_progress = pyqtSignal(int)  # 프로그레스 바 값을 업데이트하기 위한 시그널

    def run(self):
        for i in range(101):
            time.sleep(0.05)  # 총 5초 동안 실행
            self.update_progress.emit(i)  # 프로그레스 바 값을 업데이트하는 시그널 발생
        self.update_progress.emit(0)  # 완료 후 프로그레스 바 초기화
        progress_bar.hide()
        send_audio_button.show()
        server_thread.send_message(f"{current_voice} voice Ready")


class Recorder:
    def __init__(self):
        self.is_recording = False
        self.open = True
        self.rate = 44100
        self.frames_per_buffer = 4096
        self.channels = 1
        self.format = pyaudio.paInt16
        self.audio_filename = "../InputOutput/input_audio.wav"
        self.frames = []

    def start_recording(self):
        self.audio = pyaudio.PyAudio()  # PyAudio 인스턴스 생성
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.frames_per_buffer,
            input_device_index=1,
        )
        self.frames = []
        self.is_recording = True

        def record():
            while self.is_recording:
                data = self.stream.read(self.frames_per_buffer)
                self.frames.append(data)

        self.thread = threading.Thread(target=record)
        self.thread.start()

    def stop_recording(self):
        self.is_recording = False
        self.thread.join()
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

        with wave.open(self.audio_filename, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b"".join(self.frames))


recorder = Recorder()


def set_vc(name):
    sid_value = name + ".pth"
    protect_value = 0.33
    vc.get_vc(sid_value, protect_value, protect_value)


def on_button_click():
    global current_voice, first_record
    if not recorder.is_recording:
        recorder.is_recording = True
        recorder.start_recording()
        label.setText("녹음 중...")
        button.setText("녹음 중지")
        playback_button.hide()  # 녹음 중에는 재생 버튼 숨기기
        modulation_button.hide()
        send_audio_button.hide()
        server_thread.send_message("Recording ...")

    else:
        recorder.stop_recording()
        label.setText("녹음 완료")
        button.setText("다시 녹음")
        playback_button.show()  # 녹음이 완료되면 재생 버튼 표시
        if current_voice is not None:
            modulation_button.show()
        first_record = True
        server_thread.send_message("Recording complete!")


def on_dial_changed(value):
    global current_voice, first_record
    angle = value * (360 / 100)

    new_voice = None
    if 180 < angle <= 240:
        dial_label.setText("유명한 탐정")
        new_voice = "famous"
    elif 240 < angle <= 300:
        dial_label.setText("유미란")
        new_voice = "miran"
    elif 300 < angle <= 360:
        dial_label.setText("김윤지 교수님")
        new_voice = "yoonjikim"
    else:
        dial_label.setText("변조할 목소리 선택")
        modulation_button.hide()
        new_voice = None

    # 목소리가 변경되었을 때만 set_vc() 함수 호출
    if new_voice != current_voice:
        server_thread.send_message(f"{new_voice} Selected")
        current_voice = new_voice
        if new_voice is not None:
            set_vc(new_voice)
        if first_record:
            modulation_button.show()


def on_modulation_button_clicked():
    # 프로그레스 바 스레드 시작
    send_audio_button.hide()
    progress_bar.show()
    progress_thread = ProgressBarThread()
    progress_thread.update_progress.connect(progress_bar.setValue)
    progress_thread.start()

    # RVC 함수 실행
    threading.Thread(target=lambda: RVC(vc, current_voice)).start()
    server_thread.send_message("Converting ...")


def send_audio(path):
    global current_audio

    if path == "../InputOutput/output_audio.wav":
        current_audio = "O"
        send_audio_button.hide()
    else:
        current_audio = "I"
        playback_button.hide()

    QApplication.processEvents()
    server_thread.send_audio(path)


app = QApplication([])

window = QWidget()
window.setWindowTitle("Conan Bowtie")
window.setFixedSize(700, 400)

server_status_label = QLabel(window)
server_status_label.move(5, 5)  # 위치 설정
server_status_label.resize(400, 15)  # 크기 설정
server_status_label.setStyleSheet(
    """
    color: #39FF14;
    font-size: 10px;
"""
)  # 텍스트 색상 설정

server_thread = ServerThread()
server_thread.status_signal.connect(server_status_label.setText)
server_thread.start()

# 레이블 생성 및 위치, 크기, 정렬 설정
label = QLabel("버튼을 눌러 녹음 시작", window)
label.setStyleSheet("color: white;")
label.move(75, 150)  # 레이블의 위치 설정
label.resize(150, 30)  # 레이블의 크기 설정
label.setAlignment(Qt.AlignCenter)  # 텍스트를 중앙 정렬

# 녹음 버튼 생성 및 위치와 크기 설정
button = QPushButton("녹음 시작", window)
button.setStyleSheet(
    "QPushButton {"
    "background-image: url('../Imgs/button.png');"
    "border: none;"
    "font-weight: bold;"
    "}"
)
button.move(100, 200)  # 버튼의 위치 설정
button.resize(100, 30)  # 버튼의 크기 설정
button.clicked.connect(on_button_click)

# 재생 버튼 생성 및 위치와 크기 설정
playback_button = QPushButton("녹음 재생", window)
playback_button.setStyleSheet(
    "QPushButton {"
    "background-image: url('../Imgs/button.png');"
    "border: none;"
    "font-weight: bold;"
    "}"
)
playback_button.move(100, 250)  # 재생 버튼의 위치 설정
playback_button.resize(100, 30)  # 재생 버튼의 크기 설정
playback_button.clicked.connect(lambda: send_audio("../InputOutput/input_audio.wav"))
playback_button.hide()  # 초기에는 재생 버튼 숨기기

dial = QDial(window)
dial.setStyleSheet(
    """
    QDial {
        background-color: black;
    }
"""
)
dial.setRange(0, 100)  # 0에서 100까지의 범위로 설정
dial.setValue(0)
dial.resize(150, 200)
dial.move(475, 100)
dial.valueChanged.connect(on_dial_changed)

dial_label = QLabel("변조할 목소리 선택", window)  # 초기 값 설정
dial_label.setStyleSheet("color: white;")
dial_label.move(475, 100)
dial_label.resize(150, 30)
dial_label.setAlignment(Qt.AlignCenter)

modulation_button = QPushButton("변환하기", window)
modulation_button.setStyleSheet(
    "QPushButton {"
    "background-image: url('../Imgs/button.png');"
    "border: none;"
    "font-weight: bold;"
    "}"
)
modulation_button.move(500, 275)
modulation_button.resize(100, 30)
modulation_button.clicked.connect(on_modulation_button_clicked)
modulation_button.hide()  # 초기에는 숨김

# 프로그레스 바 생성 및 위치와 크기 설정
progress_bar = QProgressBar(window)
progress_bar.setStyleSheet("border-radius: 4px;")
progress_bar.setGeometry(290, 190, 120, 10)  # x, y, width, height

# 프로그레스 바 초기 설정
progress_bar.setMinimum(0)
progress_bar.setMaximum(100)
progress_bar.setValue(0)
progress_bar.setTextVisible(False)
progress_bar.hide()

# 오디오 전송 버튼
send_audio_button = QPushButton("오디오 재생", window)
send_audio_button.setStyleSheet(
    "QPushButton {"
    "background-image: url('../Imgs/button.png');"
    "border: none;"
    "font-weight: bold;"
    "}"
)
send_audio_button.move(300, 180)
send_audio_button.resize(100, 30)
send_audio_button.clicked.connect(lambda: send_audio("../InputOutput/output_audio.wav"))
send_audio_button.hide()

# 배경 설정
pixmap = QPixmap("../Imgs/background.jpg")
scaled_pixmap = pixmap.scaled(window.size(), Qt.IgnoreAspectRatio)
palette = QPalette()
palette.setBrush(QPalette.Window, QBrush(scaled_pixmap))
window.setPalette(palette)

window.show()
app.exec_()
