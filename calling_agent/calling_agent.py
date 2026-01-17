import os
import time
import uuid
import subprocess
import requests
import shutil
import socket

from gtts import gTTS
from faster_whisper import WhisperModel


# =========================
# CONFIG
# =========================
FS_HOST = "127.0.0.1"
FS_PORT = 8021
FS_PASSWORD = "ClueCon"

SIP_DOMAIN = "nexhub-c838c5deb867.sip.signalwire.com"
SIP_USERNAME = "ai-agent-retail"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = "mistralai/devstral-2512:free"

# Audio paths (FreeSWITCH can read from /tmp easily)
TMP_DIR = "/tmp/calling_agent"
os.makedirs(TMP_DIR, exist_ok=True)

# Whisper model (small = fast, good enough)
WHISPER_MODEL_SIZE = "small"


# =========================
# ESL Helper (Socket-based)
# =========================
def _recv_all(sock, timeout=2.0):
    sock.settimeout(timeout)
    data = b""
    start = time.time()

    while time.time() - start < timeout:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk

            # If we already got headers ending, we can stop
            if b"\n\n" in data:
                break

        except socket.timeout:
            break

    return data.decode("utf-8", errors="ignore")


def esl_cmd(cmd: str) -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((FS_HOST, FS_PORT))

    # ✅ 1) Read FreeSWITCH banner
    banner = _recv_all(s, timeout=5.0)
    # print("BANNER:", banner)

    if "auth/request" not in banner:
        s.close()
        raise RuntimeError(f"Did not receive auth/request from FreeSWITCH. Got:\n{banner}")

    # ✅ 2) Authenticate
    s.sendall(f"auth {FS_PASSWORD}\n\n".encode())
    auth_resp = _recv_all(s, timeout=2.0)
    print("ESL Auth response:", repr(auth_resp))

    if "+OK accepted" not in auth_resp:
        s.close()
        raise RuntimeError(f"ESL authentication failed:\n{auth_resp}")

    # ✅ 3) Run API Command
    s.sendall(f"api {cmd}\n\n".encode())
    resp = _recv_all(s, timeout=3.0)

    s.close()
    return resp


