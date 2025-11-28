#pragma once

#include "../command_router.hpp"
#include <string>

namespace isaac {

class TaskModeStrategy : public BaseStrategy {
public:
    TaskModeStrategy(std::shared_ptr<SessionManager> session,
                    std::shared_ptr<ShellAdapter> shell)
        : BaseStrategy(session, shell, 45) {}

    bool can_handle(const std::string& input) const override;
    CommandResult execute(const std::string& input, const StrategyContext& context) override;
    std::string get_help() const override;
};

} // namespace isaac