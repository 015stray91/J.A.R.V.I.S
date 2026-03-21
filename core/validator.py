"""
Validator for Jarvis X
Validates commands before execution for safety and correctness
"""

import os
from pathlib import Path
from typing import Dict, Tuple, Optional
from utils.logger import get_logger
from utils.config_manager import get_config

logger = get_logger()
config = get_config()


class Validator:
    """Validates commands before execution"""

    def __init__(self):
        self.security_config = config.get('security', {})
        self.require_confirmation = self.security_config.get('require_confirmation', {})
        self.allowed_operations = self.security_config.get('allowed_operations', {})

    def validate(self, intent: str, parameters: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate a command
        Returns: (is_valid, error_message, warning_message)
        """

        # Get the validator method for this intent
        validator_method = getattr(self, f'_validate_{intent}', None)

        if validator_method:
            return validator_method(parameters)

        # Default: allow if no specific validator
        return True, None, None

    def _validate_launch_app(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate app launch command"""
        if 'target' not in params or not params['target']:
            return False, "No application specified", None

        return True, None, None

    def _validate_close_app(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate app close command"""
        if 'target' not in params or not params['target']:
            return False, "No application specified", None

        # Check if confirmation is required
        if self.require_confirmation.get('app_close', False):
            warning = "This will close the application. Unsaved work may be lost."
            return True, None, warning

        return True, None, None

    def _validate_screenshot(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate screenshot command"""
        # Check if save path is valid
        save_path = params.get('save_path')
        if save_path:
            try:
                path = Path(save_path)
                if not path.parent.exists():
                    return False, f"Save directory does not exist: {path.parent}", None
            except Exception as e:
                return False, f"Invalid save path: {e}", None

        return True, None, None

    def _validate_delete_file(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate file deletion command"""
        if not self.allowed_operations.get('file_deletion', True):
            return False, "File deletion is disabled in security settings", None

        target = params.get('target')
        if not target:
            return False, "No file or folder specified", None

        # Check if it's a system file or directory
        if self._is_system_path(target):
            return False, "Cannot delete system files or directories", None

        # Always require confirmation for deletion
        warning = f"This will permanently delete: {target}"
        return True, None, warning

    def _validate_shutdown(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate shutdown command"""
        if self.require_confirmation.get('system_shutdown', True):
            warning = "This will shutdown the system. All applications will be closed."
            return True, None, warning

        return True, None, None

    def _validate_restart(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate restart command"""
        if self.require_confirmation.get('system_shutdown', True):
            warning = "This will restart the system. All applications will be closed."
            return True, None, warning

        return True, None, None

    def _validate_open_file(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate file open command"""
        target = params.get('target')
        if not target:
            return False, "No file or folder specified", None

        # Check if path exists
        if os.path.exists(target):
            return True, None, None

        # Path doesn't exist - not necessarily an error, might need to search
        return True, None, None

    def _validate_volume(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate volume command"""
        if 'value' in params:
            value = params['value']
            if not 0 <= value <= 100:
                return False, "Volume must be between 0 and 100", None

        return True, None, None

    def _validate_brightness(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate brightness command"""
        if 'value' in params:
            value = params['value']
            if not 0 <= value <= 100:
                return False, "Brightness must be between 0 and 100", None

        return True, None, None

    def _validate_wifi_status(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_wifi_profiles(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_wifi_connect(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        name = params.get('name', '').strip()
        if not name:
            return False, "No Wi-Fi profile name provided", None
        return True, None, None

    def _validate_wifi_disconnect(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        warning = "This will disconnect current Wi-Fi network"
        return True, None, warning

    def _validate_wifi_toggle(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        direction = params.get('direction', '').strip().lower()
        if direction not in {'on', 'off'}:
            return False, "Wi-Fi toggle must be on or off", None
        warning = f"This will turn Wi-Fi {direction}"
        return True, None, warning

    def _validate_bluetooth_toggle(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        direction = params.get('direction', '').strip().lower()
        if direction not in {'on', 'off'}:
            return False, "Bluetooth toggle must be on or off", None
        warning = f"This will turn Bluetooth {direction}"
        return True, None, warning

    def _validate_smart_switch_toggle(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        direction = params.get('direction', '').strip().lower()
        target = params.get('target', '').strip()
        if direction not in {'on', 'off'}:
            return False, 'Smart switch direction must be on or off', None
        if not target:
            return False, 'No smart switch target provided', None
        return True, None, None

    def _validate_network_discover(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_automation_status(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_ram_acceleration_status(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_ram_acceleration_enable(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_ram_acceleration_disable(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_workflow_memory_status(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_set_workflow_preferences(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        query = params.get('query', '').strip()
        if not query:
            return False, 'Tell me which workflow preferences to remember.', None
        return True, None, None

    def _validate_show_workflow_preferences(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_admin_authorize(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        phrase = params.get('query', '').strip()
        if not phrase:
            return False, 'Provide your admin passphrase to authorize maintenance actions.', None
        return True, None, None

    def _validate_admin_lock(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_self_repair_scan(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_self_repair_apply(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_dependency_alternatives(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_learning_curve_status(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_performance_peaks_report(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_performance_optimize_advice(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_export_workflow_memory(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_create_alert(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        query = params.get('query', '').strip()
        if not query:
            return False, 'Please provide alert details with a time.', None
        return True, None, None

    def _validate_create_event(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        query = params.get('query', '').strip()
        if not query:
            return False, 'Please provide event details with a time.', None
        return True, None, None

    def _validate_list_alerts_events(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_due_alerts_events(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_crypto_market_status(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_crypto_price(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        query = params.get('query', '').strip()
        if not query:
            return False, "No coin provided for price lookup", None
        return True, None, None

    def _validate_crypto_mining_status(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_hiveos_status(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_crypto_wallet_status(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_transaction_control_toggle(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        direction = params.get('direction', '').strip().lower()
        if direction not in {'enable', 'disable', 'turn on', 'turn off', 'on', 'off'}:
            return False, "Transaction control must be on/off or enable/disable", None
        warning = "Changing transaction control may allow or block automated trade actions"
        return True, None, warning

    def _validate_transaction_control_status(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_loss_prevention_check(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_open_account_service(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        target = params.get('target', '').strip()
        if not target:
            return False, "No service provided", None
        return True, None, None

    def _validate_show_lyrics(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_show_camera_video(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_firetv_connect(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        target = params.get('target', '').strip()
        if not target:
            return False, "No Fire TV IP address provided", None
        return True, None, None

    def _validate_firetv_remote(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        target = params.get('target', '').strip()
        if not target:
            return False, "No Fire TV key provided", None
        return True, None, None

    def _validate_create_folder(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate create folder command"""
        name = params.get('name')
        if not name:
            return False, "No folder name specified", None

        # Check for invalid characters
        invalid_chars = '<>:"/\\|?*'
        if any(char in name for char in invalid_chars):
            return False, f"Folder name contains invalid characters: {invalid_chars}", None

        return True, None, None

    def _validate_dev_task(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate developer workflow task command"""
        task = params.get('task', '').strip().lower()
        if not task:
            return False, "No development task specified", None

        allowed_tasks = {
            'test',
            'tests',
            'test suite',
            'unit tests',
            'build',
            'lint',
            'format',
            'install dependencies',
            'dependencies',
            'git status',
            'git pull'
        }

        if task not in allowed_tasks:
            return False, f"Development task is not allowed: {task}", None

        if task == 'git pull':
            warning = "This will update local source code from remote."
            return True, None, warning

        return True, None, None

    def _validate_web_search(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate web search command"""
        query = params.get('query', '').strip()
        if not query:
            return False, "No search query provided", None

        if len(query) > 300:
            return False, "Search query is too long", None

        return True, None, None

    def _validate_analyze_build_log(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate build log analysis command"""
        log_path = params.get('path', '').strip()
        if not log_path:
            return False, "No build log path provided", None

        if not os.path.exists(log_path):
            return False, f"Build log file not found: {log_path}", None

        if os.path.isdir(log_path):
            return False, "Provided path is a directory, not a build log file", None

        return True, None, None

    def _validate_lp_dump(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        image_path = params.get('path', '').strip()
        if not image_path:
            return False, "No image path provided for LP dump", None
        if not os.path.exists(image_path):
            return False, f"Image file not found: {image_path}", None
        return True, None, None

    def _validate_lp_unpack(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        image_path = params.get('path', '').strip()
        output_dir = params.get('output', '').strip()

        if not image_path:
            return False, "No image path provided for LP unpack", None
        if not os.path.exists(image_path):
            return False, f"Image file not found: {image_path}", None
        if not output_dir:
            return False, "No output directory provided for LP unpack", None

        warning = f"This will extract partition data into: {output_dir}"
        return True, None, warning

    def _validate_inspect_wsl(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_inspect_container(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_wsl_diagnose(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        distro = params.get('target', '').strip()
        if not distro:
            return False, "No WSL distro provided", None
        return True, None, None

    def _validate_inspect_toml(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        path = params.get('path', '').strip()
        if not path:
            return False, "No TOML file path provided", None
        if not os.path.exists(path):
            return False, f"TOML file not found: {path}", None
        return True, None, None

    def _validate_inspect_dot_config(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        path = params.get('path', '').strip()
        if not path:
            return False, "No .config file path provided", None
        if not os.path.exists(path):
            return False, f"Config file not found: {path}", None
        return True, None, None

    def _validate_inspect_go_mod(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        path = params.get('path', '').strip()
        if not path:
            return False, "No go.mod file path provided", None
        if not os.path.exists(path):
            return False, f"go.mod not found: {path}", None
        return True, None, None

    def _validate_inspect_deb(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        path = params.get('path', '').strip()
        if not path:
            return False, "No .deb package path provided", None
        if not os.path.exists(path):
            return False, f"Deb package not found: {path}", None
        return True, None, None

    def _validate_analyze_kernel_source(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        path = params.get('path', '').strip()
        if not path:
            return False, "No kernel source path provided", None
        if not os.path.exists(path):
            return False, f"Kernel source path not found: {path}", None
        if not os.path.isdir(path):
            return False, "Kernel source path must be a directory", None
        return True, None, None

    def _validate_inspect_linux_distro(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        distro = params.get('target', '').strip()
        if not distro:
            return False, "No Linux distro provided", None
        return True, None, None

    def _validate_analyze_build_environment(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        path = params.get('path', '').strip()
        if not path:
            return False, "No build environment path provided", None
        if not os.path.exists(path):
            return False, f"Build environment path not found: {path}", None
        if not os.path.isdir(path):
            return False, "Build environment path must be a directory", None
        return True, None, None

    def _validate_compose_script(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        query = params.get('query', '').strip()
        if not query:
            return False, "No script intent provided", None

        script_type = params.get('script_type', 'bash').strip().lower()
        if script_type not in {'bash', 'powershell', 'batch'}:
            return False, "Script type must be bash, powershell, or batch", None

        return True, None, None

    def _validate_open_remote_settings(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_open_kde_connect(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_kde_connect_status(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_kde_connect_pair(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        target = params.get('target', '').strip()
        if not target:
            return False, "No KDE Connect device id provided", None
        return True, None, None

    def _validate_linux_connect(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_linux_run(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        query = params.get('query', '').strip()
        if not query:
            return False, "No Linux command provided", None
        return True, None, None

    def _validate_linux_sync(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        local_path = params.get('path', '').strip()
        remote_path = params.get('output', '').strip()
        if not local_path:
            return False, "No local path provided for Linux sync", None
        if not remote_path:
            return False, "No Linux destination path provided", None
        warning = f"This will copy {local_path} to Linux path {remote_path}"
        return True, None, warning

    def _validate_linux_profile_help(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_teach_topic(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        topic = params.get('query', '').strip()
        if not topic:
            return False, "No topic provided", None
        return True, None, None

    def _validate_explain_file(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        path = params.get('path', '').strip()
        if not path:
            return False, "No file path provided", None
        if not os.path.exists(path):
            return False, f"File not found: {path}", None
        return True, None, None

    def _validate_diagnose_uefi(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_diagnose_motorola_eud(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_inspect_firehose(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        path = params.get('path', '').strip()
        if not path:
            return False, "No firehose file path provided", None
        if not os.path.exists(path):
            return False, f"Firehose file not found: {path}", None
        return True, None, None

    def _validate_inspect_elf(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        path = params.get('path', '').strip()
        if not path:
            return False, "No ELF file path provided", None
        if not os.path.exists(path):
            return False, f"ELF file not found: {path}", None
        return True, None, None

    def _validate_repo_query(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        query = params.get('query', '').strip()
        if not query:
            return False, "No repository query provided", None
        return True, None, None

    def _validate_create_design_image(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        output = params.get('output', '').strip()
        if not output:
            return False, "No output image path provided", None
        return True, None, None

    def _validate_create_boot_animation(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        source = params.get('path', '').strip()
        output = params.get('output', '').strip()
        if not source:
            return False, "No source animation path provided", None
        if not os.path.exists(source):
            return False, f"Source animation not found: {source}", None
        if not output:
            return False, "No output bootanimation path provided", None
        return True, None, None

    def _validate_adb_command(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        query = params.get('query', '').strip()
        if not query:
            return False, "No adb arguments provided", None
        return True, None, None

    def _validate_fastboot_command(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        query = params.get('query', '').strip()
        if not query:
            return False, "No fastboot arguments provided", None
        return True, None, None

    def _validate_explain_android_command(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        query = params.get('query', '').strip()
        if not query:
            return False, "No command provided to explain", None
        return True, None, None

    def _validate_phone_pull_data(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        device_path = params.get('path', '').strip()
        local_path = params.get('output', '').strip()
        if not device_path:
            return False, "No phone/device source path provided", None
        if not local_path:
            return False, "No local destination path provided", None
        warning = f"This will copy data from phone path {device_path} to {local_path}"
        return True, None, warning

    def _validate_phone_info(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_launch_scrcpy(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _validate_launch_glidex(self, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        return True, None, None

    def _is_system_path(self, path: str) -> bool:
        """Check if path is a system directory"""
        system_paths = [
            'C:\\Windows',
            'C:\\Program Files',
            'C:\\Program Files (x86)',
            os.environ.get('SYSTEMROOT', ''),
            os.environ.get('PROGRAMFILES', ''),
            os.environ.get('PROGRAMFILES(X86)', ''),
        ]

        abs_path = os.path.abspath(path).lower()

        for sys_path in system_paths:
            if sys_path and abs_path.startswith(sys_path.lower()):
                return True

        return False

    def is_safe_operation(self, intent: str) -> bool:
        """Check if an operation is generally safe to execute"""
        # Operations that are always safe
        safe_operations = [
            'greeting', 'status', 'help', 'thank',
            'time', 'date', 'weather', 'system_info',
            'list_apps', 'screenshot', 'screenshot_window'
        ]

        return intent in safe_operations

    def requires_confirmation(self, intent: str) -> bool:
        """Check if an intent requires user confirmation"""
        confirmation_intents = [
            'shutdown', 'restart', 'delete_file',
            'close_app',  # if configured
            'dev_task',
            'lp_unpack'
        ]

        if intent in ['close_app'] and not self.require_confirmation.get('app_close', False):
            return False

        return intent in confirmation_intents

