#pragma once

#include "../command_router.hpp"
#include <string>

namespace isaac {

class ConfigStrategy : public BaseStrategy {
public:
    ConfigStrategy(std::shared_ptr<SessionManager> session,
                  std::shared_ptr<ShellAdapter> shell)
        : BaseStrategy(session, shell, 35) {}

    bool can_handle(const std::string& input) const override;
    CommandResult execute(const std::string& input, const StrategyContext& context) override;
    std::string get_help() const override;
};

} // namespace isaac