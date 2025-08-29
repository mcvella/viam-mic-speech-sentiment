import asyncio
import json
from datetime import datetime, timedelta
from typing import (Any, ClassVar, Dict, Final, List, Mapping, Optional,
                    Sequence, Tuple, cast)

from typing_extensions import Self
from viam.components.sensor import *
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import Geometry, ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.services.generic import Generic
from viam.utils import SensorReading, ValueTypes, struct_to_dict

# Import the SpeechService from the speech-service-api
try:
    from speech_service_api import SpeechService
except ImportError:
    # Fallback for when the module is not available
    SpeechService = None


class MicSpeechSentiment(Sensor, EasyResource):
    # To enable debug-level logging, either run viam-server with the --debug option,
    # or configure your resource/machine to display debug logs.
    MODEL: ClassVar[Model] = Model(
        ModelFamily("mcvella", "mic-speech-sentiment"), "mic-speech-sentiment"
    )

    def __init__(self, name: str):
        super().__init__(name)
        self.speech_service = None
        self.sentiment_service = None
        self.reading_expiration_seconds = 20
        self.latest_reading = None
        self.listening_task = None
        self.is_listening = False

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        """This method creates a new instance of this Sensor component.
        The default implementation sets the name from the `config` parameter and then calls `reconfigure`.

        Args:
            config (ComponentConfig): The configuration for this resource
            dependencies (Mapping[ResourceName, ResourceBase]): The dependencies (both required and optional)

        Returns:
            Self: The resource
        """
        return super().new(config, dependencies)

    @classmethod
    def validate_config(
        cls, config: ComponentConfig
    ) -> Tuple[Sequence[str], Sequence[str]]:
        """This method allows you to validate the configuration object received from the machine,
        as well as to return any required dependencies or optional dependencies based on that `config`.

        Args:
            config (ComponentConfig): The configuration for this resource

        Returns:
            Tuple[Sequence[str], Sequence[str]]: A tuple where the
                first element is a list of required dependencies and the
                second element is a list of optional dependencies
        """
        attributes = struct_to_dict(config.attributes)
        speech_service = attributes.get("speech_service")
        sentiment_service = attributes.get("sentiment_service")
        
        required_deps = []
        if speech_service:
            required_deps.append(speech_service)
        if sentiment_service:
            required_deps.append(sentiment_service)
            
        return required_deps, []

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        """This method allows you to dynamically update your service when it receives a new `config` object.

        Args:
            config (ComponentConfig): The new configuration
            dependencies (Mapping[ResourceName, ResourceBase]): Any dependencies (both required and optional)
        """
        # Read config attributes
        attributes = struct_to_dict(config.attributes)
        
        # Extract required attributes
        speech_service_name = attributes.get("speech_service")
        sentiment_service_name = attributes.get("sentiment_service")
        reading_expiration_seconds_raw = attributes.get("reading_expiration_seconds")
        self.reading_expiration_seconds = int(reading_expiration_seconds_raw) if reading_expiration_seconds_raw is not None else 20
        
        # Initialize services as their Viam types
        if speech_service_name:
            if SpeechService is None:
                raise ImportError("speech_service_api is required. Add 'speech_service_api @ git+https://github.com/viam-labs/speech-service-api.git@main' to requirements.txt")
            speech_service_dep = dependencies[SpeechService.get_resource_name(speech_service_name)]
            self.speech_service = cast(SpeechService, speech_service_dep)
            
        if sentiment_service_name:
            sentiment_service_dep = dependencies[Generic.get_resource_name(sentiment_service_name)]
            self.sentiment_service = cast(Generic, sentiment_service_dep)
        
        if not self.speech_service:
            raise ValueError("speech_service dependency is required")
        if not self.sentiment_service:
            raise ValueError("sentiment_service dependency is required")
        
        self.logger.info(f"Configured with speech_service: {speech_service_name}, sentiment_service: {sentiment_service_name}, reading_expiration_seconds: {self.reading_expiration_seconds}")
        
        # Start listening if not already started
        if not self.is_listening:
            self.start_listening()

    def start_listening(self):
        """Start the continuous listening loop"""
        if self.is_listening:
            return
        
        self.is_listening = True
        self.listening_task = asyncio.create_task(self._listen_loop())
        self.logger.info("Started listening for speech and sentiment analysis")

    async def _listen_loop(self):
        """Continuous loop that listens for speech and analyzes sentiment"""
        try:
            while self.is_listening:
                try:
                    # Listen for speech
                    text = await self.speech_service.listen()
                    
                    if text and text.strip():
                        self.logger.info(f"Heard: {text}")
                        
                        # Get sentiment analysis
                        sentiment_result = await self.sentiment_service.do_command({
                            "command": "get_sentiment",
                            "text": text
                        })
                        
                        # Extract sentiment from result
                        sentiment = sentiment_result.get("sentiment", "Unknown")
                        self.logger.info(f"Sentiment: {sentiment}")
                        
                        # Store the reading with timestamp
                        self.latest_reading = {
                            "text_heard": text,
                            "sentiment": sentiment,
                            "time": datetime.now()
                        }
                    else:
                        self.logger.info("No speech heard")
                        
                except Exception as e:
                    self.logger.error(f"Error in listening loop: {e}")
                    await asyncio.sleep(1)  # Brief pause before retrying
                    
        except asyncio.CancelledError:
            self.logger.info("Listening loop cancelled")
        except Exception as e:
            self.logger.error(f"Fatal error in listening loop: {e}")
        finally:
            self.is_listening = False

    async def get_readings(
        self,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Mapping[str, Any]:
        """Get the latest reading if it hasn't expired"""
        if not self.latest_reading:
            # Return a default reading when no speech has been heard
            return {
                "text_heard": "",
                "sentiment": "None",
                "time": datetime.now().isoformat(),
                "is_listening": self.is_listening
            }
        
        # Check if reading has expired
        time_heard = self.latest_reading["time"]
        expiration_time = time_heard + timedelta(seconds=self.reading_expiration_seconds)
        
        if datetime.now() > expiration_time:
            # Reading has expired, clear it and return default
            self.latest_reading = None
            return {
                "text_heard": "",
                "sentiment": "None",
                "time": datetime.now().isoformat(),
                "is_listening": self.is_listening
            }
        
        # Return the reading
        return {
            "text_heard": self.latest_reading["text_heard"],
            "sentiment": self.latest_reading["sentiment"],
            "time": time_heard.isoformat(),
            "is_listening": self.is_listening
        }

    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Mapping[str, ValueTypes]:
        """Handle custom commands"""
        cmd = command.get("command", "")
        
        if cmd == "start_listening":
            self.start_listening()
            return {"status": "started"}
        elif cmd == "stop_listening":
            self.is_listening = False
            if self.listening_task:
                self.listening_task.cancel()
            return {"status": "stopped"}
        elif cmd == "get_status":
            return {
                "is_listening": self.is_listening,
                "has_reading": self.latest_reading is not None,
                "reading_expiration_seconds": self.reading_expiration_seconds
            }
        else:
            return {"error": f"Unknown command: {cmd}"}

    async def get_geometries(
        self, *, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None
    ) -> List[Geometry]:
        """Return the geometries associated with this sensor"""
        return []

    async def close(self):
        """Clean up resources when the sensor is closed"""
        self.is_listening = False
        if self.listening_task:
            self.listening_task.cancel()
            try:
                await self.listening_task
            except asyncio.CancelledError:
                pass

