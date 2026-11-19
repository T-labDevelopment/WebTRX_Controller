# WebTRX用 USBロータリーダイヤル操作器 — CH552 Rev.A 設計更新

**2026-11-18 / 設計状態: 回路ピン割当と機能定義、ファームウェア試作ソース作成。実機・KiCad/ERC未検証**

## 目的と対象

- 最終目標: [WebTRX (webtrx.jp)](https://webtrx.jp/) をPCブラウザーから操作する、Icom RC-28に近いUSB卓上コントローラー。
- ダイヤル: 無限回転エンコーダー1個（24パルス、無クリック、原点不要）。
- 操作キー: F1/F2の任意割当2キー、PTT押下/解放1キー。
- 既定MCU: **WeAct Studio CH552 Core Board V1.0 / CH552T / Micro-USB実装済み**（ユーザー提示価格332円）。
- 当面の信号: USB HID KeyboardとGamepadの**複合HIDを最終目標**とし、キーボードのみの検証用ファームウェアを先行作成。
- WebTRXの公式βユーザーガイドには2026-11-18時点で一般ユーザー向けショートカット割当の確認がない。**Web Radio Control (webradiocontrol.tech) のショートカットをWebTRX固有仕様として流用しない。**

## 基板配線（ユーザーの提示写真でシルク名称を確認、端子の実機導通は未検証）

| 対象 | CH552ボード | CH55xDuino番号 | 接続 | メモ |
|---|---|---:|---|---|
| エンコーダーA相 | P1.4 | 14 | SW1-A→P1.4 | INPUT_PULLUP |
| エンコーダーB相 | P1.5 | 15 | SW1-B→P1.5 | INPUT_PULLUP |
| エンコーダー共通 | GND | - | SW1-C→GND | 3線式接点出力 |
| F1ボタン | P1.6 | 16 | SW2一端→P1.6、他端GND | INPUT_PULLUP |
| F2ボタン | P1.7 | 17 | SW3一端→P1.7、他端GND | INPUT_PULLUP |
| PTT（モーメンタリー） | P3.2 | 32 | SW4一端→P3.2、他端GND | INPUT_PULLUP、押下=LOW |
| USB | 基板Micro-USB | - | PCへUSB | ボード実装済みUSB・給電・書込みを使用 |

**使用禁止**: P3.6（USB書込み用ボタン/USB D+系）と RST は操作ボタンに転用しない。エンコーダーに5Vは接続しない。

### 電源と配線

外付けレギュレーター/USB Type-C CC抵抗/USB D+/D-配線は新規基板に作らない。CH552ボードの電源設計に依存する。外部入力には原則、内部プルアップを使い、配線長/ESD/ノイズで問題が出た場合のみ保護部品を検討する。PTT接点の誤動作がないことを重点確認する。

## HID機能

- **キーボード試作**: エンコーダー時計回り/反時計回り、F1/F2、PTTでそれぞれキーコードを送出。キーはファームウェア上部のマクロから変更できる。
- **HID Gamepad（従来仕様）**: ダイヤルCW=Button 1、CCW=Button 2。複合HIDとして統合する工程は未実施。旧Pico版からの仕様を維持するが**今回のキーボード試作ではまだ出力しない**。
- **最終案**: Composite HIDのKeyboard+Gamepadを列挙し、ダイヤルは設定したモードに応じてKeyboardまたはGamepadに送出する。二重操作を防ぐため、1イベントを両方に送信するのは初期設定としない。
- **デフォルトキー（検証専用、WebTRXキーとは限らない）**: CW='e'、CCW='q'、F1='1'、F2='2'、PTT='p'。キー割当は上部の定義から変更可能。
- WebTRX側ではPCブラウザのフォーカス・テキスト入力状態に左右される。公開ショートカット未確認なので**物理操作だけでWebTRXを制御できると断定しない**。

## PTTの安全要件

- 物理PTT押下時に `keydown`、解放時に `keyup` とする。トグル式送信制御は初期採用しない。
- 初期試作のキーボード文字 'p' は単なるキーイベントであり、**送信操作を保証しない**。
- ブラウザの `blur`、タブ切替、デバイス切断、回線切断、通信異常、操作権喪失、キー解放イベント欠落時は、WebTRX側でPTT解除と送信タイムアウトを必須とする。
- WebTRX実際のPTT制御API/キーバインドが確認できるまで、無線機を接続した状態でPTT機能を試験しない。

## 収録物

- `hardware/BOM.csv`: WeActボード＋エンコーダー＋スイッチ3個。
- `hardware/CONNECTIONS.csv`: Rev.A端子割当。
- `docs/HID_KEYMAP.csv`: 操作と既定キーコード、今後のゲームパッド機能。
- `docs/TEST_PLAN.md`: 手動/安全試験項目。
- `firmware/ch552_keyboard_prototype/ch552_keyboard_prototype.ino`: **キーボードHIDのみ**の検証用ソース（未ビルド・未書き込み）。
- `make_schematic.py`: **旧Pico版のスクリプトを履歴保持のため残している。現行CH552版を生成しないため実行しない。**

## ファームウェア検証環境（予定）

- `CH55xDuino 0.0.26`、Arduino IDEとCH552 Board、USB Settings=`USER CODE`指定。
- 同梱スケッチはCH55xDuinoの `Generic_Examples/05.USB/HidKeyboard` に含まれる `src/userUsbHidKeyboard` フォルダーをスケッチ同階層の `src/` 以下へコピーしてからコンパイルする想定。
- 同梱していない第三者のUSBドライバーソースはバージョン管理する依存物として記録し、安易に複製・改変しない。
- この環境ではArduino CLI・CH55xDuino・KiCad CLI・実機がないため、書込み・認識・ERC・DRC・性能測定は実施していない。

## 価格概算

- WeActボード: 332円（ユーザー提示画面、時点限定セール価格）
- EC12E2430803: 110円（以前確認した秋月電子価格、在庫限り）
- F1/F2/PTT用スイッチ3個、配線、基板、ノブ、ケースは未積算。
- 主部品小計442円。**RC-28相当完成品の総製作原価ではない。**

## 出典

- Icom RC-28公式製品情報: https://www.icom.co.jp/lineup/options/RC-28/
- WebTRX公式: https://webtrx.jp/
- WebTRX β版ガイド: https://webtrx.jp/?page_id=578
- CH552複合HID先行例: https://github.com/wagiminator/CH552-USB-Knob
- CH552キーボード先行例: https://github.com/DeqingSun/ch55xduino/tree/ch55xduino/ch55xduino/ch55x/libraries/Generic_Examples/examples/05.USB/HidKeyboard
- CH55xDuinoリリース: https://github.com/DeqingSun/ch55xduino/releases

## 変更履歴

- `Rev.A/Pico`: USBロータリーゲームパッドの原型。Gitベースコミットを保持。
- `feature/ch552-keyboard-webtrx`: WeAct CH552ボードへ移行し、2つの機能キー、PTT、キーボードHID試作と最終複合HID仕様を追加。
