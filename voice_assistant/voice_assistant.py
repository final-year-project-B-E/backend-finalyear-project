import os
import json
import asyncio
import tempfile
import requests
from typing import AsyncGenerator, Optional, Dict, Any

from dotenv import load_dotenv
from faster_whisper import WhisperModel
from agents.sales_agent import SalesAgent
from database import db
from schemas import Channel

load_dotenv()

# ✅ Deepgram for realtime STT
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "").strip()

# ✅ OpenAI for TTS
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
OPENAI_BASE_URL = "https://api.openai.com/v1"

class VoiceAssistant:
    """
    ✅ Real-time Voice Assistant Core (Streaming-ready)

    This class NO LONGER transcribes from "audio_path".
    Instead it supports:
      - realtime transcription from audio chunks (websocket)
      - processing finalized transcript into SalesAgent
    """

    def __init__(self):
        self.sales_agent = SalesAgent()

        if not DEEPGRAM_API_KEY:
            print("⚠️ DEEPGRAM_API_KEY not found. Realtime STT won't work.")

    # -------------------------------------------------------------------------
    # ✅ REALTIME STT: Deepgram streaming transcript generator
    # -------------------------------------------------------------------------
    async def stream_transcription_deepgram(
        self,
        audio_chunk_generator: AsyncGenerator[bytes, None],
        sample_rate: int = 16000,
        language: str = "en",
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Accepts a generator of raw audio bytes (PCM16 recommended),
        returns live transcript events like:
            { type: "partial"|"final", text: "..." }
        """

        if not DEEPGRAM_API_KEY:
            # fallback fake realtime transcript (dev mode)
            yield {"type": "final", "text": "Hello, I want to know about your fashion products."}
            return

        # Deepgram websocket (v1)
        # Note: You must install: pip install websockets
        import websockets

        # ✅ Deepgram expects audio encoding details
        # For best realtime, send 16-bit linear PCM mono 16kHz (audio/raw)
        deepgram_url = (
            "wss://api.deepgram.com/v1/listen"
            f"?encoding=linear16"
            f"&sample_rate={sample_rate}"
            f"&channels=1"
            f"&language={language}"
            f"&interim_results=true"
            f"&smart_format=true"
            f"&punctuate=true"
            f"&endpointing=150"
            f"&vad_events=true"
        )

        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}"
        }

        async with websockets.connect(deepgram_url, extra_headers=headers) as ws:

            async def sender():
                async for chunk in audio_chunk_generator:
                    if chunk:
                        await ws.send(chunk)
                # Tell DG we're done
                await ws.send(json.dumps({"type": "CloseStream"}))

            async def receiver():
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)

                    # Deepgram transcript format
                    # data["channel"]["alternatives"][0]["transcript"]
                    if "channel" in data:
                        alt = data["channel"]["alternatives"][0]
                        text = (alt.get("transcript") or "").strip()

                        if not text:
                            continue

                        is_final = data.get("is_final", False)

                        yield {
                            "type": "final" if is_final else "partial",
                            "text": text
                        }

                    # End condition
                    if data.get("type") == "UtteranceEnd":
                        # This event means speech segment ended
                        # We don't "break" because user may continue speaking
                        pass

            sender_task = asyncio.create_task(sender())

            try:
                async for event in receiver():
                    yield event
            finally:
                sender_task.cancel()

    # -------------------------------------------------------------------------
    # ✅ PROCESS "FINAL" TRANSCRIPTS INTO SALES AGENT
    # -------------------------------------------------------------------------
    def process_transcript_message(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        channel: str = "web",
    ) -> str:
        """
        Takes finalized transcript text and returns assistant reply.
        """

        user_message = (user_message or "").strip()
        if not user_message:
            return "I couldn't hear anything clearly. Could you repeat that?"

        # ✅ user context
        user_context = {}
        if user_id:
            user = db.get_user(user_id)
            if user:
                user_context = {
                    "name": f"{user['first_name']} {user['last_name']}",
                    "loyalty_score": user["loyalty_score"],
                    "past_orders": self._get_user_orders(user_id),
                }

        # ✅ history
        chat_history = []
        if session_id:
            messages = db.get_chat_history(session_id, limit=10)
            chat_history = [
                {"role": msg["message_type"], "content": msg["content"]}
                for msg in messages
            ]

        # ✅ channel enum
        try:
            channel_enum = Channel(channel)
        except ValueError:
            channel_enum = Channel.WEB

        # ✅ Process
        response = self.sales_agent.process(
            user_message=user_message,
            history=chat_history,
            user_context=user_context,
            channel=channel_enum,
        )

        # ✅ store
        if session_id:
            db.add_chat_message(session_id, "user", user_message)
            db.add_chat_message(session_id, "assistant", response, "sales")

        return response

    def process_voice_message(
        self,
        audio_path: str,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        channel: str = "web",
    ) -> str:
        """
        Transcribes audio file and processes the transcript.
        """
        try:
            model = WhisperModel("base")
            segments, info = model.transcribe(audio_path)
            text = " ".join([segment.text for segment in segments]).strip()
            if not text:
                return "I couldn't transcribe the audio. Could you try again?"
            return self.process_transcript_message(text, session_id, user_id, channel)
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return "There was an error processing your voice message."

    def _get_user_orders(self, user_id: int) -> list:
        orders = []
        for order in db.orders:
            if order["user_id"] == user_id:
                items = []
                for item in db.order_items:
                    if item["order_id"] == order["id"]:
                        items.append(item)
                orders.append({**order, "items": items})
        return orders

    def text_to_speech(self, text: str) -> str:
        """Convert text to speech using OpenAI TTS"""
        if not OPENAI_API_KEY:
            return "mock_audio.mp3"  # Mock for testing

        try:
            url = f"{OPENAI_BASE_URL}/audio/speech"
            data = {
                "model": "tts-1",
                "input": text,
                "voice": "alloy"
            }
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_file.write(response.content)
                return temp_file.name
        except Exception as e:
            print(f"Error generating TTS: {e}")
            return None
