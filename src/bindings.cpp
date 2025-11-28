#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "core/command_router.hpp"
#include "core/tier_validator.hpp"
#include "adapters/shell_adapter.hpp"
#include "core/session_manager.hpp"
#include "core/routing/config_strategy.hpp"
#include "core/routing/device_routing_strategy.hpp"
#include "core/routing/task_mode_strategy.hpp"
#include "core/routing/agentic_mode_strategy.hpp"

namespace py = pybind11;
using namespace isaac;

PYBIND11_MODULE(isaac_core, m) {
    m.doc() = "Isaac C++ Core Module - High-performance command routing and validation";

    // CommandResult struct
    py::class_<CommandResult>(m, "CommandResult")
        .def_readonly("success", &CommandResult::success)
        .def_readonly("output", &CommandResult::output)
        .def_readonly("exit_code", &CommandResult::exit_code);

    // TierValidator class
    py::class_<TierValidator, std::shared_ptr<TierValidator>>(m, "TierValidator")
        .def(py::init<>())
        .def("get_tier", &TierValidator::get_tier)
        .def("is_safe", &TierValidator::is_safe)
        .def("requires_confirmation", &TierValidator::requires_confirmation)
        .def("requires_validation", &TierValidator::requires_validation);

    // ShellAdapter class
    py::class_<ShellAdapter, std::shared_ptr<ShellAdapter>>(m, "ShellAdapter")
        .def(py::init<>())
        .def("execute", &ShellAdapter::execute)
        .def("execute_with_timeout", &ShellAdapter::execute_with_timeout)
        .def("get_shell_name", &ShellAdapter::get_shell_name)
        .def("is_available", &ShellAdapter::is_available);

    // SessionManager class (minimal implementation)
    py::class_<SessionManager, std::shared_ptr<SessionManager>>(m, "SessionManager")
        .def(py::init<>())
        .def("get_user_id", &SessionManager::get_user_id)
        .def("is_authenticated", &SessionManager::is_authenticated);

    // CommandRouter class
    py::class_<CommandRouter, std::shared_ptr<CommandRouter>>(m, "CommandRouter")
        .def(py::init<std::shared_ptr<SessionManager>, std::shared_ptr<ShellAdapter>>())
        .def("route_command", &CommandRouter::route_command)
        .def("get_help", &CommandRouter::get_help);

    // ConfigStrategy class
    py::class_<ConfigStrategy, std::shared_ptr<ConfigStrategy>>(m, "ConfigStrategy")
        .def(py::init<std::shared_ptr<SessionManager>, std::shared_ptr<ShellAdapter>>())
        .def("can_handle", &ConfigStrategy::can_handle)
        .def("execute", &ConfigStrategy::execute)
        .def("get_priority", &ConfigStrategy::get_priority)
        .def("get_help", &ConfigStrategy::get_help);

    // DeviceRoutingStrategy class
    py::class_<DeviceRoutingStrategy, std::shared_ptr<DeviceRoutingStrategy>>(m, "DeviceRoutingStrategy")
        .def(py::init<std::shared_ptr<SessionManager>, std::shared_ptr<ShellAdapter>>())
        .def("can_handle", &DeviceRoutingStrategy::can_handle)
        .def("execute", &DeviceRoutingStrategy::execute)
        .def("get_priority", &DeviceRoutingStrategy::get_priority)
        .def("get_help", &DeviceRoutingStrategy::get_help);

    // TaskModeStrategy class
    py::class_<TaskModeStrategy, std::shared_ptr<TaskModeStrategy>>(m, "TaskModeStrategy")
        .def(py::init<std::shared_ptr<SessionManager>, std::shared_ptr<ShellAdapter>>())
        .def("can_handle", &TaskModeStrategy::can_handle)
        .def("execute", &TaskModeStrategy::execute)
        .def("get_priority", &TaskModeStrategy::get_priority)
        .def("get_help", &TaskModeStrategy::get_help);

    // AgenticModeStrategy class
    py::class_<AgenticModeStrategy, std::shared_ptr<AgenticModeStrategy>>(m, "AgenticModeStrategy")
        .def(py::init<std::shared_ptr<SessionManager>, std::shared_ptr<ShellAdapter>>())
        .def("can_handle", &AgenticModeStrategy::can_handle)
        .def("execute", &AgenticModeStrategy::execute)
        .def("get_priority", &AgenticModeStrategy::get_priority)
        .def("get_help", &AgenticModeStrategy::get_help);

    // StrategyContext struct
    py::class_<StrategyContext>(m, "StrategyContext")
        .def_readonly("router", &StrategyContext::router)
        .def_readonly("validator", &StrategyContext::validator)
        .def_readonly("shell", &StrategyContext::shell)
        .def_readonly("session", &StrategyContext::session);
}