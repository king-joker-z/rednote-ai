"""配置管理"""

import os
from pathlib import Path
from typing import Any, Optional

import yaml


def get_config_path() -> Path:
    """获取配置文件路径"""
    # 优先级: 环境变量 > 当前目录 > 默认路径
    if env_path := os.getenv("REDNOTE_CONFIG"):
        return Path(env_path)
    
    cwd_config = Path.cwd() / "config" / "config.yaml"
    if cwd_config.exists():
        return cwd_config
    
    return Path.home() / ".rednote-ai" / "config.yaml"


def load_config(config_path: Path = None) -> dict:
    """加载配置文件"""
    path = config_path or get_config_path()
    
    if not path.exists():
        return {}
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 替换环境变量 ${VAR_NAME}
    import re
    def replace_env(match):
        var_name = match.group(1)
        return os.getenv(var_name, "")
    
    content = re.sub(r'\$\{(\w+)\}', replace_env, content)
    
    return yaml.safe_load(content) or {}


def get_llm_config(config: dict, purpose: str = "writer") -> dict:
    """获取 LLM 配置
    
    Args:
        config: 完整配置
        purpose: 用途 (writer / analyze)
    """
    llm_config = config.get("llm", {}).get(purpose, {})
    
    # 如果配置为空，使用环境变量默认值
    if not llm_config:
        return {
            "provider": os.getenv("LLM_PROVIDER", "anthropic"),
            "model": os.getenv("LLM_MODEL"),
            "api_key": os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"),
            "base_url": os.getenv("LLM_BASE_URL"),
        }
    
    return llm_config


class Config:
    """配置管理类"""
    
    def __init__(self, config_path: Path = None):
        self._config = load_config(config_path)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套 key"""
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    @property
    def llm_writer(self) -> dict:
        """文案生成 LLM 配置"""
        return get_llm_config(self._config, "writer")
    
    @property
    def llm_analyze(self) -> dict:
        """分析 LLM 配置"""
        return get_llm_config(self._config, "analyze")
    
    @property
    def sources(self) -> dict:
        """信息源配置"""
        return self._config.get("sources", {})
    
    @property
    def generate(self) -> dict:
        """生成配置"""
        return self._config.get("generate", {})
