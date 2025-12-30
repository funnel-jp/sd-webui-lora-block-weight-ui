#
# extensions/sd-webui-lora-block-weight-ui/scripts/patch_lora_card.py
#
# This script monkey-patches 'ExtraNetworksPageLora.create_item' to modify the generated prompt.
# It appends the ":lbw=WEIGHT" syntax if 'additional_weight' is defined in the user metadata.
# Compatible with both A1111 WebUI and WebUI Forge.
#

import os
from modules import shared, sd_models
from modules.ui_extra_networks import quote_js

# --- 1. Import 'networks' module (Compatibility for A1111 & Forge) ---
networks = None
network = None

try:
    # Try A1111 standard import
    import network
    import networks
except ImportError:
    try:
        # Try Forge import (modules.sd_lora)
        from modules import sd_lora as networks
        network = networks 
    except ImportError as e:
        print(f"[sd-webui-lora-block-weight-ui] Failed to load networks module: {e}")

# --- 2. Import target UI class ---
ui_extra_networks_lora = None
try:
    # Standard location
    import ui_extra_networks_lora
    if not hasattr(ui_extra_networks_lora, 'ExtraNetworksPageLora'):
         raise ImportError("ExtraNetworksPageLora class not found.")
except ImportError:
    try:
        # Forge builtin location
        from extensions_builtin.sd_forge_lora import ui_extra_networks_lora
    except ImportError:
         print("[sd-webui-lora-block-weight-ui] Failed to find ui_extra_networks_lora module.")

# --- 3. Apply Patch ---
if ui_extra_networks_lora and networks:
    try:
        TargetClass = ui_extra_networks_lora.ExtraNetworksPageLora

        def patched_create_item(self, name, index=None, enable_filter=True):
            # Resolve LoRA object from available networks (Supports both A1111 and Forge structures)
            if hasattr(networks, 'available_networks'):
                lora_on_disk = networks.available_networks.get(name)
            elif hasattr(networks, 'available_loras'):
                lora_on_disk = networks.available_loras.get(name)
            else:
                return 

            if lora_on_disk is None:
                return

            path, ext = os.path.splitext(lora_on_disk.filename)

            # Get alias (Handling object differences)
            if hasattr(lora_on_disk, 'get_alias'):
                alias = lora_on_disk.get_alias()
            else:
                alias = name 

            search_terms = [self.search_terms_from_path(lora_on_disk.filename)]
            if lora_on_disk.hash:
                search_terms.append(lora_on_disk.hash)
            
            metadata = getattr(lora_on_disk, 'metadata', {})
            sd_version_obj = lora_on_disk.sd_version

            # Construct the item dictionary
            item = {
                "name": name,
                "filename": lora_on_disk.filename,
                "shorthash": lora_on_disk.shorthash,
                "preview": self.find_preview(path) or self.find_embedded_preview(path, name, metadata),
                "description": self.find_description(path),
                "search_terms": search_terms,
                "local_preview": f"{path}.{shared.opts.samples_format}",
                "metadata": metadata,
                "sort_keys": {'default': index, **self.get_sort_keys(lora_on_disk.filename)},
                # Temporary string conversion, will be finalized later
                "sd_version": sd_version_obj.name if hasattr(sd_version_obj, 'name') else str(sd_version_obj),
            }

            self.read_user_metadata(item)
            activation_text = item["user_metadata"].get("activation text")
            preferred_weight = item["user_metadata"].get("preferred weight", 0.0)
            additional_weight = item["user_metadata"].get("additional weight")

            # --- Generate Prompt with LBW Syntax ---
            default_multiplier = getattr(shared.opts, "extra_networks_default_multiplier", 1.0)
            
            # Base prompt: <lora:ALIAS:MULTIPLIER
            prompt = quote_js(f"<lora:{alias}:") + " + " + (str(preferred_weight) if preferred_weight else str(default_multiplier))

            # Append LBW argument: :lbw=WEIGHT
            if additional_weight:
                prompt += " + " + quote_js(f":lbw={additional_weight}")

            # Close tag: >
            item["prompt"] = prompt + " + " + quote_js(">")

            if activation_text:
                item["prompt"] += " + " + quote_js(" " + activation_text)

            negative_prompt = item["user_metadata"].get("negative text")
            item["negative_prompt"] = quote_js("")
            if negative_prompt:
                item["negative_prompt"] = quote_js('(' + negative_prompt + ':1)')

            # --- Finalize SD Version for Filtering ---
            user_sd_version = item["user_metadata"].get("sd version")
            final_sd_version = sd_version_obj

            if network and hasattr(network, 'SdVersion') and user_sd_version in network.SdVersion.__members__:
                final_sd_version = network.SdVersion[user_sd_version]
                item["sd_version"] = final_sd_version

            # Add 'sd_version_str' for Forge's client-side (JS) filtering
            item["sd_version_str"] = str(final_sd_version)
            
            return item

        # Assign the patched method
        TargetClass.create_item = patched_create_item
        print("[sd-webui-lora-block-weight-ui] Patch applied successfully to ExtraNetworksPageLora.")

    except Exception as e:
        import traceback
        print(f"[sd-webui-lora-block-weight-ui] Failed to apply patch: {e}")
        traceback.print_exc()
else:
    print("[sd-webui-lora-block-weight-ui] Patch skipped. Required modules not found.")
