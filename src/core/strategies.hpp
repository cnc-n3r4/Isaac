#pragma once

#include "command_router.hpp"
#include <algorithm>
#include <cctype>
#include <memory>
#include <regex>
#include <sstream>
#include <string>
#include <string_view>

namespace isaac {

// Base strategy implementation with common functionality
class BaseStrategy : public CommandStrategy {
public:
    BaseStrategy(std::shared_ptr<SessionManager> session,
                std::shared_ptr<ShellAdapter> shell, int priority)
        : CommandStrategy(session, shell), priority_(priority) {}

    int get_priority() const override { return priority_; }

protected:
    int priority_;
};

class PipeStrategy : public BaseStrategy {
public:
    PipeStrategy(std::shared_ptr<SessionManager> session,
                std::shared_ptr<ShellAdapter> shell)
        : BaseStrategy(session, shell, 10) {}

    bool can_handle(std::string_view input) const override {
        return input.find('|') != std::string_view::npos;
    }

    CommandResult execute(std::string_view input, const StrategyContext& context) override;
    std::string get_help() const override { return "Pipe commands: cmd1 | cmd2"; }
};

// CD strategy - handles directory changes
class CdStrategy : public BaseStrategy {
public:
    CdStrategy(std::shared_ptr<SessionManager> session,
              std::shared_ptr<ShellAdapter> shell)
        : BaseStrategy(session, shell, 15) {}

    bool can_handle(const std::string& input) const override {
        return input.find("cd ") == 0 || input == "cd";
    }

    CommandResult execute(const std::string& input, const StrategyContext& context) override;
    std::string get_help() const override { return "Change directory: cd <path>"; }
};

// Force execution strategy - handles ! prefix
class ForceExecutionStrategy : public BaseStrategy {
public:
    ForceExecutionStrategy(std::shared_ptr<SessionManager> session,
                          std::shared_ptr<ShellAdapter> shell)
        : BaseStrategy(session, shell, 20) {}

    bool can_handle(const std::string& input) const override {
        return !input.empty() && input[0] == '!';
    }

    CommandResult execute(const std::string& input, const StrategyContext& context) override;
    std::string get_help() const override { return "Force execute: !command"; }
};

// Exit/Quit strategy
class ExitQuitStrategy : public BaseStrategy {
public:
    ExitQuitStrategy(std::shared_ptr<SessionManager> session,
                    std::shared_ptr<ShellAdapter> shell)
        : BaseStrategy(session, shell, 25) {}

    bool can_handle(const std::string& input) const override {
        std::string lower = input;
        for (char& c : lower) c = std::tolower(c);
        return lower == "exit" || lower == "quit" || lower == "q" || lower == "/exit" || lower == "/quit" || lower == "/q";
    }

    CommandResult execute(const std::string& input, const StrategyContext& context) override;
    std::string get_help() const override { return "Exit shell: exit, quit, q"; }
};

// Meta command strategy - handles / prefix commands
class MetaCommandStrategy : public BaseStrategy {
public:
    MetaCommandStrategy(std::shared_ptr<SessionManager> session,
                       std::shared_ptr<ShellAdapter> shell)
        : BaseStrategy(session, shell, 50) {}

    bool can_handle(const std::string& input) const override {
        return !input.empty() && input[0] == '/';
    }

    CommandResult execute(const std::string& input, const StrategyContext& context) override;
    std::string get_help() const override { return "Meta commands: /help, /status, etc."; }
};

// Natural language strategy - handles "isaac" prefix
class NaturalLanguageStrategy : public BaseStrategy {
public:
    NaturalLanguageStrategy(std::shared_ptr<SessionManager> session,
                           std::shared_ptr<ShellAdapter> shell)
        : BaseStrategy(session, shell, 55) {}

    bool can_handle(const std::string& input) const override {
        std::string lower = input;
        for (char& c : lower) c = std::tolower(c);
        return lower.find("isaac") == 0;
    }

    CommandResult execute(const std::string& input, const StrategyContext& context) override;

    std::string get_help() const override { return "AI queries: isaac <question>"; }
};

// Default tier execution strategy - handles all other commands
class TierExecutionStrategy : public BaseStrategy {
public:
    TierExecutionStrategy(std::shared_ptr<SessionManager> session,
                         std::shared_ptr<ShellAdapter> shell)
        : BaseStrategy(session, shell, 100) {}

    bool can_handle(const std::string& input) const override {
        return true; // Always can handle - default strategy
    }

    CommandResult execute(const std::string& input, const StrategyContext& context) override;
    std::string get_help() const override { return "Shell commands with safety validation"; }
};

// Config strategy - handles /config commands
class ConfigStrategy : public BaseStrategy {
public:
    ConfigStrategy(std::shared_ptr<SessionManager> session,
                  std::shared_ptr<ShellAdapter> shell)
        : BaseStrategy(session, shell, 35) {}

    bool can_handle(const std::string& input) const override {
        return input.find("/config") == 0;
    }

    CommandResult execute(const std::string& input, const StrategyContext& context) override;
    std::string get_help() const override { return "Configuration commands: /config set/get/list"; }
};

class DeviceRoutingStrategy : public BaseStrategy {
public:
    DeviceRoutingStrategy(std::shared_ptr<SessionManager> session,
                         std::shared_ptr<ShellAdapter> shell)
        : BaseStrategy(session, shell, 40) {}

    bool can_handle(const std::string& input) const override {
        return !input.empty() && input[0] == '!';
    }

    CommandResult execute(const std::string& input, const StrategyContext& context) override;
    std::string get_help() const override { return "Device routing: !device command"; }
};

class ExitBlockerStrategy : public BaseStrategy {
public:
    ExitBlockerStrategy(std::shared_ptr<SessionManager> session,
                       std::shared_ptr<ShellAdapter> shell)
        : BaseStrategy(session, shell, 40) {}
    bool can_handle(const std::string& input) const override { return false; }
    CommandResult execute(const std::string& input, const StrategyContext& context) override {
        return CommandResult{false, "Exit blocker strategy not implemented", -1};
    }
};

class TaskModeStrategy : public BaseStrategy {
public:
    TaskModeStrategy(std::shared_ptr<SessionManager> session,
                    std::shared_ptr<ShellAdapter> shell)
        : BaseStrategy(session, shell, 45) {}

    bool can_handle(const std::string& input) const override {
        return input.find("isaac task:") == 0;
    }

    CommandResult execute(const std::string& input, const StrategyContext& context) override;
    std::string get_help() const override { return "Task mode: isaac task: <description>"; }
};

class AgenticModeStrategy : public BaseStrategy {
public:
    AgenticModeStrategy(std::shared_ptr<SessionManager> session,
                       std::shared_ptr<ShellAdapter> shell)
        : BaseStrategy(session, shell, 48) {}

    bool can_handle(const std::string& input) const override {
        return input.find("isaac agent:") == 0 || input.find("isaac agentic:") == 0;
    }

    CommandResult execute(const std::string& input, const StrategyContext& context) override;
    std::string get_help() const override { return "Agentic mode: isaac agent: <query>"; }
};

class UnixAliasStrategy : public BaseStrategy {
public:
    UnixAliasStrategy(std::shared_ptr<SessionManager> session,
                     std::shared_ptr<ShellAdapter> shell)
        : BaseStrategy(session, shell, 60) {}
    bool can_handle(const std::string& input) const override { return false; }
    CommandResult execute(const std::string& input, const StrategyContext& context) override {
        return CommandResult{false, "Unix alias strategy not implemented", -1};
    }
};

} // namespace isaac} // namespace isaac