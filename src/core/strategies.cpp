#include "strategies.hpp"
#include <algorithm>
#include <iostream>
#include <sstream>

namespace isaac {

CommandResult PipeStrategy::execute(const std::string& input, const StrategyContext& context) {
    // For now, execute the command as-is (pipes handled by shell)
    // In a full implementation, this might split and execute separately
    return context.shell->execute(input);
}

CommandResult CdStrategy::execute(const std::string& input, const StrategyContext& context) {
    // Extract directory from "cd <dir>"
    std::istringstream iss(input);
    std::string cmd, dir;
    iss >> cmd >> dir;

    if (dir.empty()) {
        dir = "~"; // Default to home directory
    }

    // Execute cd command
    return context.shell->execute("cd " + dir);
}

CommandResult ForceExecutionStrategy::execute(const std::string& input, const StrategyContext& context) {
    // Remove the ! prefix and execute without validation
    std::string command = input.substr(1);
    command.erase(command.begin(), std::find_if(command.begin(), command.end(),
               [](unsigned char ch) { return !std::isspace(ch); }));

    return context.shell->execute(command);
}

CommandResult ExitQuitStrategy::execute(const std::string& input, const StrategyContext& context) {
    // Signal exit - this would be handled by the main application
    return CommandResult{true, "Isaac > Goodbye!", 0};
}

CommandResult MetaCommandStrategy::execute(const std::string& input, const StrategyContext& context) {
    // Extract meta command (remove / prefix)
    std::string command = input.substr(1);
    command.erase(command.begin(), std::find_if(command.begin(), command.end(),
               [](unsigned char ch) { return !std::isspace(ch); }));

    std::transform(command.begin(), command.end(), command.begin(), ::tolower);

    if (command == "help") {
        return CommandResult{true, context.router->get_help(), 0};
    } else if (command == "status") {
        return CommandResult{true, "Isaac > System status: C++ core active", 0};
    } else {
        return CommandResult{false, "Isaac > Unknown meta command: " + command, -1};
    }
}

CommandResult NaturalLanguageStrategy::execute(const std::string& input, const StrategyContext& context) {
    // Remove "isaac" prefix and process as AI query
    std::string query = input.substr(5);
    query.erase(query.begin(), std::find_if(query.begin(), query.end(),
               [](unsigned char ch) { return !std::isspace(ch); }));

    // Placeholder - in full implementation, this would call AI router
    return CommandResult{true, "Isaac > AI query: " + query + " (C++ processing)", 0};
}

CommandResult TierExecutionStrategy::execute(const std::string& input, const StrategyContext& context) {
    // Validate command safety
    float tier = context.validator->get_tier(input);

    if (tier >= 4.0f) {
        return CommandResult{false, "Isaac > Command blocked (Tier 4 - lockdown)", -1};
    } else if (tier >= 3.0f) {
        // In full implementation, this would prompt for confirmation
        // For now, allow with warning
        auto result = context.shell->execute(input);
        result.output = "Isaac > Warning: Tier 3 command executed\n" + result.output;
        return result;
    } else if (tier == 2.5f) {
        // In full implementation, this would prompt for confirmation
        // For now, allow with warning
        auto result = context.shell->execute(input);
        result.output = "Isaac > Confirmation required for Tier 2.5 command\n" + result.output;
        return result;
    } else {
        // Safe command - execute directly
        return context.shell->execute(input);
    }
}

} // namespace isaac