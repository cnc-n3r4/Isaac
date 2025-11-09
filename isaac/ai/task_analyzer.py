"""
Task Analyzer - Intelligent task complexity detection and AI provider selection

Analyzes user requests to determine:
1. Task complexity (simple, medium, complex, expert)
2. Task type (chat, code, analysis, creative, etc.)
3. Optimal AI provider based on capabilities and cost
4. Estimated token usage for cost prediction

Part of Phase 3: Enhanced AI Routing

Configuration:
User-configurable via /config --ai-routing commands.
Settings stored in ~/.isaac/ai_routing_config.json
"""

import re
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskComplexity(Enum):
    """Task complexity levels for AI routing"""

    SIMPLE = "simple"  # Quick answers, basic commands - Grok/GPT-4o-mini
    MEDIUM = "medium"  # Standard queries, simple code - Grok
    COMPLEX = "complex"  # Multi-step reasoning, advanced code - Claude
    EXPERT = "expert"  # Architecture, deep analysis - Claude Opus


class TaskType(Enum):
    """Task type categories"""

    CHAT = "chat"  # General conversation
    CODE_READ = "code_read"  # Read/analyze code
    CODE_WRITE = "code_write"  # Write/edit code
    CODE_DEBUG = "code_debug"  # Debug/fix issues
    ANALYSIS = "analysis"  # Deep analysis/reasoning
    CREATIVE = "creative"  # Creative writing
    PLANNING = "planning"  # Project planning, architecture
    SEARCH = "search"  # Search/lookup tasks
    TOOL_USE = "tool_use"  # Tool/command execution


