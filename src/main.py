import asyncio
from viam.module.module import Module
try:
    from models.mic_speech_sentiment import MicSpeechSentiment
except ModuleNotFoundError:
    # when running as local module with run.sh
    from .models.mic_speech_sentiment import MicSpeechSentiment


if __name__ == '__main__':
    asyncio.run(Module.run_from_registry())
