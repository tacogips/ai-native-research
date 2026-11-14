# AI ハーネスの情報フロー・認可分離・評価方法

調査日: 2026-10-08。公開一次資料の全文と固定された公開コードを静的に照合した。実データ、秘密鍵、外部モデル呼出し、攻撃実験は使用していない。原本は `research/disclosures/raw/harness_20261008/information_flow/`、取得結果・ハッシュ・版・未確認点は [資料台帳](harness_information_flow_and_evaluation_sources_20261008.json) に保存した。PDF 頁は先頭を 1 とする物理頁である。

## 1. 開発への結論

個人情報を扱うハーネスでは、**内容を分類する処理、誰がどの処理を実行できるか決める認可、データの出所と閲覧者を引き継ぐ情報フロー制御を別々に持つ**必要がある。LLM が「安全」「この人へ送ってよい」と説明しても、その説明を認可の根拠にしない。分類結果は保護を強める手掛かりに使い、既存の機密区分や閲覧制限を自動で解除させない。これは本調査からの設計提案であり、以下の研究の標準機能を一括して指すものではない。

CaMeL は、道具の結果を命令として扱わないための研究として直接役立つ。2026 年 10 月の Multi-CaMeL は、親子エージェント間で信頼区分が消える問題を扱う。しかし、**その評価の機密性ポリシーは空であり、0% の攻撃成功率は個人情報の全送信先を保護した証明ではない**。形式的に証明された性質、公開実装で確認できる処理、有限個の試験結果を区別する。[CaMeL 全文](https://arxiv.org/pdf/2503.18813v2)、[Multi-CaMeL 全文 §IV–VI](https://arxiv.org/pdf/2610.05640v1)

また、これらは「平文を誰にも読ませない」秘密計算やゼロ知識証明ではない。出所ラベルだけで既知の機密情報を送信禁止にする場合は内容を毎回分類する必要がないが、文書が機密かどうかを初めて意味に基づいて決める処理は別途必要である。公開コードの CaMeL は非構造化の内容を Q-LLM へ平文で渡す。外部提供者への送信を避ける目的なら、その抽出モデルを組織が許可した局所環境へ置くなど、別の通信・実行境界を設ける必要がある。[query_quarantined_llm L39–103](https://github.com/google-research/camel-prompt-injection/blob/f083b6b396399d3b3c7f2ddaf613a5945eaf32d8/src/camel/quarantined_llm.py#L39-L103)

## 2. 混同しやすい保証

| 性質 | 意味 | それだけでは守れないもの |
|---|---|---|
| 内容の分類 | 人名、患者情報、機密案件などを検出する | 宛先の権限、分類漏れ、別経路の保存・送信 |
| 完全性のラベル | 情報が命令として信頼できる出所かを区別する | 内容の正しさ、閲覧できる相手の範囲 |
| 機密性のラベル | どの相手へ情報を渡せるかを保持する | 原本のラベル誤り、過大な公開指定 |
| 制御フロー完全性（CFI） | 実行が信頼された入力で決めた処理計画の範囲を守る | その計画内の分岐選択、許可されすぎた宛先・送金 |
| 情報の非干渉性 | 秘密・信頼できない入力を変えても、許されていない観測へ影響しない | 証明のモデル外にある通信、実装、明示的な機密解除 |
| 利用者・操作・対象の認可 | 特定の主体に、その時点で操作する権限があるかを判定する | 取得後の要約や別主体への二次送信 |
| OS による実行隔離 | ファイル、通信、子プロセス等のアクセスを制限する | 許可されたモデル API へ送る文面、認可済み道具の過大権限 |

「信頼できない」を「秘密」と同義にしない。公開ウェブ記事は公開でも命令として信頼できず、利用者自身の診断結果は正当な入力でも秘密である。この二軸を潰すと、機密情報を扱う許可と命令の信頼度が混ざる。[CaMeL §4](https://arxiv.org/pdf/2503.18813v2)、[LLMbda §5](https://arxiv.org/pdf/2602.20064v2)

## 3. CaMeL の実際の境界

論文は *Defeating Prompt Injections by Design*、arXiv:2503.18813v2、2025-06-24 改訂。125 頁の全文を保存した。公開実装は Google Research の `camel-prompt-injection`、固定コミット `f083b6b396399d3b3c7f2ddaf613a5945eaf32d8`。論文の結果と取得時のコードが完全に同一の実験版であるとは確認していない。

### 3.1 計画とデータを分ける

P-LLM は信頼された依頼から Python 風の計画を作り、Q-LLM は道具から得た文章を構造化する。独自の実行器が値の出所と許された閲覧者を追跡し、送信などの処理で規則を検査する。Q-LLM が誤った抽出値を返す可能性は残るため、構造化だけを正しさの保証にしない。[論文 §4–5、PDF pp.6–13](https://arxiv.org/pdf/2503.18813v2)

固定コードの `SecurityPolicyEngine.check_policy` は、副作用がないと登録した道具を先に許可し、秘密の制御依存を持つ副作用のある処理を拒否する。その後、登録順で**最初に名前が一致した規則の結果を返す**。一致しなければ拒否する。複数の規則を全て評価して拒否優先にまとめる一般的な認可処理ではない。`NoSecurityPolicyEngine` は常に許可するので、追跡機構の存在だけで強制検査が有効とは言えない。[security_policy.py L77–110](https://github.com/google-research/camel-prompt-injection/blob/f083b6b396399d3b3c7f2ddaf613a5945eaf32d8/src/camel/security_policy.py#L77-L110)

`NO_SIDE_EFFECT_TOOLS` には `query_ai_assistant` が含まれ、上記の規則では先に許可される。これは研究内のモデルを、通常の外部宛先の道具と同じ機密性検査で止める設計ではない。モデル提供者を許された閲覧者として別途管理する必要がある。[security_policy.py L51–68](https://github.com/google-research/camel-prompt-injection/blob/f083b6b396399d3b3c7f2ddaf613a5945eaf32d8/src/camel/security_policy.py#L51-L68)

実行器は道具の呼出し前に規則を検査し、検査例外はエラーへ変換する。外部道具の拒否結果なら例外を起こして当該呼出しを防ぐ。これは固定コードで確認した当該境界の停止処理であり、全ての障害が全会話を終える意味ではない。[interpreter.py L2048–2073](https://github.com/google-research/camel-prompt-injection/blob/f083b6b396399d3b3c7f2ddaf613a5945eaf32d8/src/camel/interpreter/interpreter.py#L2048-L2073)

銀行用の `send_money_policy` は、受取人の値が利用者に由来するかと、受取人が取引名目・金額・日付を読めるかを確認する。これは機密性と出所を使う具体例である。**受取人が利用者由来であることは、口座の操作権限や送金上限の完全な確認ではない**。本番では別の認可・残高・上限・二重送金防止の処理が必要になる。[banking.py L52–85](https://github.com/google-research/camel-prompt-injection/blob/f083b6b396399d3b3c7f2ddaf613a5945eaf32d8/src/camel/pipeline_elements/security_policies/banking.py#L52-L85)

### 3.2 非目標と暗黙的な漏れ

脅威モデルは利用者の依頼と記憶が侵害されていないと仮定する。§3.1 は、処理や情報の流れを変えない文章の改変、利用者が文書内の指示に従うよう明示した場合などを非目標として挙げる。したがって、誤った要約や全ての悪意ある文書を一般的に識別する分類器ではない。[PDF p.5](https://arxiv.org/pdf/2503.18813v2#page=5)

§7 は制御依存や例外を介する間接的な漏れを扱い、`STRICT` モードで依存関係を強める。秘密値に応じて例外が生じると、その後の通信の有無から情報を推測できる。**STRICT を有効にすれば任意の非干渉性が証明済み、とは書かれていない**。後述する 2026 年の研究は、未実行の分岐での代入と外部再試行について残る限界を具体的に指摘する。[CaMeL §7、PDF pp.19–21](https://arxiv.org/pdf/2503.18813v2#page=19)、[Multi-CaMeL §VI-B](https://arxiv.org/pdf/2610.05640v1#page=12)

固定コードの `check_policy` は、非公開の制御依存の `d.raw` を集めて拒否理由に埋め込む。実行器は、その理由を `SecurityPolicyDeniedError` の文章へ入れる。つまり、**拒否した処理の診断文そのものが秘密の原値を複製する具体的な経路**がある。これは理由と例外の構築を確認したものであり、全ての呼出し経路で外部へ漏洩すると断定するものではない。診断保存、表示、修復要求にも送信・保存検査を適用する必要がある。[security_policy.py L89–96](https://github.com/google-research/camel-prompt-injection/blob/f083b6b396399d3b3c7f2ddaf613a5945eaf32d8/src/camel/security_policy.py#L89-L96)、[interpreter.py L2061–2066](https://github.com/google-research/camel-prompt-injection/blob/f083b6b396399d3b3c7f2ddaf613a5945eaf32d8/src/camel/interpreter/interpreter.py#L2061-L2066)

固定実装のエラー整形は `is_trusted` に応じて例外文を隠し、そのエラーを計画モデルへ渡して再生成を求める。**信頼できる出所であることと、公開してよいことは別**なので、この書換えだけを全ての秘密値の除去と見なさない。修復要求もモデルへの送信として検査する。[privileged_llm.py L86–133](https://github.com/google-research/camel-prompt-injection/blob/f083b6b396399d3b3c7f2ddaf613a5945eaf32d8/src/camel/pipeline_elements/privileged_llm.py#L86-L133)、[再計画ループ L459–475](https://github.com/google-research/camel-prompt-injection/blob/f083b6b396399d3b3c7f2ddaf613a5945eaf32d8/src/camel/pipeline_elements/privileged_llm.py#L459-L475)

メール誤送信へ転用する際は、To/CC/BCC、件名、本文、添付の内容・名前を別々の値として保持し、正規化した宛先集合が全ての値の閲覧条件を満たすか検査する。利用者が入力した宛先でも権限があるとは限らない。送信直前に原本と権限の版を再確認する。この段落は設計提案であり、CaMeL の公開研究が Outlook/Gmail へそのまま実装しているとの主張ではない。

## 4. 2026 年 10 月の Multi-CaMeL

*Can CaMeLs Talk? Securing Multi-Agent Systems Against Indirect Prompt Injection Attacks*、arXiv:2610.05640v1、2026-10-05 公開、24 頁。査読済みと確認していない新しい研究である。

### 4.1 境界でデータが命令へ昇格する

親が道具の結果を文章へ埋め込んで子へ頼むと、各エージェントを個別に CaMeL 化していても、子の計画モデルがそれを信頼された命令として扱える。Multi-CaMeL は命令 `task` とデータ `variables` を分け、道具由来の値が命令側へ入る処理を拒否する。対象とする形式モデルは、親が子を道具として呼ぶ階層構造であり、循環、非同期の同等主体間通信、一般的なグラフへの保証は今後の課題である。[§III–VI、PDF pp.4–12](https://arxiv.org/pdf/2610.05640v1)

CFI は、信頼された計画にある分岐をデータが選ぶことを許す。この**分岐の誘導**は、観測できる出力に秘密の影響がないことを求める非干渉性より弱い。§VI-B は、現行 CaMeL 実行器が一部の暗黙依存を見落とし、Multi-CaMeL がその限界を継承すると明記する。また、公開実装では失敗後の再計画を避け、外部再試行による特定の漏れを防ぐ。全ての隠れた通信路を排除したことを意味しない。[PDF p.12](https://arxiv.org/pdf/2610.05640v1#page=12)

### 4.2 評価数値の読み方

| 項目 | 論文が報告する値 | 必ず添える条件 |
|---|---|---|
| MultiAgentDojo の平均攻撃成功率 | 防御なし 12.9%、個別 CaMeL 0.2%、Multi-CaMeL 0.0% | 5 モデルの非加重平均。モデル・設定ごと 949 の試験。**機密性の規則 S は空** |
| 0.0% の区間 | 各モデルについて 95% 区間 [0.0%, 0.4%] | 有限回の観測であり、将来の攻撃の確率を 0 と証明した値ではない |
| GPT-5.5、AssetOpsBench の正常課題成功率 | 87.5% → 82.1% → 79.5% | 防御なし → 個別 → Multi。141 課題から不可能な 29 を除いた 112 課題 |
| GPT-5.5、MultiAgentDojo の正常課題成功率 | 86.6% → 73.2% → 66.0% | 97 課題。基準から Multi への低下は 20.6 ポイント |
| Claude Fable 5、MultiAgentDojo | 全 97 課題で 69.1% → 52.6%、拒否例を除いた 45 課題で 91.1% → 84.4% | 拒否例を除いた分母の値だけで実運用の成功率を語らない |

[§IV-C、Table III、Appendix D、PDF pp.7、10、24](https://arxiv.org/pdf/2610.05640v1)。著者自身が防御なしの GPT-5.5 も当該試験で 0% であり、一般的な頑健性と解釈すべきでないと明記する。数値は当該論文の報告であり、この調査で再実行していない。

### 4.3 公開コードと外部サービス

著者の公開実装 `james-pete/multiagentdojo` を取得し、固定コミット `e71647382155dc6949d6ccf9a9d7ec7cf429b856` を確認した。これは元の AgentDojo の派生で、Google の実行器をそのまま埋め込んだ実装ではなく、**Sequrity Control API の Dual-LLM 実装を使う**。取得したコードから確認できるのは、通信手順・設定・規則の組立て・結果記録であり、サービス内部の実行器を全面監査したことにはならない。[README](https://github.com/james-pete/multiagentdojo/blob/e71647382155dc6949d6ccf9a9d7ec7cf429b856/README.md)

`_multicamel_orchestrator_policy` は `task.producers` が空でなければ `hard deny`、子の結果へ出所を付与する規則を生成する。子には `get_variable` を与え、命令と変数を別経路で渡す。変数は通常の Python 辞書の値であり、暗号化された値や型付きの全面的な閲覧権限証明ではない。[multi_agent.py L583–678](https://github.com/james-pete/multiagentdojo/blob/e71647382155dc6949d6ccf9a9d7ec7cf429b856/src/agentdojo/agent_pipeline/multi_agent.py#L583-L678)

`load_sequrity_headers` は単一計画、最大 P-LLM 手順 1、失敗手順 1 を設定する。コメントは、道具の結果を見た再計画が隔離を崩すため無効にしたと説明する。[sequrity_llm.py L54–89](https://github.com/james-pete/multiagentdojo/blob/e71647382155dc6949d6ccf9a9d7ec7cf429b856/src/agentdojo/agent_pipeline/llms/sequrity_llm.py#L54-L89)

さらに要求には会話本文、道具定義、外部提供者名、**上流のモデル API キー `llm_api_key`**、セッション ID を含め、`client.control.chat.create` へ渡す。モデル送信経路は Sequrity と指定された上流提供者という複数の主体を含む。導入時は鍵の委任範囲、サービスの保持、ログ、障害時挙動を個別に検証しなければならない。`uv.lock` は Sequrity 0.4.2 を固定するが、遠隔サービスの版・内部実装・保持条件まで固定しない。[sequrity_llm.py L315–397](https://github.com/james-pete/multiagentdojo/blob/e71647382155dc6949d6ccf9a9d7ec7cf429b856/src/agentdojo/agent_pipeline/llms/sequrity_llm.py#L315-L397)、[uv.lock L3534–3544](https://github.com/james-pete/multiagentdojo/blob/e71647382155dc6949d6ccf9a9d7ec7cf429b856/uv.lock#L3534-L3544)

## 5. LLMbda: 証明の強さと解除処理の限界

*The LLMbda Calculus: AI Agents, Conversations, and Information Flow*、arXiv:2602.20064v2、2026-07-10 改訂、63 頁。会話の分岐・消去、モデル生成コード、動的な情報フロー追跡を言語の操作として扱い、Lean による機械検査を伴う、終了の差を除いた確率的非干渉性を論じる。モデルの応答が常に正しいという仮定で保証する研究ではない。一方、証明の範囲と実環境の道具・通信を同一視しない。[全文 §3–6](https://arxiv.org/pdf/2602.20064v2)

機密性の解除と、信頼できないデータを命令に使ってよいと認める `endorse` を区別する。後者は用途に応じて必要でも、広く許せば攻撃者の指示を洗浄できる。§7.3 の 1,296 回中 2 回の成功は、文書の指示どおりに支払う課題で内容を承認した場合だった。つまり「誤った自然言語の依頼内容」を情報フローの正しさだけで判断できない。§9 は全データ源がプログラム内にあるモデル化、適切な出所ラベルと送信先での検査を行う信頼された道具群、過大な `endorse` の制限が今後の設計課題であることを明記する。[PDF pp.24、26](https://arxiv.org/pdf/2602.20064v2#page=24)

**検証状態:** 公式 [論文サイト](https://llmbdacalculus.github.io/) と、そのリンク先の [公式 GitHub 組織](https://github.com/llmbdacalculus) を確認し、GitHub 公開一覧も保存した。調査時点で取得できた同組織の公開リポジトリは論文サイトのみだった。Lean の実行器・証明を取得して再検査できる公開先は確認できていない。「公開されていない」と全世界について断定するものではなく、**本調査では論文の機械証明の主張をコード検証済みとしていない**。第三者の同名 Python パッケージや TypeScript 移植を著者の証明済み実装として代用しない。

## 6. 評価資料は何を測るか

| 一次資料 | 評価・分類の対象 | それだけでは保証できないもの |
|---|---|---|
| AgentDojo、arXiv:2406.13352v3 | ユーザー課題と攻撃者の目標を組み合わせた道具利用。正常時の成功率、攻撃下の正常成功率、攻撃目標の達成率を分ける | 実組織の全個人情報、モデル通信・保存の全経路、未知の適応的攻撃 |
| Agent Security Bench（ASB）、arXiv:2410.02644v4 | 10 の用途、10 エージェント、400 超の道具、23 の攻撃・防御方法等を組み合わせ、複数指標で比較する | 被害件数の世界的な傾向、実金融・医療システムの権限強制、製品の保証 |
| AgentDyn、arXiv:2602.03117v3 | 買物、GitHub、日常生活の 60 の開放的課題、560 の注入試験。動的な再計画と役に立つ第三者の指示を含む | 現実の完全な再現。著者は最新モデルに対して攻撃が比較的弱いことも限界に挙げる |
| *Simple Prompt Injection Attacks Can Leak Personal Data Observed by LLM Agents During Task Execution*、arXiv:2506.01055v1 | 架空の銀行会話・個人情報と AgentDojo 拡張。作業中に観測した情報の二次流出を測る | 実際の銀行導入事例、一般的な個人情報検出精度、すべての個人情報種別の網羅 |
| OWASP Top 10 for Agentic Applications 2026 | 自律的な道具利用・権限・記憶・供給網・他エージェントとの通信等のリスク分類と対策 | 攻撃成功率の測定、認証・法規準拠、事故の時系列分析 |

[AgentDojo §3.3–3.4](https://arxiv.org/pdf/2406.13352v3#page=6)、[ASB 全文](https://arxiv.org/pdf/2410.02644v4)、[AgentDyn 本文・Appendix A](https://arxiv.org/pdf/2602.03117v3)、[銀行データ流出研究](https://arxiv.org/pdf/2506.01055v1)、[OWASP 公式資料](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)

固定した AgentDojo 実装 `089ed468cf3ed0322acc66b0211f26d9d90dbf60` の評価は、課題ごとの `utility_from_traces` / `security_from_traces` を優先し、未定義なら最終文章と実行前後の環境で判定する。**security が真なら攻撃者の目標達成を意味する箇所がある**ため、名称だけ見て「安全率」と読まない。全文の指標の定義も、攻撃成功率と利用者課題成功率を別々に扱う。[task_suite.py L280–334](https://github.com/ethz-spylab/agentdojo/blob/089ed468cf3ed0322acc66b0211f26d9d90dbf60/src/agentdojo/task_suite/task_suite.py#L280-L334)

ASB の固定取得は `544540ff0788998072f7df463056fd17e62cc9f4`。集計コードは通常の ASR と「処理計画失敗を除いた ASR」を別々に記録する。同じ分母の数値とは限らない。拒否や計画失敗で攻撃を防いだ結果と、正常な仕事を遂行しながら防いだ結果を分ける必要がある。[res_retrieval.py L20–62](https://github.com/agiresearch/ASB/blob/544540ff0788998072f7df463056fd17e62cc9f4/scripts/res_retrieval.py#L20-L62)

銀行データ研究は、小さな課題集合で効いた防御が拡張課題で効かなくなる例を示す。内容の機密度によって漏れやすさも異なる。ローカル LLM / BERT / 規則処理の比較では「パスワードを出さなかった」だけで勝敗を決めず、氏名、連絡先、取引、組合せによる識別、変換後の情報について検査する。[銀行研究 §4–5、PDF pp.5–9](https://arxiv.org/pdf/2506.01055v1)

## 7. OWASP を漏れの経路へ対応させる

2026 版の分類名を保持し、日本語で対象を説明する。これは保護機構の実装有無を示す一覧ではなく、開発の点検項目へ対応させる提案である。

| OWASP 識別子・原題 | 点検する対象 |
|---|---|
| ASI01 Agent Goal Hijack | 外部文章が目的・命令へ昇格する経路 |
| ASI02 Tool Misuse and Exploitation | 道具名だけでなく引数・対象・操作量・副作用 |
| ASI03 Identity and Privilege Abuse | 利用者・エージェント・サービス主体の区別と認証情報の委任 |
| ASI04 Agentic Supply Chain Vulnerabilities | MCP、拡張、技能、モデル・ライブラリの供給元と更新 |
| ASI05 Unexpected Code Execution (RCE) | 生成コードの実行器、ホスト道具、子プロセス |
| ASI06 Memory & Context Poisoning | 記憶・要約・キャッシュの出所と失効 |
| ASI07 Insecure Inter-Agent Communication | 親子間の命令・データ分離、出所・閲覧者の保持 |
| ASI08 Cascading Failures | 誤り・タイムアウト・部分成功が次の処理へ伝播する条件 |
| ASI09 Human-Agent Trust Exploitation | 承認画面に実際の対象・宛先・データ区分が見えるか |
| ASI10 Rogue Agents | 操作の上限、停止、利用目的から逸脱した継続 |

[OWASP 公式 57 頁 PDF](https://genai.owasp.org/download/52117/?tmstv=1765059207)。分類の対応付けだけで認可・内容検査・OS 隔離・通信検査のどれかを省略できるものではない。

## 8. OpenFGA / Cedar / OPA と LLM を分ける

既存の [企業データの認可・監査・説明可能性調査](enterprise_data_authorization_audit_xai_20261006.md) の「検索前の認可」「派生物へ権限を引き継ぐ」「失効をキャッシュへ反映」「検出器と認可方針の所有者を分ける」を再確認した。以下は、その方針を呼出しと失敗条件へ具体化する補足である。

| 仕組み | LLM から分離する処理 | 失敗・更新時の注意 |
|---|---|---|
| OpenFGA | 利用者・組織・文書等の関係から `Check` で閲覧・操作権限を判定する | 認可モデルは不変の版。`authorization_model_id` を指定しなければ最新モデルを使う。既定 `MINIMIZE_LATENCY` はキャッシュを利用し得る。`HIGHER_CONSISTENCY` はキャッシュを迂回して保存層へ問い合わせる |
| Cedar | 主体・操作・対象・文脈（PARC）で属性と関係を判定する | 既定拒否・forbid 優先だが、**評価エラーの規則は飛ばす**。壊れた forbid と成立する permit が併存すれば許可され得る。診断のエラーも検査し、厳格なアプリ側で拒否する設計が必要 |
| OPA | Rego 方針で構造化された入力を評価する | `default allow := false` 等を明示する。文書 API の未定義の判断は HTTP 200 でも `result` が存在しない場合がある。HTTP 成功を許可と見なさず、明確な真値だけを許可する |

[OpenFGA モデル固定](https://openfga.dev/docs/getting-started/immutable-models)、[一致性の指定](https://openfga.dev/docs/interacting/consistency)、[Cedar 認可仕様](https://docs.cedarpolicy.com/auth/authorization.html)、[Cedar の安全な統合](https://docs.cedarpolicy.com/other/security.html)、[OPA REST API](https://www.openpolicyagent.org/docs/rest-api)、[Rego 言語](https://www.openpolicyagent.org/docs/policy-language)

OpenFGA の高一致性指定を、特定の分散保存層での失効伝播時間や全処理の単一トランザクションを保証する言葉へ拡張しない。実際に権限を書き込む経路と読み取る保存層、複製、アプリ側キャッシュも確認する。

Cedar の schema 検査は重要だが、要求・実体データも schema と整合していることが前提であり、schema 変更時は方針の再検査が必要になる。「既定拒否だから方針の実行エラーでも必ず全体が拒否する」と説明しない。[Cedar security considerations](https://docs.cedarpolicy.com/other/security.html)

OPA の判断ログは入力・結果を記録でき、`data.system.log.mask` 等で入力や結果を削除・置換できる。認可へ本文を渡すほど、そのログが別の機密情報経路になる。入力を利用者 ID・文書 ID・操作・目的・区分等へ縮小し、方針診断や理由にも原文を含めない。[OPA 判断ログ](https://www.openpolicyagent.org/docs/management-decision-logs)

これらの認可器は、LLM が見た全文・要約の出所を自動で追跡する機構ではない。検索の前に許可を求め、生成物に原本と方針の版を結び付け、モデル・ログ・メール・外部道具の送信前にも該当する主体と対象で再判定する。認可器へ渡す利用者 ID や区分を LLM の自由な文字列だけから作らず、信頼された認証と業務台帳から得る。

## 9. 個人情報ハーネスの設計案

以下は研究を組み合わせた提案であり、既存製品が全項目を既定で提供するとの主張ではない。

1. **取得前:** 信頼された利用者・組織・目的と、文書 ID に対して認可する。本文、添付、画像、検索結果、道具の説明、記憶等を別々の入力源として扱う。
2. **取得時:** 各値へ原本 ID、版、機密区分、許された閲覧者、命令としての信頼度を付ける。内容分類の失敗・未確定は保護を解除しない。
3. **モデル呼出し前:** 主モデル、抽出、画像、検索補助、子エージェント、キャッシュ向けの全要求を一つの通信出口で検査する。Q-LLM に原文を渡すなら、その主体も許された閲覧者であるか確認する。
4. **実行時:** 道具名・操作・対象・金額等の制約を構造化して照合する。生成コードは限定した実行器から、共通の認可経路を通る道具だけを呼べるようにする。ホスト OS への直接アクセスを別に封じる。
5. **親子間:** 命令を信頼された入力だけで作り、道具由来のデータは別の変数経路で渡す。結果へ出所と閲覧者を保持する。原文を子への依頼文へ埋め直さない。
6. **出力・副作用前:** 本文、宛先、添付、HTTP 要求、例外、途中結果を同じ規則で検査する。送金・送信等は作成と実行を分け、承認後も対象と版が一致することを確認する。
7. **保存時:** 記憶、要約、埋込み、判断ログ、道具の引数と details を機密情報の保管先として管理する。派生物を公開扱いにしない。失効時は再取得だけでなく派生物とキャッシュも使えなくする。
8. **失敗時:** 方針が欠落、診断にエラー、出所が不明、検査が時間切れ、書換えが不正、認証が失効の場合は当該処理を拒否する。原文や未検査値へ戻る挙動を禁止する。再試行は出所と認可を保持し、特権モデルへ原文を渡して修復しない。

メールでは CC の一人でも条件を満たさなければ送信を止める。公開 LLM へ送る匿名化文の作成と、原文メールの送信は別の操作として認可する。匿名化された文字列でも、内容・時刻・少人数の集団との組合せで個人が特定できる場合があるため、識別子の置換のみで無条件に公開しない。

## 10. 自社での受入評価

今回は以下の試験を実行していない。架空のデータで、安全性と正常業務を同時に測るための提案である。

| 試験群 | 調べること | 合格条件の例 |
|---|---|---|
| 内容分類 | 明示的識別子、自由文章、画像、他情報との組合せ、公開情報と秘密の区別 | 区分ごとの検出漏れと過検出を報告。全体 accuracy だけで済ませない |
| 出所保持 | 引用・要約・翻訳・分岐・例外・親子・記憶・再試行 | 派生物から原本・区分・閲覧者を追える。欠落なら拒否 |
| 認可失効 | 取得後・承認後・送信前に権限を失う場合 | 古い認可キャッシュや要約で送信・検索を継続しない |
| 障害 | 検査器の例外・時間切れ、不正結果、認可の未定義、壊れた拒否方針 | 原文・未検査値をモデル・ログ・外部へ送らない |
| 副作用 | CC/BCC、添付、同名宛先、送金上限、二重実行 | 宛先集合・操作の制限が実際の送信・実行に一致 |
| 非モデル経路 | MCP、拡張、直接 HTTP、子プロセス、ログ、途中表示 | 共通の認可・送信検査を迂回しない |
| 正常業務 | 認可された引用、第三者の役立つ説明、動的な再計画 | 拒否率、課題成功率、遅延、介入回数を保護効果と並べて示す |

攻撃成功率には対象情報・送信先・操作・分母を明示する。防御が拒否した割合、正常課題の成功率、攻撃下の正常成功率、検出漏れ、過検出、試験回数と信頼区間を別々に残す。ベンチマークの固定攻撃で 0 件でも、設計上の全経路強制と未知の攻撃への保証の代わりにしない。

## 11. 証拠・未確認点と既存調査への訂正

- 全文 PDF 8 件と公式文書、公開コード 4 リポジトリを保存した。CaMeL と MultiAgentDojo の主要境界、AgentDojo と ASB の判定・集計を静的に照合した。ライブラリや遠隔モデルを動かしていない。
- Multi-CaMeL の論文は新しい予稿である。公開実装は取得できたが、遠隔 Sequrity の実行器・同時実行・エラー時処理・データ保持・秘密鍵の保存は本調査で確認できていない。
- LLMbda の Lean 証明と実行器の公開取得先は確認できていない。公式サイトと一覧の確認に留まり、論文の保証を再証明したものではない。
- OpenFGA/Cedar/OPA は公式仕様・文書の確認であり、実運用の保存層・設定・全実装・提供サービスの監査ではない。
- 医療・銀行での実稼働事例と、架空データを使う研究を区別した。今回の CaMeL/銀行ベンチマークを、病院・銀行が導入済みの証拠として扱わない。
- [ハーネスのガードレール機構調査](harness_guardrail_mechanisms_20261008.md) §8 の CaMeL 説明を補強する点: ①平文を抽出モデルへ渡す、②Multi-CaMeL の評価は空の機密性規則、③階層構造・暗黙依存・再試行の限定、④公開調整コードと商用遠隔実行器の区別、⑤LLMbda の公開コード再検査未完了。この補足は元稿の対象領域を否定せず、保証の範囲を狭く正確にする。


## 12. 独立レビューと改善確認

[root による独立レビュー](harness_review_root_to_information_flow_20261008.md) で、Multi-CaMeL の規則・保証・試験分母、LLMbda の残留例と限界、Cedar/OPA の失敗時処理、Sequrity の送信と再計画、CaMeL の規則を一次資料と再照合した。重要な訂正事項はなかった。補足指摘に基づき、CaMeL の拒否理由が `d.raw` を複製して例外へ入れる具体例を §3.2 に追加し、診断・修復要求も保護対象にした。用語は「道具」へ統一した。レビューは静的な境界確認であり、遠隔サービスの内部監査や実行時の安全性保証を意味しない。
