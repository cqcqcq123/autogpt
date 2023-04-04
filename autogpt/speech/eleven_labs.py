"""ElevenLabs speech module"""
import os
import typing
from playsound import playsound

import requests

from autogpt.config import Config
from autogpt.speech.base import VoiceBase
from vocode.turn_based.synthesizer.eleven_labs_synthesizer import ElevenLabsSynthesizer

from autogpt.speech.vocode_base import VocodeVoiceBase

PLACEHOLDERS = {"your-voice-id"}


class ElevenLabsSpeech(VocodeVoiceBase):
    """ElevenLabs speech class"""

    def _setup(self) -> None:
        """Setup the voices, API key, etc.

        Returns:
            None: None
        """

        cfg = Config()
        default_voices = ["ErXwobaYiN019PkySvjV", "EXAVITQu4vr4xnSDxMaL"]
        voice_options = {
            "Rachel": "21m00Tcm4TlvDq8ikWAM",
            "Domi": "AZnzlk1XvdvUeBnXmlld",
            "Bella": "EXAVITQu4vr4xnSDxMaL",
            "Antoni": "ErXwobaYiN019PkySvjV",
            "Elli": "MF3mGyEYCl7XYWbV9V6O",
            "Josh": "TxGEqnHWrfWFTfGW9XjX",
            "Arnold": "VR6AewLTigWG4xSOukaG",
            "Adam": "pNInz6obpgDQGcFmaJgB",
            "Sam": "yoZ06aMxZJJ28mfd3POQ",
        }
        self._voices = default_voices.copy()
        if cfg.elevenlabs_voice_1_id in voice_options:
            cfg.elevenlabs_voice_1_id = voice_options[cfg.elevenlabs_voice_1_id]
        if cfg.elevenlabs_voice_2_id in voice_options:
            cfg.elevenlabs_voice_2_id = voice_options[cfg.elevenlabs_voice_2_id]
        self._use_custom_voice(cfg.elevenlabs_voice_1_id, 0)
        self._use_custom_voice(cfg.elevenlabs_voice_2_id, 1)
        super()._setup()

    def _create_synthesizer(self) -> ElevenLabsSynthesizer:
        cfg = Config()
        return ElevenLabsSynthesizer(
            api_key=cfg.elevenlabs_api_key, voice_id=self._voices[0]
        )

    def _use_custom_voice(self, voice, voice_index) -> None:
        """Use a custom voice if provided and not a placeholder

        Args:
            voice (str): The voice ID
            voice_index (int): The voice index

        Returns:
            None: None
        """
        # Placeholder values that should be treated as empty
        if voice and voice not in PLACEHOLDERS:
            self._voices[voice_index] = voice

    def _speech(self, text: str, voice_index: int = 0) -> bool:
        """Speak text using elevenlabs.io's API

        Args:
            text (str): The text to speak
            voice_index (int, optional): The voice to use. Defaults to 0.

        Returns:
            bool: True if the request was successful, False otherwise
        """
        typing.cast(ElevenLabsSynthesizer, self.synthesizer).voice_id = self._voices[
            voice_index
        ]
        return super()._speech(text)
