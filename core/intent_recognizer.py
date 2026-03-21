"""
Intent Recognizer for Jarvis X
Identifies user intent from natural language commands
"""

import re
from typing import Dict, List, Tuple
from utils.logger import get_logger

logger = get_logger()


class IntentRecognizer:
    """Recognizes user intent from commands"""

    def __init__(self):
        self.intent_patterns = self._build_patterns()

    def _build_patterns(self) -> Dict[str, List[Tuple[re.Pattern, Dict]]]:
        """Build regex patterns for intent recognition"""

        patterns = {
            'launch_scrcpy': [
                (re.compile(r'\b(open|launch|start)\s+(scrcpy|screen\s*copy|scrappy)\b', re.I), {}),
                (re.compile(r'\b(mirror|screen\s+mirror)\s+(my\s+)?phone\b', re.I), {}),
            ],

            'launch_glidex': [
                (re.compile(r'\b(open|launch|start)\s+(glidex|glide\s*x)\b', re.I), {}),
            ],

            'wifi_status': [
                (re.compile(r'\b(wifi|wi[-\s]?fi)\s+(status|state)\b', re.I), {}),
                (re.compile(r'\b(network|internet)\s+status\b', re.I), {}),
            ],

            'wifi_profiles': [
                (re.compile(r'\b(list|show)\s+(wifi|wi[-\s]?fi)\s+(profiles|networks)\b', re.I), {}),
            ],

            'wifi_connect': [
                (re.compile(r'\b(connect)\s+(to\s+)?(wifi|wi[-\s]?fi)\s+(.+)', re.I), {'name_group': 4}),
            ],

            'wifi_disconnect': [
                (re.compile(r'\b(disconnect)\s+(wifi|wi[-\s]?fi)\b', re.I), {}),
            ],

            'wifi_toggle': [
                (re.compile(r'\b(turn|set)\s+(wifi|wi[-\s]?fi)\s+(on|off)\b', re.I), {'direction_group': 3}),
            ],

            'bluetooth_toggle': [
                (re.compile(r'\b(turn|set)\s+bluetooth\s+(on|off)\b', re.I), {'direction_group': 2}),
            ],

            'smart_switch_toggle': [
                (re.compile(r'\b(turn|set)\s+(on|off)\s+(outside\s+lights?|porch\s+lights?|smart\s+switch\s+.+)\b', re.I), {'direction_group': 2, 'target_group': 3}),
                (re.compile(r'\b(outside\s+lights?|porch\s+lights?)\s+(on|off)\b', re.I), {'target_group': 1, 'direction_group': 2}),
            ],

            'network_discover': [
                (re.compile(r'\b(discover|scan|find|list)\s+(network\s+)?devices\b', re.I), {}),
                (re.compile(r'\bwho\s+is\s+on\s+my\s+network\b', re.I), {}),
            ],

            'automation_status': [
                (re.compile(r'\b(automation|schedule|scheduler)\s+status\b', re.I), {}),
            ],

            'ram_acceleration_status': [
                (re.compile(r'\b(zram|ram\s+acceleration|ram\s+mode)\s+(status|state)\b', re.I), {}),
                (re.compile(r'\b(check|show)\s+(zram|ram\s+acceleration)\b', re.I), {}),
            ],

            'ram_acceleration_enable': [
                (re.compile(r'\b(enable|turn\s+on|start)\s+(zram|ram\s+acceleration|ram\s+mode)\b', re.I), {}),
            ],

            'ram_acceleration_disable': [
                (re.compile(r'\b(disable|turn\s+off|stop)\s+(zram|ram\s+acceleration|ram\s+mode)\b', re.I), {}),
            ],

            'workflow_memory_status': [
                (re.compile(r'\b(workflow|memory)\s+(status|retention)\b', re.I), {}),
                (re.compile(r'\bhow\s+much\s+do\s+you\s+remember\b', re.I), {}),
            ],

            'set_workflow_preferences': [
                (re.compile(r'\b(set|save|remember)\s+(my\s+)?(workflow|preferences?)\s+(.+)', re.I), {'query_group': 4}),
                (re.compile(r'\bdo\s+not\s+repeat\s+yourself\b', re.I), {'query_group': 0}),
                (re.compile(r'\buse\s+markdown\s+instructions\b', re.I), {'query_group': 0}),
            ],

            'show_workflow_preferences': [
                (re.compile(r'\b(show|list|check)\s+(my\s+)?(workflow|response)\s+preferences\b', re.I), {}),
            ],

            'admin_authorize': [
                (re.compile(r'\b(admin|administrator)\s+(authorize|unlock)\s+(.+)', re.I), {'query_group': 3}),
                (re.compile(r'\bauthorize\s+admin\s+(.+)', re.I), {'query_group': 1}),
            ],

            'admin_lock': [
                (re.compile(r'\b(admin|administrator)\s+(lock|logout|revoke)\b', re.I), {}),
                (re.compile(r'\block\s+admin\s+session\b', re.I), {}),
            ],

            'self_repair_scan': [
                (re.compile(r'\b(self\s*repair|self\s*amend)\s+(scan|diagnose|check)\b', re.I), {}),
                (re.compile(r'\b(check|scan)\s+(dependencies|environment)\b', re.I), {}),
            ],

            'self_repair_apply': [
                (re.compile(r'\b(self\s*repair|self\s*amend)\s+(run|apply|fix|now)\b', re.I), {}),
                (re.compile(r'\b(fix|repair)\s+(missing\s+)?dependencies\b', re.I), {}),
            ],

            'dependency_alternatives': [
                (re.compile(r'\b(alternative|fallback)\s+(for\s+)?(dependencies|programs|tools)\b', re.I), {}),
                (re.compile(r'\b(find|show)\s+(usable\s+)?alternatives\b', re.I), {}),
            ],

            'learning_curve_status': [
                (re.compile(r'\b(learning\s+curve|learning\s+status|are\s+you\s+learning)\b', re.I), {}),
                (re.compile(r'\bhow\s+well\s+am\s+i\s+doing\s+over\s+time\b', re.I), {}),
            ],

            'performance_peaks_report': [
                (re.compile(r'\b(performance\s+peaks?|peak\s+performance|best\s+performance\s+hours?)\b', re.I), {}),
                (re.compile(r'\bwhen\s+does\s+the\s+system\s+run\s+best\b', re.I), {}),
            ],

            'performance_optimize_advice': [
                (re.compile(r'\b(optimi[sz]e|improve|boost)\s+(my\s+)?performance\b', re.I), {}),
                (re.compile(r'\bhelp\s+me\s+get\s+better\s+performance\b', re.I), {}),
            ],

            'export_workflow_memory': [
                (re.compile(r'\b(export|backup|save)\s+(workflow|memory)\s*(to\s+(.+))?\b', re.I), {'path_group': 4}),
                (re.compile(r'\bexport\s+workflow\s+package\b', re.I), {}),
            ],

            'create_alert': [
                (re.compile(r'\b(add|set|create)\s+alert\s+(.+)', re.I), {'query_group': 2}),
                (re.compile(r'\bremind\s+me\s+to\s+(.+)', re.I), {'query_group': 1}),
            ],

            'create_event': [
                (re.compile(r'\b(add|set|create)\s+event\s+(.+)', re.I), {'query_group': 2}),
            ],

            'list_alerts_events': [
                (re.compile(r'\b(list|show|open|check|what\s+are)\s+(my\s+)?(alerts|events|alerts\s+and\s+events|events\s+and\s+alerts)\b', re.I), {'target_group': 3}),
            ],

            'due_alerts_events': [
                (re.compile(r'\b(list|show|check)\s+(due|upcoming)\s+(alerts|events|alerts\s+and\s+events|events\s+and\s+alerts)\b', re.I), {'target_group': 3}),
            ],

            'crypto_market_status': [
                (re.compile(r'\b(crypto|market)\s+(status|overview|summary)\b', re.I), {}),
                (re.compile(r'\bhow\s+is\s+the\s+crypto\s+market\b', re.I), {}),
            ],

            'crypto_price': [
                (re.compile(r'\b(price|value)\s+of\s+(.+)', re.I), {'query_group': 2}),
                (re.compile(r'\bcrypto\s+price\s+(.+)', re.I), {'query_group': 1}),
            ],

            'crypto_mining_status': [
                (re.compile(r'\b(mining|hashrate|difficulty)\s+(status|overview|report)\b', re.I), {}),
                (re.compile(r'\bcrypto\s+mining\s+(status|report)\b', re.I), {}),
            ],

            'hiveos_status': [
                (re.compile(r'\b(hive\s*os|hiveos)\s+(status|farm|report)\b', re.I), {}),
                (re.compile(r'\bcheck\s+hive\s*os\b', re.I), {}),
            ],

            'crypto_wallet_status': [
                (re.compile(r'\b(wallet|wallets|coinbase|kraken|trust\s*wallet|token\s*pocket)\s+(status|overview|summary)\b', re.I), {}),
                (re.compile(r'\bcrypto\s+wallet\s+(status|overview)\b', re.I), {}),
            ],

            'transaction_control_toggle': [
                (re.compile(r'\b(enable|disable|turn\s+on|turn\s+off)\s+(transaction\s+control|trading\s+control)\b', re.I), {'direction_group': 1}),
                (re.compile(r'\btransaction\s+control\s+(on|off)\b', re.I), {'direction_group': 1}),
            ],

            'transaction_control_status': [
                (re.compile(r'\b(transaction\s+control|trading\s+control)\s+status\b', re.I), {}),
            ],

            'loss_prevention_check': [
                (re.compile(r'\b(loss\s+prevention|stop\s+loss)\s+(check|status|run)\b', re.I), {}),
                (re.compile(r'\bcheck\s+my\s+losses\b', re.I), {}),
            ],

            'open_account_service': [
                (re.compile(r'\b(open|launch|start)\s+(gmail|email|alexa|alexa\s*skills|facebook|instagram|github|discord|dropbox|meshare|me\s*share|smartz|coinbase|kraken|trust\s*wallet)\b', re.I), {'target_group': 2}),
            ],

            'show_lyrics': [
                (re.compile(r'\b(show|open|find)\s+lyrics\s+(for\s+)?(.+)', re.I), {'query_group': 3}),
                (re.compile(r'\blyrics\s+for\s+(.+)', re.I), {'query_group': 1}),
                (re.compile(r'\b(show|open)\s+lyrics\b', re.I), {}),
            ],

            'show_camera_video': [
                (re.compile(r'\b(show|open|bring\s+up|view)\s+(camera|video|camera\s+video)\s*(on\s+(pc|computer))?\b', re.I), {}),
                (re.compile(r'\b(open|show)\s+alexa\s+cameras?\b', re.I), {}),
            ],

            'firetv_connect': [
                (re.compile(r'\b(connect)\s+(fire\s*tv|firetv)\s+(to\s+)?([0-9]{1,3}(?:\.[0-9]{1,3}){3}(?::[0-9]{2,5})?)\b', re.I), {'target_group': 4}),
                (re.compile(r'\b(fire\s*tv|firetv)\s+connect\s+([0-9]{1,3}(?:\.[0-9]{1,3}){3}(?::[0-9]{2,5})?)\b', re.I), {'target_group': 2}),
            ],

            'firetv_remote': [
                (re.compile(r'\b(fire\s*tv|firetv)\s+(home|back|up|down|left|right|select|ok|play\s*pause|menu)\b', re.I), {'target_group': 2}),
                (re.compile(r'\b(send)\s+(home|back|up|down|left|right|select|ok|play\s*pause|menu)\s+(to\s+)?(fire\s*tv|firetv)\b', re.I), {'target_group': 2}),
            ],

            # Application Control
            'launch_app': [
                (re.compile(r'\b(open|launch|start|run)\s+(.+)', re.I), {'target_group': 2}),
                (re.compile(r'\bi need\s+(.+)', re.I), {'target_group': 1}),
                (re.compile(r'\bshow me\s+(.+)', re.I), {'target_group': 1}),
            ],

            'close_app': [
                (re.compile(r'\b(close|quit|exit|kill|terminate|end)\s+(.+)', re.I), {'target_group': 2}),
                (re.compile(r'\bstop\s+(.+)', re.I), {'target_group': 1}),
            ],

            'switch_app': [
                (re.compile(r'\b(switch to|go to|focus|bring up)\s+(.+)', re.I), {'target_group': 2}),
            ],

            'list_apps': [
                (re.compile(r'\b(list|show|what).*?(running|open|active).*?(apps|applications|programs)', re.I), {}),
            ],

            # Screenshot Operations
            'screenshot': [
                (re.compile(
                    r'\b(take|capture|grab|screenshot|screencap)\s+(a\s+)?(screenshot|screen|capture)',
                    re.I), {}),
                (re.compile(r'\bscreenshot\b', re.I), {}),
            ],

            'screenshot_window': [
                (re.compile(r'\bscreenshot\s+(this|the|active)?\s*window', re.I), {}),
                (re.compile(r'\bcapture\s+(this|the|active)?\s*window', re.I), {}),
            ],

            'screenshot_region': [
                (re.compile(r'\bscreenshot\s+(this|an?)?\s*area', re.I), {}),
                (re.compile(r'\bcapture\s+region', re.I), {}),
            ],

            # System Control
            'volume': [
                (re.compile(r'\b(set|change|adjust)?\s*volume\s+(to\s+)?(\d+)\s*%?', re.I), {'value_group': 3}),
                (re.compile(r'\bvolume\s+(up|down)', re.I), {'direction_group': 1}),
            ],

            'mute': [
                (re.compile(r'\b(mute|unmute|silence)', re.I), {}),
            ],

            'brightness': [
                (re.compile(r'\b(set|change|adjust)?\s*brightness\s+(to\s+)?(\d+)\s*%?', re.I), {'value_group': 3}),
                (re.compile(r'\bbrightness\s+(up|down)', re.I), {'direction_group': 1}),
            ],

            'system_info': [
                (re.compile(r'\bhow.?s\s+(the\s+)?(system|computer|pc)', re.I), {}),
                (re.compile(r'\b(system|computer)\s+(status|info|information)', re.I), {}),
                (re.compile(r'\ball systems', re.I), {}),
            ],

            'lock_screen': [
                (re.compile(r'\block\s+(my\s+)?(computer|screen|workstation|pc)', re.I), {}),
            ],

            'shutdown': [
                (re.compile(r'\b(shutdown|shut down|power off|turn off)', re.I), {}),
            ],

            'restart': [
                (re.compile(r'\b(restart|reboot)', re.I), {}),
            ],

            'sleep': [
                (re.compile(r'\b(sleep|hibernate)', re.I), {}),
            ],

            # File Operations
            'open_file': [
                (re.compile(r'\bopen\s+(file|folder|directory)?\s*(.+)', re.I), {'target_group': 2}),
            ],

            'find_files': [
                (re.compile(r'\b(find|search|locate)\s+(all\s+)?(.+?)\s+(files?|in)', re.I), {'query_group': 3}),
                (re.compile(r'\bwhere\s+(is|are)\s+(.+)', re.I), {'query_group': 2}),
            ],

            'dev_task': [
                (re.compile(r'\b(run|execute|start)\s+(tests?|test suite|unit tests|build|lint|format|install dependencies|dependencies|git status|git pull)\b', re.I), {'task_group': 2}),
                (re.compile(r'\b(check)\s+(git status)\b', re.I), {'task_group': 2}),
                (re.compile(r'\b(update)\s+(dependencies)\b', re.I), {'task_group': 2}),
            ],

            'web_search': [
                (re.compile(r'\b(search|look up|find|google)\s+(for\s+)?(.+)', re.I), {'query_group': 3}),
                (re.compile(r'\bwhat is\s+(.+)', re.I), {'query_group': 1}),
            ],

            'analyze_build_log': [
                (re.compile(r'\b(analyze|check|review)\s+(kernel|rom|build)?\s*log\s+(.+)', re.I), {'path_group': 3}),
                (re.compile(r'\bdebug\s+build\s+errors\s+in\s+(.+)', re.I), {'path_group': 1}),
            ],

            'lp_dump': [
                (re.compile(r'\b(lp\s*dump|lpdump)\s+(.+)', re.I), {'path_group': 2}),
            ],

            'lp_unpack': [
                (re.compile(r'\b(lp\s*unpack|lpunpack)\s+(.+?)\s+(to|into)\s+(.+)', re.I), {'path_group': 2, 'output_group': 4}),
            ],

            'inspect_wsl': [
                (re.compile(r'\b(list|show|check)\s+wsl\s+(distros|instances|status)', re.I), {}),
                (re.compile(r'\bwsl\s+status\b', re.I), {}),
            ],

            'inspect_container': [
                (re.compile(r'\b(list|show|check)\s+(docker\s+)?containers?\b', re.I), {}),
                (re.compile(r'\b(container|docker)\s+logs\s+(.+)', re.I), {'target_group': 2}),
            ],

            'wsl_diagnose': [
                (re.compile(r'\brun\s+wsl\s+diagnostics?\s+on\s+(.+)', re.I), {'target_group': 1}),
            ],

            'inspect_toml': [
                (re.compile(r'\b(check|inspect|parse|analyze)\s+toml\s+(.+)', re.I), {'path_group': 2}),
            ],

            'inspect_dot_config': [
                (re.compile(r'\b(check|inspect|parse|analyze)\s+(dot\s*config|\.config|kernel config)\s+(.+)', re.I), {'path_group': 3}),
            ],

            'inspect_go_mod': [
                (re.compile(r'\b(check|inspect|parse|analyze)\s+go\s+mod\s+(.+)', re.I), {'path_group': 3}),
                (re.compile(r'\b(check|inspect|parse|analyze)\s+go\.mod\s+(.+)', re.I), {'path_group': 2}),
            ],

            'inspect_deb': [
                (re.compile(r'\b(check|inspect|analyze)\s+deb\s+(.+)', re.I), {'path_group': 2}),
                (re.compile(r'\b(check|inspect|analyze)\s+debian\s+package\s+(.+)', re.I), {'path_group': 3}),
            ],

            'analyze_kernel_source': [
                (re.compile(r'\b(analyze|inspect|check)\s+kernel\s+source\s+(.+)', re.I), {'path_group': 3}),
                (re.compile(r'\b(mainline|mainlining)\s+kernel\s+check\s+(.+)', re.I), {'path_group': 3}),
            ],

            'inspect_linux_distro': [
                (re.compile(r'\b(check|inspect|analyze)\s+(kali|ubuntu|debian|linux)\s+(distro|environment|setup)\s*(.+)?', re.I), {'target_group': 2}),
                (re.compile(r'\b(check|inspect|analyze)\s+linux\s+on\s+wsl\s+(.+)', re.I), {'target_group': 2}),
            ],

            'analyze_build_environment': [
                (re.compile(r'\b(analyze|inspect|check)\s+build\s+environment\s+(.+)', re.I), {'path_group': 3}),
            ],

            'compose_script': [
                (re.compile(r'\b(compose|generate|create)\s+(bash|powershell|batch)\s+script\s+for\s+(.+)', re.I), {'script_type_group': 2, 'query_group': 3}),
                (re.compile(r'\b(compose|generate|create)\s+script\s+for\s+(.+)', re.I), {'query_group': 2}),
            ],

            'open_remote_settings': [
                (re.compile(r'\b(remote\s+desktop\s+settings|enable\s+remote\s+desktop|go\s+to\s+remote\s+desktop\s+settings)\b', re.I), {}),
            ],

            'open_kde_connect': [
                (re.compile(r'\b(open|launch|start)\s+kde\s+connect\b', re.I), {}),
            ],

            'kde_connect_status': [
                (re.compile(r'\b(kde\s+connect\s+status|list\s+kde\s+devices|show\s+kde\s+devices)\b', re.I), {}),
            ],

            'kde_connect_pair': [
                (re.compile(r'\b(pair)\s+kde\s+connect\s+device\s+(.+)', re.I), {'target_group': 2}),
            ],

            'linux_connect': [
                (re.compile(r'\b(connect|test|check|ping)\s+(to\s+)?linux\b', re.I), {}),
                (re.compile(r'\blinux\s+(connection|status)\b', re.I), {}),
            ],

            'linux_run': [
                (re.compile(r'\b(on\s+linux\s+run|linux\s+run|run\s+on\s+linux)\s+(.+)', re.I), {'query_group': 2}),
                (re.compile(r'\blinux\s+execute\s+(.+)', re.I), {'query_group': 1}),
            ],

            'linux_sync': [
                (re.compile(r'\b(sync|copy|send)\s+(.+?)\s+(to\s+linux|to\s+server)\s+(.+)', re.I), {'path_group': 2, 'output_group': 4}),
            ],

            'linux_profile_help': [
                (re.compile(r'\b(linux\s+profile\s+help|setup\s+linux\s+profile|configure\s+linux\s+profile)\b', re.I), {}),
            ],

            'teach_topic': [
                (re.compile(r'\b(teach|coach me on|help me understand)\s+(.+)', re.I), {'query_group': 2}),
                (re.compile(r'\bexplain\s+(?!((adb|fastboot)\b))(.+)', re.I), {'query_group': 3}),
            ],

            'explain_file': [
                (re.compile(r'\b(explain|review|walk me through)\s+(file\s+)?(.+)', re.I), {'path_group': 3}),
            ],

            'diagnose_uefi': [
                (re.compile(r'\b(run|check|diagnose)\s+(uefi|efi|bootloader|boot)\s+(diagnostics?|status)', re.I), {}),
                (re.compile(r'\b(check|diagnose)\s+(uefi|efi|bootloader)\b', re.I), {}),
            ],

            'diagnose_motorola_eud': [
                (re.compile(r'\b(run|check|diagnose)\s+(motorola\s+)?eud\s+(diagnostics?|status)', re.I), {}),
                (re.compile(r'\b(check|diagnose)\s+(motorola\s+)?eud\b', re.I), {}),
                (re.compile(r'\bmotorola\s+eud\b', re.I), {}),
            ],

            'inspect_firehose': [
                (re.compile(r'\b(check|inspect|analyze)\s+firehose\s+(.+)', re.I), {'path_group': 2}),
            ],

            'inspect_elf': [
                (re.compile(r'\b(check|inspect|analyze)\s+elf\s+(.+)', re.I), {'path_group': 2}),
            ],

            'repo_query': [
                (re.compile(r'\b(find in repo|search repo|lookup in files|look in files)\s+(.+)', re.I), {'query_group': 2}),
            ],

            'create_design_image': [
                (re.compile(r'\b(create|make|generate)\s+(image|poster|graphic)\s+(.+?)\s+(to|as)\s+(.+)', re.I), {'query_group': 3, 'output_group': 5}),
            ],

            'create_boot_animation': [
                (re.compile(r'\b(create|make|generate)\s+(boot\s+animation|bootimage)\s+from\s+(.+?)\s+(to|as)\s+(.+)', re.I), {'path_group': 3, 'output_group': 5}),
            ],

            'adb_command': [
                (re.compile(r'\badb\s+(.+)', re.I), {'query_group': 1}),
            ],

            'fastboot_command': [
                (re.compile(r'\b(fastboot|fast\s*food)\s+(.+)', re.I), {'query_group': 2}),
            ],

            'explain_android_command': [
                (re.compile(r'\b(explain|teach|show\s+syntax\s+for)\s+((adb|fastboot)\s+.+)', re.I), {'query_group': 2}),
            ],

            'phone_pull_data': [
                (re.compile(r'\b(pull|copy|get|extract)\s+(from\s+phone|phone\s+data)\s+(.+?)\s+(to|into)\s+(.+)', re.I), {'path_group': 3, 'output_group': 5}),
                (re.compile(r'\bphone\s+pull\s+(.+?)\s+(to|into)\s+(.+)', re.I), {'path_group': 1, 'output_group': 3}),
            ],

            'phone_info': [
                (re.compile(r'\b(phone|android)\s+(info|status|diagnostics?)\b', re.I), {}),
                (re.compile(r'\bcheck\s+(my\s+)?phone\b', re.I), {}),
            ],

            'create_folder': [
                (re.compile(r'\bcreate\s+(a\s+)?(new\s+)?(folder|directory)\s+(.+)', re.I), {'name_group': 4}),
                (re.compile(r'\bnew\s+folder\s+(.+)', re.I), {'name_group': 1}),
            ],

            'delete_file': [
                (re.compile(r'\bdelete\s+(.+)', re.I), {'target_group': 1}),
                (re.compile(r'\bremove\s+(.+)', re.I), {'target_group': 1}),
            ],

            # Window Management
            'maximize': [
                (re.compile(r'\bmaximize', re.I), {}),
            ],

            'minimize': [
                (re.compile(r'\bminimize', re.I), {}),
            ],

            'split_screen': [
                (re.compile(r'\bsplit\s+screen', re.I), {}),
                (re.compile(r'\bside\s+by\s+side', re.I), {}),
            ],

            # Information Queries
            'time': [
                (re.compile(r'\b(what.?s\s+the\s+time|what time|current time)', re.I), {}),
            ],

            'date': [
                (re.compile(r'\b(what.?s\s+the\s+date|what date|today.?s date)', re.I), {}),
            ],

            'weather': [
                (re.compile(r'\b(what.?s\s+the\s+weather|weather|forecast)', re.I), {}),
            ],

            # General
            'greeting': [
                (re.compile(r'\b(hello|hi|hey|greetings)', re.I), {}),
            ],

            'status': [
                (re.compile(r'\b(status|are you (there|online|working))', re.I), {}),
            ],

            'help': [
                (re.compile(r'\b(help|what can you do|commands|capabilities)', re.I), {}),
            ],

            'thank': [
                (re.compile(r'\b(thank you|thanks|thx)', re.I), {}),
            ],
        }

        return patterns

    def recognize(self, command: str) -> Dict:
        """
        Recognize intent from command
        Returns dict with: intent, confidence, parameters
        """
        command = command.strip()

        if not command:
            return {
                'intent': 'unknown',
                'confidence': 0.0,
                'parameters': {},
                'raw_command': command
            }

        # Try to match against all patterns
        best_match = {
            'intent': 'unknown',
            'confidence': 0.0,
            'parameters': {},
            'raw_command': command
        }

        for intent, patterns in self.intent_patterns.items():
            for pattern, config in patterns:
                match = pattern.search(command)
                if match:
                    confidence = self._calculate_confidence(match, command)

                    if confidence > best_match['confidence']:
                        parameters = self._extract_parameters(match, config, command)
                        best_match = {
                            'intent': intent,
                            'confidence': confidence,
                            'parameters': parameters,
                            'raw_command': command
                        }

        logger.debug(f"Intent recognized: {best_match['intent']} (confidence: {best_match['confidence']:.2f})")
        return best_match

    def _calculate_confidence(self, match: re.Match, command: str) -> float:
        """Calculate confidence score for a match"""
        # Base confidence on how much of the command was matched
        matched_length = len(match.group(0))
        command_length = len(command)

        if command_length == 0:
            return 0.0

        coverage = matched_length / command_length

        # Higher confidence if match is at the start
        if match.start() == 0:
            coverage *= 1.2

        # Cap at 1.0
        return min(coverage, 1.0)

    def _extract_parameters(self, match: re.Match, config: Dict, command: str) -> Dict:
        """Extract parameters from matched pattern"""
        parameters = {}

        def _get_group(group_index):
            try:
                value = match.group(group_index)
            except IndexError:
                return None
            return value.strip() if isinstance(value, str) else None

        # Extract target (app name, file, etc.)
        if 'target_group' in config:
            target = _get_group(config['target_group'])
            if target:
                parameters['target'] = self._clean_target(target)

        # Extract value (for volume, brightness, etc.)
        if 'value_group' in config:
            try:
                value = int(match.group(config['value_group']))
                parameters['value'] = value
            except (ValueError, IndexError):
                pass

        # Extract direction (up/down)
        if 'direction_group' in config:
            direction = _get_group(config['direction_group'])
            if direction:
                parameters['direction'] = direction.lower()

        # Extract query string
        if 'query_group' in config:
            query = _get_group(config['query_group'])
            if query:
                parameters['query'] = query

        # Extract name
        if 'name_group' in config:
            name = _get_group(config['name_group'])
            if name:
                parameters['name'] = name

        # Extract development task phrase
        if 'task_group' in config:
            task = _get_group(config['task_group'])
            if task:
                parameters['task'] = task.lower()

        if 'path_group' in config:
            path = _get_group(config['path_group'])
            if path:
                parameters['path'] = path.strip('"\'')

        if 'output_group' in config:
            out = _get_group(config['output_group'])
            if out:
                parameters['output'] = out.strip('"\'')

        if 'script_type_group' in config:
            script_type = _get_group(config['script_type_group'])
            if script_type:
                parameters['script_type'] = script_type.lower()

        return parameters

    def _clean_target(self, target: str) -> str:
        """Clean up target string"""
        # Remove articles
        target = re.sub(r'\b(a|an|the)\b', '', target, flags=re.I)

        # Remove trailing words like "application", "program"
        target = re.sub(r'\s+(application|program|app)$', '', target, flags=re.I)

        # Clean whitespace
        target = ' '.join(target.split())

        return target.strip()

    def get_possible_intents(self) -> List[str]:
        """Get list of all possible intents"""
        return list(self.intent_patterns.keys())

