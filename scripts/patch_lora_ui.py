#
# extensions/sd-webui-lora-block-weight-ui/scripts/patch_lora_ui.py
#
# This script monkey-patches the LoraUserMetadataEditor to add an "Additional weight" field.
# It allows users to save/load LBW (LoRA Block Weight) presets directly in the metadata editor.
#

import gradio as gr
import re
import html
import random
import datetime

# --- Attempt to import the target editor class ---
try:
    from ui_edit_user_metadata import LoraUserMetadataEditor, build_tags, re_comma
    if not hasattr(LoraUserMetadataEditor, 'create_editor'):
         raise ImportError("LoraUserMetadataEditor seems to be an unexpected class.")

except ImportError as e:
    # If import fails, skip patching (e.g., incompatible WebUI version)
    print(f"[sd-webui-lora-block-weight-ui] Failed to import 'ui_edit_user_metadata'. {e}")
    LoraUserMetadataEditor = None

# --- Apply patch only if the editor class is available ---
if LoraUserMetadataEditor:
    
    # Keep reference to the original __init__
    original_init = LoraUserMetadataEditor.__init__

    # --- Patched __init__: Initialize custom fields ---
    def patched_init(self, ui, tabname, page):
        original_init(self, ui, tabname, page) 
        self.edit_additional_weight = None

    # --- Patched save_lora_user_metadata: Save 'additional weight' to metadata ---
    def patched_save_lora_user_metadata(self, name, desc, sd_version, activation_text, preferred_weight, additional_weight, negative_text, notes):
        user_metadata = self.get_user_metadata(name)
        user_metadata["description"] = desc
        user_metadata["sd version"] = sd_version
        user_metadata["activation text"] = activation_text
        user_metadata["preferred weight"] = preferred_weight
        user_metadata["additional weight"] = additional_weight  # Custom field
        user_metadata["negative text"] = negative_text
        user_metadata["notes"] = notes
        self.write_user_metadata(name, user_metadata)

    # --- Patched put_values_into_components: Load 'additional weight' into UI ---
    def patched_put_values_into_components(self, name):
        user_metadata = self.get_user_metadata(name)
        values = super(LoraUserMetadataEditor, self).put_values_into_components(name) 

        item = self.page.items.get(name, {})
        metadata = item.get("metadata") or {}

        tags = build_tags(metadata) 
        gradio_tags = [(tag, str(count)) for tag, count in tags[0:24]]

        return [
            *values[0:5],
            item.get("sd_version", "Unknown"),
            gr.HighlightedText.update(value=gradio_tags, visible=True if tags else False),
            user_metadata.get('activation text', ''),
            float(user_metadata.get('preferred weight', 0.0)),
            user_metadata.get('additional weight', ''), # Load custom field
            user_metadata.get('negative text', ''),
            gr.update(visible=True if tags else False),
            gr.update(value=self.generate_random_prompt_from_tags(tags), visible=True if tags else False),
        ]

    # --- Patched create_editor: Override UI layout to include new inputs ---
    def patched_create_editor_full_override(self):
        self.create_default_editor_elems()

        self.taginfo = gr.HighlightedText(label="Training dataset tags")
        self.edit_activation_text = gr.Text(label='Activation text', info="Will be added to prompt along with Lora")
        self.slider_preferred_weight = gr.Slider(label='Preferred weight', info="Set to 0 to disable", minimum=0.0, maximum=2.0, step=0.01)
        
        # Add Input for LoRA Block Weight
        self.edit_additional_weight = gr.Textbox(label="Additional weight", info="for LoRA Block Weight")
        
        self.edit_negative_text = gr.Text(label='Negative prompt', info="Will be added to negative prompts")
        with gr.Row() as row_random_prompt:
            with gr.Column(scale=8):
                random_prompt = gr.Textbox(label='Random prompt', lines=4, max_lines=4, interactive=False)
            with gr.Column(scale=1, min_width=120):
                generate_random_prompt = gr.Button('Generate', size="lg", scale=1)

        self.edit_notes = gr.TextArea(label='Notes', lines=4)

        generate_random_prompt.click(fn=self.generate_random_prompt, inputs=[self.edit_name_input], outputs=[random_prompt], show_progress=False)

        def select_tag(activation_text, evt: gr.SelectData):
            tag = evt.value[0]
            words = re.split(re_comma, activation_text)
            if tag in words:
                words = [x for x in words if x != tag and x.strip()]
                return ", ".join(words)
            return activation_text + ", " + tag if activation_text else tag

        self.taginfo.select(fn=select_tag, inputs=[self.edit_activation_text], outputs=[self.edit_activation_text], show_progress=False)
        self.create_default_buttons()

        viewed_components = [
            self.edit_name, self.edit_description, self.html_filedata,
            self.html_preview, self.edit_notes, self.select_sd_version,
            self.taginfo, self.edit_activation_text, self.slider_preferred_weight,
            self.edit_additional_weight, # Include in view
            self.edit_negative_text, row_random_prompt, random_prompt,
        ]

        self.button_edit\
            .click(fn=self.put_values_into_components, inputs=[self.edit_name_input], outputs=viewed_components)\
            .then(fn=lambda: gr.update(visible=True), inputs=[], outputs=[self.box])

        edited_components = [
            self.edit_description, self.select_sd_version, self.edit_activation_text,
            self.slider_preferred_weight,
            self.edit_additional_weight, # Include in save list
            self.edit_negative_text, self.edit_notes,
        ]

        self.setup_save_handler(self.button_save, self.save_lora_user_metadata, edited_components)
    
    # --- Apply patches to the class ---
    LoraUserMetadataEditor.__init__ = patched_init
    LoraUserMetadataEditor.save_lora_user_metadata = patched_save_lora_user_metadata
    LoraUserMetadataEditor.put_values_into_components = patched_put_values_into_components
    LoraUserMetadataEditor.create_editor = patched_create_editor_full_override
    
    print("[sd-webui-lora-block-weight-ui] Patch applied successfully to UI editor.")
