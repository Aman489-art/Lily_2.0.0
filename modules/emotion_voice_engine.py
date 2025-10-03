import os
import tempfile
from gtts import gTTS
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
import librosa
from pathlib import Path
import soundfile as sf
import numpy as np

class EmotionVoiceEngine:
    """Emotion-based voice processing engine with enhanced natural sound"""

    EMOTION_PROFILES = {
        'neutral': {'speed': 1.15, 'volume': 1.1, 'pitch_shift': 2, 'tts_slow': False},
        'happy': {'speed': 1.25, 'volume': 1.15, 'pitch_shift': 3, 'tts_slow': False},
        'excited': {'speed': 1.35, 'volume': 1.25, 'pitch_shift': 4, 'tts_slow': False},
        'sad': {'speed': 0.90, 'volume': 0.95, 'pitch_shift': -1, 'tts_slow': False},
        'angry': {'speed': 1.20, 'volume': 1.20, 'pitch_shift': 1, 'tts_slow': False},
        'calm': {'speed': 1.10, 'volume': 1.00, 'pitch_shift': 1, 'tts_slow': False},
        'curious': {'speed': 1.15, 'volume': 1.05, 'pitch_shift': 2, 'tts_slow': False},
        'playful': {'speed': 1.30, 'volume': 1.15, 'pitch_shift': 3, 'tts_slow': False},
        'warm': {'speed': 1.05, 'volume': 1.05, 'pitch_shift': 1, 'tts_slow': False},
        'professional': {'speed': 1.10, 'volume': 1.05, 'pitch_shift': 0, 'tts_slow': False},
        'whisper': {'speed': 0.95, 'volume': 0.80, 'pitch_shift': -2, 'tts_slow': False},
        'energetic': {'speed': 1.40, 'volume': 1.25, 'pitch_shift': 4, 'tts_slow': False}
    }

    def __init__(self):
        self.cache_dir = Path("audio_cache")
        self.cache_dir.mkdir(exist_ok=True)

    def generate_base_tts(self, text, slow=False, tld='com'):
        """
        Generate base TTS with optimized settings
        
        Args:
            text: Text to convert
            slow: Whether to use slow speech (DISABLED by default for better sound)
            tld: Top-level domain for accent ('com'=US, 'co.uk'=British, 'com.au'=Australian)
        """
        # Always use fast speech for more natural sound
        tts = gTTS(text=text, lang='en', slow=False, tld=tld)
        temp_mp3 = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        tts.save(temp_mp3.name)

        sound = AudioSegment.from_mp3(temp_mp3.name)
        wav_path = temp_mp3.name.replace(".mp3", ".wav")
        sound.export(wav_path, format="wav")
        os.unlink(temp_mp3.name)
        return wav_path

    def change_speed(self, sound, speed=1.0):
        """Change playback speed without affecting pitch"""
        if speed == 1.0:
            return sound
        
        altered = sound._spawn(sound.raw_data, overrides={
            "frame_rate": int(sound.frame_rate * speed)
        })
        return altered.set_frame_rate(sound.frame_rate)

    def pitch_shift(self, audio_segment, semitones):
        """
        Shift pitch of audio by semitones using librosa
        Positive values = higher pitch (brighter)
        Negative values = lower pitch (deeper)
        """
        if semitones == 0:
            return audio_segment
        
        # Export to temporary wav for processing
        temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        audio_segment.export(temp_wav.name, format="wav")
        
        # Load with librosa
        y, sr = librosa.load(temp_wav.name, sr=None)
        
        # Pitch shift
        y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=semitones)
        
        # Save shifted audio
        shifted_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        sf.write(shifted_wav.name, y_shifted, sr)
        
        # Load back as AudioSegment
        result = AudioSegment.from_wav(shifted_wav.name)
        
        # Cleanup
        os.unlink(temp_wav.name)
        os.unlink(shifted_wav.name)
        
        return result

    def enhance_audio(self, audio):
        """Apply audio enhancements for clearer, more natural sound"""
        # Normalize audio levels
        audio = normalize(audio)
        
        # Apply gentle compression for consistent volume
        audio = compress_dynamic_range(audio, threshold=-20.0, ratio=3.0)
        
        # Boost high frequencies slightly for clarity (simple high-pass effect)
        # This makes voice sound brighter and clearer
        audio = audio.high_pass_filter(100)
        
        return audio

    def apply_emotion(self, text, emotion='neutral', tld='com'):
        """
        Apply emotion-based voice modifications
        
        Args:
            text: Text to speak
            emotion: Emotion profile to use
            tld: Accent ('com', 'co.uk', 'com.au', 'co.in')
        """
        profile = self.EMOTION_PROFILES.get(emotion, self.EMOTION_PROFILES['neutral'])

        # Generate base audio (always fast for natural sound)
        base_audio_path = self.generate_base_tts(text, slow=False, tld=tld)
        audio = AudioSegment.from_wav(base_audio_path)

        # Apply pitch shift FIRST (before speed changes)
        if profile.get('pitch_shift', 0) != 0:
            try:
                audio = self.pitch_shift(audio, profile['pitch_shift'])
            except Exception as e:
                print(f"[Pitch shift warning: {e}]")

        # Apply speed changes
        if profile['speed'] != 1.0:
            audio = self.change_speed(audio, profile['speed'])

        # Apply volume changes
        if profile['volume'] != 1.0:
            volume_change = (profile['volume'] - 1.0) * 10
            audio += volume_change

        # Enhance audio quality
        audio = self.enhance_audio(audio)

        # Cleanup
        os.unlink(base_audio_path)

        return audio

    def set_voice_accent(self, accent='us'):
        """
        Set voice accent/region
        
        Options:
            'us' or 'com' - American English
            'uk' or 'co.uk' - British English
            'au' or 'com.au' - Australian English
            'in' or 'co.in' - Indian English
        """
        accent_map = {
            'us': 'com',
            'uk': 'co.uk',
            'au': 'com.au',
            'in': 'co.in'
        }
        return accent_map.get(accent, accent)

# Initialize engine
engine = EmotionVoiceEngine()
print("✅ Enhanced emotion engine ready!")
print("🎵 Voice optimized for natural, energetic speech\n")