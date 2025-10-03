import os
import subprocess
from pathlib import Path
from hashlib import sha256
from modules.emotion_voice_engine import EmotionVoiceEngine
import re 
import io
import sys

CACHE_DIR = Path("tts_cache")
CACHE_DIR.mkdir(exist_ok=True)

engine = EmotionVoiceEngine()

# Set preferred accent (options: 'us', 'uk', 'au', 'in')
VOICE_ACCENT = 'us'

def extract_emotion(text):
    """Extract emotion markers from text like (happy) or (sad)"""
    match = re.match(r"\((.*?)\)", text)
    if match:
        emotion = match.group(1).lower()
        clean_text = re.sub(r"^\(.*?\)\s*", "", text)
        return emotion, clean_text
    return "neutral", text

def remove_emojis(text):
    """Remove all emojis from text"""
    # Comprehensive emoji pattern covering most Unicode emoji ranges
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002500-\U00002BEF"  # chinese char
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
        "\U00002600-\U000026FF"  # miscellaneous symbols
        "\U00002B50"              # star
        "\U0001F004"              # mahjong tile
        "\U0001F0CF"              # playing card
        "\U0001F170-\U0001F251"  # enclosed characters supplement
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)

def remove_markdown_formatting(text):
    """Remove markdown formatting like **bold**, *italic*, `code`, etc."""
    # Remove bold (**text** or __text__)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    
    # Remove italic (*text* or _text_)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    
    # Remove code blocks (```code```)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    
    # Remove inline code (`code`)
    text = re.sub(r'`(.+?)`', r'\1', text)
    
    # Remove strikethrough (~~text~~)
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    
    return text

def remove_special_symbols(text):
    """Remove special symbols and emote actions like *blushes* or ~nervous~"""
    # Remove action emotes like *action* or ~action~
    text = re.sub(r'\*[^*]+\*', '', text)
    text = re.sub(r'~[^~]+~', '', text)
    
    # Remove other special symbols but keep basic punctuation and Unicode characters (for Hindi)
    # Modified to preserve Devanagari script (Hindi): \u0900-\u097F
    text = re.sub(r'[^\u0900-\u097Fa-zA-Z0-9\s.,!?;:\'-]', '', text)
    
    return text

def remove_urls(text):
    """Remove URLs from text"""
    # Remove http/https URLs
    text = re.sub(r'https?://\S+', '', text)
    # Remove www URLs
    text = re.sub(r'www\.\S+', '', text)
    return text

def remove_citations(text):
    """Remove citation tags and references"""
    # Remove XML-style citation tags
    text = re.sub(r']*>.*?', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)  # Remove any remaining HTML/XML tags
    
    # Remove citation references like [1], [2], etc.
    text = re.sub(r'\[\d+\]', '', text)
    
    return text

