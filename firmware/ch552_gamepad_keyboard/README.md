# CH552 ゲームパッド＋キーボードHID Rev.A

## 前提
- WeAct CH552 Core Board V1.0
- CH55xDuino **0.0.26**（Arduino IDEで使用）
- USB Settings: `USER CODE w/ 148B USB ram`等 USER_USB_RAM が有効な設定
- 開発中にのみ `VID 1209 / PID 0001` を使用。製造・頒布時は禁止。

## 使用方法
1. CH55xDuino 0.0.26をインストールする。
2. `HidKeyboardMouse`のArduino例（同版の`Generic_Examples/examples/05.USB/HidKeyboardMouse`）を探す。
3. 本リポジトリ直下で `python tools/prepare_firmware.py "/.../HidKeyboardMouse"` を実行し、同版のUSBソースを`firmware/ch552_gamepad_keyboard/src`へコピーして部分変更する。
4. `ch552_gamepad_keyboard.ino` をArduino IDEで開く。対象CH552、USER USB RAMを選択。
5. `config.h` でキー割当を変更。F1/F2/PTTは Keyboard / Gamepad Button から選択可能。
6. ビルド後、書き込み用P36/RSTスイッチでブートローダーを起動してUSB書き込みを行う。
7. 書込み後に、USBView/Windowsの`joy.cpl`/キーボード入力で列挙とキー操作を確認する。

**未検証**: 上記は予定手順です。この環境ではCH55xDuino、SDCC、実機がなくコンパイル・USB列挙を実行していません。`prepare_firmware.py` はデバイス記述子を置換する試作パッチです。上流USBソースとバージョンの差異があればスクリプトは明示的に停止します。

ゲームパッドのX軸は回転速度の符号付き値であり、エンコーダーの累積位置を出力しません。スイッチは任意のキーコードで出力できますが、WebTRX側の対応は別途必要です。
