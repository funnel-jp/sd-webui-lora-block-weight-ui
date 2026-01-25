import sys
import random
import inspect
import os
from modules import scripts, script_callbacks

# ターゲットとなるLBWのコミットハッシュ（このバージョン以前の場合のみ適用）
TARGET_HASH = "b403cb7300f288360023c2a1978b86a361934e24"

# -----------------------------------------------------------
# ユーティリティ: ファイル名の幹（Stem）を取得
# -----------------------------------------------------------
def get_name_stem(path_str):
    """
    パス文字列からフォルダと拡張子を取り除いた「ファイル名のみ」を返す
    """
    if not isinstance(path_str, str):
        return str(path_str)
    # 区切り文字を統一
    path_str = path_str.replace("\\", "/")
    # ファイル名取得
    filename = path_str.split("/")[-1]
    # 拡張子削除
    stem, _ = os.path.splitext(filename)
    return stem

# -----------------------------------------------------------
# 修正ロジック (lbwf_fixed)
# -----------------------------------------------------------
def lbwf_fixed(target_globals, after_applying_lora_patches, ms, lwei, elements, starts, flux, names):
    """
    修正版 lbwf: ファイル名Stemベースのマッチング機能付き
    """
    errormodules = []
    dict_lora_patches = dict(after_applying_lora_patches.items())
    
    # 必要な定数・関数をターゲットのglobalsから取得
    LORAS = target_globals.get("LORAS", ["lora", "loha", "lokr"])
    ratiodealer = target_globals.get("ratiodealer")

    # マッチング処理
    for name, m, l, e, s in zip(names, ms, lwei, elements, starts):
        target_hash_key = None
        target_patches = None

        # LBWから来た名前の Stem を取得
        lbw_stem = get_name_stem(name)

        # Forgeのキーを走査してマッチするものを探す
        for k, v in dict_lora_patches.items():
            forge_key_str = str(k[0])
            forge_stem = get_name_stem(forge_key_str)

            # 判定: ファイル名部分（拡張子なし）が一致すればOKとする
            if forge_stem == lbw_stem:
                target_hash_key = k
                target_patches = v
                break
        
        # マッチしない（TEがない等）場合はスキップ
        if target_patches is None:
            continue
        
        # 処理対象が見つかったら、辞書から削除（重複適用防止）
        if target_hash_key in dict_lora_patches:
            del dict_lora_patches[target_hash_key]

        # ウェイト適用処理
        for key, vals in target_patches.items():
            n_vals = []
            lvs = [v for v in vals if v[1][0] in LORAS]
            for v in lvs:
                # 元モジュールの ratiodealer を使用
                ratio, picked = ratiodealer(key.replace(".","_"), l, e, flux)
                n_vals.append([ratio * m if s is None or s == 0 else 0, *v[1:]])
                if not picked:
                    errormodules.append(key)
            target_patches[key] = n_vals

        lbw_key = ",".join([str(m)] + [str(int(w) if type(w) is int or w.is_integer() else float(w)) for w in l]) + e
        new_hash = (target_hash_key[0], lbw_key, *target_hash_key[2:])

        after_applying_lora_patches[new_hash] = after_applying_lora_patches[target_hash_key]
        if new_hash != target_hash_key:
            del after_applying_lora_patches[target_hash_key]

    if len(errormodules) > 0:
        print(f"Unknown modules: {errormodules}")


