#
# extensions/sd-webui-lora-block-weight-ui/scripts/patch_lora_card.py
#
# このスクリプトは Lora のモデルカードが生成するプロンプト文字列を変更します。
# scripts/ フォルダの即時実行タイミングでパッチを適用します。
#

# --- 改造版 'create_item' メソッドが必要とするモジュール ---
import os
try:
    # Lora 組み込み拡張機能のモジュール
    import network
    import networks
except ImportError as e:
    print(f"[sd-webui-lora-block-weight-ui] 'network' または 'networks' のインポートに失敗。 {e}")
    network = None
    networks = None

from modules import shared
from modules.ui_extra_networks import quote_js

# --- パッチを適用する対象のモジュール ---
try:
    import ui_extra_networks_lora
    if not hasattr(ui_extra_networks_lora, 'ExtraNetworksPageLora'):
         raise ImportError("ExtraNetworksPageLora class not found in module.")

except ImportError as e:
    print(f"[sd-webui-lora-block-weight-ui] パッチ対象 'ui_extra_networks_lora' のインポートに失敗。 {e}")
    ui_extra_networks_lora = None

# --- すべてのモジュールが正常にインポートできた場合のみパッチを適用 ---
if ui_extra_networks_lora and network and networks:
    try:
        # パッチを適用するクラスを取得
        TargetClass = ui_extra_networks_lora.ExtraNetworksPageLora

        # --- 4. 改造版 create_item (完全上書き) ---
        # ユーザー提供のコードに基づき、create_item メソッドを丸ごと置き換える
        def patched_create_item(self, name, index=None, enable_filter=True):
            lora_on_disk = networks.available_networks.get(name)
            if lora_on_disk is None:
                return

            path, ext = os.path.splitext(lora_on_disk.filename)

            alias = lora_on_disk.get_alias()

            search_terms = [self.search_terms_from_path(lora_on_disk.filename)]
            if lora_on_disk.hash:
                search_terms.append(lora_on_disk.hash)
            item = {
                "name": name,
                "filename": lora_on_disk.filename,
                "shorthash": lora_on_disk.shorthash,
                "preview": self.find_preview(path) or self.find_embedded_preview(path, name, lora_on_disk.metadata),
                "description": self.find_description(path),
                "search_terms": search_terms,
                "local_preview": f"{path}.{shared.opts.samples_format}",
                "metadata": lora_on_disk.metadata,
                "sort_keys": {'default': index, **self.get_sort_keys(lora_on_disk.filename)},
                "sd_version": lora_on_disk.sd_version.name,
            }

            self.read_user_metadata(item)
            activation_text = item["user_metadata"].get("activation text")
            preferred_weight = item["user_metadata"].get("preferred weight", 0.0)

            # --- ▼ ここからが改造部分 ▼ ---
            additional_weight = item["user_metadata"].get("additional weight")

            prompt = quote_js(f"<lora:{alias}:") + " + " + (str(preferred_weight) if preferred_weight else "opts.extra_networks_default_multiplier")

            if additional_weight:
                prompt += " + " + quote_js(f":lbw={additional_weight}")

            item["prompt"] = prompt + " + " + quote_js(">")
            # --- ▲ ここまでが改造部分 ▲ ---

            if activation_text:
                item["prompt"] += " + " + quote_js(" " + activation_text)

            negative_prompt = item["user_metadata"].get("negative text")
            item["negative_prompt"] = quote_js("")
            if negative_prompt:
                item["negative_prompt"] = quote_js('(' + negative_prompt + ':1)')

            sd_version = item["user_metadata"].get("sd version")
            if sd_version in network.SdVersion.__members__:
                item["sd_version"] = sd_version
                sd_version = network.SdVersion[sd_version]
            else:
                sd_version = lora_on_disk.sd_version

            if shared.opts.lora_show_all or not enable_filter or not shared.sd_model:
                pass
            elif sd_version == network.SdVersion.Unknown:
                model_version = network.SdVersion.SDXL if shared.sd_model.is_sdxl else network.SdVersion.SD2 if shared.sd_model.is_sd2 else network.SdVersion.SD1
                if model_version.name in shared.opts.lora_hide_unknown_for_versions:
                    return None
            elif shared.sd_model.is_sdxl and sd_version != network.SdVersion.SDXL:
                return None
            elif shared.sd_model.is_sd2 and sd_version != network.SdVersion.SD2:
                return None
            elif shared.sd_model.is_sd1 and sd_version != network.SdVersion.SD1:
                return None

            return item

        # --- パッチをクラスに適用 ---
        TargetClass.create_item = patched_create_item
        print("[sd-webui-lora-block-weight-ui] Patch applied successfully to ExtraNetworksPageLora.create_item.")

    except Exception as e:
        print(f"[sd-webui-lora-block-weight-ui] Failed to apply patch to ExtraNetworksPageLora.create_item: {e}")
