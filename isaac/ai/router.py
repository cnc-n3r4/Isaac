"""
AI Router - Phase 3 Enhanced
Intelligent routing with automatic task analysis, cost optimization, and smart fallback
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import AIResponse, BaseAIClient
from .claude_client import ClaudeClient
from .cost_optimizer import CostOptimizer
from .grok_client import GrokClient
from .openai_client import OpenAIClient
from .routing_config import RoutingConfigManager
from .task_analyzer import TaskAnalyzer


class AIRouter:
    """
    Phase 3: Enhanced AI Router with Intelligent Task Analysis and Cost Optimization

    Features:
    - Automatic task complexity detection
    - Intelligent provider selection based on task type
    - Advanced cost tracking and budget management
    - Smart fallback with context preservation
    - Performance monitoring and analytics
    """

    def __init__(self, config_path: Optional[Path] = None, session_mgr=None):
        """
        Initialize router with Phase 3 enhancements

        Args:
            config_path: Path to AI config file (defaults to ~/.isaac/ai_config.json)
            session_mgr: SessionManager instance (optional, for Isaac integration)
        """
        self.session_mgr = session_mgr
        if config_path is None:
            config_path = Path.home() / ".isaac" / "ai_config.json"

        self.config_path = config_path
        self.config = self._load_config()

        # Initialize Phase 3 components
        routing_config_path = Path.home() / ".isaac" / "ai_routing_config.json"
        cost_storage_path = Path.home() / ".isaac" / "cost_tracking.json"

        self.routing_config = RoutingConfigManager(routing_config_path)
        self.task_analyzer = TaskAnalyzer(config_manager=self.routing_config)
        self.cost_optimizer = CostOptimizer(self.routing_config, cost_storage_path)

        # Initialize clients
        self.clients: Dict[str, Optional[BaseAIClient]] = {
            "grok": None,
            "claude": None,
            "openai": None,
        }

        self._init_clients()

        # Legacy usage tracking (kept for backward compatibility)
        self.usage_stats = {
            "grok": {"calls": 0, "tokens": 0, "cost": 0.0, "failures": 0},
            "claude": {"calls": 0, "tokens": 0, "cost": 0.0, "failures": 0},
            "openai": {"calls": 0, "tokens": 0, "cost": 0.0, "failures": 0},
        }

        # Phase 3: Performance tracking
        self.performance_stats = {
            "grok": {"total_time": 0.0, "requests": 0, "avg_time": 0.0},
            "claude": {"total_time": 0.0, "requests": 0, "avg_time": 0.0},
            "openai": {"total_time": 0.0, "requests": 0, "avg_time": 0.0},
        }

    def _load_config(self) -> Dict[str, Any]:
        """Load AI configuration"""
        default_config = {
            "providers": {
                "grok": {
                    "enabled": True,
                    "api_key_env": "XAI_API_KEY",
                    "model": "grok-beta",
                    "timeout": 60,
                    "max_retries": 2,
                },
                "claude": {
                    "enabled": True,
                    "api_key_env": "ANTHROPIC_API_KEY",
                    "model": "claude-3-5-sonnet-20241022",
                    "timeout": 60,
                    "max_retries": 1,
                },
                "openai": {
                    "enabled": True,
                    "api_key_env": "OPENAI_API_KEY",
                    "model": "gpt-4o-mini",
                    "timeout": 60,
                    "max_retries": 1,
                },
            },
            "routing": {
                "strategy": "fallback",  # 'fallback' or 'cost_optimized'
                "prefer_provider": "grok",  # Primary provider
                "cost_limit_daily": 10.0,  # Daily cost limit in USD
                "enable_tracking": True,
            },
            "defaults": {"temperature": 0.7, "max_tokens": 4096},
        }

        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    loaded_config = json.load(f)
                # Merge with defaults
                for key in default_config:
                    if key not in loaded_config:
                        loaded_config[key] = default_config[key]
                return loaded_config
            except Exception as e:
                print(f"Warning: Failed to load AI config: {e}")
                return default_config
        else:
            # Save default config
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(default_config, f, indent=2)
            return default_config

    def _init_clients(self):
        """Initialize AI clients from config"""
        for provider, settings in self.config["providers"].items():
            if not settings["enabled"]:
                continue

            # Get API key - first try session manager, then environment
            api_key = None
            if self.session_mgr:
                # Get API key from session config
                if provider == "grok":
                    api_key = self.session_mgr.config.get(
                        "xai_api_key"
                    ) or self.session_mgr.config.get("api_key")
                elif provider == "claude":
                    api_key = self.session_mgr.config.get(
                        "claude_api_key"
                    ) or self.session_mgr.config.get("anthropic_api_key")
                elif provider == "openai":
                    api_key = self.session_mgr.config.get("openai_api_key")
            else:
                # Get API key from environment
                api_key_env = settings["api_key_env"]
                api_key = os.environ.get(api_key_env)

            if not api_key:
                print(f"Warning: API key not found for {provider}, disabled")
                continue

            # Initialize client
            client_config = {"timeout": settings["timeout"], "model": settings["model"]}

            try:
                if provider == "grok":
                    self.clients["grok"] = GrokClient(api_key, client_config)
                elif provider == "claude":
                    self.clients["claude"] = ClaudeClient(api_key, client_config)
                elif provider == "openai":
                    self.clients["openai"] = OpenAIClient(api_key, client_config)
            except Exception as e:
                print(f"Warning: Failed to initialize {provider}: {e}")

    def _get_fallback_order(self, prefer: Optional[str] = None) -> List[str]:
        """Get provider fallback order"""
        prefer = prefer or self.config["routing"]["prefer_provider"]

        # Default order
        default_order = ["grok", "claude", "openai"]

        # Move preferred to front
        if prefer in default_order:
            order = [prefer]
            order.extend([p for p in default_order if p != prefer])
            return order

        return default_order

    def _update_stats(self, provider: str, response: AIResponse, success: bool):
        """Update usage statistics (legacy, kept for backward compatibility)"""
        stats = self.usage_stats[provider]
        stats["calls"] += 1

        if success:
            tokens = response.usage.get("prompt_tokens", 0) + response.usage.get(
                "completion_tokens", 0
            )
            stats["tokens"] += tokens

            client = self.clients[provider]
            if client:
                cost = client.get_cost_estimate(response.usage)
                stats["cost"] += cost
        else:
            stats["failures"] += 1

    def _update_performance_stats(self, provider: str, elapsed_time: float):
        """Phase 3: Track performance metrics"""
        stats = self.performance_stats[provider]
        stats["total_time"] += elapsed_time
        stats["requests"] += 1
        stats["avg_time"] = stats["total_time"] / stats["requests"]

    def _check_cost_limit(self) -> bool:
        """Check if daily cost limit exceeded"""
        if not self.config["routing"]["enable_tracking"]:
            return True

        total_cost = sum(stats["cost"] for stats in self.usage_stats.values())
        limit = self.config["routing"]["cost_limit_daily"]

        return total_cost < limit

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        prefer_provider: Optional[str] = None,
        **kwargs,
    ) -> AIResponse:
        """
        Phase 3: Enhanced chat with intelligent routing and cost optimization

        Args:
            messages: Conversation messages
            tools: Optional tool schemas
            prefer_provider: Override preferred provider (bypasses TaskAnalyzer)
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            AIResponse with enhanced metadata about routing decisions
        """
        # Phase 3: Analyze task to determine optimal provider
        task_analysis = None
        if prefer_provider is None:
            # Use TaskAnalyzer for intelligent provider selection
            task_analysis = self.task_analyzer.analyze_task(
                messages=messages,
                tools=tools,
                context={"available_providers": self.get_available_providers()},
            )
            recommended_provider = task_analysis["recommended_provider"]

            # Estimate token usage for budget check
            estimated_tokens = task_analysis.get(
                "estimated_tokens", {"input": 1000, "output": 1000}
            )
        else:
            # User specified provider preference
            recommended_provider = prefer_provider
            estimated_tokens = {"input": 1000, "output": 1000}  # Conservative estimate

        # Phase 3: Check if we can afford this request
        can_afford, affordability_reason = self.cost_optimizer.can_afford_request(
            provider=recommended_provider, estimated_tokens=estimated_tokens
        )

        if not can_afford:
            # Try to suggest cheaper alternative
            cheaper_provider = self.cost_optimizer.suggest_cheaper_provider(
                complexity=task_analysis.get("complexity", "medium") if task_analysis else "medium",
                estimated_tokens=estimated_tokens,
            )

            if cheaper_provider and cheaper_provider in self.get_available_providers():
                # Use cheaper alternative
                recommended_provider = cheaper_provider
                affordability_reason = f"Switched to {cheaper_provider} (more affordable)"
            else:
                # Cannot afford any provider
                return AIResponse(
                    content="",
                    error=f"Budget limit reached: {affordability_reason}",
                    provider="router",
                    metadata={
                        "budget_status": self.cost_optimizer.check_budget_status(),
                        "reason": affordability_reason,
                    },
                )

        # Build fallback order with recommended provider first
        fallback_order = self._get_fallback_order(recommended_provider)

        # Phase 3: Context preservation for fallback
        routing_context = {
            "original_provider": recommended_provider,
            "task_analysis": task_analysis,
            "affordability": affordability_reason,
            "attempt_history": [],
        }

        # Try each provider in fallback order
        last_error = None
        for provider in fallback_order:
            client = self.clients.get(provider)
            if not client:
                routing_context["attempt_history"].append(
                    {
                        "provider": provider,
                        "status": "unavailable",
                        "reason": "Client not initialized",
                    }
                )
                continue

            try:
                # Start performance timer
                start_time = time.time()

                # Get provider-specific settings
                provider_config = self.config["providers"][provider]
                model = kwargs.get("model") or provider_config["model"]
                temperature = kwargs.get("temperature") or self.config["defaults"]["temperature"]
                max_tokens = kwargs.get("max_tokens") or self.config["defaults"]["max_tokens"]

                # Make request
                response = client.chat(
                    messages=messages,
                    model=model,
                    tools=tools,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **{
                        k: v
                        for k, v in kwargs.items()
                        if k not in ["model", "temperature", "max_tokens"]
                    },
                )

                # Track performance
                elapsed_time = time.time() - start_time
                self._update_performance_stats(provider, elapsed_time)

                # Update legacy stats
                self._update_stats(provider, response, response.success)

                # If successful, track with CostOptimizer
                if response.success:
                    # Extract token usage
                    input_tokens = response.usage.get("prompt_tokens", 0)
                    output_tokens = response.usage.get("completion_tokens", 0)

                    # Determine task type from analysis
                    task_type = (
                        task_analysis.get("task_type", "unknown") if task_analysis else "unknown"
                    )

                    # Track usage with CostOptimizer
                    cost_result = self.cost_optimizer.track_usage(
                        provider=provider,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        task_type=task_type,
                    )

                    # Add Phase 3 metadata to response
                    response.metadata = response.metadata or {}
                    response.metadata.update(
                        {
                            "routing": {
                                "recommended_provider": recommended_provider,
                                "actual_provider": provider,
                                "complexity": (
                                    task_analysis.get("complexity") if task_analysis else "unknown"
                                ),
                                "task_type": task_type,
                                "reasoning": (
                                    task_analysis.get("reasoning")
                                    if task_analysis
                                    else "User preference"
                                ),
                                "fallback_used": provider != recommended_provider,
                            },
                            "cost": {
                                "this_request": cost_result["cost"],
                                "daily_total": cost_result["daily_total"],
                                "monthly_total": cost_result["monthly_total"],
                                "budget_status": cost_result.get("budget_status", "ok"),
                            },
                            "performance": {
                                "response_time": elapsed_time,
                                "provider_avg": self.performance_stats[provider]["avg_time"],
                            },
                        }
                    )

                    routing_context["attempt_history"].append(
                        {
                            "provider": provider,
                            "status": "success",
                            "time": elapsed_time,
                            "cost": cost_result["cost"],
                        }
                    )

                    return response

                # Request failed but didn't raise exception
                last_error = response.error
                routing_context["attempt_history"].append(
                    {"provider": provider, "status": "failed", "error": last_error}
                )

            except Exception as e:
                last_error = f"{provider} exception: {str(e)}"
                self._update_stats(
                    provider, AIResponse(content="", error=last_error, provider=provider), False
                )
                routing_context["attempt_history"].append(
                    {"provider": provider, "status": "exception", "error": str(e)}
                )
                continue

        # All providers failed
        return AIResponse(
            content="",
            error=f"All providers failed. Last error: {last_error}",
            provider="router",
            metadata={
                "routing_context": routing_context,
                "available_providers": self.get_available_providers(),
            },
        )

    def get_stats(self) -> Dict[str, Any]:
        """Phase 3: Get comprehensive usage, cost, and performance statistics"""
        # Get Phase 3 cost report
        cost_report = self.cost_optimizer.get_cost_report(days=30)
        budget_status = self.cost_optimizer.check_budget_status()

        return {
            # Legacy stats (backward compatibility)
            "usage": self.usage_stats.copy(),
            "total_cost": sum(stats["cost"] for stats in self.usage_stats.values()),
            "total_calls": sum(stats["calls"] for stats in self.usage_stats.values()),
            "total_tokens": sum(stats["tokens"] for stats in self.usage_stats.values()),
            # Phase 3: Enhanced cost tracking
            "cost_tracking": {
                "daily": {
                    "spent": budget_status["daily"]["spent"],
                    "limit": budget_status["daily"]["limit"],
                    "remaining": budget_status["daily"]["remaining"],
                    "status": budget_status["daily"]["status"],
                },
                "monthly": {
                    "spent": budget_status["monthly"]["spent"],
                    "limit": budget_status["monthly"]["limit"],
                    "remaining": budget_status["monthly"]["remaining"],
                    "status": budget_status["monthly"]["status"],
                },
                "forecast": self.cost_optimizer.forecast_monthly_cost(),
                "report": cost_report,
            },
            # Phase 3: Performance metrics
            "performance": self.performance_stats.copy(),
            # Phase 3: Routing configuration
            "routing_config": {
                "preferences": self.routing_config.get_all_settings()["routing_preferences"],
                "enabled_providers": self.routing_config.get_enabled_providers(),
            },
        }

    def reset_stats(self):
        """Reset usage statistics (call daily)"""
        for provider in self.usage_stats:
            self.usage_stats[provider] = {"calls": 0, "tokens": 0, "cost": 0.0, "failures": 0}

    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return [name for name, client in self.clients.items() if client is not None]

    def update_config(self, updates: Dict[str, Any]):
        """Update configuration and save"""

        # Deep merge updates
        def deep_merge(base, updates):
            for key, value in updates.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value

        deep_merge(self.config, updates)

        # Save to file
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)

        # Reinitialize clients if provider settings changed
        if "providers" in updates:
            self._init_clients()

    # Phase 3: Additional utility methods

    def get_recent_alerts(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Phase 3: Get recent cost and budget alerts

        Args:
            count: Number of alerts to retrieve

        Returns:
            List of recent alerts with severity, type, and message
        """
        return self.cost_optimizer.get_recent_alerts(count=count)

    def analyze_task_preview(
        self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Phase 3: Analyze a task without executing it (for debugging/preview)

        Args:
            messages: Conversation messages
            tools: Optional tool schemas

        Returns:
            Task analysis including complexity, type, and recommended provider
        """
        return self.task_analyzer.analyze_task(
            messages=messages,
            tools=tools,
            context={"available_providers": self.get_available_providers()},
        )

    def get_cost_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Phase 3: Get cost summary and analytics

        Args:
            days: Number of days to include in report

        Returns:
            Cost report with breakdown by provider and task type
        """
        return self.cost_optimizer.get_cost_report(days=days)

    def check_budget_health(self) -> Dict[str, Any]:
        """
        Phase 3: Check budget health and get recommendations

        Returns:
            Budget status with recommendations for optimization
        """
        budget_status = self.cost_optimizer.check_budget_status()
        forecast = self.cost_optimizer.forecast_monthly_cost()

        # Generate recommendations
        recommendations = []

        if budget_status["daily"]["status"] == "warning":
            recommendations.append(
                "Daily budget at 80%. Consider simpler queries or cheaper providers."
            )

        if budget_status["daily"]["status"] == "exceeded":
            recommendations.append(
                "Daily budget exceeded. Requests will use cheapest available providers."
            )

        if not forecast["on_track"]:
            recommendations.append(
                f"Monthly forecast: ${forecast['projected_total']:.2f} (over budget). Reduce usage or increase limits."
            )

        # Check if any expensive providers are being overused
        report = self.cost_optimizer.get_cost_report(days=7)
        for provider, cost in report["provider_totals"].items():
            if cost > report["total_cost"] * 0.7:  # One provider is >70% of costs
                recommendations.append(
                    f"{provider.title()} is {cost/report['total_cost']*100:.0f}% of costs. Consider routing simple tasks elsewhere."
                )

        return {
            "budget_status": budget_status,
            "forecast": forecast,
            "recommendations": recommendations,
            "health_score": self._calculate_budget_health_score(budget_status, forecast),
        }

    def _calculate_budget_health_score(
        self, budget_status: Dict[str, Any], forecast: Dict[str, Any]
    ) -> str:
        """Calculate overall budget health score"""
        if (
            budget_status["daily"]["status"] == "exceeded"
            or budget_status["monthly"]["status"] == "exceeded"
        ):
            return "critical"
        elif budget_status["daily"]["status"] == "warning" or not forecast["on_track"]:
            return "warning"
        elif budget_status["daily"]["percentage"] < 50 and forecast["on_track"]:
            return "excellent"
        else:
            return "good"