# -----------------------------------------------------------
# パッチ適用関数生成器
# -----------------------------------------------------------
def create_patched_function(original_globals):
    
    def load_loras_blocks_patched(self, names, lwei, te, unet, elements, ltype="lora", starts=None):
        importer = original_globals.get("importer")
        lbw = original_globals.get("lbw")
        setall = original_globals.get("setall")
        lbwrf = original_globals.get("lbwrf")
        shared = original_globals.get("shared")

        oldnew = []

        if "lora" == ltype:
            lora = importer(self)
            self.lora = lora.loaded_loras
            for loaded in lora.loaded_loras:
                for n, name in enumerate(names):
                    if name == loaded.name:
                        if (lwei[n] == [1] * 26 or lwei[n] == [1] * 61) and elements[n] == "": continue
                        lbw(loaded, lwei[n], elements[n])
                        setall(loaded, te[n], unet[n])
                        newname = loaded.name + "_in_LBW_" + str(round(random.random(), 3))
                        oldname = loaded.name
                        loaded.name = newname
                        oldnew.append([oldname, newname])

        elif "lyco" == ltype:
            try:
                import lycoris as lycomo
            except ImportError:
                lycomo = None
            
            if lycomo and hasattr(lycomo, "loaded_lycos"):
                self.lycoris = lycomo.loaded_lycos
                for loaded in lycomo.loaded_lycos:
                    for n, name in enumerate(names):
                        if name == loaded.name:
                            lbw(loaded, lwei[n], elements[n])
                            setall(loaded, te[n], unet[n])

        elif "nets" == ltype:
            try:
                import networks as nets
            except ImportError:
                nets = None

            if nets and hasattr(nets, "loaded_networks"):
                self.networks = nets.loaded_networks
                for loaded in nets.loaded_networks:
                    for n, name in enumerate(names):
                        if name == loaded.name:
                            lbw(loaded, lwei[n], elements[n])
                            setall(loaded, te[n], unet[n])

        elif "forge" == ltype:
            # ★Forge用修正パッチ★
            forge_objs = shared.sd_model.forge_objects_after_applying_lora
            
            unet_patches = forge_objs.unet.patches if "reforge" in ltype else forge_objs.unet.lora_patches
            lbwf_fixed(original_globals, unet_patches, unet, lwei, elements, starts, self.is_flux, names)

            clip_patches = forge_objs.clip.patcher.patches if "reforge" in ltype else forge_objs.clip.patcher.lora_patches
            lbwf_fixed(original_globals, clip_patches, te, lwei, elements, starts, self.is_flux, names)

        elif "reforge" == ltype:
            lbwrf(te, unet, lwei, elements, starts)

        try:
            import lora_ctl_network as ctl
            for old, new in oldnew:
                if old in ctl.lora_weights.keys():
                    ctl.lora_weights[new] = ctl.lora_weights[old]
        except:
            pass

    return load_loras_blocks_patched


# -----------------------------------------------------------
# エントリーポイント
# -----------------------------------------------------------
def apply_patch_force(block, *args, **kwargs):
    # Forge環境チェック
    try:
        from modules import launch_utils
        if launch_utils.git_tag()[0:2] != "f2":
            return
    except:
        return

    # LBWインスタンスを探す
    target_script = None
    all_scripts = []
    if hasattr(scripts, "scripts_txt2img") and scripts.scripts_txt2img:
        all_scripts.extend(scripts.scripts_txt2img.alwayson_scripts)
    if hasattr(scripts, "scripts_img2img") and scripts.scripts_img2img:
        all_scripts.extend(scripts.scripts_img2img.alwayson_scripts)

    for script in all_scripts:
        if script.title() == "LoRA Block Weight":
            target_script = script
            break

    if not target_script:
        return

    try:
        if hasattr(target_script.process, "__globals__"):
            target_globals = target_script.process.__globals__
        elif hasattr(target_script.process, "__func__"):
            target_globals = target_script.process.__func__.__globals__
        else:
            return

        if "load_loras_blocks" not in target_globals:
            return
        
        # バグを含むコードかどうかの簡易チェック（zipの使用箇所）
        if "lbwf" in target_globals:
            lbwf_src = inspect.getsource(target_globals["lbwf"])
            if "zip(ms, lwei, elements, starts, list(after_applying_lora_patches.keys()))" in lbwf_src:
                # パッチ適用
                patched_func = create_patched_function(target_globals)
                target_globals["load_loras_blocks"] = patched_func
                # print("LoRA Block Weight patch applied.") # 必要であればコメントアウトを解除

    except Exception:
        pass

# アプリケーション起動完了時に実行
script_callbacks.on_app_started(apply_patch_force)
