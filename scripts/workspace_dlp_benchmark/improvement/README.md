# 事例調査の改善案の検証（文脈補強の検知規則と是正フロー）

[企業の取り組み事例の調査](../../../research/technology/enterprise_sensitive_data_detection_case_studies_20261116.md)で共通していた改善案を、既存の検知精度の検証と是正（削除）フローの実験に取り込み、効果をローカルで検証するコード。結果と解釈は[検証報告](../../../research/technology/dlp_case_study_improvements_verification_20261118.md)を参照。

**Google実環境では測っていない。** 検知はRE2によるローカル検査、フローは前提値に依存するモデル計算である。

| ファイル | 内容 |
|---|---|
| `context_rules.py` | 文脈で補う検知規則（v4-context）。Workspaceの規則で書ける形（RE2の正規表現と、AND・OR・NOTの組合せ）だけを使う。手法T1・T2・T3を条件群に付け、効果を切り分けられる |
| `holdout_cases.json` | 独立に作った評価用の架空資料340件（陽性186・陰性124・判断保留30）。規則の作者とは別の担当が、規則と既存資料を見ずに作成した |
| `holdout_generator.py` | 上の資料を同じバイト列で再生成する生成器（乱数の種を固定） |
| `frozen.json` | 規則と評価資料のSHA-256。規則は評価資料の受領前に固定した |
| `evaluate_context.py` | 既存の正規表現（v3）と改善規則を、v3資料（開発用）と評価資料で比べる |
| `flow.py` | 是正フローの状態遷移と、現行案F0・改善案F1の週単位シミュレーション |
| `test_improvement.py` | 固定記録・評価資料の形式・規則の上限・空欄の除外・状態遷移の不変条件の試験 |

## 実行

```sh
# RE2は extended/README.md の手順で導入する
PY=/任意の場所/re2venv/bin/python
$PY scripts/workspace_dlp_benchmark/extended/reproduce.py make --output /新しい保存先/v3
$PY scripts/workspace_dlp_benchmark/improvement/evaluate_context.py \
  --v3-dataset /新しい保存先/v3 --report /保存先/context_report.json
python3 scripts/workspace_dlp_benchmark/improvement/flow.py \
  --context-report /保存先/context_report.json --seeds 10 --report /保存先/flow_report.json
$PY -m unittest discover -s scripts/workspace_dlp_benchmark/improvement -p 'test_*.py'
```

`flow.py`は標準ライブラリだけで動く。`--context-report`を省くと仮の検知性能で計算する。

## 検知規則の3手法

| 手法 | 内容 | Workspaceでの表し方 |
|---|---|---|
| T1 見出しと値の書き方を広げる | 区切りにタブ・改行・「は」を含める。英語見出し・全角数字を足す。見出しの直後に値の文字があることを必須にし、空欄・伏字・区切り記号だけの欄を除く | 正規表現1つ |
| T2 見出しのない値を拾う | 値の形（12桁、英字2＋数字7など）と、同じファイル内の「人」を示す語（氏名、社員、さん、様など）をANDで組み合わせる | 正規表現2つ以上をAND |
| T3 除外条件 | 業務番号（注文、型番、管理番号など）、統計・法令解説・案内の語があれば外す | 条件群の中のNOT |

独自正規表現は92個で、規則で参照できる上限100に近い。最長は213文字（上限1,000）。

## 是正フローの比較

| 案 | 流れ |
|---|---|
| F0 現行案 | DLP検知 → 管理者が全件確認 → 作成者へ削除・修正依頼 → 作成者が削除か共有解除 |
| F1 改善案 | 共有の棚卸し（公開・外部共有で1年更新なしを可逆に解除）→ 検知結果を優先度順に所有者へ「提案」→ 所有者が確定 → ラベル＋外部共有制限 → 4週の猶予後に削除。所有者不在・無応答は上長へ。新規ファイルは既定ラベル「社内限」 |

両案とも、最初の2週は監査のみにする。状態遷移で禁止した遷移は例外にし、試験で「確定と猶予を経ない削除がない」「未完了の案件にはすべて担当者がいる」「通知に一致値を載せない」を確認する。

前提値（ファイル数2万、機微ファイル15%、外部共有12%・公開リンク3%、所有者不在6%、所有者の週あたり応答率50%など）は`DEFAULT_SCENARIO`にあり、感度分析は`SENSITIVITY`で振る。値は公開調査の幅を参考にした仮定で、特定組織の実態ではない。

## 固定の手順

規則を変えたら、`evaluate_context.py`の開発資料の結果だけを見て調整する。評価資料の結果を見てから規則を直した場合、その評価資料はもう独立ではないので、新しい評価資料を別の担当が作って`frozen.json`を更新する。`test_improvement.py`は記録と実ファイルの不一致を失敗にする。
