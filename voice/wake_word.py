"""
Wake Word Detection for Jarvis X
Listens for wake word to activate voice commands
"""

import struct
import re
from difflib import SequenceMatcher
from threading import Thread, Event
from typing import Optional, Callable
try:
    import pyaudio
except ImportError:
    pyaudio = None
from utils.logger import get_logger
from utils.config_manager import get_config

logger = get_logger()
config = get_config()


class WakeWordDetector:
    """Detects wake word to activate Jarvis"""

    def __init__(self, wake_word: Optional[str] = None):
        self.wake_word = wake_word or config.get('voice.wake_word', 'jarvis')
        self.is_listening = False
        self.stop_event = Event()
        self.listen_thread = None
        self.porcupine = None
        self.audio_stream = None
        self.pa = None

        # Try to initialize Porcupine
        self._init_porcupine()

    def _init_porcupine(self):
        """Initialize Porcupine wake word engine"""
        try:
            import pvporcupine

            # Initialize Porcupine with built-in wake word
            # Note: This requires a Picovoice access key
            access_key = config.get('advanced.api_keys.picovoice_key', '')

            if not access_key:
                logger.warning("Picovoice access key not found. Wake word detection disabled.")
                logger.info("Get a free key at: https://console.picovoice.ai/")
                return

            # Available built-in wake words: 'alexa', 'americano', 'blueberry',
            # 'bumblebee', 'computer', 'grapefruit', 'grasshopper', 'hey google',
            # 'hey siri', 'jarvis', 'ok google', 'picovoice', 'porcupine', 'terminator'

            wake_words = ['jarvis'] if self.wake_word.lower() == 'jarvis' else ['computer']

            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keywords=wake_words
            )

            logger.info(f"Wake word detector initialized for: {wake_words}")

        except ImportError:
            logger.warning("pvporcupine not installed. Wake word detection disabled.")
            logger.info("Install with: pip install pvporcupine")
        except Exception as e:
            logger.error(f"Error initializing wake word detector: {e}")

    def start(self, callback: Callable):
        """
        Start listening for wake word

        Args:
            callback: Function to call when wake word is detected
        """
        if self.is_listening:
            logger.warning("Wake word detector already running")
            return

        if not self.porcupine:
            logger.warning("Wake word detector not available")
            return

        self.is_listening = True
        self.stop_event.clear()
        self.listen_thread = Thread(target=self._listen_loop, args=(callback,))
        self.listen_thread.daemon = True
        self.listen_thread.start()

        logger.info(f"Wake word detection started. Listening for '{self.wake_word}'...")

    def stop(self):
        """Stop listening for wake word"""
        if not self.is_listening:
            return

        logger.info("Stopping wake word detection")
        self.is_listening = False
        self.stop_event.set()

        if self.listen_thread:
            self.listen_thread.join(timeout=2)

        self._cleanup()

    def _listen_loop(self, callback: Callable):
        """Main listening loop"""
        try:
            if pyaudio is None:
                logger.warning("pyaudio is not installed. Wake word audio stream is unavailable.")
                return

            self.pa = pyaudio.PyAudio()

            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )

            logger.debug("Audio stream opened for wake word detection")

            while self.is_listening and not self.stop_event.is_set():
                try:
                    pcm = self.audio_stream.read(self.porcupine.frame_length,
                                                exception_on_overflow=False)
                    pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)

                    keyword_index = self.porcupine.process(pcm)

                    if keyword_index >= 0:
                        logger.info(f"Wake word '{self.wake_word}' detected!")
                        if callback:
                            callback()

                except Exception as e:
                    if self.is_listening:
                        logger.error(f"Error in wake word detection loop: {e}")
                    break

        except Exception as e:
            logger.error(f"Error setting up wake word detection: {e}")
        finally:
            self._cleanup()

    def _cleanup(self):
        """Clean up audio resources"""
        try:
            if self.audio_stream:
                self.audio_stream.close()
                self.audio_stream = None

            if self.pa:
                self.pa.terminate()
                self.pa = None

            logger.debug("Wake word detector cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Destructor"""
        self.stop()
        if self.porcupine:
            self.porcupine.delete()


# Fallback simple wake word detector using speech recognition
class SimpleWakeWordDetector:
    """Simple wake word detection using speech recognition"""

    def __init__(self, wake_word: Optional[str] = None):
        self.wake_word = wake_word or config.get('voice.wake_word', 'jarvis')
        self.wake_word_min_similarity = float(config.get('voice.wake_word_min_similarity', 0.86))
        self.wake_word_aliases = config.get('voice.wake_word_aliases', [])
        self.is_listening = False
        self.stop_event = Event()
        self.listen_thread = None

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text before wake phrase matching."""
        lowered = text.lower().strip()
        cleaned = re.sub(r"[^a-z0-9' ]+", " ", lowered)
        return " ".join(cleaned.split())

    def _matches_phrase(self, source_text: str, phrase: str) -> bool:
        """Match wake phrase using strict containment and similarity windows."""
        normalized_source = self._normalize_text(source_text)
        normalized_phrase = self._normalize_text(phrase)

        if not normalized_source or not normalized_phrase:
            return False

        if normalized_phrase in normalized_source:
            return True

        source_tokens = normalized_source.split()
        phrase_tokens = normalized_phrase.split()

        if len(source_tokens) < len(phrase_tokens):
            similarity = SequenceMatcher(None, normalized_source, normalized_phrase).ratio()
            return similarity >= self.wake_word_min_similarity

        phrase_len = len(phrase_tokens)
        for i in range(0, len(source_tokens) - phrase_len + 1):
            window = " ".join(source_tokens[i:i + phrase_len])
            similarity = SequenceMatcher(None, window, normalized_phrase).ratio()
            if similarity >= self.wake_word_min_similarity:
                return True

        return False

    def _matches_wake_word(self, source_text: str) -> bool:
        """Check wake phrase and aliases with similarity safeguards."""
        if self._matches_phrase(source_text, self.wake_word):
            return True

        for alias in self.wake_word_aliases:
            if isinstance(alias, str) and alias and self._matches_phrase(source_text, alias):
                return True

        return False

    def start(self, callback: Callable):
        """Start listening for wake word"""
        if self.is_listening:
            return

        from voice.speech_recognition import SpeechRecognizer

        self.is_listening = True
        self.stop_event.clear()

        recognizer = SpeechRecognizer()

        def listen_loop():
            logger.info(f"Simple wake word detection started for '{self.wake_word}'")

            while self.is_listening and not self.stop_event.is_set():
                result = recognizer.listen(timeout=2)

                if result['success']:
                    text = result['text']
                    if self._matches_wake_word(text):
                        logger.info(f"Wake word '{self.wake_word}' detected!")
                        if callback:
                            callback()

        self.listen_thread = Thread(target=listen_loop)
        self.listen_thread.daemon = True
        self.listen_thread.start()

    def stop(self):
        """Stop listening"""
        self.is_listening = False
        self.stop_event.set()
        if self.listen_thread:
            self.listen_thread.join(timeout=2)
        logger.info("Simple wake word detection stopped")

