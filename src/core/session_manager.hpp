#pragma once

#include <memory>
#include <string>

namespace isaac {

class SessionManager {
public:
    SessionManager() = default;
    ~SessionManager() = default;

    // Placeholder methods - will be expanded based on Python implementation
    std::string get_user_id() const { return "default_user"; }
    bool is_authenticated() const { return true; }
};

} // namespace isaac