# =========================
# TTS -> WAV (Playable by FreeSWITCH)
# =========================
def tts_to_wav(text: str, wav_path: str):
    """
    Uses gTTS to generate MP3 then converts to 8kHz mono WAV for telephony playback.
    """
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "FFmpeg not found. Install FFmpeg and add it to PATH. "
            "Download from https://www.gyan.dev/ffmpeg/builds/ and add bin to PATH."
        )

    mp3_path = wav_path.replace(".wav", ".mp3")

    tts = gTTS(text=text, lang="en")
    tts.save(mp3_path)

    # Convert MP3 -> WAV (8kHz mono) for FreeSWITCH playback
    subprocess.check_call([
        "ffmpeg", "-y",
        "-i", mp3_path,
        "-ar", "8000",
        "-ac", "1",
        wav_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # cleanup mp3
    if os.path.exists(mp3_path):
        os.remove(mp3_path)


# =========================
# Whisper STT
# =========================
class WhisperSTT:
    def __init__(self):
        self.model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")

    def transcribe(self, audio_path: str) -> str:
        segments, info = self.model.transcribe(audio_path)
        text = " ".join(seg.text.strip() for seg in segments if seg.text.strip())
        return text.strip()


# =========================
# OpenRouter LLM
# =========================
def openrouter_chat(history):
    """
    history = [{"role":"system"/"user"/"assistant", "content":"..."}]
    """
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is missing. Set it in environment variables.")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": history,
        "temperature": 0.4
    }

    res = requests.post(url, headers=headers, json=payload, timeout=60)
    res.raise_for_status()
    data = res.json()
    return data["choices"][0]["message"]["content"].strip()


# =========================
# Call Logic (turn-based)
# =========================
def make_call(to_number: str, max_turns: int = 2):
    """
    Makes an outbound call through FreeSWITCH gateway, then does a simple conversation:
    - Bot speaks
    - Records customer
    - Transcribes
    - AI replies
    - Bot speaks reply
    """

    call_id = str(uuid.uuid4())[:8]
    print(f"\n📞 Starting call session: {call_id}")
    print(f"➡️ Calling: {to_number}")

    # Create unique filenames
    greet_wav = f"{TMP_DIR}/greet_{call_id}.wav"
    reply_wav = f"{TMP_DIR}/reply_{call_id}.wav"
    rec_wav = f"{TMP_DIR}/rec_{call_id}.wav"

    # Initial greeting
    greeting_text = (
        "Hello! This is an automated calling assistant. "
        "I just need a quick feedback. Are you available to speak for one minute?"
    )
    tts_to_wav(greeting_text, greet_wav)

    # Conversation state for LLM
    history = [
        {
            "role": "system",
            "content": (
                "You are a polite, short and professional phone calling agent in India. "
                "Ask one question at a time. Keep responses under 2 sentences. "
                "If the user is busy, politely ask for a better time and end the call."
            )
        }
    ]

    # FreeSWITCH originate string:
    # - play greeting
    # - record response
    #
    # We'll do it in steps using uuid_* commands for reliability.

    # Step 1: originate the call and immediately answer into a "park"
    originate_cmd = (
        f"originate {{origination_caller_id_number={SIP_USERNAME},ignore_early_media=true}}"
        f"sofia/external/{to_number}@{SIP_DOMAIN} &park()"
    )

    out = esl_cmd(originate_cmd)
    print("FreeSWITCH originate output:", out)

    # Extract UUID from output (common format)
    # If output includes uuid, it might appear like: "+OK <uuid>"
    uuid_line = out.split()
    call_uuid = None
    for token in uuid_line:
        if len(token) >= 30 and "-" in token:
            call_uuid = token
            break

    if not call_uuid:
        # sometimes fs_cli doesn't return uuid cleanly
        # you can still check last channel but that’s complex
        raise RuntimeError(f"Could not get call UUID. Output:\n{out}")

    print(f"✅ Call UUID: {call_uuid}")

    # Small wait for call to connect
    time.sleep(2)

    # Step 2: Speak greeting
    print("🗣️ Playing greeting...")
    esl_cmd(f"uuid_broadcast {call_uuid} {greet_wav} aleg")

    # Wait for greeting to finish (rough estimate)
    time.sleep(6)

    # turns
    for turn in range(1, max_turns + 1):
        print(f"\n🔁 Turn {turn}/{max_turns}")

        # Step 3: Record customer response
        if os.path.exists(rec_wav):
            os.remove(rec_wav)

        print("🎙️ Recording customer (max 8 sec)...")
        esl_cmd(f"uuid_record {call_uuid} start {rec_wav}")

        time.sleep(8)

        esl_cmd(f"uuid_record {call_uuid} stop {rec_wav}")

        if not os.path.exists(rec_wav):
            print("⚠️ Recording not found. Ending call.")
            break

        # Step 4: Transcribe
        print("🧠 Transcribing with Whisper...")
        stt = WhisperSTT()
        user_text = stt.transcribe(rec_wav)

        print("👤 Customer said:", user_text if user_text else "(no speech detected)")

        if not user_text:
            bot_text = "Sorry, I couldn't hear you clearly. Thanks for your time. Goodbye!"
            tts_to_wav(bot_text, reply_wav)
            esl_cmd(f"uuid_broadcast {call_uuid} {reply_wav} aleg")
            time.sleep(4)
            break

        history.append({"role": "user", "content": user_text})

        # Step 5: LLM Reply
        print("🤖 Generating reply from OpenRouter...")
        bot_text = openrouter_chat(history)

        # Guardrail: keep it short
        bot_text = bot_text.replace("\n", " ").strip()
        if len(bot_text) > 250:
            bot_text = bot_text[:250]

        print("🤖 Bot reply:", bot_text)
        history.append({"role": "assistant", "content": bot_text})

        # Step 6: Speak reply
        tts_to_wav(bot_text, reply_wav)
        esl_cmd(f"uuid_broadcast {call_uuid} {reply_wav} aleg")
        time.sleep(6)

        # Exit if user wants to end
        lower = user_text.lower()
        if any(x in lower for x in ["no", "not interested", "stop", "busy", "later", "bye"]):
            ending = "No problem at all. Thank you, have a great day. Goodbye!"
            tts_to_wav(ending, reply_wav)
            esl_cmd(f"uuid_broadcast {call_uuid} {reply_wav} aleg")
            time.sleep(4)
            break

    # Step 7: Hangup
    print("📴 Hanging up...")
    esl_cmd(f"uuid_kill {call_uuid}")

    print("✅ Call ended.\n")


# =========================
# Run
# =========================
if __name__ == "__main__":
    """
    Example:
    export OPENROUTER_API_KEY="xxxx"
    python3 calling_agent.py +919876543210
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python calling_agent.py +919876543210")
        exit(1)

    TO_NUMBER = sys.argv[1].strip()

    if not TO_NUMBER.startswith("+"):
        print("❌ Number must be in E.164 format like +919876543210")
        exit(1)

    make_call(TO_NUMBER, max_turns=3)