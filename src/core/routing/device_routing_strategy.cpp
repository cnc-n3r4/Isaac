#include "device_routing_strategy.hpp"
#include "strategies.hpp"
#include <iostream>
#include <sstream>
#include <vector>

namespace isaac {

CommandResult DeviceRoutingStrategy::execute(std::string_view input, const StrategyContext& context) {
    // Convert to string for processing
    std::string input_str(input);

    // Parse device alias and command
    std::string device_spec, device_cmd;
    size_t space_pos = input_str.find(' ', 1); // Skip the '!'
    if (space_pos == std::string::npos) {
        return CommandResult{false, "Usage: !device_alias /command\n       !device_alias:strategy /command", 1};
    }
    
    device_spec = input_str.substr(1, space_pos - 1);
    device_cmd = input_str.substr(space_pos + 1);
    
    // Parse device spec for strategy (alias:strategy)
    std::string device_alias = device_spec;
    std::string strategy_name = "least_load"; // default
    
    size_t colon_pos = device_spec.find(':');
    if (colon_pos != std::string::npos) {
        device_alias = device_spec.substr(0, colon_pos);
        strategy_name = device_spec.substr(colon_pos + 1);
    }
    
    // Log the routing attempt
    std::cout << "Isaac > Executing on " << device_alias << ": " << device_cmd << std::endl;
    
    // TODO: Implement actual device routing logic
    // This would involve:
    // 1. Check if device_alias is a registered machine
    // 2. Check if it's a group name
    // 3. Try local network execution
    // 4. Fall back to cloud routing
    // 5. Queue for later sync if needed
    
    // For now, simulate routing logic
    if (device_alias == "local" || device_alias == "localhost") {
        // Execute locally
        return CommandResult{true, "Isaac > Executed locally: " + device_cmd + "\nNote: Full local execution requires shell adapter integration", 0};
    }
    else if (device_alias.find("group") == 0) {
        // Group execution
        return CommandResult{true, "Isaac > Load balancing across group '" + device_alias + "' with strategy '" + strategy_name + "': " + device_cmd + "\nNote: Full group execution requires MachineRegistry integration", 0};
    }
    else {
        // Remote or cloud execution
        return CommandResult{true, "Isaac > Command queued for " + device_alias + " (strategy: " + strategy_name + "): " + device_cmd + "\nNote: Full remote execution requires RemoteExecutor and cloud integration", 0};
    }
}

} // namespace isaac