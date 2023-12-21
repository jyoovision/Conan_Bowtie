#include <WiFi.h>
#include <driver/i2s.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

const char *ssid = "KT_GiGA_Mesh_048A";     // Wi-Fi 네트워크 이름
const char *password = "3fg5czb747"; // Wi-Fi 네트워크 비밀번호

const char* host = "172.30.1.51";  // 서버의 IP 주소
const uint16_t port = 12345;       // 서버의 포트 번호
WiFiClient client;

#define CHUNK_SIZE 4096  // 청크 데이터 크기
uint8_t audioChunk[CHUNK_SIZE];

#define MESSAGE_BUFFER_SIZE 100  // 메시지 버퍼 크기
char messageBuffer[MESSAGE_BUFFER_SIZE];  // 메시지 수신용 버퍼

// OLED 디스플레이의 사이즈 정의
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

// OLED 디스플레이의 I2C 주소 (대부분의 모듈은 0x3C를 사용)
#define OLED_RESET    -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

void setup() {
  Serial.begin(115200);

  // I2S 설정
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = 24000,  // 샘플 레이트
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,  // 샘플 폭: 16비트
    .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,  // 채널 포맷: 스테레오
    .communication_format = I2S_COMM_FORMAT_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 64,
    .use_apll = false,
    .tx_desc_auto_clear = true,
    .fixed_mclk = 0
  };

  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_pin_config_t pin_config = {
      .bck_io_num = 26, // BCLK
      .ws_io_num = 25, // LRCLK
      .data_out_num = 27, // DIN
      .data_in_num = I2S_PIN_NO_CHANGE
  };
  i2s_set_pin(I2S_NUM_0, &pin_config);

  // 메시지 버퍼 초기화
  memset(messageBuffer, 0, MESSAGE_BUFFER_SIZE);

  // OLED 초기화
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 allocation failed"));
    for(;;);
  }

  // 디스플레이 설정
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.println(F("Conan Bowtie"));
  display.display();

  // Wi-Fi 연결
  WiFi.begin(ssid, password);
  Serial.println("Wi-Fi에 연결을 시도합니다...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi에 연결되었습니다.");
  Serial.print("IP 주소: ");
  Serial.println(WiFi.localIP());

  // 서버에 연결
  if (!client.connect(host, port)) {
    Serial.println("서버에 연결할 수 없습니다.");
    while(1);
  }
  Serial.println("서버에 연결되었습니다.");
}

void loop() {
  // 서버에서 데이터 수신
  if (client.available()) {
    // 헤더 확인을 위해 첫 문자열 읽기
    String header = client.readStringUntil(':');

    if (header == "text") {
      // 텍스트 메시지 처리
      int messageLength = client.readBytesUntil('\n', messageBuffer, MESSAGE_BUFFER_SIZE - 1);
      messageBuffer[messageLength] = '\0';  // 문자열 종료 문자 추가

      // 디스플레이에 메시지 출력
      display.clearDisplay();  // 디스플레이 클리어
      display.setCursor(0,0);  // 커서 초기화
      display.println(messageBuffer);  // 메시지 출력
      display.display();  // 변경 사항 적용
      
    } else if (header == "audio") {
      // 오디오 데이터 길이 수신
      uint32_t totalLength = 0;
      client.readBytes((char*)&totalLength, sizeof(totalLength));
      Serial.print("Total audio length: ");
      Serial.println(totalLength);

      // 전체 데이터 수신 및 바로 재생
      size_t receivedLength = 0;
      while (receivedLength < totalLength) {
        size_t bytesToRead = min(static_cast<size_t>(CHUNK_SIZE), static_cast<size_t>(totalLength - receivedLength));
        size_t bytesRead = client.read(audioChunk, bytesToRead);

        if (bytesRead > 0) {
          receivedLength += bytesRead;
          size_t bytes_written;
          i2s_write(I2S_NUM_0, audioChunk, bytesRead, &bytes_written, portMAX_DELAY);
          Serial.print("Played audio chunk: ");
          Serial.print(bytesRead);
          Serial.print(" bytes, Total received: ");
          Serial.println(receivedLength);
        } else {
          delay(10); // 네트워크 지연 대기
        }
      }
      // 버퍼 초기화
      memset(audioChunk, 0, CHUNK_SIZE);
      Serial.println("Audio playback completed and buffer cleared");
    }
  }
}
