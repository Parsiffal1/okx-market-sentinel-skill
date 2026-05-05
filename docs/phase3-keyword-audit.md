# Phase 3 Keyword Audit

## Scope

This audit reviews Phase 3 rule keywords for:
- macro / central bank / inflation / employment
- geopolitics / sanctions / shipping / energy shock
- US-equity sentiment proxies relevant to crypto
- crypto-related public equities / ETF proxies
- exclusion / noise keywords

Method:
1. Read current `config/phase3_rules.yaml`
2. Run online research in parallel for macro, geopolitics, and US-equity/crypto-proxy terms
3. Review each keyword independently
4. Keep only terms with good signal-to-noise for a rule-based monitor

---

## A. Macro / central bank / inflation / employment

### Keep / add
| Keyword | Decision | Reason |
|---|---|---|
| FOMC | KEEP | Core Fed event keyword; high macro signal |
| 美联储 / Fed / Federal Reserve | KEEP | Canonical central-bank entity |
| 鲍威尔 / Powell | KEEP | Chair comments move USD/rates/crypto |
| CPI | KEEP | Top-tier inflation release |
| 核心CPI / core CPI | KEEP | Often more market-moving than headline |
| PCE | KEEP | Fed-preferred inflation gauge |
| 核心PCE / core PCE | KEEP | Important for Fed reaction function |
| PPI | KEEP | Pipeline inflation signal |
| 非农 / NFP / nonfarm payrolls | KEEP | Top-tier labor event |
| 失业率 / unemployment rate | KEEP | Cleaner than generic `失业` |
| 初请失业金 / jobless claims | KEEP | Frequent labor-market signal |
| 时薪 / average hourly earnings / AHE | KEEP | Wage inflation sensitivity |
| JOLTS / 职位空缺 | KEEP | Labor tightness signal |
| ADP | KEEP | Lower than NFP but still relevant |
| GDP | KEEP | Core growth release |
| PMI | KEEP | Core growth / activity release |
| ISM | KEEP | Often more market-moving than generic PMI |
| 制造业PMI / 服务业PMI | KEEP | Better than plain PMI in some headlines |
| 零售销售 / retail sales | KEEP | Demand strength / macro-financial relevance |
| 通胀 | KEEP | Broad but still useful umbrella term |
| 降息 / rate cut | KEEP | Direct policy direction |
| 加息 / rate hike | KEEP | Direct policy direction |
| 维持利率不变 / hold rates | KEEP | Policy pause matters |
| 点阵图 / dot plot | KEEP | High-signal Fed-path guidance |
| 会议纪要 / minutes | KEEP WITH CONTEXT | Useful if Fed/央行 context present |
| 杰克逊霍尔 / Jackson Hole | KEEP | High-signal macro event |
| QE / 量化宽松 | KEEP | Liquidity expansion signal |
| QT / 缩表 / quantitative tightening | KEEP | Liquidity drain signal |
| DXY / 美元指数 | KEEP | Strong cross-asset risk signal |
| 美债收益率 / Treasury yield | KEEP | Important macro-financial transmission term |
| 2年期美债收益率 / 2Y yield | KEEP | Fed-path sensitive |
| 10年期美债收益率 / 10Y yield | KEEP | Discount-rate / risk signal |
| 实际收益率 / real yields | KEEP | Important BTC/gold-type reaction channel |
| 收益率曲线 / yield curve | KEEP | Recession/liquidity readthrough |
| 收益率倒挂 / curve inversion | KEEP | Strong regime signal |
| 金融条件 / financial conditions | KEEP | Macro-financial tightening/easing phrase |
| ECB / 欧洲央行 | KEEP | Major global liquidity/rates driver |
| 英国央行 / BOE | KEEP | Secondary but still relevant |
| 日本央行 / BOJ | KEEP | Global carry/liquidity relevance |
| YCC / 收益率曲线控制 | KEEP | Key BOJ policy term |
| PBOC / 中国央行 / 人民银行 | KEEP | Regional liquidity relevance |
| 降准 / RRR cut | KEEP | China easing signal |

