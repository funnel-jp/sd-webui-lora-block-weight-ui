# sd-webui-lora-block-weight-ui

Stable Diffusion WebUI (Automatic1111) の Extra Networks (LoRAカード) 画面を拡張し、**LoRA Block Weight (LBW)** の設定を各LoRAのメタデータとして保存・利用できるようにする拡張機能です。

LoRAごとに好みの階層マージ設定（プリセット名や数値）を記憶させ、カードをクリックするだけで自動的に `:lbw=...` 付きのプロンプトを入力できるようになります。

## 概要

通常、LoRA Block Weight を使用する場合、`<lora:ModelName:1.0:lbw=ALL>` のように手動で入力するか、LBW拡張機能のUIからコピー＆ペーストする必要があります。

この拡張機能を導入すると、WebUI標準の「LoRAカードのメタデータ編集画面」に **"Additional weight"** という項目が追加されます。ここに `INS` や `ALL`、あるいは `1,0,0...` といった値を保存しておくと、そのLoRAカードをクリックした際に、自動的にLBWの構文を含んだ状態でプロンプトに追加されます。

## 必須拡張機能

この拡張機能はUIとプロンプト入力を補助するものであり、実際に階層別適用を行うには以下の拡張機能がインストールされている必要があります。

* **[sd-webui-lora-block-weight](https://github.com/hako-mikan/sd-webui-lora-block-weight)**

## インストール方法

1.  WebUIの `Extensions` タブを開きます。
2.  `Install from URL` タブを選択します。
3.  `URL for extension's git repository` にこのリポジトリのURLを入力します。
4.  `Install` ボタンをクリックします。
5.  WebUIを再起動（Reload UI）してください。

## 使い方

1.  **メタデータの編集**:
    * `LoRA` タブ（Extra Networks）を開きます。
    * 設定したいLoRAカードの右上にある 🔧 アイコン（または ℹ️ アイコン）をクリックして、メタデータ編集画面を開きます。
    * 新しく追加された **"Additional weight"** という項目に、LBWのプリセット名（例: `INS`, `OUTF`, `ALL`）や、直接ウェイト数値（例: `1,0,0,1...`）を入力します。
    * `Save` ボタンで保存します。

2.  **プロンプトへの入力**:
    * 編集画面を閉じ、そのLoRAカードをクリックします。
    * プロンプト入力欄に、自動的に以下のような形式で入力されます。
        ```
        <lora:YourLoraName:1.0:lbw=INS>
        ```
        ※ `Preferred weight`（推奨ウェイト）が設定されている場合は、その値も反映されます。
