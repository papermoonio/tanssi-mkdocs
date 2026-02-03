import io
from pathlib import Path

import yaml
import json
import re
from babel.messages.catalog import Catalog
from babel.messages.pofile import read_po, write_po
from babel.messages.mofile import write_mo
from babel.support import Translations
from mkdocs.plugins import event_priority


def _flatten(prefix, value, dest):
    if isinstance(value, dict):
        for k, v in value.items():
            key = f"{prefix}.{k}" if prefix else k
            _flatten(key, v, dest)
    else:
        dest[prefix] = value


def _load_yaml_translations(locale_dir):
    translations = {}
    if not locale_dir.exists():
        return translations
    for path in locale_dir.glob("*.yml"):
        data = yaml.safe_load(path.read_text()) or {}
        flat = {}
        _flatten("", data, flat)
        translations[path.stem] = flat
    return translations


def _load_gettext_translations(i18n_dir):
    translations = {}
    if not i18n_dir.exists():
        return translations
    for lang_dir in i18n_dir.iterdir():
        if not lang_dir.is_dir():
            continue
        lc_dir = lang_dir / "LC_MESSAGES"
        if not lc_dir.exists():
            continue
        po_path = lc_dir / "messages.po"
        mo_path = lc_dir / "messages.mo"
        translator = None
        if po_path.exists():
            with po_path.open("r", encoding="utf-8") as po_file:
                catalog = read_po(po_file)
            buffer = io.BytesIO()
            write_mo(buffer, catalog)
            buffer.seek(0)
            translator = Translations(fp=buffer)
        elif mo_path.exists():
            with mo_path.open("rb") as mo_file:
                translator = Translations(mo_file)
        if translator is not None:
            translations[lang_dir.name] = translator
    return translations


def _build_translator(config):
    docs_dir = Path(config.get("docs_dir", "docs"))
    yaml_translations = _load_yaml_translations(docs_dir / "locale")
    gettext_translations = _load_gettext_translations(docs_dir / "i18n")
    default_lang = config.get("theme", {}).get("language", "en")

    def translate(key, lang=None):
        current_lang = lang or default_lang
        translator = gettext_translations.get(current_lang)
        if translator:
            value = translator.gettext(key)
            if value and value != key:
                return value
        yaml_lang = yaml_translations.get(current_lang, {})
        if key in yaml_lang:
            return yaml_lang[key]
        fallback_translator = gettext_translations.get(default_lang)
        if fallback_translator:
            value = fallback_translator.gettext(key)
            if value and value != key:
                return value
        return yaml_translations.get(default_lang, {}).get(key, key)

    return translate


def _has_custom_translation(yaml_translations, gettext_translations, key, lang, default_lang):
    if key in yaml_translations.get(lang, {}):
        return True
    if key in yaml_translations.get(default_lang, {}):
        return True
    translator = gettext_translations.get(lang)
    if translator:
        value = translator.gettext(key)
        if value and value != key:
            return True
    fallback_translator = gettext_translations.get(default_lang)
    if fallback_translator:
        value = fallback_translator.gettext(key)
        if value and value != key:
            return True
    return False


def _sync_theme_translations(config):
    docs_dir = Path(config.get("docs_dir", "docs"))
    yaml_translations = _load_yaml_translations(docs_dir / "locale")
    if not yaml_translations:
        return

    theme = config.get("theme", {})
    custom_dir = getattr(theme, "custom_dir", None)
    if not custom_dir and hasattr(theme, "get"):
        custom_dir = theme.get("custom_dir")
    if not custom_dir:
        return

    base_dir = Path(__file__).resolve().parent
    custom_path = Path(custom_dir)
    if not custom_path.is_absolute():
        custom_path = base_dir / custom_path

    translations_dir = custom_path / ".translations"
    translations_dir.mkdir(parents=True, exist_ok=True)

    project_name = config.get("site_name") or Path(__file__).resolve().parent.name or "Docs"
    for locale, data in yaml_translations.items():
        target = translations_dir / f"{locale}.json"
        target.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _write_po_translations(docs_dir, locale, data, project_name)


def _get_catalog_metadata(catalog):
    metadata = getattr(catalog, "metadata", None)
    if metadata is not None:
        return dict(metadata)
    headers = getattr(catalog, "mime_headers", None)
    if headers is None:
        return {}
    return {key: value for key, value in headers}


def _set_catalog_metadata(catalog, metadata):
    if hasattr(catalog, "metadata"):
        catalog.metadata.update(metadata)
        return
    headers = list(getattr(catalog, "mime_headers", []) or [])
    if not headers:
        catalog.mime_headers = list(metadata.items())
        return
    index = {key: idx for idx, (key, _value) in enumerate(headers)}
    for key, value in metadata.items():
        if key in index:
            headers[index[key]] = (key, value)
        else:
            headers.append((key, value))
    catalog.mime_headers = headers


def _write_po_translations(docs_dir, locale, data, project_name):
    i18n_dir = docs_dir / "i18n" / locale / "LC_MESSAGES"
    i18n_dir.mkdir(parents=True, exist_ok=True)
    po_path = i18n_dir / "messages.po"

    existing_metadata = {}
    if po_path.exists():
        with po_path.open("r", encoding="utf-8") as po_file:
            existing_catalog = read_po(po_file)
        existing_metadata = _get_catalog_metadata(existing_catalog)

    catalog = Catalog(
        locale=locale,
        project=existing_metadata.get("Project-Id-Version", project_name),
    )
    metadata = dict(existing_metadata)
    metadata.setdefault("Project-Id-Version", project_name)
    metadata.setdefault("POT-Creation-Date", "2025-01-01 00:00+0000")
    metadata.setdefault("Language", locale)
    metadata.setdefault("Content-Type", "text/plain; charset=UTF-8")
    metadata.setdefault("Content-Transfer-Encoding", "8bit")
    _set_catalog_metadata(catalog, metadata)

    for key in sorted(data):
        catalog.add(key, data[key] if data[key] is not None else "")

    with po_path.open("wb") as po_file:
        write_po(po_file, catalog, width=0)


def on_config(config):
    _sync_theme_translations(config)
    return config


def on_env(env, config, files):
    """
    Expose a translation helper that supports custom keys not covered by Material's built-in language packs.
    """
    translator = _build_translator(config)
    env.globals["trans"] = translator
    env.filters["trans"] = translator
    return env


def on_post_page(output, page, config):
    """
    Render simple trans() placeholders left in snippets.
    """
    if not output or not page:
        return output

    # Only do work when placeholders exist.
    if "{{" not in output:
        return output

    i18n = config.plugins.get("i18n")
    default_lang = config.get("theme", {}).get("language", "en")
    if i18n:
        default_lang = next(
            (lang.locale for lang in i18n.config.languages if getattr(lang, "default", False)),
            default_lang,
        )

    page_locale = getattr(getattr(page, "file", None), "locale", None) or default_lang
    translator = _build_translator(config)

    def replace_translation(match):
        key = match.group(1).strip()
        return translator(key, lang=page_locale)

    # match {{ t("key") }} or {{ trans("key") }} including cases where quotes are escaped
    output = re.sub(
        r"{{\s*(?:trans|t)\(\s*\\?['\"]([^'\"]+)\\?['\"]\s*\)\s*}}",
        replace_translation,
        output,
    )

    return output


@event_priority(-1000)
def on_post_build(config):
    """
    404 post-processing disabled for baseline testing.

    Previous custom 404 generation logic was moved to `tanssi-mkdocs/tmp/404-disabled/`
    so it can be re-enabled later if needed.
    """
    return