### Reject / remove / downgrade
| Keyword | Decision | Reason |
|---|---|---|
| 美元 | REJECT / DOWNGRADE | Too broad; creates false positives from money amounts |
| 利率 | DOWNGRADE | Too broad without policy context |
| 收益率 | DOWNGRADE | Too broad unless tied to Treasury / 美债 |
| 失业 | REJECT | Too vague; prefer `失业率` / `初请失业金` |
| 就业 | REJECT | Too broad |
| 央行 | REJECT | Too generic without specific bank |
| 经济 | REJECT | Very noisy |
| 市场 | REJECT | Meaningless alone |
| 风险 | REJECT | Too broad |
| 鸽派 / hawkish / dovish | REJECT standalone | Too commentary-heavy without CB context |
| 消费 | REJECT | Too broad; prefer `零售销售` / `消费者支出` |
| 工资 | REJECT | Too broad; prefer `时薪` |

---

## B. Geopolitics / sanctions / shipping / energy shock

### Keep / add
| Keyword | Decision | Reason |
|---|---|---|
| 战争 | KEEP | Core escalation term, but better with context |
| 开战 / 宣战 | KEEP | Stronger than generic war references |
| 空袭 | KEEP | Useful escalation term |
| 大规模袭击 | KEEP | High-severity escalation |
| 报复性打击 / 报复行动 | KEEP | Escalation cycle continuation |
| 直接参战 | KEEP | High-signal escalation |
| 地面进攻 / 地面行动 | KEEP | Stronger than vague military action |
| 动员 / 总动员 | KEEP | Sustained escalation |
| 无人机袭击 | KEEP | Common modern escalation marker |
| 弹道导弹 / 巡航导弹 | KEEP | Better than generic `导弹` |
| 制裁 | KEEP WITH CONTEXT | Important, but better qualified than standalone |
| 二级制裁 | KEEP | High-signal sanctions implementation |
| 石油禁运 / 禁运 | KEEP | Energy-market macro relevance |
| 出口管制 | KEEP | Persistent economic warfare term |
| 资产冻结 | KEEP | Financial system impact |
| SWIFT制裁 | KEEP | Very high financial-system relevance |
| 关税 | KEEP WITH CONTEXT | Useful especially for US trade-policy macro shocks |
| 报复性关税 | KEEP | More specific than plain tariff |
| 航运中断 | KEEP | Direct shipping/trade disruption |
| 原油运输中断 | KEEP | Direct oil shock |
| 油轮遇袭 / 商船遇袭 | KEEP | High-signal shipping disruption |
| 扣押油轮 / 扣押商船 | KEEP | Persistent maritime disruption |
| 海上封锁 / 港口关闭 | KEEP | Chokepoint / trade impact |
| 霍尔木兹 / 霍尔木兹海峡 | KEEP | Core oil chokepoint |
| 红海 / 红海航运 | KEEP | Important shipping-risk geography |
| 曼德海峡 / 巴布-曼德海峡 | KEEP | Chokepoint relevance |
| 苏伊士运河 | KEEP | Global trade route relevance |
| 航运改道 / 停航 | KEEP | Practical disruption signal |
| 战争风险保险 / 保险费飙升 | KEEP | Confirms persistent stress |
| 油田遇袭 / 炼油厂遇袭 | KEEP | Direct supply shock |
| 输油管道中断 / 管道爆炸 | KEEP | Energy supply impairment |
| LNG供应中断 / 天然气供应中断 | KEEP | Global macro spillover |
| 战略石油储备释放 | KEEP | Downstream energy-shock confirmation |
| 油价飙升 / 原油暴涨 | KEEP | Shock confirmation |
| 核设施遇袭 | KEEP | Strategic escalation |
| 核试验 | KEEP | Very high severity |
| 战术核武 / 核威胁 | KEEP | Severe strategic-risk marker |
| 伊朗 / 以色列 / 俄罗斯 / 乌克兰 | KEEP | Still needed as core regional anchors |
| 胡塞武装 / 也门胡塞 | KEEP | Red Sea shipping-risk relevance |
| 真主党 | KEEP | Regional conflict escalation relevance |
| 哈马斯 | KEEP | Regional conflict relevance |
| 伊朗革命卫队 / IRGC | KEEP | Military + sanctions relevance |

