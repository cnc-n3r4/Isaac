# Import Cycle Analysis

**Agent 5: Dead Code Hunter**

**Modules analyzed:** 311

**Import cycles found:** 5

## Summary by Severity

- **Critical:** 2 cycles
- **High:** 2 cycles
- **Low:** 1 cycles

---

## Detailed Findings

### Cycle 1: Critical Severity

**Description:** Direct circular import (A imports B, B imports A)

**Cycle length:** 2 modules

**Import chain:**

```
isaac.core.command_router
  ↓ imports
isaac.ai.task_planner
  ↓ imports
isaac.core.command_router
```

**Modules involved:**

- `isaac.ai.task_planner`
- `isaac.core.command_router`

**Breaking strategy:** Use lazy imports (import inside functions) OR Extract shared dependencies to a separate module OR Use TYPE_CHECKING for type hint imports

**Estimated effort:** 2-4 hours (high priority)

---

### Cycle 2: Critical Severity

**Description:** Direct circular import (A imports B, B imports A)

**Cycle length:** 2 modules

**Import chain:**

```
isaac.core.cli_command_router
  ↓ imports
isaac.commands.backup
  ↓ imports
isaac.core.cli_command_router
```

**Modules involved:**

- `isaac.commands.backup`
- `isaac.core.cli_command_router`

**Breaking strategy:** Use lazy imports (import inside functions) OR Extract shared dependencies to a separate module OR Use TYPE_CHECKING for type hint imports

**Estimated effort:** 2-4 hours (high priority)

---

### Cycle 3: High Severity

**Description:** Three-way circular import

**Cycle length:** 3 modules

**Import chain:**

```
isaac.core.command_router
  ↓ imports
isaac.ai.task_planner
  ↓ imports
isaac.ui.permanent_shell
  ↓ imports
isaac.core.command_router
```

**Modules involved:**

- `isaac.ai.task_planner`
- `isaac.core.command_router`
- `isaac.ui.permanent_shell`

**Breaking strategy:** Use lazy imports (import inside functions) OR Extract shared dependencies to a separate module OR Use TYPE_CHECKING for type hint imports

**Estimated effort:** 1-3 hours

---

### Cycle 4: High Severity

**Description:** Three-way circular import

**Cycle length:** 3 modules

**Import chain:**

```
isaac.core.cli_command_router
  ↓ imports
isaac.commands.backup
  ↓ imports
isaac.commands.restore
  ↓ imports
isaac.core.cli_command_router
```

**Modules involved:**

- `isaac.commands.backup`
- `isaac.commands.restore`
- `isaac.core.cli_command_router`

**Breaking strategy:** Use lazy imports (import inside functions) OR Extract shared dependencies to a separate module OR Use TYPE_CHECKING for type hint imports

**Estimated effort:** 1-3 hours

---

### Cycle 5: Low Severity

**Description:** Long cycle (8 modules) - possibly indirect

**Cycle length:** 8 modules

**Import chain:**

```
isaac.core.command_router
  ↓ imports
isaac.ai.task_planner
  ↓ imports
isaac.ui.permanent_shell
  ↓ imports
isaac.commands.list
  ↓ imports
isaac.core.cli_command_router
  ↓ imports
isaac.commands.backup
  ↓ imports
isaac.commands.restore
  ↓ imports
isaac.commands.msg.run
  ↓ imports
isaac.core.command_router
```

**Modules involved:**

- `isaac.ai.task_planner`
- `isaac.commands.backup`
- `isaac.commands.list`
- `isaac.commands.msg.run`
- `isaac.commands.restore`
- `isaac.core.cli_command_router`
- `isaac.core.command_router`
- `isaac.ui.permanent_shell`

**Breaking strategy:** Use lazy imports (import inside functions) OR Extract shared dependencies to a separate module OR Use TYPE_CHECKING for type hint imports

**Estimated effort:** < 1 hour (low priority)

---


## Recommendations

1. **Address Critical and High severity cycles first** - these can cause import errors
2. **Use lazy imports** - import inside functions when possible
3. **Extract shared code** - move common dependencies to separate modules
4. **Use TYPE_CHECKING** - for type hint imports only
5. **Refactor module structure** - consider if modules have too many responsibilities

