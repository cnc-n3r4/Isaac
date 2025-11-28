#include "shell_adapter.hpp"
#include <array>
#include <cstdio>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <thread>
#include <chrono>
#include <fcntl.h>

#ifdef _WIN32
#include <windows.h>
#include <processthreadsapi.h>
#include <synchapi.h>
#define popen _popen
#define pclose _pclose
#else
#include <unistd.h>
#include <sys/wait.h>
#include <signal.h>
#endif

namespace isaac {

ShellAdapter::ShellAdapter() {
#ifdef _WIN32
    // Windows-specific initialization
    detect_shell_type();
#else
    // Unix-like systems
    shell_type_ = ShellType::BASH;
#endif
}

ShellAdapter::~ShellAdapter() = default;

CommandResult ShellAdapter::execute(const std::string& command) {
    return execute_with_timeout(command, 30); // Default 30 second timeout
}

CommandResult ShellAdapter::execute_with_timeout(const std::string& command, int timeout_seconds) {
#ifdef _WIN32
    return execute_windows(command, timeout_seconds);
#else
    return execute_unix(command, timeout_seconds);
#endif
}

CommandResult ShellAdapter::execute_windows(const std::string& command, int timeout_seconds) {
    std::string cmd = "powershell.exe -NoProfile -Command " + command;
    std::array<char, 128> buffer;
    std::string result;
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd.c_str(), "r"), pclose);

    if (!pipe) {
        return CommandResult{false, "Isaac > Failed to execute command", -1};
    }

    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
        result += buffer.data();
    }

    int exit_code = pclose(pipe.release());
    return CommandResult{exit_code == 0, result, exit_code};
}

#ifndef _WIN32
CommandResult ShellAdapter::execute_unix(const std::string& command, int timeout_seconds) {
    // Use popen for Unix-like systems (could be optimized further with fork/exec)
    std::array<char, 128> buffer;
    std::string result;
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(command.c_str(), "r"), pclose);

    if (!pipe) {
        return CommandResult{false, "Isaac > Failed to execute command", -1};
    }

    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
        result += buffer.data();
    }

    int exit_code = WEXITSTATUS(pclose(pipe.release()));
    return CommandResult{exit_code == 0, result, exit_code};
}
#endif

void ShellAdapter::read_pipe(HANDLE pipe, std::string& output) {
    DWORD bytes_read;
    CHAR buffer[4096];

    while (ReadFile(pipe, buffer, sizeof(buffer) - 1, &bytes_read, NULL) && bytes_read > 0) {
        buffer[bytes_read] = '\0';
        output += buffer;
    }
}

void ShellAdapter::detect_shell_type() {
#ifdef _WIN32
    // Check for PowerShell 7+ first
    if (system("where pwsh >nul 2>nul") == 0) {
        shell_type_ = ShellType::POWERSHELL_CORE;
    } else {
        shell_type_ = ShellType::POWERSHELL;
    }
#endif
}

std::string ShellAdapter::get_shell_name() const {
    switch (shell_type_) {
        case ShellType::BASH: return "bash";
        case ShellType::ZSH: return "zsh";
        case ShellType::POWERSHELL: return "PowerShell";
        case ShellType::POWERSHELL_CORE: return "PowerShell Core";
        default: return "Unknown";
    }
}

bool ShellAdapter::is_available() const {
#ifdef _WIN32
    return true; // Windows always has cmd.exe
#else
    return system("which bash > /dev/null 2>&1") == 0;
#endif
}

} // namespace isaac