import sys
sys.path.append('third_party/Matcha-TTS')
from cosyvoice.cli.cosyvoice import CosyVoice, CosyVoice2
from cosyvoice.utils.file_utils import load_wav
import torchaudio
import opencc

# s2t
converter = opencc.OpenCC('s2t.json')

cosyvoice_base = CosyVoice2(
    'pretrained_models/Cosyvoice2-Yue',
    load_jit=False, load_trt=False, load_vllm=False, fp16=False
)

cosyvoice_zjg = CosyVoice2(
    'pretrained_models/Cosyvoice2-Yue-ZoengJyutGaai',
    load_jit=False, load_trt=False, load_vllm=False, fp16=False
)

prompt_speech_16k = load_wav('asset/sg_017_090.wav', 16000)

text = '收到朋友从远方寄嚟嘅生日礼物，嗰份意外嘅惊喜同埋深深嘅祝福令我心入面充满咗甜蜜嘅快乐，笑容好似花咁绽放。'
text = converter.convert(text)

for i, j in enumerate(cosyvoice_base.inference_instruct2(text, '用粤语说这句话', prompt_speech_16k, stream=False)):
    torchaudio.save('base_{}.wav'.format(i), j['tts_speech'], cosyvoice.sample_rate)

for i, j in enumerate(cosyvoice_zjg.inference_instruct2(text, '用粤语说这句话', prompt_speech_16k, stream=False)):
    torchaudio.save('zjg_{}.wav'.format(i), j['tts_speech'], cosyvoice.sample_rate)
