from prometheus_client import Counter, Histogram
from prometheus_client import Gauge


tool_calls_total = Counter(
    "tool_calls_total",
    "Total tool calls",
    labelnames=("tool", "result"),
)

tool_call_latency_ms = Histogram(
    "tool_call_latency_ms",
    "Tool call latency in ms",
    labelnames=("tool",),
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2000),
)

mqtt_publish_total = Counter(
    "mqtt_publish_total",
    "MQTT publish operations",
    labelnames=("topic",),
)

mqtt_wait_time_ms = Histogram(
    "mqtt_wait_time_ms",
    "Wait time for MQTT state messages in ms",
    labelnames=("topic",),
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2000, 5000),
)

trigger_firings_total = Counter(
    "trigger_firings_total",
    "Number of trigger firings",
    labelnames=("rule_id", "result"),
)

agent_commands_total = Counter(
    "agent_commands_total",
    "Agent commands processed",
    labelnames=("intent", "result"),
)

agent_step_latency_ms = Histogram(
    "agent_step_latency_ms",
    "Per-step latency for agent executor",
    labelnames=("tool",),
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2000),
)

critical_actions_total = Counter(
    "critical_actions_total",
    "Critical actions executed",
    labelnames=("tool",),
)

rules_version = Gauge(
    "rules_version",
    "Monotonic version of active rules set",
)


# Analysis metrics
analysis_insights_total = Counter(
    "analysis_insights_total",
    "Number of analysis insights generated",
    labelnames=("kind",),
)

analysis_ticks_total = Counter(
    "analysis_ticks_total",
    "Background analyzer ticks",
)


# Vision/Gemini metrics
vision_calls_total = Counter(
    "vision_calls_total",
    "Vision API calls",
    labelnames=("provider", "op", "result"),
)

vision_call_latency_ms = Histogram(
    "vision_call_latency_ms",
    "Vision API call latency in ms",
    labelnames=("provider", "op"),
    buckets=(25, 50, 100, 200, 400, 800, 1500, 3000, 5000, 10000),
)

gemini_calls_total = Counter(
    "gemini_calls_total",
    "Gemini LLM calls",
    labelnames=("model", "result"),
)

gemini_call_latency_ms = Histogram(
    "gemini_call_latency_ms",
    "Gemini LLM latency in ms",
    labelnames=("model",),
    buckets=(50, 100, 200, 400, 800, 1500, 3000, 5000, 10000, 20000),
)


