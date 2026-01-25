import modules.scripts as scripts
import gradio as gr

class XYZPlotLBWHelper(scripts.Script):
    def title(self):
        return "XYZ Plot LBW Helper"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with gr.Accordion("XYZ Plot LBW Helper", open=False):
            with gr.Group():
                with gr.Row():
                    # Base Weights: 初期値をすべて1に設定 (SDXL想定で20個)
                    default_base = ",".join(["1"] * 20)
                    base_weights = gr.Textbox(label="Base Weights", 
                                              value=default_base, 
                                              info="Default weights to be replaced. (SDXL:20, SD1.5:26)")
                    
                with gr.Row():
                    # Test Values: 初期値を 0, 1 に設定
                    test_values = gr.Textbox(label="Test Values", value="0, 1", info="Values to cycle through.")

                with gr.Row():
                    # ブロック選択肢
                    block_choices = ["BASE", "IN00", "IN01", "IN02", "IN03", "IN04", "IN05", "IN06", "IN07", "IN08", 
                                     "IN09", "IN10", "IN11", "M00", 
                                     "OUT00", "OUT01", "OUT02", "OUT03", "OUT04", "OUT05", "OUT06", "OUT07", "OUT08", 
                                     "OUT09", "OUT10", "OUT11"]
                    
                    # 初期値ですべてTrue（全選択）にする
                    target_blocks = gr.CheckboxGroup(label="Target Blocks", choices=block_choices, value=block_choices, info="Select blocks to modify.")
                
                with gr.Row():
                    # 出力欄
                    output_text = gr.TextArea(label="Output for X/Y/Z Plot (Prompt S/R)", interactive=False, show_copy_button=True, lines=4)
                    
            # イベントリスナー
            inputs = [base_weights, test_values, target_blocks]
            for input_component in inputs:
                input_component.change(
                    fn=self.generate_xyz_string,
                    inputs=inputs,
                    outputs=[output_text]
                )

        return [base_weights, test_values, target_blocks, output_text]

    def generate_xyz_string(self, base_weights_str, test_values_str, target_blocks):
        if not base_weights_str or not test_values_str or not target_blocks:
            return ""

        try:
            base_weights = [float(x.strip()) for x in base_weights_str.split(',')]
            test_values = [float(x.strip()) for x in test_values_str.split(',')]
        except ValueError:
            return "Error: Check number format."

        # ブロックマッピング判定
        length = len(base_weights)
        block_map = {}
        
        if length == 20: # SDXL
            blocks = ["BASE"] + [f"IN{i:02d}" for i in range(9)] + ["M00"] + [f"OUT{i:02d}" for i in range(9)]
            for i, name in enumerate(blocks):
                block_map[name] = i
        elif length == 26: # SD1.5
            blocks = ["BASE"] + [f"IN{i:02d}" for i in range(12)] + ["M00"] + [f"OUT{i:02d}" for i in range(12)]
            for i, name in enumerate(blocks):
                block_map[name] = i
        else:
            return f"Error: Base Weights length is {length}. Expected 20 or 26."

        result_parts = []

        # 1. 先頭にBase Weightsそのものを追加
        base_w_str = ",".join([str(int(w)) if w.is_integer() else str(w) for w in base_weights])
        result_parts.append(f'"{base_w_str}"')
        
        # 2. 変動パターンの生成
        for block in target_blocks:
            if block not in block_map:
                continue
            
            idx = block_map[block]
            
            for val in test_values:
                # 重み作成
                current_weights = base_weights[:]
                current_weights[idx] = val
                
                # 重複チェック: Base Weightsと全く同じになるパターンはスキップ
                # (既に先頭に追加済みであるため)
                if current_weights == base_weights:
                    continue

                # 文字列化
                w_str = ",".join([str(int(w)) if w.is_integer() else str(w) for w in current_weights])
                result_parts.append(f'"{w_str}"')

        return ", ".join(result_parts)

    def run(self, p, *args):
        return None
