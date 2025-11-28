#include "command_router.hpp"
#include "strategies.hpp"
#include "routing/config_strategy.hpp"
#include "routing/device_routing_strategy.hpp"
#include "routing/task_mode_strategy.hpp"
#include "routing/agentic_mode_strategy.hpp"
#include <algorithm>
#include <memory>
#include <vector>
#include <string_view>

namespace isaac {

CommandRouter::CommandRouter(std::shared_ptr<SessionManager> session_mgr,
                           std::shared_ptr<ShellAdapter> shell)
    : session_(session_mgr), shell_(shell), validator_(std::make_shared<TierValidator>()) {
    // Initialize with lazy loading - strategies loaded on first use
}

CommandRouter::~CommandRouter() = default;

CommandResult CommandRouter::route_command(std::string_view input_text) {
    // Ensure strategies are loaded
    ensure_strategies_loaded();

    // Build context for strategies
    StrategyContext context{
        shared_from_this(),
        validator_,
        shell_,
        session_
    };

    // Try each strategy in priority order
    for (auto& strategy : strategies_) {
        if (strategy->can_handle(input_text)) {
            return strategy->execute(input_text, context);
        }
    }

    // Should never reach here - default strategy should handle all
    return CommandResult{false, "Isaac > No strategy could handle command", -1};
}

void CommandRouter::ensure_strategies_loaded() {
    if (!strategies_loaded_) {
        load_strategies();
        strategies_loaded_ = true;
    }
}

void CommandRouter::load_strategies() {
    // Create all strategies with proper priority ordering
    strategies_ = {
        // High priority strategies (10-30)
        std::make_shared<PipeStrategy>(session_, shell_),
        std::make_shared<CdStrategy>(session_, shell_),
        std::make_shared<ForceExecutionStrategy>(session_, shell_),
        std::make_shared<ExitQuitStrategy>(session_, shell_),
        std::make_shared<ConfigStrategy>(session_, shell_),
        std::make_shared<DeviceRoutingStrategy>(session_, shell_),
        std::make_shared<ExitBlockerStrategy>(session_, shell_),
        std::make_shared<TaskModeStrategy>(session_, shell_),
        std::make_shared<AgenticModeStrategy>(session_, shell_),

        // Medium priority strategies (50-60)
        std::make_shared<MetaCommandStrategy>(session_, shell_),
        std::make_shared<NaturalLanguageStrategy>(session_, shell_),
        std::make_shared<UnixAliasStrategy>(session_, shell_),

        // Low priority - default strategy (100)
        std::make_shared<TierExecutionStrategy>(session_, shell_)
    };

    // Sort by priority (lower number = higher priority)
    std::sort(strategies_.begin(), strategies_.end(),
              [](const auto& a, const auto& b) {
                  return a->get_priority() < b->get_priority();
              });
}

std::string CommandRouter::get_help() const {
    std::string help = "Isaac Command Router - Available command types:\n";
    for (const auto& strategy : strategies_) {
        std::string strategy_help = strategy->get_help();
        if (!strategy_help.empty()) {
            help += "  • " + strategy_help + "\n";
        }
    }
    return help;
}

} // namespace isaac