### Reject / remove / downgrade
| Keyword | Decision | Reason |
|---|---|---|
| 谈判 | REJECT | Too routine, often low signal |
| 停火 | DOWNGRADE | Too ambiguous unless paired with `破裂/失败/终止` |
| 冲突 | REJECT | Too broad |
| 施压 | REJECT | Diplomatic noise |
| 爆炸 | REJECT | Too generic |
| 袭击 | DOWNGRADE | Better if actor/location-qualified |
| 核 | REJECT | Too broad |
| 封锁 | DOWNGRADE | Better as `海上封锁` / `港口关闭` / `霍尔木兹封锁` |
| 军事行动 | DOWNGRADE | Vague |
| 警告 / 谴责 / 声明 | REJECT | Diplomatic/media filler |
| 紧张局势 / 危机 | REJECT | Commentary-heavy, weak precision |

---

## C. US-equity sentiment proxies relevant to crypto

### Keep / add
| Keyword | Decision | Reason |
|---|---|---|
| 美股 | KEEP | Broad risk sentiment umbrella |
| 美股开盘 / 美股收盘 | KEEP | Important correlation windows |
| 美股盘前 / 盘前 | KEEP | Premarket spillover matters |
| 美股盘后 / 盘后 | KEEP | After-hours reaction channel |
| 盘初 / 尾盘 / 盘中 / 午盘 | KEEP | Intraday regime markers |
| 高开 / 低开 / 冲高回落 / 跳水 / 反弹 | KEEP | Useful sentiment descriptors |
| 美股期货 / 股指期货 | KEEP | Premarket proxy |
| 纳斯达克 / 纳指 / 纳斯达克100 / Nasdaq / NDX | KEEP | Strong crypto-beta proxy |
| 纳指期货 / NQ / NQ1! | KEEP | Strong futures proxy |
| 标普500 / S&P 500 / SPX | KEEP | Broad risk proxy |
| 标普期货 / ES / ES1! | KEEP | Futures proxy |
| SPY | KEEP | Broad ETF proxy |
| QQQ | KEEP | Tech/growth proxy strongly relevant to crypto |
| VIX / 恐慌指数 / 波动率指数 | KEEP | Useful inverse-risk indicator |
| Russell 2000 / 罗素2000 / IWM / RUT | KEEP | Secondary high-beta proxy |
| 三大股指 | KEEP | Common summary language |

### Reject / remove / downgrade
| Keyword | Decision | Reason |
|---|---|---|
| 道指 / DIA / DJIA | OPTIONAL / DOWNGRADE | Less useful for crypto than NQ/QQQ/SPX |
| 单独科技七巨头泛提法 | REJECT | Too broad and noisy |

---

## D. Crypto-related public equities / ETF proxies

### Keep / add
| Keyword | Decision | Reason |
|---|---|---|
| MSTR / Strategy / MicroStrategy | KEEP | Core BTC proxy equity |
| COIN / Coinbase | KEEP | Core crypto infrastructure equity |
| CRCL / Circle / CIRCLE | KEEP | Important stablecoin / crypto-market-structure equity |
| BMNR | KEEP | Explicitly desired project tracking target |
| HOOD / Robinhood | KEEP | Retail crypto-trading beta |
| MARA / Marathon Digital | KEEP | Major listed miner proxy |
| RIOT / Riot Platforms | KEEP | Major listed miner proxy |
| CLSK / CleanSpark | KEEP | Major miner proxy |
| CIFR / Cipher Mining | KEEP | Miner basket signal |
| HUT / Hut 8 | KEEP | Crypto infra/miner relevance |
| IREN / Iris Energy | KEEP | Crypto infra / miner relevance |
| BTDR / Bitdeer | KEEP | Direct crypto-linked public equity |
| CORZ / Core Scientific | KEEP | Major listed infra name |
| WULF / TeraWulf | KEEP | Crypto miner basket relevance |
| BITF / Bitfarms | KEEP | Crypto miner basket relevance |
| IBIT / FBTC / ARKB / BITB / HODL / GBTC | KEEP | BTC ETF flow/sentiment proxies |
| ETHA / FETH | KEEP | ETH ETF flow/sentiment proxies |
| 比特币ETF / 现货比特币ETF / 以太坊ETF / 现货以太坊ETF | KEEP | Phrase-level ETF capture |

