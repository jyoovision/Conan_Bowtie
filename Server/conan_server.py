import socket
import pyaudio
import wave

# 오디오 파일 설정
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000

# 오디오 파일 열기
wf = wave.open("../InputOutput/output_audio.wav", "rb")

# PyAudio 시작
p = pyaudio.PyAudio()

# 소켓 설정
host = "172.30.1.51"  # 서버의 IP 주소
port = 12345  # 포트 번호
backlog = 5  # 대기 큐의 최대 크기
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host, port))
s.listen(backlog)

print(f"서버 시작: {host}에서 {port} 포트를 리스닝 중")

conn = None
try:
    conn, addr = s.accept()
    print(f"연결됨: {addr}")

    # 오디오 데이터 전송
    data = wf.readframes(CHUNK)
    while data:
        conn.send(data)
        data = wf.readframes(CHUNK)

except Exception as e:
    print(f"에러 발생: {e}")

finally:
    if conn:
        conn.close()
    s.close()
    p.terminate()


# from pydub import AudioSegment

# # 원본 오디오 파일 열기
# input_file = "../InputOutput/output_audio.wav"
# audio = AudioSegment.from_wav(input_file)

# # 샘플 레이트를 44100Hz로 변경
# target_sample_rate = 48000
# audio = audio.set_frame_rate(target_sample_rate)

# # 음량을 10dB 증가시킴
# volume_increase_dB = 5
# audio = audio + volume_increase_dB

# # 변경된 오디오를 새 파일로 저장
# output_file = "../InputOutput/output_audio_up.wav"
# audio.export(output_file, format="wav")

# print(
#     f"샘플 레이트를 {target_sample_rate} Hz로 변경하고, 음량을 {volume_increase_dB}dB 증가시킨 오디오를 저장했습니다."
# )
