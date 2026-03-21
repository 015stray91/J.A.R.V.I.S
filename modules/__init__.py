"""
Modules package for Jarvis X
Desktop control modules
"""

from .application_manager import ApplicationManager
from .screenshot_manager import ScreenshotManager
from .system_controller import SystemController
from .file_manager import FileManager
from .window_manager import WindowManager
from .development_manager import DevelopmentManager
from .research_manager import ResearchManager
from .kernel_rom_manager import KernelRomManager
from .rom_ops_manager import RomOpsManager
from .source_analyzer import SourceAnalyzer
from .build_env_manager import BuildEnvManager
from .remote_access_manager import RemoteAccessManager
from .tutor_manager import TutorManager
from .uefi_manager import UefiManager
from .motorola_manager import MotorolaManager
from .firehose_manager import FirehoseManager
from .repo_intel_manager import RepoIntelManager
from .image_creator_manager import ImageCreatorManager
from .android_tools_manager import AndroidToolsManager
from .crypto_manager import CryptoManager
from .integration_manager import IntegrationManager
from .smart_home_manager import SmartHomeManager
from .network_manager import NetworkManager
from .alerts_manager import AlertsManager
from .workflow_memory_manager import WorkflowMemoryManager
from .automation_scheduler import AutomationScheduler

__all__ = [
    'ApplicationManager',
    'ScreenshotManager',
    'SystemController',
    'FileManager',
    'WindowManager',
    'DevelopmentManager',
    'ResearchManager',
    'KernelRomManager',
    'RomOpsManager',
    'SourceAnalyzer',
    'BuildEnvManager',
    'RemoteAccessManager',
    'TutorManager',
    'UefiManager',
    'MotorolaManager',
    'FirehoseManager',
    'RepoIntelManager',
    'ImageCreatorManager',
    'AndroidToolsManager',
    'CryptoManager',
    'IntegrationManager',
    'SmartHomeManager',
    'NetworkManager',
    'AlertsManager',
    'WorkflowMemoryManager',
    'AutomationScheduler'
]

