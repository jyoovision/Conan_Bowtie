import os
from pydub import AudioSegment
from dotenv import load_dotenv
from configs.config import Config
from infer.modules.vc.modules import VC


def RVC(vc, name):
    try:
        result = vc.vc_single(
            0,  # spk_item_value
            "../InputOutput/input_audio.wav",  # input_audio0_value
            1.0,  # vc_transform0_value
            None,  # f0_file_value
            "rmvpe",  # f0method0_value
            "",  # file_index1_value
            "assets/model/" + name + ".index",  # file_index2_value
            0.75,  # index_rate1_value
            3,  # filter_radius0_value
            0,  # resample_sr0_value
            0.25,  # rms_mix_rate0_value
            0.33,  # protect0_value
        )

        if isinstance(result, tuple) and result[1][0] is not None:
            message, audio_data_tuple = result
            tgt_sr, audio_opt = audio_data_tuple
            audio = AudioSegment(
                audio_opt.tobytes(),
                frame_rate=tgt_sr,
                sample_width=audio_opt.dtype.itemsize,
                channels=1,
            )

            if not os.path.exists("../InputOutput"):
                os.makedirs("../InputOutput")

            audio_output_path = os.path.join("../InputOutput", "output_audio.wav")
            audio.export(audio_output_path, format="wav")

            text_output_path = os.path.join("../InputOutput", "output_text.txt")
            with open(text_output_path, "w") as f:
                f.write(message)
        else:
            print("An error occurred:", result[0])
    except Exception as e:
        print(f"Error in rvc: {e}")


if __name__ == "__main__":
    load_dotenv()
    vc = VC(Config())
    sid_value = "famous.pth"
    protect_value = 0.33
    vc.get_vc(sid_value, protect_value, protect_value)
    RVC(vc, "famous")
