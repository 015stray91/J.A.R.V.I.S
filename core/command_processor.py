"""
Command Processor for Jarvis X
Processes commands and routes them to appropriate modules
"""

from datetime import datetime, timedelta
import time
from typing import Dict, Any
from utils.logger import get_logger
from utils.config_manager import get_config
from core.intent_recognizer import IntentRecognizer
from core.validator import Validator
from personality.response_generator import ResponseGenerator
from modules import (
    ApplicationManager,
    ScreenshotManager,
    SystemController,
    FileManager,
    WindowManager,
    DevelopmentManager,
    ResearchManager,
    KernelRomManager,
    RomOpsManager,
    SourceAnalyzer,
    BuildEnvManager,
    RemoteAccessManager,
    TutorManager,
    UefiManager,
    MotorolaManager,
    FirehoseManager,
    RepoIntelManager,
    ImageCreatorManager,
    AndroidToolsManager,
    CryptoManager,
    IntegrationManager,
    SmartHomeManager,
    NetworkManager,
    AlertsManager,
    WorkflowMemoryManager
)

logger = get_logger()
config = get_config()


class CommandProcessor:
    """Processes and executes commands"""

    def __init__(self):
        self.intent_recognizer = IntentRecognizer()
        self.validator = Validator()
        self.response_generator = ResponseGenerator()

        # Initialize modules
        self.app_manager = ApplicationManager()
        self.screenshot_manager = ScreenshotManager()
        self.system_controller = SystemController()
        self.file_manager = FileManager()
        self.window_manager = WindowManager()
        self.development_manager = DevelopmentManager()
        self.research_manager = ResearchManager()
        self.kernel_rom_manager = KernelRomManager()
        self.rom_ops_manager = RomOpsManager()
        self.source_analyzer = SourceAnalyzer()
        self.build_env_manager = BuildEnvManager()
        self.remote_access_manager = RemoteAccessManager()
        self.tutor_manager = TutorManager()
        self.uefi_manager = UefiManager()
        self.motorola_manager = MotorolaManager()
        self.firehose_manager = FirehoseManager()
        self.repo_intel_manager = RepoIntelManager()
        self.image_creator_manager = ImageCreatorManager()
        self.android_tools_manager = AndroidToolsManager()
        self.crypto_manager = CryptoManager()
        self.integration_manager = IntegrationManager()
        self.smart_home_manager = SmartHomeManager()
        self.network_manager = NetworkManager()
        self.alerts_manager = AlertsManager()
        self.workflow_memory_manager = WorkflowMemoryManager()

        admin_cfg = config.get('security.admin_control', {})
        self.admin_control_enabled = bool(admin_cfg.get('enabled', True))
        self.admin_passphrase = str(admin_cfg.get('passphrase', '') or '').strip()
        self.admin_session_minutes = int(admin_cfg.get('session_minutes', 20) or 20)
        self.admin_session_expires_at = None
        self._last_response_normalized = ''
        self._last_response_timestamp = None

        logger.info("Command processor initialized")

    def process(self, command: str) -> Dict[str, Any]:
        """
        Process a command and return response

        Returns dict with:
        - success: bool
        - response: str (message to user)
        - data: any (additional data)
        - requires_confirmation: bool
        """
        logger.command(command)

        # Recognize intent
        intent_result = self.intent_recognizer.recognize(command)
        intent = intent_result['intent']
        confidence = intent_result['confidence']
        parameters = intent_result['parameters']

        logger.debug(f"Intent: {intent}, Confidence: {confidence:.2f}, Params: {parameters}")

        # Handle unknown intent
        if intent == 'unknown' or confidence < 0.3:
            response = self.response_generator.generate('unknown')
            result = {
                'success': False,
                'response': response,
                'intent': 'unknown'
            }
            self._record_workflow(command, 'unknown', 0.0, {}, result, latency_ms=0.0)
            return result

        # Validate command
        is_valid, error, warning = self.validator.validate(intent, parameters)

        if not is_valid:
            response = self.response_generator.generate('error', intent=intent, error=error)
            result = {
                'success': False,
                'response': response,
                'intent': intent
            }
            self._record_workflow(command, intent, confidence, parameters, result, latency_ms=0.0)
            return result

        # Check if confirmation is required
        if warning and self.validator.requires_confirmation(intent):
            result = {
                'success': False,
                'requires_confirmation': True,
                'intent': intent,
                'parameters': parameters,
                'warning': warning,
                'response': self.response_generator.generate('confirmation',
                                                            intent=intent,
                                                            details=warning)
            }
            self._record_workflow(command, intent, confidence, parameters, result, latency_ms=0.0)
            return result

        # Execute command
        started = time.perf_counter()
        result = self._execute_command(intent, parameters)
        result = self._apply_response_preferences(intent, result)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        self._record_workflow(command, intent, confidence, parameters, result, latency_ms=elapsed_ms)
        return result

    def _apply_response_preferences(self, intent: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply user workflow preferences to outgoing responses."""
        if not isinstance(result, dict) or 'response' not in result:
            return result

        prefs = self.workflow_memory_manager.get_preferences()
        response = str(result.get('response', '') or '').strip()
        if not response:
            return result

        if prefs.get('anti_repeat', True):
            normalized = ' '.join(response.lower().split())
            if normalized == self._last_response_normalized:
                response = 'No change from the previous result. Ready for your next command.'
            self._last_response_normalized = normalized
            self._last_response_timestamp = datetime.now()

        should_markdown = prefs.get('markdown_instructions', True) and intent in {
            'help',
            'set_workflow_preferences',
            'show_workflow_preferences',
            'self_repair_scan',
            'self_repair_apply',
            'dependency_alternatives',
            'performance_optimize_advice'
        }
        if should_markdown:
            response = self._to_markdown_instructions(response, prefs.get('instruction_style', 'numbered'))

        result['response'] = response
        return result

    @staticmethod
    def _to_markdown_instructions(text: str, style: str) -> str:
        text = (text or '').strip()
        if not text:
            return text

        if text.startswith('#') or text.startswith('- ') or text.startswith('1. '):
            return text

        parts = [p.strip() for p in text.replace('\n', ' ').split('. ') if p.strip()]
        if len(parts) <= 1:
            return text

        if style == 'bullets':
            return '\n'.join([f"- {part.rstrip('.')}" for part in parts])

        return '\n'.join([f"{idx}. {part.rstrip('.')}" for idx, part in enumerate(parts, start=1)])

    def _record_workflow(self,
                         command: str,
                         intent: str,
                         confidence: float,
                         parameters: Dict,
                         result: Dict,
                         latency_ms: float = 0.0) -> None:
        """Persist command execution history for long-term workflow retention."""
        try:
            self.workflow_memory_manager.record(
                command=command,
                intent=intent,
                success=bool(result.get('success', False)),
                response=str(result.get('response', '')),
                parameters=parameters,
                confidence=confidence,
                latency_ms=latency_ms
            )
        except Exception as exc:
            logger.debug(f'Workflow memory record skipped: {exc}')

    def _execute_command(self, intent: str, parameters: Dict) -> Dict[str, Any]:
        """Execute a command based on intent"""

        # Get execution method
        executor = getattr(self, f'_execute_{intent}', None)

        if not executor:
            # Try generic execution
            return self._execute_generic(intent, parameters)

        try:
            result = executor(parameters)
            return result
        except Exception as e:
            logger.error(f"Error executing command {intent}: {e}")
            response = self.response_generator.generate('error',
                                                       intent=intent,
                                                       error=str(e))
            return {
                'success': False,
                'response': response,
                'intent': intent
            }

    # Application Control
    def _execute_launch_app(self, params: Dict) -> Dict:
        target = params.get('target', '')

        # Route common phone-integration launch phrases to dedicated handlers.
        lowered = target.lower().strip()
        if lowered in {'scrappy', 'scrcpy', 'screen copy'}:
            return self._execute_launch_scrcpy({})
        if lowered in {'glidex', 'glide x'}:
            return self._execute_launch_glidex({})

        result = self.app_manager.launch(target)

        if result['success']:
            response = self.response_generator.generate(
                'success',
                intent='launch_app',
                details=target
            )
        else:
            response = self.response_generator.generate(
                'error',
                intent='launch_app',
                error=result['message']
            )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'launch_app'
        }

    def _execute_close_app(self, params: Dict) -> Dict:
        target = params.get('target', '')

        # Check for "all"
        if 'all' in target.lower():
            # Extract type (e.g., "all browsers")
            app_type = target.lower().replace('all', '').strip()
            if app_type:
                result = self.app_manager.close_all(app_type)
            else:
                result = {'success': False, 'message': 'Please specify what to close'}
        else:
            result = self.app_manager.close(target)

        if result['success']:
            response = self.response_generator.generate(
                'success',
                intent='close_app',
                details=result.get('message', target)
            )
        else:
            response = self.response_generator.generate(
                'error',
                intent='close_app',
                error=result.get('message', 'Failed to close application')
            )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'close_app'
        }

    def _execute_switch_app(self, params: Dict) -> Dict:
        target = params.get('target', '')
        result = self.app_manager.switch_to(target)

        if result['success']:
            response = self.response_generator.generate(
                'success',
                intent='switch_app',
                details=result.get('message', '')
            )
        else:
            response = self.response_generator.generate(
                'error',
                intent='switch_app',
                error=result.get('message', 'Failed to switch application')
            )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'switch_app'
        }

    def _execute_list_apps(self, params: Dict) -> Dict:
        result = self.app_manager.list_running()

        if result['success']:
            apps = result['apps'][:10]  # Top 10
            app_list = '\n'.join([f"- {app['name']} ({app['memory_mb']} MB)"
                                 for app in apps])
            details = f"Running {result['count']} applications:\n{app_list}"
            response = self.response_generator.generate(
                'success',
                intent='list_apps',
                details=details
            )
        else:
            response = self.response_generator.generate(
                'error',
                intent='list_apps',
                error=result.get('message', 'Failed to list applications')
            )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'list_apps',
            'data': result.get('apps', [])
        }

    # Screenshot Operations
    def _execute_screenshot(self, params: Dict) -> Dict:
        result = self.screenshot_manager.capture_full_screen()

        if result['success']:
            response = self.response_generator.generate(
                'success',
                intent='screenshot',
                details=result.get('message', '')
            )
        else:
            response = self.response_generator.generate(
                'error',
                intent='screenshot',
                error=result.get('message', 'Failed to capture screenshot')
            )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'screenshot',
            'filepath': result.get('filepath')
        }

    def _execute_screenshot_window(self, params: Dict) -> Dict:
        result = self.screenshot_manager.capture_window()

        if result['success']:
            response = self.response_generator.generate(
                'success',
                intent='screenshot',
                details=result.get('message', '')
            )
        else:
            response = self.response_generator.generate(
                'error',
                intent='screenshot',
                error=result.get('message', 'Failed to capture window screenshot')
            )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'screenshot_window',
            'filepath': result.get('filepath')
        }

    # System Control
    def _execute_volume(self, params: Dict) -> Dict:
        if 'value' in params:
            result = self.system_controller.set_volume(params['value'])
        elif 'direction' in params:
            result = self.system_controller.adjust_volume(params['direction'])
        else:
            result = {'success': False, 'message': 'No volume value or direction specified'}

        if result['success']:
            response = self.response_generator.generate(
                'success',
                intent='volume',
                details=result.get('message', '')
            )
        else:
            response = self.response_generator.generate(
                'error',
                intent='volume',
                error=result.get('message', 'Failed to adjust volume')
            )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'volume'
        }

    def _execute_mute(self, params: Dict) -> Dict:
        result = self.system_controller.mute()

        if result['success']:
            response = self.response_generator.generate(
                'success',
                intent='mute',
                details=result.get('message', '')
            )
        else:
            response = self.response_generator.generate(
                'error',
                intent='mute',
                error=result.get('message', 'Failed to mute')
            )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'mute'
        }

    def _execute_system_info(self, params: Dict) -> Dict:
        result = self.system_controller.get_system_info()

        if result['success']:
            cpu = result['cpu']
            memory = result['memory']
            disk = result['disk']
            battery = result.get('battery')

            details = f"All systems nominal, sir. "
            details += f"CPU at {cpu['percent']:.0f}%, "
            details += f"RAM usage {memory['percent']:.0f}%, "

            if battery:
                details += f"battery at {battery['percent']:.0f}%. "

            details += f"You have {disk['free']} of free storage remaining."

            response = self.response_generator.generate(
                'success',
                intent='system_info',
                details=details
            )
        else:
            response = self.response_generator.generate(
                'error',
                intent='system_info',
                error=result.get('message', 'Failed to get system info')
            )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'system_info',
            'data': result if result['success'] else None
        }

    def _execute_wifi_status(self, params: Dict) -> Dict:
        result = self.system_controller.get_wifi_status()
        response = result.get('output', result.get('message', 'Unable to read Wi-Fi status'))
        return {
            'success': result['success'],
            'response': response,
            'intent': 'wifi_status',
            'data': result
        }

    def _execute_wifi_profiles(self, params: Dict) -> Dict:
        result = self.system_controller.list_wifi_profiles()
        response = result.get('output', result.get('message', 'Unable to list Wi-Fi profiles'))
        return {
            'success': result['success'],
            'response': response,
            'intent': 'wifi_profiles',
            'data': result
        }

    def _execute_wifi_connect(self, params: Dict) -> Dict:
        profile_name = params.get('name', '').strip()
        result = self.system_controller.wifi_connect(profile_name)
        response = result.get('message', 'Wi-Fi connect command completed')
        return {
            'success': result['success'],
            'response': response,
            'intent': 'wifi_connect',
            'data': result
        }

    def _execute_wifi_disconnect(self, params: Dict) -> Dict:
        result = self.system_controller.wifi_disconnect()
        response = result.get('message', 'Wi-Fi disconnect command completed')
        return {
            'success': result['success'],
            'response': response,
            'intent': 'wifi_disconnect',
            'data': result
        }

    def _execute_wifi_toggle(self, params: Dict) -> Dict:
        direction = params.get('direction', '').strip().lower()
        result = self.system_controller.wifi_toggle(direction == 'on')
        response = result.get('message', 'Wi-Fi toggle command completed')
        return {
            'success': result['success'],
            'response': response,
            'intent': 'wifi_toggle',
            'data': result
        }

    def _execute_bluetooth_toggle(self, params: Dict) -> Dict:
        direction = params.get('direction', '').strip().lower()
        result = self.system_controller.bluetooth_toggle(direction == 'on')
        response = result.get('message', 'Bluetooth toggle command completed')
        return {
            'success': result['success'],
            'response': response,
            'intent': 'bluetooth_toggle',
            'data': result
        }

    def _execute_lock_screen(self, params: Dict) -> Dict:
        result = self.system_controller.lock_screen()

        response = self.response_generator.generate(
            'success',
            intent='lock_screen'
        )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'lock_screen'
        }

    def _execute_shutdown(self, params: Dict) -> Dict:
        result = self.system_controller.shutdown()

        return {
            'success': result['success'],
            'response': "Shutting down now, sir.",
            'intent': 'shutdown'
        }

    def _execute_restart(self, params: Dict) -> Dict:
        result = self.system_controller.restart()

        return {
            'success': result['success'],
            'response': "Restarting now, sir.",
            'intent': 'restart'
        }

    def _execute_sleep(self, params: Dict) -> Dict:
        result = self.system_controller.sleep()

        return {
            'success': result['success'],
            'response': "Putting system to sleep, sir.",
            'intent': 'sleep'
        }

    # File Operations
    def _execute_open_file(self, params: Dict) -> Dict:
        target = params.get('target', '')
        result = self.file_manager.open_file(target)

        if result['success']:
            response = self.response_generator.generate(
                'success',
                intent='open_file',
                details=result.get('message', '')
            )
        else:
            response = self.response_generator.generate(
                'error',
                intent='open_file',
                error=result.get('message', 'Failed to open file')
            )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'open_file'
        }

    def _execute_find_files(self, params: Dict) -> Dict:
        query = params.get('query', '')
        result = self.file_manager.find_files(query)

        if result['success']:
            count = result['count']
            if count > 0:
                files = result['files'][:5]  # Show first 5
                file_list = '\n'.join([f"- {f['name']} ({f['size']})"
                                      for f in files])
                details = f"I found {count} file(s):\n{file_list}"
                if result.get('truncated'):
                    details += "\n(Showing first 5 results)"
            else:
                details = f"I couldn't find any files matching '{query}'"

            response = self.response_generator.generate(
                'success',
                intent='find_files',
                details=details
            )
        else:
            response = self.response_generator.generate(
                'error',
                intent='find_files',
                error=result.get('message', 'Failed to search for files')
            )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'find_files',
            'data': result.get('files', [])
        }

    def _execute_create_folder(self, params: Dict) -> Dict:
        name = params.get('name', '')
        result = self.file_manager.create_folder(name)

        if result['success']:
            response = self.response_generator.generate(
                'success',
                intent='create_folder',
                details=result.get('message', '')
            )
        else:
            response = self.response_generator.generate(
                'error',
                intent='create_folder',
                error=result.get('message', 'Failed to create folder')
            )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'create_folder'
        }

    def _execute_delete_file(self, params: Dict) -> Dict:
        target = params.get('target', '')
        result = self.file_manager.delete_file(target)

        if result['success']:
            response = self.response_generator.generate(
                'success',
                intent='delete_file',
                details=result.get('message', '')
            )
        else:
            response = self.response_generator.generate(
                'error',
                intent='delete_file',
                error=result.get('message', 'Failed to delete file')
            )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'delete_file'
        }

    def _execute_dev_task(self, params: Dict) -> Dict:
        spoken_task = params.get('task', '').strip().lower()

        task_map = {
            'test': 'run_tests',
            'tests': 'run_tests',
            'test suite': 'run_tests',
            'unit tests': 'run_unit_tests',
            'build': 'build',
            'lint': 'lint',
            'format': 'lint',
            'install dependencies': 'install_dependencies',
            'dependencies': 'install_dependencies',
            'git status': 'git_status',
            'git pull': 'git_pull'
        }

        task = task_map.get(spoken_task)
        if not task:
            return {
                'success': False,
                'response': f"I can run tests, build, lint, install dependencies, or check git status. I did not understand '{spoken_task}'.",
                'intent': 'dev_task'
            }

        result = self.development_manager.run_task(task)

        if result['success']:
            output = result.get('output', 'No output')
            response = f"Development task '{spoken_task}' completed. {output}"
        else:
            output = result.get('output', result.get('message', 'Task failed'))
            response = f"Development task '{spoken_task}' failed. {output}"

        return {
            'success': result['success'],
            'response': response,
            'intent': 'dev_task',
            'data': result
        }

    def _execute_web_search(self, params: Dict) -> Dict:
        query = params.get('query', '').strip()
        result = self.research_manager.search_web(query)

        # Offline mode fallback: local workspace search
        if not result.get('success') and 'offline mode' in str(result.get('message', '')).lower():
            result = self.research_manager.search_workspace(query)

        if result['success']:
            summary = result.get('summary', '')
            results = result.get('results', [])
            if summary:
                response = f"Here is what I found for '{query}': {summary}"
            elif results:
                top = results[0]
                response = f"Top result for '{query}': {top.get('snippet', 'No details available.')}"
            else:
                response = f"I could not find an instant answer for '{query}', but the search completed."
        else:
            response = self.response_generator.generate(
                'error',
                intent='web_search',
                error=result.get('message', 'Search failed')
            )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'web_search',
            'data': result
        }

    def _execute_analyze_build_environment(self, params: Dict) -> Dict:
        path = params.get('path', '').strip()
        result = self.build_env_manager.analyze_environment(path)

        if result['success']:
            response = (
                f"Build environment analysis complete for {path}. "
                f"Detected files: {result.get('detected_files', {})}. "
                f"Hints: {' | '.join(result.get('tool_hints', []))}"
            )
        else:
            response = self.response_generator.generate('error', intent='analyze_build_environment', error=result.get('message', 'Build environment analysis failed'))

        return {
            'success': result['success'],
            'response': response,
            'intent': 'analyze_build_environment',
            'data': result
        }

    def _execute_compose_script(self, params: Dict) -> Dict:
        request = params.get('query', '').strip()
        script_type = params.get('script_type', 'bash').strip().lower()
        result = self.build_env_manager.compose_script(request, script_type)

        if result['success']:
            save_path = result.get('filename', 'generated_build.sh')
            save_result = self.build_env_manager.save_script(save_path, result.get('script', ''))

            if save_result['success']:
                response = f"Generated {script_type} build script and saved it to {save_result.get('path')}"
            else:
                response = f"Script generated but not saved: {save_result.get('message', '')}"
        else:
            response = self.response_generator.generate('error', intent='compose_script', error=result.get('message', 'Script composition failed'))

        return {
            'success': result['success'],
            'response': response,
            'intent': 'compose_script',
            'data': result
        }

    def _execute_open_remote_settings(self, params: Dict) -> Dict:
        result = self.remote_access_manager.open_remote_desktop_settings()
        response = result.get('message', 'Remote settings action completed')
        return {
            'success': result['success'],
            'response': response,
            'intent': 'open_remote_settings',
            'data': result
        }

    def _execute_open_kde_connect(self, params: Dict) -> Dict:
        result = self.remote_access_manager.open_kde_connect()
        response = result.get('message', 'KDE Connect action completed')
        return {
            'success': result['success'],
            'response': response,
            'intent': 'open_kde_connect',
            'data': result
        }

    def _execute_kde_connect_status(self, params: Dict) -> Dict:
        result = self.remote_access_manager.kde_connect_status()
        response = result.get('output', result.get('message', 'KDE Connect status unavailable'))
        return {
            'success': result['success'],
            'response': response,
            'intent': 'kde_connect_status',
            'data': result
        }

    def _execute_kde_connect_pair(self, params: Dict) -> Dict:
        device_id = params.get('target', '').strip()
        result = self.remote_access_manager.kde_connect_pair(device_id)
        response = result.get('output', result.get('message', 'KDE Connect pairing action completed'))
        return {
            'success': result['success'],
            'response': response,
            'intent': 'kde_connect_pair',
            'data': result
        }

    def _execute_linux_connect(self, params: Dict) -> Dict:
        result = self.remote_access_manager.linux_ping('default')
        if result['success']:
            response = "Linux link is online and reachable over SSH."
        else:
            response = result.get('message', 'Linux connection failed')
        return {
            'success': result['success'],
            'response': response,
            'intent': 'linux_connect',
            'data': result
        }

    def _execute_linux_run(self, params: Dict) -> Dict:
        command = params.get('query', '').strip()
        result = self.remote_access_manager.linux_run(command, 'default')
        response = result.get('output', result.get('message', 'Linux command completed'))
        return {
            'success': result['success'],
            'response': response,
            'intent': 'linux_run',
            'data': result
        }

    def _execute_linux_sync(self, params: Dict) -> Dict:
        local_path = params.get('path', '').strip()
        remote_path = params.get('output', '').strip()
        result = self.remote_access_manager.linux_sync_to(local_path, remote_path, 'default')
        if result['success']:
            response = f"Synced {local_path} to Linux path {remote_path}."
        else:
            response = result.get('message', 'Linux sync failed')
        return {
            'success': result['success'],
            'response': response,
            'intent': 'linux_sync',
            'data': result
        }

    def _execute_linux_profile_help(self, params: Dict) -> Dict:
        result = self.remote_access_manager.get_linux_profile_help()
        response = result.get('message', 'Linux profile help is available in config')
        example = result.get('example')
        if example:
            response = f"{response}. Example: {example}"
        return {
            'success': result['success'],
            'response': response,
            'intent': 'linux_profile_help',
            'data': result
        }

    def _execute_analyze_build_log(self, params: Dict) -> Dict:
        log_path = params.get('path', '').strip()
        result = self.kernel_rom_manager.analyze_build_log(log_path)

        if result['success']:
            findings = result.get('findings', [])
            if findings:
                top = findings[0]
                response = (
                    f"I analyzed the build log and found {result.get('error_count', 0)} likely errors. "
                    f"Top issue: {top.get('details', '')}. Suggested fix: {top.get('hint', '')}"
                )
            else:
                response = "I analyzed the build log and did not find explicit error signatures."
        else:
            response = self.response_generator.generate(
                'error',
                intent='analyze_build_log',
                error=result.get('message', 'Build log analysis failed')
            )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'analyze_build_log',
            'data': result
        }

    def _execute_lp_dump(self, params: Dict) -> Dict:
        image_path = params.get('path', '').strip()
        result = self.rom_ops_manager.lp_dump(image_path)
        response = (
            f"LP dump completed for {image_path}. {result.get('output', '')}"
            if result['success']
            else f"LP dump failed for {image_path}. {result.get('output', result.get('message', 'No details'))}"
        )
        return {
            'success': result['success'],
            'response': response,
            'intent': 'lp_dump',
            'data': result
        }

    def _execute_lp_unpack(self, params: Dict) -> Dict:
        image_path = params.get('path', '').strip()
        output_dir = params.get('output', 'output_lp').strip()
        result = self.rom_ops_manager.lp_unpack(image_path, output_dir)
        response = (
            f"LP unpack completed to {output_dir}. {result.get('output', '')}"
            if result['success']
            else f"LP unpack failed. {result.get('output', result.get('message', 'No details'))}"
        )
        return {
            'success': result['success'],
            'response': response,
            'intent': 'lp_unpack',
            'data': result
        }

    def _execute_inspect_wsl(self, params: Dict) -> Dict:
        result = self.rom_ops_manager.wsl_list()
        response = (
            f"WSL environments: {result.get('output', '')}"
            if result['success']
            else f"Unable to inspect WSL. {result.get('output', result.get('message', 'No details'))}"
        )
        return {
            'success': result['success'],
            'response': response,
            'intent': 'inspect_wsl',
            'data': result
        }

    def _execute_inspect_container(self, params: Dict) -> Dict:
        target = params.get('target', '').strip()
        if target:
            result = self.rom_ops_manager.container_logs(target)
            response = (
                f"Recent logs for container {target}: {result.get('output', '')}"
                if result['success']
                else f"Unable to get logs for {target}. {result.get('output', result.get('message', 'No details'))}"
            )
        else:
            result = self.rom_ops_manager.container_list()
            response = (
                f"Container list: {result.get('output', '')}"
                if result['success']
                else f"Unable to inspect containers. {result.get('output', result.get('message', 'No details'))}"
            )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'inspect_container',
            'data': result
        }

    def _execute_wsl_diagnose(self, params: Dict) -> Dict:
        distro = params.get('target', '').strip()
        diag_cmd = "uname -a; ls /; df -h; free -h"
        result = self.rom_ops_manager.wsl_exec(distro, diag_cmd)
        response = (
            f"WSL diagnostics for {distro}: {result.get('output', '')}"
            if result['success']
            else f"WSL diagnostics failed for {distro}. {result.get('output', result.get('message', 'No details'))}"
        )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'wsl_diagnose',
            'data': result
        }

    def _execute_inspect_toml(self, params: Dict) -> Dict:
        path = params.get('path', '').strip()
        result = self.source_analyzer.analyze_toml(path)
        if result['success']:
            keys = ', '.join(result.get('keys', [])[:10]) or 'no keys'
            response = f"TOML parsed successfully. Top sections: {keys}."
        else:
            response = self.response_generator.generate('error', intent='inspect_toml', error=result.get('message', 'TOML inspection failed'))

        return {
            'success': result['success'],
            'response': response,
            'intent': 'inspect_toml',
            'data': result
        }

    def _execute_inspect_dot_config(self, params: Dict) -> Dict:
        path = params.get('path', '').strip()
        result = self.source_analyzer.analyze_dot_config(path)
        if result['success']:
            compression = ', '.join(result.get('kernel_compression', [])) or 'not detected'
            response = (
                f"Config parsed. Enabled: {result.get('enabled_count', 0)}, "
                f"Modules: {result.get('module_count', 0)}, "
                f"Disabled: {result.get('disabled_count', 0)}, "
                f"Kernel compression: {compression}."
            )
        else:
            response = self.response_generator.generate('error', intent='inspect_dot_config', error=result.get('message', 'Config inspection failed'))

        return {
            'success': result['success'],
            'response': response,
            'intent': 'inspect_dot_config',
            'data': result
        }

    def _execute_inspect_go_mod(self, params: Dict) -> Dict:
        path = params.get('path', '').strip()
        result = self.source_analyzer.analyze_go_module(path)
        if result['success']:
            response = (
                f"Go module parsed. Module: {result.get('module', 'unknown')}, "
                f"Go version: {result.get('go_version', 'unknown')}, "
                f"Dependencies: {result.get('require_count', 0)}."
            )
        else:
            response = self.response_generator.generate('error', intent='inspect_go_mod', error=result.get('message', 'go.mod inspection failed'))

        return {
            'success': result['success'],
            'response': response,
            'intent': 'inspect_go_mod',
            'data': result
        }

    def _execute_inspect_deb(self, params: Dict) -> Dict:
        path = params.get('path', '').strip()
        result = self.source_analyzer.inspect_deb(path)
        if result['success']:
            response = f"Deb package inspection completed. {result.get('message', '')}"
        else:
            response = self.response_generator.generate('error', intent='inspect_deb', error=result.get('message', 'Deb inspection failed'))

        return {
            'success': result['success'],
            'response': response,
            'intent': 'inspect_deb',
            'data': result
        }

    def _execute_analyze_kernel_source(self, params: Dict) -> Dict:
        path = params.get('path', '').strip()
        result = self.source_analyzer.analyze_kernel_source(path)
        if result['success']:
            compression = ', '.join(result.get('compression', [])) or 'not set'
            response = (
                f"Kernel source looks readable. Version: {result.get('kernel_version', 'unknown')}. "
                f"Compression: {compression}. Readiness flags: {result.get('readiness', {})}."
            )
        else:
            response = self.response_generator.generate('error', intent='analyze_kernel_source', error=result.get('message', 'Kernel source analysis failed'))

        return {
            'success': result['success'],
            'response': response,
            'intent': 'analyze_kernel_source',
            'data': result
        }

    def _execute_inspect_linux_distro(self, params: Dict) -> Dict:
        distro = params.get('target', '').strip()
        if not distro:
            distro = 'Ubuntu'

        distro_l = distro.lower()
        if distro_l == 'linux':
            distro = 'Ubuntu'

        diag_cmd = (
            "cat /etc/os-release; "
            "uname -a; "
            "which gcc || true; "
            "which clang || true; "
            "which make || true; "
            "which python3 || true; "
            "which git || true; "
            "if command -v apt >/dev/null 2>&1; then apt --version; fi"
        )

        result = self.rom_ops_manager.wsl_exec(distro, diag_cmd)
        if result['success']:
            response = f"{distro} diagnostics completed. {result.get('output', '')}"
        else:
            response = self.response_generator.generate('error', intent='inspect_linux_distro', error=result.get('output', result.get('message', 'Linux distro inspection failed')))

        return {
            'success': result['success'],
            'response': response,
            'intent': 'inspect_linux_distro',
            'data': result
        }

    def _execute_teach_topic(self, params: Dict) -> Dict:
        topic = params.get('query', '').strip()
        result = self.tutor_manager.explain_topic(topic)
        response = result.get('explanation', result.get('message', 'No explanation available'))
        return {
            'success': result['success'],
            'response': response,
            'intent': 'teach_topic',
            'data': result
        }

    def _execute_explain_file(self, params: Dict) -> Dict:
        path = params.get('path', '').strip()
        result = self.tutor_manager.explain_file(path)
        response = result.get('explanation', result.get('message', 'Unable to explain file'))
        return {
            'success': result['success'],
            'response': response,
            'intent': 'explain_file',
            'data': result
        }

    def _execute_diagnose_uefi(self, params: Dict) -> Dict:
        result = self.uefi_manager.run_diagnostics()
        response = f"UEFI diagnostics complete. Failed checks: {result.get('failed_checks', 0)}"
        return {
            'success': result['success'],
            'response': response,
            'intent': 'diagnose_uefi',
            'data': result
        }

    def _execute_diagnose_motorola_eud(self, params: Dict) -> Dict:
        result = self.motorola_manager.diagnose_eud()
        response = f"Motorola EUD diagnostics mode: {result.get('mode', 'unknown')}. {result.get('guidance', '')}"
        return {
            'success': result['success'],
            'response': response,
            'intent': 'diagnose_motorola_eud',
            'data': result
        }

    def _execute_inspect_firehose(self, params: Dict) -> Dict:
        path = params.get('path', '').strip()
        result = self.firehose_manager.inspect_firehose(path)
        response = result.get('guidance', result.get('message', 'Firehose inspection complete'))
        return {
            'success': result['success'],
            'response': response,
            'intent': 'inspect_firehose',
            'data': result
        }

    def _execute_inspect_elf(self, params: Dict) -> Dict:
        path = params.get('path', '').strip()
        result = self.firehose_manager.inspect_elf(path)
        response = result.get('guidance', result.get('message', 'ELF inspection complete'))
        return {
            'success': result['success'],
            'response': response,
            'intent': 'inspect_elf',
            'data': result
        }

    def _execute_repo_query(self, params: Dict) -> Dict:
        query = params.get('query', '').strip()
        result = self.repo_intel_manager.search(query)
        if result.get('success') and result.get('results'):
            first = result['results'][0]
            response = f"Found {result.get('count', 0)} matches. First: {first.get('path')}:{first.get('line')} -> {first.get('text')}"
        else:
            response = result.get('message', 'No repository matches found')
        return {
            'success': result['success'],
            'response': response,
            'intent': 'repo_query',
            'data': result
        }

    def _execute_create_design_image(self, params: Dict) -> Dict:
        text = params.get('query', '').strip()
        output = params.get('output', '').strip()
        result = self.image_creator_manager.create_design_image(text, output)
        response = result.get('message', 'Image creation complete')
        return {
            'success': result['success'],
            'response': response,
            'intent': 'create_design_image',
            'data': result
        }

    def _execute_create_boot_animation(self, params: Dict) -> Dict:
        source = params.get('path', '').strip()
        output = params.get('output', '').strip()
        result = self.image_creator_manager.create_boot_animation(source, output)
        response = result.get('message', 'Boot animation creation complete')
        return {
            'success': result['success'],
            'response': response,
            'intent': 'create_boot_animation',
            'data': result
        }

    def _execute_adb_command(self, params: Dict) -> Dict:
        args = params.get('query', '').strip()
        result = self.android_tools_manager.run_adb(args)
        response = result.get('output', result.get('message', 'adb command completed'))
        return {
            'success': result['success'],
            'response': response,
            'intent': 'adb_command',
            'data': result
        }

    def _execute_fastboot_command(self, params: Dict) -> Dict:
        args = params.get('query', '').strip()
        result = self.android_tools_manager.run_fastboot(args)
        response = result.get('output', result.get('message', 'fastboot command completed'))
        return {
            'success': result['success'],
            'response': response,
            'intent': 'fastboot_command',
            'data': result
        }

    def _execute_explain_android_command(self, params: Dict) -> Dict:
        command = params.get('query', '').strip()
        result = self.android_tools_manager.explain_command(command)
        response = result.get('explanation', result.get('message', 'No explanation available'))
        return {
            'success': result['success'],
            'response': response,
            'intent': 'explain_android_command',
            'data': result
        }

    def _execute_phone_pull_data(self, params: Dict) -> Dict:
        device_path = params.get('path', '').strip()
        local_path = params.get('output', '').strip()
        result = self.android_tools_manager.pull_from_phone(device_path, local_path)
        if result.get('success'):
            response = f"Pulled data from {device_path} to {local_path}."
        else:
            response = result.get('message', result.get('output', 'Phone data pull failed'))
        return {
            'success': result['success'],
            'response': response,
            'intent': 'phone_pull_data',
            'data': result
        }

    def _execute_phone_info(self, params: Dict) -> Dict:
        result = self.android_tools_manager.get_phone_info()
        if result.get('success'):
            report = result.get('report', {})
            response = (
                f"Phone connected. Model: {report.get('model', 'unknown')}. "
                f"Android: {report.get('android_version', 'unknown')}. "
                f"Serial: {report.get('serial', 'unknown')}."
            )
        else:
            response = result.get('message', 'Unable to read phone info')
        return {
            'success': result['success'],
            'response': response,
            'intent': 'phone_info',
            'data': result
        }

    def _execute_launch_scrcpy(self, params: Dict) -> Dict:
        result = self.android_tools_manager.launch_scrcpy()
        return {
            'success': result['success'],
            'response': result.get('message', 'scrcpy launch completed'),
            'intent': 'launch_scrcpy',
            'data': result
        }

    def _execute_launch_glidex(self, params: Dict) -> Dict:
        result = self.android_tools_manager.launch_glidex()
        return {
            'success': result['success'],
            'response': result.get('message', 'GlideX launch completed'),
            'intent': 'launch_glidex',
            'data': result
        }

    def _execute_crypto_market_status(self, params: Dict) -> Dict:
        result = self.crypto_manager.market_overview()
        if result.get('success'):
            data = result.get('data', {})
            lines = []
            for coin, info in list(data.items())[:8]:
                price = info.get('usd')
                change = info.get('usd_24h_change')
                lines.append(f"{coin}: ${price} ({change:.2f}% 24h)" if isinstance(change, (int, float)) else f"{coin}: ${price}")
            response = ' | '.join(lines) if lines else 'Market data received but empty.'
        else:
            response = result.get('message', 'Crypto market lookup failed')

        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'crypto_market_status',
            'data': result
        }

    def _execute_crypto_price(self, params: Dict) -> Dict:
        coin = params.get('query', '').strip()
        result = self.crypto_manager.coin_price(coin)
        if result.get('success'):
            response = (
                f"{result.get('coin')}: ${result.get('price_usd')} | "
                f"24h: {result.get('change_24h'):.2f}%"
                if isinstance(result.get('change_24h'), (int, float))
                else f"{result.get('coin')}: ${result.get('price_usd')}"
            )
        else:
            response = result.get('message', 'Coin price lookup failed')

        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'crypto_price',
            'data': result
        }

    def _execute_crypto_mining_status(self, params: Dict) -> Dict:
        result = self.crypto_manager.mining_status()
        if result.get('success'):
            diff = result.get('difficulty', {}).get('bitcoin')
            mcap = result.get('hashrate', {}).get('market_cap_usd')
            response = f"Mining monitor: BTC difficulty={diff}, market cap USD={mcap}"
        else:
            response = result.get('message', 'Mining status lookup failed')

        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'crypto_mining_status',
            'data': result
        }

    def _execute_hiveos_status(self, params: Dict) -> Dict:
        result = self.crypto_manager.hiveos_status()
        if result.get('success'):
            farm_name = result.get('data', {}).get('name', 'unknown farm')
            response = f"HiveOS connected. Farm: {farm_name}."
        else:
            response = result.get('message', 'HiveOS status failed')

        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'hiveos_status',
            'data': result
        }

    def _execute_crypto_wallet_status(self, params: Dict) -> Dict:
        result = self.crypto_manager.wallet_overview()
        wallets = result.get('wallets', [])
        exchanges = result.get('exchanges', [])
        response = (
            f"Wallet watch loaded: {len(wallets)} wallet(s), {len(exchanges)} exchange account(s). "
            "Read-only mode is enabled."
        )
        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'crypto_wallet_status',
            'data': result
        }

    def _execute_transaction_control_toggle(self, params: Dict) -> Dict:
        direction = params.get('direction', '').strip().lower()
        enabled = direction in {'enable', 'turn on', 'on'}
        result = self.crypto_manager.set_transaction_control(enabled)
        return {
            'success': result.get('success', False),
            'response': result.get('message', 'Transaction control update failed'),
            'intent': 'transaction_control_toggle',
            'data': result
        }

    def _execute_transaction_control_status(self, params: Dict) -> Dict:
        result = self.crypto_manager.transaction_control_status()
        response = (
            f"Transaction control is {'ON' if result.get('enabled') else 'OFF'}. "
            f"Mode: {result.get('trade_mode')}. Drop threshold: ${result.get('threshold_usd')}"
        )
        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'transaction_control_status',
            'data': result
        }

    def _execute_loss_prevention_check(self, params: Dict) -> Dict:
        result = self.crypto_manager.evaluate_loss_prevention()
        if not result.get('success'):
            response = result.get('message', 'Loss prevention check failed')
        else:
            alerts = result.get('alerts', [])
            if alerts:
                top = alerts[0]
                response = (
                    f"Loss prevention alert(s): {len(alerts)}. "
                    f"Top: {top.get('coin')} drop ${top.get('drop_total_usd')} ({top.get('drop_percent')}%)."
                )
            else:
                response = 'Loss prevention check: no positions currently breaching your thresholds.'
        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'loss_prevention_check',
            'data': result
        }

    def _execute_open_account_service(self, params: Dict) -> Dict:
        target = params.get('target', '').strip()
        result = self.integration_manager.open_service(target)
        return {
            'success': result.get('success', False),
            'response': result.get('message', 'Service open failed'),
            'intent': 'open_account_service',
            'data': result
        }

    def _execute_show_lyrics(self, params: Dict) -> Dict:
        query = params.get('query', '').strip()
        result = self.integration_manager.open_lyrics(query)
        return {
            'success': result.get('success', False),
            'response': result.get('message', 'Lyrics lookup failed'),
            'intent': 'show_lyrics',
            'data': result
        }

    def _execute_show_camera_video(self, params: Dict) -> Dict:
        result = self.integration_manager.open_camera_video()
        return {
            'success': result.get('success', False),
            'response': result.get('message', 'Camera video could not be opened'),
            'intent': 'show_camera_video',
            'data': result
        }

    def _execute_firetv_connect(self, params: Dict) -> Dict:
        ip = params.get('target', '').strip()
        result = self.android_tools_manager.firetv_connect(ip)
        response = result.get('output', result.get('message', 'Fire TV connect command completed'))
        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'firetv_connect',
            'data': result
        }

    def _execute_firetv_remote(self, params: Dict) -> Dict:
        key_name = params.get('target', '').strip()
        result = self.android_tools_manager.firetv_key(key_name)
        response = result.get('output', result.get('message', 'Fire TV key command completed'))
        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'firetv_remote',
            'data': result
        }

    def _execute_smart_switch_toggle(self, params: Dict) -> Dict:
        direction = params.get('direction', '').strip().lower()
        target = params.get('target', '').strip()
        normalized_state = 'on' if direction in {'on', 'enable', 'turn on'} else 'off'

        result = self.smart_home_manager.set_switch(target, normalized_state)
        return {
            'success': result.get('success', False),
            'response': result.get('message', 'Smart switch command failed'),
            'intent': 'smart_switch_toggle',
            'data': result
        }

    def _execute_network_discover(self, params: Dict) -> Dict:
        result = self.network_manager.discover_devices()
        if not result.get('success'):
            response = result.get('message', 'Network discovery failed')
        else:
            devices = result.get('devices', [])
            top = devices[:8]
            summary = ', '.join([d.get('ip', '?') for d in top])
            response = f"Discovered {len(devices)} device(s): {summary}" if devices else 'No devices found in ARP table.'

        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'network_discover',
            'data': result
        }

    def _execute_automation_status(self, params: Dict) -> Dict:
        automation_cfg = config.get('automations', {})
        schedules = automation_cfg.get('schedules', [])
        enabled = automation_cfg.get('enabled', False)
        response = f"Automation is {'enabled' if enabled else 'disabled'}. Schedules configured: {len(schedules)}"
        return {
            'success': True,
            'response': response,
            'intent': 'automation_status',
            'data': {
                'enabled': enabled,
                'schedules': schedules
            }
        }

    def _execute_ram_acceleration_status(self, params: Dict) -> Dict:
        result = self.system_controller.get_ram_acceleration_status()
        response = result.get('output', result.get('message', 'Unable to read RAM acceleration status'))
        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'ram_acceleration_status',
            'data': result
        }

    def _execute_ram_acceleration_enable(self, params: Dict) -> Dict:
        allowed, message = self._require_admin_session()
        if not allowed:
            return {
                'success': False,
                'response': message,
                'intent': 'ram_acceleration_enable'
            }

        result = self.system_controller.enable_ram_acceleration()
        return {
            'success': result.get('success', False),
            'response': result.get('message', 'Failed to enable RAM acceleration'),
            'intent': 'ram_acceleration_enable',
            'data': result
        }

    def _execute_ram_acceleration_disable(self, params: Dict) -> Dict:
        allowed, message = self._require_admin_session()
        if not allowed:
            return {
                'success': False,
                'response': message,
                'intent': 'ram_acceleration_disable'
            }

        result = self.system_controller.disable_ram_acceleration()
        return {
            'success': result.get('success', False),
            'response': result.get('message', 'Failed to disable RAM acceleration'),
            'intent': 'ram_acceleration_disable',
            'data': result
        }

    def _execute_workflow_memory_status(self, params: Dict) -> Dict:
        result = self.workflow_memory_manager.status()
        top = result.get('top_intents', [])
        top_str = ', '.join([f"{name}({count})" for name, count in top[:3]]) if top else 'none yet'
        avg_latency = result.get('avg_latency_ms')
        latency_part = f" Average latency: {avg_latency} ms." if isinstance(avg_latency, (int, float)) else ''
        response = (
            f"Workflow memory retention: {result.get('total_entries', 0)}/{result.get('retention_limit', 0)} entries. "
            f"Success rate: {result.get('success_rate', 0)}%. Top intents: {top_str}.{latency_part}"
        )
        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'workflow_memory_status',
            'data': result
        }

    def _execute_set_workflow_preferences(self, params: Dict) -> Dict:
        query = params.get('query', '').strip().lower()
        updates = {}

        if 'not repeat' in query or 'do not repeat' in query or "don't repeat" in query:
            updates['anti_repeat'] = True
        if 'repeat' in query and ('allow' in query or 'disable' in query or 'off' in query):
            updates['anti_repeat'] = False

        if 'markdown' in query:
            updates['markdown_instructions'] = True
        if 'no markdown' in query or 'plain text' in query:
            updates['markdown_instructions'] = False

        if 'bullet' in query:
            updates['instruction_style'] = 'bullets'
        elif 'number' in query or 'step by step' in query:
            updates['instruction_style'] = 'numbered'

        if 'concise' in query or 'short' in query:
            updates['verbosity'] = 'concise'
        elif 'detailed' in query or 'full detail' in query:
            updates['verbosity'] = 'detailed'

        if not updates:
            return {
                'success': False,
                'response': 'I did not detect a preference change. Example: set workflow preferences no repeat and markdown numbered.',
                'intent': 'set_workflow_preferences'
            }

        result = self.workflow_memory_manager.update_preferences(updates)
        prefs = result.get('preferences', {})
        response = (
            f"Workflow preferences saved. "
            f"anti_repeat={prefs.get('anti_repeat')}, "
            f"markdown_instructions={prefs.get('markdown_instructions')}, "
            f"instruction_style={prefs.get('instruction_style')}, "
            f"verbosity={prefs.get('verbosity')}."
        )
        return {
            'success': True,
            'response': response,
            'intent': 'set_workflow_preferences',
            'data': result
        }

    def _execute_show_workflow_preferences(self, params: Dict) -> Dict:
        prefs = self.workflow_memory_manager.get_preferences()
        response = (
            f"Current workflow preferences: anti_repeat={prefs.get('anti_repeat')}, "
            f"markdown_instructions={prefs.get('markdown_instructions')}, "
            f"instruction_style={prefs.get('instruction_style')}, verbosity={prefs.get('verbosity')}."
        )
        return {
            'success': True,
            'response': response,
            'intent': 'show_workflow_preferences',
            'data': {
                'preferences': prefs
            }
        }

    def _execute_admin_authorize(self, params: Dict) -> Dict:
        phrase = params.get('query', '').strip()

        if not self.admin_control_enabled:
            return {
                'success': False,
                'response': 'Admin control is disabled in configuration.',
                'intent': 'admin_authorize'
            }

        if not self.admin_passphrase:
            return {
                'success': False,
                'response': 'Admin passphrase is not configured. Set security.admin_control.passphrase in config.json.',
                'intent': 'admin_authorize'
            }

        if phrase != self.admin_passphrase:
            return {
                'success': False,
                'response': 'Admin authorization failed.',
                'intent': 'admin_authorize'
            }

        self.admin_session_expires_at = datetime.now() + timedelta(minutes=self.admin_session_minutes)
        return {
            'success': True,
            'response': f'Admin maintenance session enabled for {self.admin_session_minutes} minutes.',
            'intent': 'admin_authorize',
            'data': {
                'expires_at': self.admin_session_expires_at.isoformat(timespec='seconds')
            }
        }

    def _execute_admin_lock(self, params: Dict) -> Dict:
        self.admin_session_expires_at = None
        return {
            'success': True,
            'response': 'Admin maintenance session locked.',
            'intent': 'admin_lock'
        }

    def _execute_self_repair_scan(self, params: Dict) -> Dict:
        allowed, message = self._require_admin_session()
        if not allowed:
            return {
                'success': False,
                'response': message,
                'intent': 'self_repair_scan'
            }

        result = self.development_manager.diagnose_environment()
        checks = result.get('checks', [])
        failed = [c for c in checks if not c.get('success')]
        if result.get('success'):
            alternatives = result.get('alternatives', [])
            response = (
                f"Self-repair scan complete. {len(checks) - len(failed)}/{len(checks)} checks passed. "
                f"{'Environment healthy.' if result.get('healthy') else 'Repairs recommended.'}"
            )
            if alternatives:
                response += f" Found {len(alternatives)} fallback option group(s). Say 'show alternatives' for details."
        else:
            response = result.get('message', 'Self-repair scan failed.')

        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'self_repair_scan',
            'data': result
        }

    def _execute_self_repair_apply(self, params: Dict) -> Dict:
        allowed, message = self._require_admin_session()
        if not allowed:
            return {
                'success': False,
                'response': message,
                'intent': 'self_repair_apply'
            }

        result = self.development_manager.apply_self_repair()
        failed = result.get('failed_steps', [])
        if result.get('success'):
            response = 'Self repair completed successfully. Dependencies and compile checks are healthy.'
        else:
            response = f"Self repair completed with issues: {', '.join(failed)}"

        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'self_repair_apply',
            'data': result
        }

    def _execute_dependency_alternatives(self, params: Dict) -> Dict:
        allowed, message = self._require_admin_session()
        if not allowed:
            return {
                'success': False,
                'response': message,
                'intent': 'dependency_alternatives'
            }

        alternatives = self.development_manager.get_dependency_alternatives()
        if not alternatives:
            response = 'No missing dependency/tool alternatives detected right now.'
        else:
            top = alternatives[0]
            options = ', '.join(top.get('alternatives', [])[:3])
            response = f"Fallback options for {top.get('missing')}: {options}. Total groups: {len(alternatives)}"

        return {
            'success': True,
            'response': response,
            'intent': 'dependency_alternatives',
            'data': {
                'alternatives': alternatives
            }
        }

    def _execute_learning_curve_status(self, params: Dict) -> Dict:
        result = self.workflow_memory_manager.learning_curve(days=7)
        if result.get('daily'):
            response = (
                f"Learning trend: {result.get('trend')}. "
                f"Success moved from {result.get('early_success_rate')}% to {result.get('late_success_rate')}% "
                f"over {result.get('days')} days."
            )
        else:
            response = result.get('message', 'Not enough history yet to compute learning trend.')

        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'learning_curve_status',
            'data': result
        }

    def _execute_performance_peaks_report(self, params: Dict) -> Dict:
        result = self.workflow_memory_manager.performance_peaks(min_samples=2)
        best = result.get('best_hours', [])
        if best:
            top = best[0]
            response = (
                f"Peak hour is around {int(top.get('hour')):02d}:00 with "
                f"{top.get('success_rate')}% success and {top.get('avg_latency_ms')} ms avg latency."
            )
        else:
            response = 'Not enough samples yet for reliable peak-hour performance analysis.'

        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'performance_peaks_report',
            'data': result
        }

    def _execute_performance_optimize_advice(self, params: Dict) -> Dict:
        result = self.workflow_memory_manager.optimization_advice()
        advice = result.get('advice', [])
        response = advice[0] if advice else 'No optimization advice available yet.'
        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'performance_optimize_advice',
            'data': result
        }

    def _require_admin_session(self):
        if not self.admin_control_enabled:
            return False, 'Admin control is disabled in configuration.'

        if self.admin_session_expires_at is None:
            return False, 'Admin authorization required. Say: admin authorize <your passphrase>.'

        if datetime.now() > self.admin_session_expires_at:
            self.admin_session_expires_at = None
            return False, 'Admin session expired. Re-authorize to run self-repair actions.'

        return True, ''

    def _execute_export_workflow_memory(self, params: Dict) -> Dict:
        output = params.get('path', '').strip()
        result = self.workflow_memory_manager.export_package(output_path=output or None)
        response = f"Workflow package exported: {result.get('path')}"
        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'export_workflow_memory',
            'data': result
        }

    def _execute_create_alert(self, params: Dict) -> Dict:
        phrase = params.get('query', '').strip()
        result = self.alerts_manager.add_alert(phrase)
        if result.get('success'):
            item = result.get('item', {})
            response = f"Alert added: {item.get('title')} at {item.get('due_at')}"
        else:
            response = result.get('message', 'Failed to add alert')

        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'create_alert',
            'data': result
        }

    def _execute_create_event(self, params: Dict) -> Dict:
        phrase = params.get('query', '').strip()
        result = self.alerts_manager.add_event(phrase)
        if result.get('success'):
            item = result.get('item', {})
            response = f"Event added: {item.get('title')} at {item.get('due_at')}"
        else:
            response = result.get('message', 'Failed to add event')

        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'create_event',
            'data': result
        }

    def _execute_list_alerts_events(self, params: Dict) -> Dict:
        target = params.get('target', '').strip().lower()
        kind = 'all'
        if target == 'alerts':
            kind = 'alerts'
        elif target == 'events':
            kind = 'events'

        result = self.alerts_manager.list_items(kind=kind, due_only=False)
        response = self._format_alert_event_list(result, due_only=False)
        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'list_alerts_events',
            'data': result
        }

    def _execute_due_alerts_events(self, params: Dict) -> Dict:
        target = params.get('target', '').strip().lower()
        kind = 'all'
        if target == 'alerts':
            kind = 'alerts'
        elif target == 'events':
            kind = 'events'

        result = self.alerts_manager.list_items(kind=kind, due_only=True)
        response = self._format_alert_event_list(result, due_only=True)
        return {
            'success': result.get('success', False),
            'response': response,
            'intent': 'due_alerts_events',
            'data': result
        }

    def _format_alert_event_list(self, result: Dict, due_only: bool) -> str:
        if not result.get('success'):
            return result.get('message', 'Could not read alerts and events')

        kind = result.get('kind', 'all')
        if kind in {'alerts', 'events'}:
            items = result.get('items', [])
            label = kind
            if not items:
                return f"No {'due ' if due_only else ''}{label} found."

            preview = ', '.join([f"{i.get('title')} ({i.get('due_at')})" for i in items[:5]])
            return f"{len(items)} {'due ' if due_only else ''}{label}: {preview}"

        alerts = result.get('alerts', [])
        events = result.get('events', [])
        if not alerts and not events:
            return f"No {'due ' if due_only else ''}alerts or events found."

        sections = []
        if alerts:
            sections.append(
                'Alerts: ' + ', '.join([f"{i.get('title')} ({i.get('due_at')})" for i in alerts[:3]])
            )
        if events:
            sections.append(
                'Events: ' + ', '.join([f"{i.get('title')} ({i.get('due_at')})" for i in events[:3]])
            )
        return ' | '.join(sections)

    # Window Management
    def _execute_maximize(self, params: Dict) -> Dict:
        result = self.window_manager.maximize_window()

        if result['success']:
            response = self.response_generator.generate(
                'success',
                intent='maximize',
                details=result.get('message', '')
            )
        else:
            response = self.response_generator.generate(
                'error',
                intent='maximize',
                error=result.get('message', 'Failed to maximize window')
            )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'maximize'
        }

    def _execute_minimize(self, params: Dict) -> Dict:
        result = self.window_manager.minimize_window()

        if result['success']:
            response = self.response_generator.generate(
                'success',
                intent='minimize',
                details=result.get('message', '')
            )
        else:
            response = self.response_generator.generate(
                'error',
                intent='minimize',
                error=result.get('message', 'Failed to minimize window')
            )

        return {
            'success': result['success'],
            'response': response,
            'intent': 'minimize'
        }

    # Information Queries
    def _execute_time(self, params: Dict) -> Dict:
        current_time = datetime.now().strftime("%I:%M %p")
        response = f"It's {current_time}, sir."

        return {
            'success': True,
            'response': response,
            'intent': 'time'
        }

    def _execute_date(self, params: Dict) -> Dict:
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        response = f"Today is {current_date}, sir."

        return {
            'success': True,
            'response': response,
            'intent': 'date'
        }

    # General Responses
    def _execute_greeting(self, params: Dict) -> Dict:
        response = self.response_generator.generate('greeting')
        return {
            'success': True,
            'response': response,
            'intent': 'greeting'
        }

    def _execute_status(self, params: Dict) -> Dict:
        response = self.response_generator.generate('status')
        return {
            'success': True,
            'response': response,
            'intent': 'status'
        }

    def _execute_help(self, params: Dict) -> Dict:
        response = self.response_generator.generate('help')
        return {
            'success': True,
            'response': response,
            'intent': 'help'
        }

    def _execute_thank(self, params: Dict) -> Dict:
        response = self.response_generator.generate('thank')
        return {
            'success': True,
            'response': response,
            'intent': 'thank'
        }

    def _execute_generic(self, intent: str, parameters: Dict) -> Dict:
        """Generic execution for unhandled intents"""
        response = f"I understand you want to {intent.replace('_', ' ')}, but I haven't implemented that yet, sir."
        return {
            'success': False,
            'response': response,
            'intent': intent
        }

