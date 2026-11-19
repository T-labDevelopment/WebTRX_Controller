# WebTRX Controller Rev.A.2 — KiCad 10 編集可能データ

## 回路・採用部品

- A1: **WeAct Studio CH552 Core Board V1.0 / CH552T**。専用シンボル／専用フットプリント（2×10ピン、2.54mmピッチ・端子列間15.24mm）。ボード内蔵の Micro-USB を電源・USB HID・書き込みに使用する。外付けUSBコネクタやCH552T単体部品は実装しない。USBコネクタはPCB上端側を向く。
- SW1: **ALPS Alpine EC12E2420801** 24クリック／24パルス。メーカー取付寸法（端子A-C-B、2.5mm刻み、支持金具間13.2mm、端子列と支持穴間7.5mm）に基づく専用シンボル・フットプリント。金具M1/M2は電気的に未接続で、支持・はんだ付け用途。
- SW2, SW3, SW4: F1/F2/PTT、12mm角モーメンタリNO。KiCad標準シンボル `Switch:SW_Push` と標準フットプリント `Button_Switch_THT:SW_PUSH-12mm` を採用。標準フットプリントはE-Switch TL1100系の12.5×5mm穴ピッチ。**任意の12mm角タクトに合うわけではないため型番・実物寸法の一致確認が必須**。
- GPIO入力は内部プルアップを利用、押下時にGND。回転A=P1.4、B=P1.5、共通C=GND、F1=P1.6、F2=P1.7、PTT=P3.2。
- P3.6/P3.7/RSTをゲームボタンとして利用しない。モジュール側既存のUSB/書き込み機能を維持する。

## 部品実装と基板

`WebTRX_Controller.kicad_sch`: 専用モジュール・エンコーダー・標準タクトを接続した回路図。グローバルラベルを使用。未使用モジュール端子にはNo Connectを付与。

`WebTRX_Controller.kicad_pcb`: 100×70mm、2層、1ozを想定した**試作レイアウト**。5信号+GNDの配線をB.Cuに追加し、USBコネクタ方向と操作スイッチを上面に示す。**KiCad CLIのDRC検査は実行していないため、製造承認・Gerber確定ではない。**

`WebTRX_Custom.kicad_sym`, `WebTRX_Custom.pretty/`: 正規のKiCad編集可能な独立ライブラリ。エンコーダー・CH552専用シンボルのピン番号とPCBパッド番号を一致させる。`sym-lib-table` / `fp-lib-table` でプロジェクト相対パス登録。

既存 HID の「1クリック→X軸 0→±127」およびF1/F2/PTTの任意キー割り当ては変更なし。ソフトウェアのUSBデバイスIDも変更しない。

## 根拠と制約

- WeAct Studio: https://github.com/WeActStudio/WeActStudio.CH552CoreBoard
- ピン配列・20端子2.54mm/15.24mm: オープンソース実装例 https://github.com/rgoulter/keyboard-labs （`pcb/ProjectLocal.kicad_sym` と `pcb/keyboard-ch552-44.kicad_pcb`）。**外形・USBコネクタの立体干渉はメーカー機械図の現物確認未完了。**
- エンコーダー: https://tech.alpsalpine.com/e/products/detail/EC12E2420801/ および公式カタログ https://tech.alpsalpine.com/assets/catalog/product-catalog-ec-all.en.pdf のD-13 取付穴図。支持金具孔の現物適合を優先確認。
- KiCad標準12mmタクト: https://github.com/KiCad/kicad-footprints/blob/master/Button_Switch_THT.pretty/SW_PUSH-12mm.kicad_mod

## 重要: 検証状況

- 内部静的検査: ピン番号、ネット名、シンボル／フットプリント一致、50mil、基板トラック端点、ネット配線、カスタムライブラリ構文の整合をチェック。
- KiCad 10.0.x実アプリでの読み込み・ERC/DRC・描画・フットプリントからPCB同期: **未実行**。本環境にはKiCad CLI/GUIがない。
- 実機組立・クリック誤計数・PTT安全機能・WebTRX運用: **未検証**。
- **フットプリント機械寸法とUSB挿抜・コネクタ高さの干渉は、製造前に実機で確認すること。**

Power Flagは内蔵USB給電を独立部品として表現しないため、外部回路には不要と判断している。A1の5V/3V3はNC、GNDは受動端子とし誤った給電宣言を避けた。

Windows PowerShellのKiCad CLI検証例：

```powershell
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch erc .\WebTRX_Controller.kicad_sch -o ERC_report.txt
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' pcb drc .\WebTRX_Controller.kicad_pcb -o DRC_report.txt
```
