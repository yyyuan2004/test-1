"""Slang / emoji / meme dictionary for cultural context mapping.

Maps formal expressions to colloquial ones, and provides
emoji semantic interpretation (e.g., [微笑] → sarcastic/dismissive in certain contexts).

Supports loading custom dictionaries per persona or group.
"""

from __future__ import annotations

import json
from pathlib import Path


# Built-in emoji semantic map (Chinese social media conventions)
_EMOJI_SEMANTICS: dict[str, str] = {
    "[微笑]": "阴阳怪气/无语的语气",
    "[呲牙]": "尴尬/敷衍的笑",
    "[捂脸]": "无奈/哭笑不得",
    "[破涕为笑]": "自嘲",
    "[吃瓜]": "看热闹/围观",
    "[裂开]": "崩溃/emo",
    "[叹气]": "无语/失望",
    "[翻白眼]": "不屑/鄙视",
    "😅": "尴尬",
    "🤡": "自嘲/小丑竟是我自己",
    "💀": "笑死/绝了",
    "😭": "夸张地笑或真的难过",
    "🥺": "撒娇/求求了",
    "😊": "礼貌性微笑（可能是敷衍）",
    "👀": "感兴趣/吃瓜",
    "🐶": "卖萌/装可怜",
    "🤪": "发疯/抽象",
}

# Internet slang dictionary (abbreviations → meaning)
_SLANG_MAP: dict[str, str] = {
    "yyds": "永远的神",
    "绝绝子": "非常绝/极致",
    "芭比Q了": "完蛋了",
    "栓Q": "谢谢/无语感谢",
    "CPU": "被PUA了",
    "emo": "情绪低落",
    "破防": "情绪崩溃",
    "摆烂": "放弃挣扎",
    "卷": "内卷/过度竞争",
    "润": "离开/出走",
    "6": "厉害",
    "xswl": "笑死我了",
    "dbq": "对不起",
    "awsl": "啊我死了（太可爱了）",
    "u1s1": "有一说一",
    "srds": "虽然但是",
    "nbcs": "nobody cares",
    "yygq": "阴阳怪气",
    "byd": "不要的/别样的",
}

# Formal → casual replacements for more natural output
_FORMAL_TO_CASUAL: dict[str, str] = {
    "因此": "所以",
    "然而": "但是",
    "此外": "还有",
    "尽管如此": "不过",
    "值得注意的是": "话说",
    "需要指出的是": "其实",
    "毫无疑问": "肯定",
    "事实上": "其实",
    "总而言之": "反正",
    "换言之": "就是说",
    "由此可见": "所以",
    "与此同时": "而且",
}


class SlangDict:
    """Manages slang/emoji dictionaries with support for custom extensions."""

    def __init__(self, custom_dict_path: Path | None = None) -> None:
        self._emoji_map = dict(_EMOJI_SEMANTICS)
        self._slang_map = dict(_SLANG_MAP)
        self._formal_to_casual = dict(_FORMAL_TO_CASUAL)
        self._custom: dict[str, str] = {}

        if custom_dict_path and custom_dict_path.exists():
            self._load_custom(custom_dict_path)

    def _load_custom(self, path: Path) -> None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self._custom = data.get("replacements", {})
            self._emoji_map.update(data.get("emojis", {}))
            self._slang_map.update(data.get("slang", {}))
        except Exception:
            pass

    def apply(self, text: str) -> str:
        """Apply formal-to-casual replacements to text."""
        for formal, casual in self._formal_to_casual.items():
            text = text.replace(formal, casual)
        for old, new in self._custom.items():
            text = text.replace(old, new)
        return text

    def explain_emoji(self, emoji: str) -> str:
        """Get the cultural meaning of an emoji."""
        return self._emoji_map.get(emoji, "")

    def explain_slang(self, term: str) -> str:
        """Get the meaning of a slang term."""
        return self._slang_map.get(term.lower(), "")

    def get_all_emoji_context(self) -> str:
        """Return a prompt-friendly emoji context string."""
        lines = []
        for emoji, meaning in self._emoji_map.items():
            lines.append(f"  {emoji} = {meaning}")
        return "\n".join(lines)

    def save_custom(self, path: Path) -> None:
        data = {
            "replacements": self._custom,
            "emojis": {k: v for k, v in self._emoji_map.items() if k not in _EMOJI_SEMANTICS},
            "slang": {k: v for k, v in self._slang_map.items() if k not in _SLANG_MAP},
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
