# WebTRX用 USBダイヤルコントローラー — Rev.A Gamepad X detent pulse + Keyboard

**更新: 2026-11-19**  /  設計状態: **USB HID仕様・ソース作成。実機・USB列挙・KiCad/ERCは未検証**

## 対象と採用部品

- 将来用途はWebTRXを操作するRC-28スタイルの卓上操作器。Icom純正機器を模倣したUSB識別子は使用しない。
- MCU: **WeAct Studio CH552 Core Board V1.0 / CH552T / Micro-USB**（ユーザー提示価格332円）。
- 回転: **EC12E2420801** 2相・無限回転エンコーダー、P1.4/P1.5に接続。共通端子GND。
- F1=P1.6、F2=P1.7、PTT=P3.2。各スイッチはGNDへのモーメンタリー接点。
- P3.6 / RSTを入力に転用しない。USBおよび電源回路はWeActボードの既存機能を使用する。

## この改訂の変更点（2026-11-19 クリック単位改訂）

1. **廃止**: ダイヤルのCW/CCWをButton1/2やキーボードQ/Eで出力する方式。
2. **採用・更新**: EC12E2420801（24クリック/24パルス）を1クリックにつき1イベントとして検出し、HID X軸でCW=+127 → 0、CCW=-127 → 0を1回ずつ送信。**速度比例は廃止**。イベントはFIFO（64件）で順序保持。35msの最大軸保持＋25msの中立保持を初期値とする（実機調整が必要）。
3. F1/F2/PTTは任意のUSB HIDキーボードキーへコンパイル時割当（仮初期値1,2,p）。各々独立にGamepad Button1..3へ切替可能。**キーとボタンの同時送信はしない**。
4. HID実装目標は1つのHIDインターフェース内にKeyboard(Report ID 1)とGamepad(Report ID 2)を載せる2つのトップレベルCollection。OS側の扱いとWebTRX連携は実機検証が必要。
5. プロジェクト型番 `WTRX-DIAL-CH552-RA`。USB VID:PID = **`1209:0001` は私的試験専用**。正式製品用PIDは未取得。詳細は `docs/USB_IDS.md`。

## 資料

- `hardware/CONNECTIONS.csv` : GPIO接続
- `hardware/BOM.csv` : 部品表（既存）
- `docs/HID_SPEC.md` : HID/回転/キー仕様
- `docs/WEBTRX_GAMEPAD_EDGE.md` : WebTRX側のGamepad APIエッジ検出例（未統合）
- `docs/HID_KEYMAP.csv` : キー割当表
- `docs/USB_IDS.md` : 製品型番とVID/PIDの規則
- `docs/TEST_PLAN.md` : 未実施の試験一覧
- `firmware/ch552_gamepad_keyboard/` : 24クリック・1クリック1ジョイスティック最大値イベントの新HIDソース
- `tools/prepare_firmware.py` : CH55xDuino 0.0.26の上流HIDサンプルを複合HID化する再現スクリプト
- `firmware/ch552_keyboard_prototype/` : 以前の**キーボードのみの旧試作**（履歴保持、今後の本命ではない）
- `make_schematic.py` : **旧Pico用スクリプト**（履歴保持）。現行CH552のKiCad回路図は未生成。

## ホスト環境での試験（実機動作保証ではない）

- `g++ -std=c++17 -Wall -Wextra -Werror tests/test_rotary_event.cpp -o /tmp/test_rotary && /tmp/test_rotary`
- `python tools/test_usb_spec.py`
- `python tools/test_firmware_mock.py`

3項目ともモック/静的試験に限る。CH552向け実コンパイルおよびUSB接続試験は含まない。

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
