# USB Rotary Dial Gamepad — Rev.A

**設計基準**: 2026-11-18 / KiCad 10.0.x（10.0.8を参照）

## 電気回路

- A1: Raspberry Pi Pico (RP2040、内蔵 Micro-USB)。USBはPCへ接続し、Pico本体から給電する。
- SW1: ALPS EC12E2430803（ノンクリック、24パルス/回転、プッシュスイッチなし）。
- SW1.A → Pico GP2 (物理4番ピン)、内部プルアップ3.3Vを使用。
- SW1.B → Pico GP3 (物理5番ピン)、内部プルアップ3.3Vを使用。
- SW1.C → Pico GND (物理3番ピン)。
- リセットボタン、角度原点設定、外付けUSB PHY、外付け電源レギュレータは不要。
- 原型はGPIO入力→スイッチ→GNDの構成。現行の3信号に対して外付けR/Cを実装しない。ノイズ評価で必要と判断したら後日追加する。
- PicoのGPIOには5Vを入力しない。

## HID出力

初期仕様：CW=ゲームパッドButton 1、CCW=Button 2。回転停止中は両方OFF。
ゲームパッドのアナログ軸は絶対量であり、無限回転で蓄積した角度の相対値をそのまま無制限には表現できない。
アナログ軸エミュレーションはソフトウェアの将来の選択肢に留める。

## KiCad 10図面の生成

`make_schematic.py` は**インストール済みのKiCad 10正規ライブラリ**から正式シンボル全文を読み、埋め込みデータとして利用して回路図を生成する。簡略化した独自シンボルや独自キャッシュは作成しない。

WindowsのKiCad 10.0がインストール済みの場合、プロジェクトの最上位ディレクトリで次を実行する：

```
py -3 make_schematic.py
```

検索できない場合は次を指定する：

```
py -3 make_schematic.py --symbol-root "C:\\Program Files\\KiCad\\10.0\\share\\kicad\\symbols"
```

生成されるファイル: `hardware/USB_Rotary_Dial.kicad_sch`。KiCad 10で開いて回路図を確認すること。

**注意**: 実行環境にKiCadがなく、現在このZIPに生成済み `.kicad_sch` は含まれない。今回の納品物は回路・設計資料・KiCad生成スクリプトであり、ERC/DRC済み・PCB製造可能を意味しない。

### 未完了・次の段階

1. KiCad 10.0.8で回路図を生成後、ERCを実行し、エラー0・警告0を確認する。
2. EncoderのPCBフットプリント（特に金属爪・穴径・軸長25mm）をメーカー図面と照合する。現段階ではフットプリントを未確定としている。
3. KiCad PCBの外形・配線設計とDRC。
4. エンコーダーのチャタリング、最高回転速度、PC側でのHID認識と入力欠落を実機検証。
5. firmwareディレクトリは予約。回路仕様を固定した後、Arduino-Pico 6.4.0に対応するファームウェアを追加する。

## 資料（確認日: 2026-11-18）

- Raspberry Pi Pico: https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html
- Pico pinout: https://pip-assets.raspberrypi.com/categories/610-raspberry-pi-pico/documents/RP-008309-DS-1-Pico-R3-A4-Pinout.pdf
- ALPS EC12E2430803: https://tech.alpsalpine.com/e/products/detail/EC12E2430803/
- 秋月電子 EC12E2430803: https://akizukidenshi.com/catalog/g/g106358/
- KiCad 10.0.8: https://www.kicad.org/blog/2026/10/KiCad-10.0.8-Release/
- KiCad official MCU symbol: https://gitlab.com/kicad/libraries/kicad-symbols/-/raw/10.0.8/MCU_Module.kicad_symdir/RaspberryPi_Pico.kicad_sym
- KiCad official encoder symbol: https://gitlab.com/kicad/libraries/kicad-symbols/-/raw/10.0.8/Device.kicad_symdir/RotaryEncoder.kicad_sym
- Arduino-Pico: https://arduino-pico.readthedocs.io/en/latest/usb.html

## 製造・検証ステータス

| チェック | 結果 |
|---|---|
| 配線設計 | 原理構成確定（実機未検証） |
| KiCad正式シンボル | 公式名称を確認。スクリプトはライブラリファイルを参照 |
| 回路図生成 | 未実施（KiCad 10ライブラリが本実行環境にないため） |
| ERC | 未実施 |
| PCB / DRC | 未実施 |
| エンコーダーフットプリント | 未確定 |
| ファームウェア | 未作成 |
| 製造承認 | 未承認 |
