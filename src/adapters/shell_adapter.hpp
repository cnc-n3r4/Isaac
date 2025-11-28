#pragma once

#include <memory>
#include <string>

#ifdef _WIN32
#include <windows.h>
#endif

namespace isaac {

struct CommandResult {
    bool success;
    std::string output;
    int exit_code;
};

enum class ShellType {
    BASH,
    ZSH,
    POWERSHELL,
    POWERSHELL_CORE
};

// Forward declaration
class SessionManager;

class ShellAdapter {
public:
    ShellAdapter();
    ~ShellAdapter();

    // Execute command with default timeout (30 seconds)
    CommandResult execute(const std::string& command);

    // Execute command with custom timeout
    CommandResult execute_with_timeout(const std::string& command, int timeout_seconds);

    // Get shell information
    std::string get_shell_name() const;
    bool is_available() const;

private:
    CommandResult execute_windows(const std::string& command, int timeout_seconds);
    CommandResult execute_unix(const std::string& command, int timeout_seconds);
    void read_pipe(HANDLE pipe, std::string& output);
    void detect_shell_type();

    ShellType shell_type_;
};

} // namespace isaac