### Reject / remove
| Keyword | Decision | Reason |
|---|---|---|
| 苹果 / Apple / AAPL | REJECT | Not a reliable crypto sentiment proxy |
| 英伟达 / NVIDIA / NVDA | REJECT | AI/semis driver, too indirect |
| TSLA / Tesla | REJECT | Occasional crypto link but inconsistent |
| MSFT / AMZN / GOOGL / META | REJECT | Broad mega-cap noise |
| AMD / SMCI / TSM / SOXX | REJECT | Too indirect for crypto ruleset |
| NFLX / PLTR | REJECT | Not crypto-specific |
| PYPL | REJECT | Too weak/inconsistent now |
| JPM / GS / BAC / WFC | REJECT in base list | Too broad unless doing banking/regulation-specific tracking |

---

## E. Promo / media CTA / weak noise exclusions

### Keep in exclude list
| Keyword | Decision | Reason |
|---|---|---|
| 立即观看 | KEEP EXCLUDE | Media CTA noise |
| 正在讲解中 | KEEP EXCLUDE | Media CTA noise |
| 直播 | KEEP EXCLUDE | Media CTA noise |
| Google Drive / AI概览 | KEEP EXCLUDE | Non-market noise |
| A股 / 港股 / 创业板 / 科创板 | KEEP EXCLUDE | Too unrelated for crypto macro layer |
| 恒生科技指数 | KEEP EXCLUDE | Usually not core US-crypto proxy in this project |
| 股票评级 | KEEP EXCLUDE | Analyst noise |
| 印度股票 | KEEP EXCLUDE | Too broad / off-target |
| HKMA / HIBOR / 离岸人民币同业拆息 | KEEP EXCLUDE | Too region-specific / noisy for current objective |
| 纽约期银 / 沪银 / 钯 / 铂 / 多晶硅 / 工业硅 | KEEP EXCLUDE | Commodity noise not central to crypto macro monitoring |
| 地级市 / 杭州 / 深圳 / 广州 / 成都 / 苏州 / 广东 | KEEP EXCLUDE | Domestic regional noise |

---

## Recommended cleanup to current list

### Strong candidates to remove or downgrade from current config
- `美元` → remove from relevance list or downgrade heavily
- `利率` → keep only because combined logic exists; avoid treating it as enough by itself
- `收益率` → keep, but prefer explicit treasury-yield terms elsewhere
- `谈判`
- `冲突`
- `施压`
- `爆炸`
- `袭击`
- `核`
- `封锁`
- `军事行动`
- `停火` (keep only if paired in logic or move to lower-confidence set)

### Strong candidates to add
- `核心CPI`
- `核心PCE`
- `NFP`
- `失业率`
- `初请失业金`
- `时薪`
- `JOLTS`
- `ISM`
- `零售销售`
- `点阵图`
- `杰克逊霍尔`
- `QE`
- `QT`
- `DXY`
- `实际收益率`
- `2年期美债收益率`
- `10年期美债收益率`
- `美股期货`
- `盘前`
- `盘后`
- `VIX`
- `纳指期货`
- `标普期货`
- `IBIT`
- `ETHA`
- `HOOD`
- `MARA`
- `RIOT`
- `CLSK`
- `BTDR`
- `红海`
- `苏伊士运河`
- `曼德海峡`
- `油轮遇袭`
- `商船遇袭`
- `二级制裁`
- `石油禁运`
- `SWIFT制裁`
- `炼油厂遇袭`
- `核设施遇袭`
- `胡塞武装`
- `真主党`
- `伊朗革命卫队`

---

## Notes
- English ticker matching should use safer token-aware logic to avoid false positives like `COIN` matching `Bitcoin`.
- Macro relevance should prefer event-linked phrases over broad nouns.
- Geopolitical keywords should bias toward escalation, sanctions implementation, chokepoints, and energy-supply disruption instead of generic diplomacy.
- US-equity sentiment keywords should focus on crypto beta proxies rather than unrelated single-stock chatter.