def detect_language(text):
    """Detect if text contains Hindi (Devanagari script)"""
    # Check if text contains Devanagari characters
    devanagari_pattern = re.compile(r'[\u0900-\u097F]')
    has_hindi = bool(devanagari_pattern.search(text))
    
    # Count Hindi vs English characters
    hindi_chars = len(devanagari_pattern.findall(text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    
    # If more than 30% Hindi characters, consider it Hindi
    total_chars = hindi_chars + english_chars
    if total_chars > 0 and (hindi_chars / total_chars) > 0.3:
        return 'hi'  # Hindi
    elif has_hindi:
        return 'mixed'  # Mixed Hindi-English
    else:
        return 'en'  # English

def sanitize_text(text):
    """Comprehensive text sanitization for TTS"""
    # First, remove citations and tags
    text = remove_citations(text)
    
    # Remove URLs
    text = remove_urls(text)
    
    # Remove emojis
    text = remove_emojis(text)
    
    # Remove markdown formatting
    text = remove_markdown_formatting(text)
    
    # Remove special symbols and emote actions (preserves Hindi)
    text = remove_special_symbols(text)
    
    # Remove fancy quotes and replace with standard ones
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Clean up multiple punctuation marks
    text = re.sub(r'([.!?]){2,}', r'\1', text)
    
    return text.strip()

def split_long_text(text, max_length=500):
    """Split long text into smaller chunks for better TTS processing"""
    if len(text) <= max_length:
        return [text]
    
    # Try to split by sentences first
    sentences = re.split(r'([.!?।]+\s)', text)  # Added Hindi full stop (।)
    chunks = []
    current_chunk = ""
    
    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        if i + 1 < len(sentences):
            sentence += sentences[i + 1]  # Add punctuation back
        
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks if chunks else [text]

def speak(text, emotion="neutral", verbose=True):
    """
    Convert text to speech with emotion and comprehensive sanitization
    Supports both English and Hindi text
    
    Args:
        text: Text to speak (English or Hindi)
        emotion: Emotion to apply (default: neutral)
        verbose: Whether to print the text being spoken (default: True)
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not text or len(text.strip()) < 2:
        return False

    # Sanitize the text completely
    clean_text = sanitize_text(text)
    
    # Check if there's anything left to speak after sanitization
    if not clean_text or len(clean_text.strip()) < 2:
        return False

    # CRITICAL FIX: Print BEFORE suppressing stderr
    if verbose:
        print()
        print("─" * 60)
        print(f"🤖 Lily: {clean_text}")
        print("─" * 60)
        print()


    # Split long text into chunks
    text_chunks = split_long_text(clean_text)
    
    # Detect language
    language = detect_language(clean_text)
    
    # Suppress engine initialization messages AFTER printing
    old_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    success = True
    try:
        for i, chunk in enumerate(text_chunks):
            if not chunk.strip():
                continue
            
            # Determine TLD based on language
            if language == 'hi' or language == 'mixed':
                tld = 'co.in'  # Use Indian English/Hindi TLD
                accent = 'in'
            else:
                tld = engine.set_voice_accent(VOICE_ACCENT)
                accent = VOICE_ACCENT
            
            # Create hash for cache
            hash_name = sha256(f"{accent}_{language}_{emotion}_{chunk}".encode()).hexdigest()
            filename = CACHE_DIR / f"{hash_name}.mp3"

            if filename.exists():
                if not play_audio(filename):
                    success = False
            else:
                try:
                    # Apply emotion with appropriate language settings
                    audio = engine.apply_emotion(chunk, emotion, tld=tld)
                    audio.export(filename, format="mp3", bitrate="192k")
                    if not play_audio(filename):
                        success = False

                except Exception as e:
                    print(f"[TTS ERROR] {e}")
                    success = False

    finally:
        # Restore stderr
        sys.stderr = old_stderr
    
    return success

def play_audio(path):
    """Play audio file using ffplay"""
    try:
        subprocess.run(["ffplay", "-nodisp", "-autoexit", str(path)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"[Audio Play Error] {e}")
        return False

def speak_raw(text):
    """Speak text with neutral emotion"""
    return speak(text, emotion="neutral", verbose=True)

def speak_happy(text):
    """Speak with happy, cheerful tone"""
    return speak(text, emotion="happy", verbose=True)

def speak_excited(text):
    """Speak with excitement and enthusiasm"""
    return speak(text, emotion="excited", verbose=True)

def speak_energetic(text):
    """Speak with high energy (fastest, brightest)"""
    return speak(text, emotion="energetic", verbose=True)

def speak_playful(text):
    """Speak with playful, fun tone"""
    return speak(text, emotion="playful", verbose=True)

def speak_calm(text):
    """Speak in calm, soothing manner"""
    return speak(text, emotion="calm", verbose=True)

def speak_hindi(text):
    """Speak Hindi text with proper accent"""
    global VOICE_ACCENT
    original_accent = VOICE_ACCENT
    VOICE_ACCENT = 'in'  # Set to Indian accent for Hindi
    result = speak(text, emotion="neutral", verbose=True)
    VOICE_ACCENT = original_accent
    return result

def set_voice_accent(accent='us'):
    """
    Change Lily's accent
    
    Options:
        'us' - American English (default)
        'uk' - British English
        'au' - Australian English
        'in' - Indian English (best for Hindi/mixed content)
    """
    global VOICE_ACCENT
    VOICE_ACCENT = accent
    print(f"🎵 Voice accent changed to: {accent}")
    # Clear cache to regenerate with new accent
    import shutil
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        CACHE_DIR.mkdir(exist_ok=True)
        print("🔄 Cache cleared for new accent")