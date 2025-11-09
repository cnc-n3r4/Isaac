#!/usr/bin/env python3
"""
Test Machine Registry Command
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from isaac.commands.machine.run import MachineCommand


class TestMachineCommand:
    """Test the machine registry command"""

    def test_machine_command_init(self):
        """Test command initialization"""
        cmd = MachineCommand()
        assert cmd.registry is not None

    def test_list_machines_empty(self):
        """Test listing machines when none registered"""
        cmd = MachineCommand()
        result = cmd.execute({'action': 'list'})
        assert "No machines registered" in result

    def test_register_machine(self):
        """Test registering a machine"""
        cmd = MachineCommand()

        args = {
            'action': 'register',
            'hostname': 'test-host',
            'ip_address': '192.168.1.100',
            'port': 8080,
            'tags': 'test,development'
        }

        result = cmd.execute(args)
        assert "Registered machine 'test-host'" in result
        assert "CPU cores" in result
        assert "GB RAM" in result

    def test_list_machines_after_register(self):
        """Test listing machines after registration"""
        cmd = MachineCommand()

        # Register first
        cmd.execute({
            'action': 'register',
            'hostname': 'test-host-2',
            'ip_address': '192.168.1.101',
            'port': 8080,
            'tags': 'test'
        })

        # List
        result = cmd.execute({'action': 'list'})
        assert "Registered Machines" in result
        assert "test-host-2" in result
        assert "192.168.1.101:8080" in result

    def test_show_machine(self):
        """Test showing machine details"""
        cmd = MachineCommand()

        # Register first
        cmd.execute({
            'action': 'register',
            'hostname': 'detail-host',
            'ip_address': '192.168.1.102',
            'port': 8080,
            'tags': 'detail'
        })

        # Get the machine ID from registry
        machines = cmd.registry.list_machines()
        machine_id = machines[0].machine_id

        # Show details
        result = cmd.execute({'action': 'show', 'machine_id': machine_id})
        assert "Machine: detail-host" in result
        assert "Capabilities:" in result
        assert "Current Status:" in result
        assert "Tags: detail" in result

    def test_find_machines_by_tags(self):
        """Test finding machines by tags"""
        cmd = MachineCommand()

        # Register machines with different tags
        cmd.execute({
            'action': 'register',
            'hostname': 'gpu-host',
            'ip_address': '192.168.1.103',
            'port': 8080,
            'tags': 'gpu,high-mem'
        })

        cmd.execute({
            'action': 'register',
            'hostname': 'cpu-host',
            'ip_address': '192.168.1.104',
            'port': 8080,
            'tags': 'cpu,standard'
        })

        # Find by tag
        result = cmd.execute({'action': 'find', 'filter_tags': 'gpu'})
        assert "Found Machines" in result
        assert "gpu-host" in result
        assert "cpu-host" not in result

    def test_create_group(self):
        """Test creating machine groups"""
        cmd = MachineCommand()

        # Register machines first
        cmd.execute({
            'action': 'register',
            'hostname': 'group-host-1',
            'ip_address': '192.168.1.105',
            'port': 8080,
            'tags': 'group'
        })

        cmd.execute({
            'action': 'register',
            'hostname': 'group-host-2',
            'ip_address': '192.168.1.106',
            'port': 8080,
            'tags': 'group'
        })

        # Get machine IDs
        machines = cmd.registry.list_machines()
        machine_ids = [m.machine_id for m in machines if 'group-host' in m.hostname]

        # Create group
        result = cmd.execute({
            'action': 'group',
            'group_name': 'test-group',
            'group_members': ','.join(machine_ids)
        })

        assert "Created group 'test-group'" in result

    def test_list_groups(self):
        """Test listing machine groups"""
        cmd = MachineCommand()

        # Create a group first (minimal setup)
        cmd.execute({
            'action': 'register',
            'hostname': 'group-list-host',
            'ip_address': '192.168.1.107',
            'port': 8080,
            'tags': 'group-list'
        })

        machines = cmd.registry.list_machines()
        machine_id = machines[-1].machine_id

        cmd.execute({
            'action': 'group',
            'group_name': 'list-test-group',
            'group_members': machine_id
        })

        # List groups
        result = cmd.execute({'action': 'groups'})
        assert "Machine Groups" in result
        assert "list-test-group" in result

    def test_update_status(self):
        """Test updating machine status"""
        cmd = MachineCommand()

        # Register machine
        cmd.execute({
            'action': 'register',
            'hostname': 'status-host',
            'ip_address': '192.168.1.108',
            'port': 8080,
            'tags': 'status'
        })

        machines = cmd.registry.list_machines()
        machine_id = machines[-1].machine_id

        # Update status
        result = cmd.execute({'action': 'status', 'machine_id': machine_id})
        assert "Updated status for machine 'status-host'" in result

    def test_unregister_machine(self):
        """Test unregistering a machine"""
        cmd = MachineCommand()

        # Register machine
        cmd.execute({
            'action': 'register',
            'hostname': 'unregister-host',
            'ip_address': '192.168.1.109',
            'port': 8080,
            'tags': 'unregister'
        })

        machines_before = cmd.registry.list_machines()
        machine_id = machines_before[-1].machine_id

        # Unregister
        result = cmd.execute({'action': 'unregister', 'machine_id': machine_id})
        assert f"Unregistered machine '{machine_id}'" in result

        # Verify gone
        machines_after = cmd.registry.list_machines()
        assert len(machines_after) == len(machines_before) - 1

    def test_invalid_action(self):
        """Test invalid action handling"""
        cmd = MachineCommand()
        result = cmd.execute({'action': 'invalid'})
        assert "Invalid action" in result

    def test_missing_required_args(self):
        """Test missing required arguments"""
        cmd = MachineCommand()

        # Test register without hostname
        result = cmd.execute({'action': 'register', 'ip_address': '192.168.1.1'})
        assert "Hostname and IP address required" in result

        # Test show without machine_id
        result = cmd.execute({'action': 'show'})
        assert "Machine ID required" in result


def test_machine_command_main():
    """Test the main function with command line args"""
    import sys
    from io import StringIO

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()

    try:
        # Test help (no args)
        sys.argv = ['run.py']
        try:
            from isaac.commands.machine.run import main
            main()
        except SystemExit:
            pass  # Expected for help

        output = captured_output.getvalue()
        assert "Usage:" in output

    finally:
        sys.stdout = old_stdout


if __name__ == "__main__":
    pytest.main([__file__])