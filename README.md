# Module mic-speech-sentiment 

A modular sensor component that combines speech-to-text and sentiment analysis capabilities. This module continuously listens for speech using a speech service (like stt-vosk), analyzes the sentiment of the heard text using a sentiment service, and provides readings with configurable expiration times.

## Model mcvella:mic-speech-sentiment:mic-speech-sentiment

A sensor component that provides real-time speech-to-text with sentiment analysis. The component automatically starts listening when configured and continuously processes speech input, analyzing sentiment for each heard phrase.

### Dependencies

This model requires two services to be configured on your machine and specified in the attributes:

1. **Speech Service**: A service that implements the [Speech Service API](https://github.com/viam-labs/speech-service-api) with the `listen()` method (e.g., [stt-vosk](https://github.com/viam-labs/stt-vosk))
2. **Sentiment Service**: A service that implements `do_command()` for sentiment analysis (e.g., [text-sentiment](https://app.viam.com/module/mcvella/text-sentiment))

### Configuration
The following attribute template can be used to configure this model:

```json
{
  "speech_service": "speech_service",
  "sentiment_service": "sentiment_service",
  "reading_expiration_seconds": 20
}
```

#### Attributes

The following attributes are available for this model:

| Name                      | Type   | Inclusion | Description                                                                                |
|---------------------------|--------|-----------|--------------------------------------------------------------------------------------------|
| `speech_service`          | string | Required  | Name of the speech service to use for listening (e.g., "speech_service")                |
| `sentiment_service`       | string | Required  | Name of the sentiment service to use for analysis (e.g., "sentiment_service")           |
| `reading_expiration_seconds` | int    | Optional  | Number of seconds after which a reading expires and is no longer returned. Default: 20 |

#### Example Configuration

```json
{
  "speech_service": "speech_service",
  "sentiment_service": "sentiment_service", 
  "reading_expiration_seconds": 30
}
```

### Readings

The sensor returns readings in the following format:

```json
{
  "text_heard": "Good morning to you",
  "sentiment": "Positive", 
  "time": "2024-01-15T10:30:45.123456"
}
```

Each reading includes:
- **text_heard**: The transcribed text from the speech service
- **sentiment**: The sentiment analysis result (e.g., "Positive", "Negative", "Neutral")
- **time**: ISO format timestamp of when the speech was heard

Readings automatically expire after the configured number of seconds and will return an empty result until new speech is detected.

### DoCommand

The model supports several commands for controlling the listening behavior:

#### Start Listening
```json
{
  "command": "start_listening"
}
```
Starts the continuous listening loop if it's not already running.

#### Stop Listening
```json
{
  "command": "stop_listening"
}
```
Stops the continuous listening loop.

#### Get Status
```json
{
  "command": "get_status"
}
```
Returns the current status of the sensor:
```json
{
  "is_listening": true,
  "has_reading": true,
  "reading_expiration_seconds": 20
}
```

### Usage Example

1. Configure a speech service (e.g., stt-vosk) on your machine that implements the [Speech Service API](https://github.com/viam-labs/speech-service-api)
2. Configure a sentiment service (e.g., text-sentiment) on your machine  
3. Add this sensor component and specify the speech and sentiment service names in the attributes
4. The sensor will automatically start listening and analyzing sentiment
5. Use `get_readings()` to retrieve the latest speech and sentiment data

### Error Handling

The sensor includes robust error handling:
- Automatically retries on speech service errors
- Logs all errors for debugging
- Continues listening even if individual sentiment analysis calls fail
- Gracefully handles service disconnections
