# WebTRX用 USBダイヤルコントローラー — Rev.A Gamepad X + Keyboard

**更新: 2026-11-19**  /  設計状態: **USB HID仕様・ソース作成。実機・USB列挙・KiCad/ERCは未検証**

## 対象と採用部品

- 将来用途はWebTRXを操作するRC-28スタイルの卓上操作器。Icom純正機器を模倣したUSB識別子は使用しない。
- MCU: **WeAct Studio CH552 Core Board V1.0 / CH552T / Micro-USB**（ユーザー提示価格332円）。
- 回転: **EC12E2430803** 2相・無限回転エンコーダー、P1.4/P1.5に接続。共通端子GND。
- F1=P1.6、F2=P1.7、PTT=P3.2。各スイッチはGNDへのモーメンタリー接点。
- P3.6 / RSTを入力に転用しない。USBおよび電源回路はWeActボードの既存機能を使用する。

## この改訂の変更点

1. **廃止**: ダイヤルのCW/CCWをButton1/2やキーボードQ/Eで出力する方式。
2. **採用**: HID GamepadのX軸でCW=正、CCW=負、停止=0。値は-127..+127、回転速度により32..127の絶対値を持つ（暫定アルゴリズム）。停止120msで0へ復帰。
3. F1/F2/PTTは任意のUSB HIDキーボードキーへコンパイル時割当（仮初期値1,2,p）。各々独立にGamepad Button1..3へ切替可能。**キーとボタンの同時送信はしない**。
4. HID実装目標は1つのHIDインターフェース内にKeyboard(Report ID 1)とGamepad(Report ID 2)を載せる2つのトップレベルCollection。OS側の扱いとWebTRX連携は実機検証が必要。
5. プロジェクト型番 `WTRX-DIAL-CH552-RA`。USB VID:PID = **`1209:0001` は私的試験専用**。正式製品用PIDは未取得。詳細は `docs/USB_IDS.md`。

## 資料

- `hardware/CONNECTIONS.csv` : GPIO接続
- `hardware/BOM.csv` : 部品表（既存）
- `docs/HID_SPEC.md` : HID/回転/キー仕様
- `docs/HID_KEYMAP.csv` : キー割当表
- `docs/USB_IDS.md` : 製品型番とVID/PIDの規則
- `docs/TEST_PLAN.md` : 未実施の試験一覧
- `firmware/ch552_gamepad_keyboard/` : 新HIDソース
- `tools/prepare_firmware.py` : CH55xDuino 0.0.26の上流HIDサンプルを複合HID化する再現スクリプト
- `firmware/ch552_keyboard_prototype/` : 以前の**キーボードのみの旧試作**（履歴保持、今後の本命ではない）
- `make_schematic.py` : **旧Pico用スクリプト**（履歴保持）。現行CH552のKiCad回路図は未生成。

## 未確認事項

WebTRXがHTML Gamepad APIで軸値を入力として受けられるか、またブラウザが該当HID gamepad collectionを認識するかは未検証。PTTは入力途絶・USB切断・ウィンドウフォーカス喪失などでWebTRX側が送信を停止する安全制御なしに実無線機へ接続しない。

**ソースコードは作成済みだが、CH552実コンパイル・実機書き込み・Windows HID列挙・WebTRX動作確認・KiCad 10のERC/DRCは未実施。**

## 外部資料

- WeAct Studio CH552 Core Board: https://github.com/WeActStudio/WeActStudio.CH552CoreBoard
- CH55xDuino 0.0.26: https://github.com/DeqingSun/ch55xduino/releases
- CH55xDuino HID KeyboardMouse例: https://github.com/DeqingSun/ch55xduino/tree/ch55xduino/ch55xduino/ch55x/libraries/Generic_Examples/examples/05.USB/HidKeyboardMouse
- pid.codes私的試験専用USB ID: https://pid.codes/1209/0001/
- pid.codes正式PID申請: https://pid.codes/howto/
- Icom RC-28公式: https://www.icom.co.jp/lineup/options/RC-28/
