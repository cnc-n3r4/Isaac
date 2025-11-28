#pragma once

#include "tier_validator.hpp"
#include "../adapters/shell_adapter.hpp"
#include "memory_pool.hpp"
#include <memory>
#include <string>
#include <string_view>
#include <vector>

namespace isaac {

// Forward declarations
class SessionManager;
class CommandStrategy;
struct StrategyContext;

// Context passed to strategies during execution
struct StrategyContext {
    std::shared_ptr<class CommandRouter> router;
    std::shared_ptr<TierValidator> validator;
    std::shared_ptr<ShellAdapter> shell;
    std::shared_ptr<SessionManager> session;
};

// CommandResult struct
struct CommandResult : public Poolable {
    CommandResult() = default;
    CommandResult(bool success, std::string output, int exit_code)
        : success(success), output(std::move(output)), exit_code(exit_code) {}

    bool success = false;
    std::string output;
    int exit_code = -1;
};

// Abstract base class for command strategies
class CommandStrategy {
public:
    CommandStrategy(std::shared_ptr<SessionManager> session,
                   std::shared_ptr<ShellAdapter> shell)
        : session_(session), shell_(shell) {}

    virtual ~CommandStrategy() = default;

    virtual bool can_handle(std::string_view input) const = 0;
    virtual CommandResult execute(std::string_view input, const StrategyContext& context) = 0;
    virtual int get_priority() const = 0;
    virtual std::string get_help() const { return ""; }

protected:
    std::shared_ptr<SessionManager> session_;
    std::shared_ptr<ShellAdapter> shell_;
};

// Main command router class
class CommandRouter : public std::enable_shared_from_this<CommandRouter> {
public:
    CommandRouter(std::shared_ptr<SessionManager> session_mgr,
                 std::shared_ptr<ShellAdapter> shell);
    ~CommandRouter();

    CommandResult route_command(std::string_view input_text);
    std::string get_help() const;

private:
    void ensure_strategies_loaded();
    void load_strategies();

    std::shared_ptr<SessionManager> session_;
    std::shared_ptr<ShellAdapter> shell_;
    std::shared_ptr<TierValidator> validator_;
    std::vector<std::shared_ptr<CommandStrategy>> strategies_;
    bool strategies_loaded_ = false;

    // Memory pool for CommandResult objects
    MemoryPool<CommandResult> result_pool_;
};

// Strategy implementations (forward declarations for now)
class PipeStrategy;
class CdStrategy;
class ForceExecutionStrategy;
class ExitQuitStrategy;
class ConfigStrategy;
class DeviceRoutingStrategy;
class ExitBlockerStrategy;
class TaskModeStrategy;
class AgenticModeStrategy;
class MetaCommandStrategy;
class NaturalLanguageStrategy;
class UnixAliasStrategy;
class TierExecutionStrategy;

} // namespace isaac