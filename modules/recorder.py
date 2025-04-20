import sounddevice as sd
import scipy.io.wavfile as wav
import tempfile

def record_audio_chunk(duration=10, samplerate=16000):
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()

    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    wav.write(tmpfile.name, samplerate, recording)

    return tmpfile.name