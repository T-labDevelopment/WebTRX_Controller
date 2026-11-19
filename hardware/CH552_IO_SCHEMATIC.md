# Rev.A CH552 Core Board 外付け操作部 回路図

## 目的

KiCad 10対応の編集可能な `WebTRX_Controller.kicad_sch` を実装。USB/電源はWeAct Studio CH552 Core Board V1.0完成基板が担当し、この回路図には外付け操作部（24クリック・2相エンコーダー、F1、F2、PTT）の配線のみを含める。

## 電気接続

| J1 pin | WeAct上の表示 | グローバルネット | 操作部 |
|---|---|---|---|
| 1 | P1.4（14） | ENC_A | SW1 A |
| 2 | P1.5（15） | ENC_B | SW1 B |
| 3 | P1.6（16） | KEY_F1 | SW2片側 |
| 4 | P1.7（17） | KEY_F2 | SW3片側 |
| 5 | P3.2（32） | KEY_PTT | SW4片側 |
| 6 | GND | GND | SW1 C、SW2/3/4もう片側 |

J1は **6線ハーネスの論理インターフェース**で、WeAct製ボードの正確な基板取付フットプリント・物理ヘッダ位置を表したものではない。J1の6線接続順序は設計上の割当であり、WeActボード上の物理端子と自動的に一列対応するわけではない。電源線は引かず、ボードのUSBコネクターから給電する。

## 回路設計上の注意

- SW1：ALPS Alpine EC12E2420801、24クリック/24パルス。メーカー基板取付面図で信号端子はA-C-B。ピン名A/B/Cを含むKiCad公式`Device:RotaryEncoder`をそのまま埋め込む。
- SW2/3/4：KiCad公式`Switch:SW_Push`。採用する実体型番・フットプリントは未決定。
- J1：KiCad公式`Connector_Generic:Conn_01x06`。ハーネスの種類・ピン並び・フットプリントは未決定。
- F1/F2/PTT：GNDへ落とすNOモーメンタリー、GPIO内部プルアップ前提。接点電流および実機のノイズ・チャタリングは未検証。
- USBのVBUSや3.3V給電線は外付け回路へ出さないため、回路図に電源入力シンボルは存在せず、外部のPWR_FLAGも不要。完成ボード内部のUSB給電回路を省略していることを明記。
- P3.6（USB/BOOT）とRSTは予約。入力に転用しない。
- ファームウェア仕様の`0→+127 / 0→-127`、F1/F2/PTTキー割当、USB VID/PID方針は変更しない。

## 調達・実装状況

| Ref | 部品 | 数量 | PCBフットプリント |
|---|---|---:|---|
| A1 | WeAct CH552 Core Board V1.0 / CH552T | 1 | **完成基板、対象回路図の外部** |
| SW1 | EC12E2420801 | 1 | 未設定（メーカー取付図を確認して選定） |
| SW2～SW4 | タクト/モーメンタリーボタン | 3 | 未選定 |
| J1 | 6線ハーネス（論理インターフェース） | 1 | 未選定 |

## 正本・検証

- Gitブランチ：`feature/kicad10-io-schematic`。mainは更新しない。
- 標準シンボルはKiCad 10向け公式リポジトリの読み出しをミラーした`pellicleai/kicad-symbols`から取得。取得した**完全なシンボル本文**を回路図へ同梱し、独自の簡略キャッシュに置き換えていない。
- 50milグリッドに全接続点・グローバルラベルを整列。構文括弧整合、ネット端点数、端子番号、UUID重複なしをスクリプト側で検査。
- KiCad 10実アプリ/CLIはこの環境では利用できないため、**ERC 0件とは判断しない**。実機・PCB/DRC・フットプリント照合も未実施。製造データではない。

## 参照
- https://tech.alpsalpine.com/e/products/detail/EC12E2420801/
- https://github.com/WeActStudio/WeActStudio.CH552CoreBoard
- https://gitlab.com/kicad/libraries/kicad-symbols
