![Frame 5](https://github.com/jyoovision/Conan_Bowtie/assets/124518704/b1d03904-803e-4980-9280-ffd2feef063c)

# Conan_Bowtie
This repository is a project that turns the anime Detective Conan's bow tie into a real device and controls it in pyQT.


이 레포지토리는 만화 명탐정 코난의 나비넥타이를 실제 장치로 바꾸고 이를 pyQt에서 제어하는 ​​프로젝트입니다.


## 기능
1. UI에서 녹음하고, 녹음한 내용을 playback 하면, 녹음된 목소리가 장치에서 재생됩니다.

2. 다이얼을 통해 변환할 목소리를 선택하면 해당 목소리로 녹음된 음성을 변환할 수 있습니다. (유명한 탐정, 미란이 등)

3. 오디오 재생을 누르면 장치에서 변환된 목소리가 출력됩니다.

4. 장치에서 버튼을 누르면 변환된 목소리가 출력됩니다.

5. 디스플레이를 통해 ui 에서 진행 중인 내용을  텍스트로 확인할 수 있습니다. 

6. 와이파이 통신을 사용하기 때문에 보조배터리만 있다면 무선으로 사용 가능합니다.

![Frame 3](https://github.com/jyoovision/Conan_Bowtie/assets/124518704/9902cc3e-5701-40a5-8ec1-bccff80aa390)



## 제작 방식

![Frame 6](https://github.com/jyoovision/Conan_Bowtie/assets/124518704/6893fb7a-60da-4046-850e-d1a48af60e07)


### 나비넥타이 ui  
음성변조를 위해 RVC를 사용하였습니다. RVC 레포지토리는 [여기](https://github.com/RVC-Project)에서 확인할 수 있습니다.  

RVC 를 활용하여 유명한 탐정, 미란이 목소리를 미리 학습시키고, pyQt Ui와 연동하여 실시간 변환을 진행합니다.


### 나비넥타이 device  
ESP32-PICO-V3기기를 사용하여 와이파이 통신으로 오디오 스트리밍 방식을 구현하였습니다.

브레드보드에서 프로토타입을 제작하여 테스트한 뒤,

만능기판을 이용하여, 손바닥만한 작은 사이즈로 패키징하였습니다.

또한 빨간 천으로 마감처리하여 코난의 나비넥타이 외형을 더욱 살렸습니다.



![Frame 8](https://github.com/jyoovision/Conan_Bowtie/assets/124518704/236f4d4b-35b7-469e-9a22-278514c5df07)


![제목 없음-1](https://github.com/jyoovision/Conan_Bowtie/assets/124518704/3a71e300-b531-4e0d-84a0-a6c0930a8569)
