#include "tier_validator.hpp"
#include <algorithm>
#include <fstream>
#include <sstream>
#include <regex>

namespace isaac {

TierValidator::TierValidator() {
    load_tier_defaults();
}

TierValidator::~TierValidator() = default;

float TierValidator::get_tier(const std::string& command) const {
    // Handle empty or whitespace-only commands
    if (command.empty() || std::all_of(command.begin(), command.end(), ::isspace)) {
        return 3.0f;
    }

    // Extract base command (first word)
    std::istringstream iss(command);
    std::string base_cmd;
    iss >> base_cmd;

    // Convert to lowercase for comparison
    std::transform(base_cmd.begin(), base_cmd.end(), base_cmd.begin(), ::tolower);

    // Check user overrides first (if implemented)
    // TODO: Add user preference overrides

    // Check default tiers
    for (const auto& [tier_str, commands] : tier_defaults_) {
        for (const auto& cmd : commands) {
            std::string lower_cmd = cmd;
            std::transform(lower_cmd.begin(), lower_cmd.end(), lower_cmd.begin(), ::tolower);
            if (base_cmd == lower_cmd) {
                return std::stof(tier_str);
            }
        }
    }

    // Unknown commands default to Tier 3 (validation required)
    return 3.0f;
}

bool TierValidator::is_safe(const std::string& command) const {
    float tier = get_tier(command);
    return tier <= 2.0f; // Tiers 1 and 2 are considered safe
}

bool TierValidator::requires_confirmation(const std::string& command) const {
    float tier = get_tier(command);
    return tier == 2.5f; // Tier 2.5 requires confirmation
}

bool TierValidator::requires_validation(const std::string& command) const {
    float tier = get_tier(command);
    return tier >= 3.0f; // Tiers 3+ require validation
}

void TierValidator::load_tier_defaults() {
    // Try to load from JSON file first
    if (!load_from_file()) {
        // Fall back to hardcoded defaults
        load_hardcoded_defaults();
    }
}

bool TierValidator::load_from_file() {
    try {
        // Look for tier_defaults.json in data directory
        std::ifstream file("../isaac/data/tier_defaults.json");
        if (!file.is_open()) {
            return false;
        }

        std::string json_content((std::istreambuf_iterator<char>(file)),
                                std::istreambuf_iterator<char>());

        // Simple JSON parsing (could use a proper JSON library for production)
        parse_json(json_content);
        return true;
    } catch (...) {
        return false;
    }
}

void TierValidator::load_hardcoded_defaults() {
    tier_defaults_ = {
        {"1", {
            "ls", "cd", "clear", "cls", "pwd", "echo", "cat", "type",
            "Get-ChildItem", "Set-Location", "Get-Location"
        }},
        {"2", {
            "grep", "Select-String", "head", "tail", "sort", "uniq"
        }},
        {"2.5", {
            "find", "sed", "awk", "Where-Object", "ForEach-Object"
        }},
        {"3", {
            "cp", "mv", "git", "npm", "pip", "reset",
            "Copy-Item", "Move-Item", "New-Item", "Remove-Item"
        }},
        {"4", {
            "rm", "del", "format", "dd", "Remove-Item", "Format-Volume", "Clear-Disk"
        }}
    };
}

void TierValidator::parse_json(const std::string& json_content) {
    // Simple JSON parser for tier defaults
    // This is a basic implementation - production code should use a proper JSON library
    std::string pattern = "\"(\\d+(?:\\.\\d+)?)\":\\s*\\[(.*?)\\]\"";
    std::regex tier_regex(pattern);
    std::smatch match;

    std::string::const_iterator search_start(json_content.cbegin());
    while (std::regex_search(search_start, json_content.cend(), match, tier_regex)) {
        std::string tier = match[1];
        std::string commands_str = match[2];

        std::vector<std::string> commands;
        std::string cmd_pattern = "\"([^\"]+)\"";
        std::regex cmd_regex(cmd_pattern);
        std::smatch cmd_match;
        std::string::const_iterator cmd_search(commands_str.cbegin());

        while (std::regex_search(cmd_search, commands_str.cend(), cmd_match, cmd_regex)) {
            commands.push_back(cmd_match[1]);
            cmd_search = cmd_match.suffix().first;
        }

        tier_defaults_[tier] = commands;
        search_start = match.suffix().first;
    }
}

} // namespace isaac