class TaskAnalyzer:
    """
    Analyzes tasks to determine optimal AI provider and routing strategy.

    Uses heuristics based on:
    - Message content analysis (keywords, patterns)
    - Tool requirements
    - Historical context
    - Token estimation
    """

    # Complexity indicators
    SIMPLE_INDICATORS = [
        r"\b(what is|who is|define|explain briefly|quick question)\b",
        r"^(hi|hello|hey|thanks|thank you)\b",
        r"\b(yes|no|ok|sure)\b$",
        r"\b(2\s*[\+\-\*\/]\s*2)",  # Simple math
    ]

    COMPLEX_INDICATORS = [
        r"\b(architecture|design pattern|refactor|optimize)\b",
        r"\b(debug|troubleshoot|diagnose|investigate)\b",
        r"\b(analyze|examine|review|assess|evaluate)\b",
        r"\b(explain in detail|comprehensive|thorough)\b",
        r"\b(multi-step|workflow|pipeline|integration)\b",
        r"\b(compare and contrast|trade-offs|pros and cons)\b",
    ]

    EXPERT_INDICATORS = [
        r"\b(system design|scalability|performance optimization)\b",
        r"\b(security audit|vulnerability|threat model)\b",
        r"\bdistributed\b.*\b(system|cache|caching|database|storage)\b",
        r"\b(microservices|event-driven)\b",
        r"\b(machine learning|neural network|algorithm design)\b",
        r"\b(database schema|data model|normalization)\b",
        r"\b(high availability|load balancing|fault tolerance)\b",
    ]

    # Task type patterns
    CODE_WRITE_PATTERNS = [
        r"\b(write|create|implement|build|generate|add)\b.*\b(function|class|method|component|API|endpoint|service|module)\b",
        r"\b(fix|patch|correct)\b.*\b(bug|error|issue)\b",
    ]

    CODE_READ_PATTERNS = [
        r"\b(read|show|display|view)\b.*\b(file|code|function|contents?)\b",
        r"\b(what does|how does)\b.*\b(work|function|do)\b",
        r"\bcontents? of\b.*\.(py|js|java|cpp|c|go|rs|rb)",
    ]

    ANALYSIS_PATTERNS = [
        r"\b(analyze|examine|review|audit|assess)\b",
        r"\b(find|search|locate)\b.*\b(pattern|issue|problem)\b",
    ]

    # Provider capabilities
    PROVIDER_CAPABILITIES = {
        "grok": {
            "max_complexity": TaskComplexity.COMPLEX,
            "strengths": [TaskType.CHAT, TaskType.SEARCH, TaskType.CODE_READ],
            "cost_per_1m_tokens": {"input": 5.0, "output": 15.0},
            "speed": "fast",
            "context_window": 128000,
        },
        "claude": {
            "max_complexity": TaskComplexity.EXPERT,
            "strengths": [
                TaskType.CODE_WRITE,
                TaskType.CODE_DEBUG,
                TaskType.ANALYSIS,
                TaskType.PLANNING,
                TaskType.TOOL_USE,
            ],
            "cost_per_1m_tokens": {"input": 3.0, "output": 15.0},
            "speed": "medium",
            "context_window": 200000,
        },
        "openai": {
            "max_complexity": TaskComplexity.MEDIUM,
            "strengths": [TaskType.CHAT, TaskType.CREATIVE, TaskType.SEARCH],
            "cost_per_1m_tokens": {"input": 0.15, "output": 0.60},  # GPT-4o-mini
            "speed": "fast",
            "context_window": 128000,
        },
    }

    def __init__(self, config_manager=None):
        """
        Initialize the task analyzer.

        Args:
            config_manager: Optional RoutingConfigManager instance.
                          If None, will create default instance.
        """
        # Load user configuration
        if config_manager is None:
            from isaac.ai.routing_config import RoutingConfigManager

            self.config_manager = RoutingConfigManager()
        else:
            self.config_manager = config_manager

        # Compile regex patterns for efficiency
        self.simple_patterns = [re.compile(p, re.IGNORECASE) for p in self.SIMPLE_INDICATORS]
        self.complex_patterns = [re.compile(p, re.IGNORECASE) for p in self.COMPLEX_INDICATORS]
        self.expert_patterns = [re.compile(p, re.IGNORECASE) for p in self.EXPERT_INDICATORS]

        self.code_write_patterns = [re.compile(p, re.IGNORECASE) for p in self.CODE_WRITE_PATTERNS]
        self.code_read_patterns = [re.compile(p, re.IGNORECASE) for p in self.CODE_READ_PATTERNS]
        self.analysis_patterns = [re.compile(p, re.IGNORECASE) for p in self.ANALYSIS_PATTERNS]

        # Load provider capabilities from config
        self._load_provider_capabilities()

    def _load_provider_capabilities(self):
        """Load provider capabilities from user configuration"""
        config = self.config_manager.get_all_settings()
        providers_config = config.get("providers", {})

        # Update PROVIDER_CAPABILITIES with user config
        for provider_name, provider_config in providers_config.items():
            if provider_name in self.PROVIDER_CAPABILITIES:
                # Update with user settings
                self.PROVIDER_CAPABILITIES[provider_name]["max_complexity"] = TaskComplexity(
                    provider_config.get("max_complexity", "medium")
                )
                self.PROVIDER_CAPABILITIES[provider_name]["cost_per_1m_tokens"] = {
                    "input": provider_config["pricing"]["input_per_1m"],
                    "output": provider_config["pricing"]["output_per_1m"],
                }
                self.PROVIDER_CAPABILITIES[provider_name]["speed"] = provider_config.get(
                    "speed", "medium"
                )
                self.PROVIDER_CAPABILITIES[provider_name]["context_window"] = provider_config.get(
                    "context_window", 128000
                )

                # Convert strength strings to TaskType enums
                strength_strs = provider_config.get("strengths", [])
                strengths = []
                for s in strength_strs:
                    try:
                        strengths.append(TaskType(s))
                    except ValueError:
                        pass  # Skip invalid task types
                self.PROVIDER_CAPABILITIES[provider_name]["strengths"] = strengths

    def analyze_task(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a task to determine complexity, type, and optimal provider.

        Args:
            messages: Conversation messages
            tools: Available tools (if any)
            context: Additional context (history, preferences, etc.)

        Returns:
            Analysis results with recommended provider
        """
        # Get the user's latest message
        user_message = self._get_latest_user_message(messages)
        if not user_message:
            return self._default_analysis()

        # Analyze complexity
        complexity = self._detect_complexity(user_message, tools, context)

        # Detect task type
        task_type = self._detect_task_type(user_message, tools)

        # Estimate token usage
        token_estimate = self._estimate_tokens(messages, tools)

        # Select optimal provider
        recommended_provider = self._select_provider(complexity, task_type, token_estimate, context)

        # Estimate cost
        cost_estimate = self._estimate_cost(recommended_provider, token_estimate)

        # Build analysis result
        analysis = {
            "complexity": complexity.value,
            "task_type": task_type.value,
            "recommended_provider": recommended_provider,
            "fallback_providers": self._get_fallback_providers(recommended_provider, complexity),
            "token_estimate": token_estimate,
            "cost_estimate": cost_estimate,
            "reasoning": self._explain_recommendation(complexity, task_type, recommended_provider),
            "confidence": self._calculate_confidence(user_message, complexity, task_type),
        }

        return analysis

    def _get_latest_user_message(self, messages: List[Dict[str, str]]) -> str:
        """Extract the latest user message from conversation"""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content", "")
        return ""

    def _detect_complexity(
        self, message: str, tools: Optional[List[Dict[str, Any]]], context: Optional[Dict[str, Any]]
    ) -> TaskComplexity:
        """Detect task complexity based on message content and context"""

        # Check for expert indicators first
        expert_score = sum(1 for pattern in self.expert_patterns if pattern.search(message))
        if expert_score >= 1:
            return TaskComplexity.EXPERT

        # Check for complex indicators
        complex_score = sum(1 for pattern in self.complex_patterns if pattern.search(message))
        if complex_score >= 1:  # Changed from 2 to 1 - single complex indicator is enough
            return TaskComplexity.COMPLEX

        # Check for simple indicators
        simple_score = sum(1 for pattern in self.simple_patterns if pattern.search(message))

        # Consider message length
        word_count = len(message.split())

        # Simple task criteria (must meet ALL):
        # 1. Has simple indicators OR very short message
        # 2. No complex indicators
        # 3. Short length (< 15 words)
        if (simple_score >= 1 or word_count < 8) and complex_score == 0 and word_count < 15:
            return TaskComplexity.SIMPLE

        # Complex task criteria (any one):
        # 1. Long message (> 50 words)
        # 2. Multiple tools (> 2)
        # 3. Contains "explain the difference" or comparison language
        if word_count > 50 or (tools and len(tools) > 2):
            return TaskComplexity.COMPLEX

        # Check for explanation/comparison requests (medium complexity minimum)
        if re.search(
            r"\b(explain|describe|compare|contrast|difference between)\b", message, re.IGNORECASE
        ):
            # If it's asking for differences or comparisons, at least MEDIUM
            if re.search(r"\b(difference|compare|contrast)\b", message, re.IGNORECASE):
                return TaskComplexity.MEDIUM

        # Default to medium for anything else
        return TaskComplexity.MEDIUM

    def _detect_task_type(self, message: str, tools: Optional[List[Dict[str, Any]]]) -> TaskType:
        """Detect the primary task type"""

        # Check for code writing
        if any(pattern.search(message) for pattern in self.code_write_patterns):
            return TaskType.CODE_WRITE

        # Check for code reading
        if any(pattern.search(message) for pattern in self.code_read_patterns):
            return TaskType.CODE_READ

        # Check for analysis
        if any(pattern.search(message) for pattern in self.analysis_patterns):
            return TaskType.ANALYSIS

        # Check for debugging keywords
        if re.search(r"\b(debug|fix|error|bug|issue|problem)\b", message, re.IGNORECASE):
            return TaskType.CODE_DEBUG

        # Check for planning keywords
        if re.search(r"\b(plan|design|architect|structure)\b", message, re.IGNORECASE):
            return TaskType.PLANNING

        # Check for search keywords
        if re.search(r"\b(search|find|lookup|locate)\b", message, re.IGNORECASE):
            return TaskType.SEARCH

        # Check if tools are provided
        if tools and len(tools) > 0:
            return TaskType.TOOL_USE

        # Default to chat
        return TaskType.CHAT

    def _estimate_tokens(
        self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, int]:
        """
        Estimate token usage for the request.

        Rough estimation: 1 token ≈ 4 characters for English text
        """
        # Calculate input tokens
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        input_tokens = total_chars // 4

        # Add tokens for tools (schema overhead)
        if tools:
            tool_tokens = len(tools) * 200  # Rough estimate per tool
            input_tokens += tool_tokens

        # Estimate output tokens based on task complexity
        # Simple tasks: ~100-500 tokens
        # Medium tasks: ~500-2000 tokens
        # Complex tasks: ~2000-8000 tokens
        output_tokens = 1000  # Default estimate

        return {
            "input": input_tokens,
            "output": output_tokens,
            "total": input_tokens + output_tokens,
        }

    def _select_provider(
        self,
        complexity: TaskComplexity,
        task_type: TaskType,
        token_estimate: Dict[str, int],
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Select the optimal AI provider based on task analysis and user configuration"""

        # Check context for user preferences (highest priority)
        if context and "prefer_provider" in context:
            preferred = context["prefer_provider"]
            # Validate if preferred provider can handle the complexity
            if self._can_handle_complexity(preferred, complexity):
                return preferred

        # Check for task-type specific overrides in config
        task_type_provider = self.config_manager.get_provider_for_task_type(task_type.value)
        if task_type_provider and self._can_handle_complexity(task_type_provider, complexity):
            return task_type_provider

        # Use complexity-based routing from config
        complexity_provider = self.config_manager.get_provider_for_complexity(complexity.value)
        if self._can_handle_complexity(complexity_provider, complexity):
            return complexity_provider

        # Fallback: use enabled providers in order of capability
        enabled_providers = self.config_manager.get_enabled_providers()
        for provider in ["claude", "grok", "openai"]:
            if provider in enabled_providers and self._can_handle_complexity(provider, complexity):
                return provider

        # Last resort: return first enabled provider
        if enabled_providers:
            return enabled_providers[0]

        # Absolute fallback (should never happen)
        return "grok"

    def _can_handle_complexity(self, provider: str, complexity: TaskComplexity) -> bool:
        """Check if a provider can handle the given complexity level"""
        if provider not in self.PROVIDER_CAPABILITIES:
            return False

        provider_info = self.PROVIDER_CAPABILITIES[provider]
        max_complexity = provider_info["max_complexity"]

        complexity_levels = [
            TaskComplexity.SIMPLE,
            TaskComplexity.MEDIUM,
            TaskComplexity.COMPLEX,
            TaskComplexity.EXPERT,
        ]

        return complexity_levels.index(complexity) <= complexity_levels.index(max_complexity)

    def _get_fallback_providers(self, primary: str, complexity: TaskComplexity) -> List[str]:
        """Get ordered fallback providers"""
        all_providers = ["grok", "claude", "openai"]

        # Remove primary
        fallbacks = [p for p in all_providers if p != primary]

        # Filter by capability
        fallbacks = [p for p in fallbacks if self._can_handle_complexity(p, complexity)]

        # Sort by capability (prefer more capable providers)
        capability_order = {"claude": 3, "grok": 2, "openai": 1}
        fallbacks.sort(key=lambda p: capability_order.get(p, 0), reverse=True)

        return fallbacks

    def _estimate_cost(self, provider: str, token_estimate: Dict[str, int]) -> Dict[str, float]:
        """Estimate the cost for this request"""
        if provider not in self.PROVIDER_CAPABILITIES:
            return {"input": 0.0, "output": 0.0, "total": 0.0}

        pricing = self.PROVIDER_CAPABILITIES[provider]["cost_per_1m_tokens"]

        input_cost = (token_estimate["input"] / 1_000_000) * pricing["input"]
        output_cost = (token_estimate["output"] / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost

        return {"input": input_cost, "output": output_cost, "total": total_cost}

    def _explain_recommendation(
        self, complexity: TaskComplexity, task_type: TaskType, provider: str
    ) -> str:
        """Provide human-readable explanation for the provider selection"""
        reasons = []

        # Complexity reasoning
        if complexity == TaskComplexity.EXPERT:
            reasons.append("Expert-level complexity requires advanced reasoning")
        elif complexity == TaskComplexity.COMPLEX:
            reasons.append("Complex task benefits from sophisticated analysis")
        elif complexity == TaskComplexity.SIMPLE:
            reasons.append("Simple task optimized for cost-efficiency")

        # Task type reasoning
        if task_type == TaskType.CODE_WRITE:
            reasons.append("Code generation requires strong programming capabilities")
        elif task_type == TaskType.TOOL_USE:
            reasons.append("Tool calling requires reliable function support")
        elif task_type == TaskType.ANALYSIS:
            reasons.append("Deep analysis benefits from advanced reasoning")

        # Provider reasoning
        provider_info = self.PROVIDER_CAPABILITIES.get(provider, {})
        speed = provider_info.get("speed", "unknown")
        reasons.append(f"Selected {provider} for {speed} response")

        return " | ".join(reasons)

    def _calculate_confidence(
        self, message: str, complexity: TaskComplexity, task_type: TaskType
    ) -> float:
        """Calculate confidence score (0.0 to 1.0) for the analysis"""
        confidence = 0.5  # Base confidence

        # Increase confidence for clear indicators
        if any(pattern.search(message) for pattern in self.expert_patterns):
            confidence += 0.3
        elif any(pattern.search(message) for pattern in self.complex_patterns):
            confidence += 0.2
        elif any(pattern.search(message) for pattern in self.simple_patterns):
            confidence += 0.2

        # Increase confidence for clear task type indicators
        if any(pattern.search(message) for pattern in self.code_write_patterns):
            confidence += 0.2
        elif any(pattern.search(message) for pattern in self.analysis_patterns):
            confidence += 0.1

        # Cap at 1.0
        return min(confidence, 1.0)

    def _default_analysis(self) -> Dict[str, Any]:
        """Return default analysis when no user message is found"""
        return {
            "complexity": TaskComplexity.MEDIUM.value,
            "task_type": TaskType.CHAT.value,
            "recommended_provider": "grok",
            "fallback_providers": ["claude", "openai"],
            "token_estimate": {"input": 100, "output": 500, "total": 600},
            "cost_estimate": {"input": 0.0005, "output": 0.0075, "total": 0.008},
            "reasoning": "Default analysis - no specific task detected",
            "confidence": 0.3,
        }

    def get_provider_info(self, provider: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a provider's capabilities"""
        return self.PROVIDER_CAPABILITIES.get(provider)

    def compare_providers(
        self, complexity: TaskComplexity, task_type: TaskType
    ) -> List[Dict[str, Any]]:
        """
        Compare all providers for a given task.

        Returns ranked list of providers with scores.
        """
        comparisons = []

        for provider, info in self.PROVIDER_CAPABILITIES.items():
            score = 0.0

            # Can handle complexity?
            if self._can_handle_complexity(provider, complexity):
                score += 3.0
            else:
                continue  # Skip if can't handle

            # Task type strength
            if task_type in info["strengths"]:
                score += 2.0

            # Speed bonus
            if info["speed"] == "fast":
                score += 1.0
            elif info["speed"] == "medium":
                score += 0.5

            # Cost efficiency (inverse of cost)
            avg_cost = (
                info["cost_per_1m_tokens"]["input"] + info["cost_per_1m_tokens"]["output"]
            ) / 2
            cost_score = 10.0 / avg_cost  # Higher score for lower cost
            score += cost_score

            comparisons.append(
                {
                    "provider": provider,
                    "score": score,
                    "speed": info["speed"],
                    "cost_per_1m": info["cost_per_1m_tokens"],
                    "strengths": [t.value for t in info["strengths"]],
                }
            )

        # Sort by score descending
        comparisons.sort(key=lambda x: x["score"], reverse=True)

        return comparisons
