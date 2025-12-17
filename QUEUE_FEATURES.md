# Queue Manager Feature Documentation

## Overview

The Queue Manager is a sophisticated request management system that mimics human usage patterns for interacting with Perplexity AI. It provides rate limiting, priority handling, and intelligent account rotation to prevent detection and API blocking.

## Key Features

### 1. Human Behavior Simulation
- **Variable Delays**: Configurable min/max delays between requests (default: 5-20 seconds)
- **Peak Hours**: Higher activity during configurable peak hours (default: 9 AM - 5 PM)
- **Weekend Behavior**: Reduced activity on weekends (configurable factor)
- **Burst Patterns**: Random bursts of requests mimicking human behavior
- **Idle Periods**: Random idle periods between requests

### 2. Priority System
- **LOW**: Background tasks, non-urgent queries
- **NORMAL**: Standard queries (default)
- **HIGH**: Important queries requiring faster processing
- **URGENT**: Critical queries, processed first

### 3. Account Management
- **Automatic Selection**: Chooses accounts based on availability and usage patterns
- **Load Balancing**: Distributes requests across multiple accounts
- **Concurrent Limits**: Configurable max concurrent requests per account (default: 3)
- **Usage Tracking**: Tracks when each account was last used

### 4. Request Queuing
- **Per-Priority Queues**: Separate queues for each priority level
- **Smart Processing**: Always processes highest priority available requests
- **Statistics**: Tracks total, completed, and failed requests

## API Endpoints

### Queue-Based Queries
```
GET /api/query_queue_sync
- Submits query and waits for completion
- Parameters: query, priority, timeout (default: 300s)

GET /api/query_queue_async
- Submits query and returns immediately with request ID
- Use GET /api/queue/status to check progress
```

### Queue Management
```
GET /api/queue/status
- Returns queue status, sizes, active requests, account usage

GET /api/queue/settings/behavior
- Returns current human behavior settings

POST /api/queue/settings/behavior
- Updates human behavior settings
- Body: JSON with delay settings, peak hours, etc.

POST /api/queue/start
- Starts the queue manager

POST /api/queue/stop
- Stops the queue manager

DELETE /api/queue/active_requests
- Cancels all active requests
```

## Configuration

### HumanBehaviorSettings
```json
{
  "min_delay_seconds": 5.0,      // Minimum delay between requests
  "max_delay_seconds": 20.0,     // Maximum delay between requests  
  "peak_hours_start": 9,          // Peak hours start (24h)
  "peak_hours_end": 17,           // Peak hours end (24h)
  "weekend_factor": 0.3,          // Activity reduction on weekends
  "burst_probability": 0.1,        // Probability of burst behavior
  "burst_size": 3,                // Maximum burst size
  "idle_probability": 0.05         // Probability of idle periods
}
```

### QueueManager Settings
```python
QueueManager(
    cookie_manager=cookie_manager,
    behavior_settings=behavior_settings,
    max_concurrent_requests=3       // Max concurrent per account
)
```

## Usage Examples

### 1. Basic Queue Query
```bash
curl "http://localhost:8000/api/query_queue_sync?q=What%20is%20AI?&priority=normal&timeout=300"
```

### 2. High Priority Query
```bash
curl "http://localhost:8000/api/query_queue_async?q=Urgent%20question&priority=high"
```

### 3. Get Queue Status
```bash
curl "http://localhost:8000/api/queue/status"
```

### 4. Update Behavior Settings
```bash
curl -X POST "http://localhost:8000/api/queue/settings/behavior" \
  -H "Content-Type: application/json" \
  -d '{
    "min_delay_seconds": 10.0,
    "max_delay_seconds": 30.0,
    "peak_hours_start": 8,
    "peak_hours_end": 18
  }'
```

## Dashboard Features

The web dashboard includes:
- **Real-time Queue Status**: Active requests, queue sizes, account usage
- **Behavior Settings Control**: Configure human-like timing patterns
- **Queue Controls**: Start/stop queue, refresh status
- **API Examples**: Ready-to-use curl commands

## Advanced Features

### 1. Burst Behavior
Randomly processes multiple requests quickly (mimicking rapid human queries), then takes a longer break.

### 2. Account Rotation
Automatically selects accounts based on:
- Current concurrent request limits
- Time since last use
- Account availability

### 3. Error Handling
- Automatic retry on failed requests
- Graceful degradation when accounts are invalid
- Detailed error reporting with account context

### 4. Statistics & Monitoring
- Request completion rates
- Average wait times
- Hourly request patterns
- Account usage distribution

## Best Practices

### 1. Production Settings
```json
{
  "min_delay_seconds": 10.0,
  "max_delay_seconds": 45.0,
  "peak_hours_start": 9,
  "peak_hours_end": 17,
  "weekend_factor": 0.2,
  "burst_probability": 0.05,
  "burst_size": 2,
  "idle_probability": 0.1
}
```

### 2. Development Settings
```json
{
  "min_delay_seconds": 2.0,
  "max_delay_seconds": 10.0,
  "peak_hours_start": 9,
  "peak_hours_end": 17,
  "weekend_factor": 0.5,
  "burst_probability": 0.2,
  "burst_size": 3,
  "idle_probability": 0.05
}
```

### 3. Monitoring
- Check `/api/queue/status` regularly for queue health
- Monitor failed requests to detect account issues
- Adjust behavior settings based on usage patterns

## Implementation Notes

- **Memory Management**: Uses asyncio for efficient concurrent processing
- **Thread Safety**: Safe for multiple concurrent users
- **Scalability**: Handles thousands of requests efficiently
- **Compatibility**: Works with existing Perplexity client features

The queue manager transforms high-volume API usage into natural, human-like patterns that are less likely to trigger detection or rate limiting.