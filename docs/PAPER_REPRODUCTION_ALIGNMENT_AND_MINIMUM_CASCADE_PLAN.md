# Paper reproduction alignment and minimum cascade plan

## 1. 鐩爣璁烘枃韬唤涓庡師濮嬭祫鏂欑姸鎬?

- 棰樺悕锛氥€婇珮姣斾緥椋庣數绯荤粺杩為攣鏁呴殰鍒嗘瀽涓庢姂鍒舵帾鏂界爺绌躲€?
- 浣滆€咃細璁镐綉娆?
- 绫诲瀷锛氬崕鍖楃數鍔涘ぇ瀛︿笓涓氱澹浣嶈鏂?
- 绛旇京鏃堕棿锛?024 骞?5 鏈?
- 鍘熷 PDF锛氭湰鍦版枃浠跺瓨鍦紝SHA-256 璁板綍浜?source manifest锛?3 椤靛潎鏈夊彲鎻愬彇鏂囨湰灞傘€?
- `paper_source_status = available_primary_paper_source`

## 2. 褰撳墠椤圭洰鐨勪弗鏍煎鐜拌竟鐣?

褰撳墠 PNNL 39-bus / 3IBR / DFIG trial 涓嶆槸璁烘枃绯荤粺鐨勪竴姣斾竴澶嶇幇銆傛嫇鎵戞棌銆?
涓€涓?Type-3 DFIG 鍜岃嫢骞蹭簨浠舵帴鍙ｅ叿鏈夌粨鏋勫榻愪环鍊硷紝浣嗘瘝绾挎浛鎹€佹簮鍙傛暟銆佹晠闅?
閰嶇疆銆佺嚎璺繚鎶ゃ€佸噺杞姐€佸父瑙勬満缁勪繚鎶ゅ拰琛ュ伩璁惧鍧囨湭閫愰」澶嶇幇銆?

## 3. 璁烘枃浜嬫晠閾炬満鍒舵媶瑙?

璁烘枃鐩存帴缁欏嚭涓ょ鏈哄埗銆備笌褰撳墠 DFIG 鍩虹璁炬柦鏈€鎺ヨ繎鐨勬槸鑴辩綉涓诲閾撅細

`鍒濆涓夌浉鐭矾 -> PCC 鐢靛帇鎵板姩 -> 椋庢満鐢靛帇绌胯秺澶辫触/鑴辩綉 -> 鍔熺巼缂洪 -> 娼祦澶у箙杞Щ -> 绾胯矾杩囪礋鑽峰€欓€?-> 绾胯矾寮€鏂?-> 鍑忚浇/鍏朵綑椋庢満鎴栨満缁勪繚鎶銆?

杩囪浇涓诲閾惧垯浠庣煭璺仮澶嶉樁娈电殑绾胯矾杩囪浇鍜屽紑鏂紑濮嬶紝鍐嶆帹鍔ㄦ洿澶氭疆娴佽浆绉汇€?
婧愯嵎淇濇姢鍜岃В鍒椼€傝鏂囨槑纭彁閱掑浘绀轰簨浠跺苟闈炰弗鏍煎崟鍚戝洜鏋溿€?

## 4. 褰撳墠妯″瀷宸插叿澶囩殑鍩虹璁炬柦

宸插璁★細DFIG LVRT 涓庢湰鍦拌劚缃戦摼銆両BR2/IBR3 trial-only 鏈湴寮€鏂帴鍙ｃ€佷笁婧?
event packet銆乧ollector銆乧hronology锛屼互鍙婁笁婧?V/P/Q monitor-only 璁板綍銆?
褰撳墠涓夋潵婧愬彈鎺ф椂搴忎笌 V/P/Q Run 灞炰簬鍩虹璁炬柦楠岃瘉鍜岃褰曟€у姩鎬佽瘉鎹紱瀹冧滑
涓嶆瀯鎴愯鏂囩殑鑷劧杩為攣鏁呴殰澶嶇幇銆?

## 5. 褰撳墠妯″瀷涓庤鏂囩殑閫愰」宸窛鐭╅樀

瀹屾暣鐭╅樀瑙?`data/reference/paper_reproduction_alignment_matrix.csv`銆傚垎绫昏鏁帮細
{"partially_aligned": 5, "structurally_aligned_adaptation": 1, "missing": 9, "contradicted": 1}銆傚叧閿缂哄彛鏄細娌℃湁闈㈠悜鐪熷疄杈撶數鏀矾鐨?
P/Q/I/璐熻浇鐜囬€氶亾锛屽洜鑰屾棤娉曡瀵熲€滄簮鑴辩綉/鏁呴殰 -> 娼祦閲嶅垎甯?-> 鏀矾杩囪浇鈥濅紶鎾摼銆?

## 6. 褰撳墠鏈€瀹夊叏鐨勯」鐩懡鍚?

`controlled-interface validation scaffold`

涓嶈兘浣跨敤 `strict paper reproduction`銆傚湪瀹屾垚绾胯矾涓庝繚鎶ゆ満鍒跺墠锛屼篃涓嶅疁鎶婂綋鍓?
宸ョ▼绉颁负瀹屾暣鐨?`partial mechanism reproduction`銆?

## 7. 鏈€灏忚鏂囧紡浜嬫晠閾惧€欓€夋柟妗?

棣栭€夊€欓€変负璁烘枃琛?2-2 / 鍥?3-4 鏀寔鐨勮劚缃戜富瀵奸摼銆傚綋鍓?DFIG LVRT 鍙壙鎺ョ涓€
淇濇姢鍔ㄤ綔锛屼絾缃戠粶浼犳挱閾剧己灏戠湡瀹炵嚎璺娴嬨€傜幇鏈夊浐瀹?DFIG -> IBR2 -> IBR3
瀹氭椂搴忓垪浠呬负 `controlled interface-validation sequence`锛屼笉鏄?paper cascade chain銆?

## 8. 涓嬩竴闃舵鍞竴鎺ㄨ崘

`next_stage = branch observability only`

鍙鍔犵洰鏍囩嚎璺殑 P/Q/I/璐熻浇鐜?monitor-only 杈撳嚭锛涗笉鎺ユ柇璺櫒锛屼笉澧炲姞 relay銆?
璇ラ『搴忕敱 E003銆丒010銆丒012 鐩存帴鏀寔锛氳鏂囨妸娼祦閲嶅垎甯冨拰绾胯矾杩囪礋鑽风疆浜庨鏈?
鑴辩綉鍚庣殑浼犳挱鐜妭锛岃€?CAP03 璇佹槑褰撳墠鎭扮己灏戣繖涓€鍙娴嬫ˉ姊併€?

鏆傜紦 shadow UVRT锛氬綋鍓嶅凡鏈?DFIG LVRT 鏈湴閾撅紝涓嬩竴澶勮鏂囨満鍒剁己鍙ｅ湪缃戠粶渚с€?
鏆傜紦 overload shadow relay锛氬皻鏃犲彲杩芥函绾胯矾閲忋€佺洰鏍囩嚎璺竟鐣屽拰楠岃瘉杈撳叆銆?
鏆傜紦榛樿鍩虹嚎 Run锛氶噸澶?Run 涓嶈兘琛ラ綈缂哄け鐨勭嚎璺祴閲忔帴鍙ｃ€?

## 9. 褰撳墠涓嶈兘鍋氱殑浜嬫儏

涓嶈兘鎶婂畾鏃跺紑鏂啓鎴愯嚜鐒剁骇鑱旓紱涓嶈兘鎶婃湭鏉?shadow 璁捐鍐欐垚宸插疄鐜颁繚鎶わ紱涓嶈兘
鍦ㄧ己灏戠嚎璺娴嬫椂杩炴帴绾胯矾鏂矾鍣紱涓嶈兘鍏堝姞鍏?SVC/STATCOM 骞跺绉版姂鍒舵晥鏋溿€?

## 10. 缁撹杈圭晫

鏈疆浠呭畬鎴愬師璁烘枃璇佹嵁鐧昏銆佸綋鍓嶆ā鍨嬮潤鎬佺洏鐐广€侀€愰」宸窛鏄犲皠涓庢渶灏忎簨鏁呴摼
璁捐銆傚悗缁缓妯″簲鐢辫鏂囦腑鏄庣‘鐨勨€滄晠闅溾€斾繚鎶も€旂綉缁滈噸鍒嗗竷鈥斿悗缁繚鎶も€濋摼鏉?
鍐冲畾銆傛湰杞病鏈変慨鏀?PSCAD銆佹病鏈?Build銆佹病鏈?Run锛屼篃娌℃湁楠岃瘉鑷劧绾ц仈銆?
鐗╃悊鍥犳灉銆佺ǔ瀹氭€с€佷繚鎶ゅ崗璋冦€佺數鍘嬫敮鎾戞垨 MATLAB 鑰﹀悎銆?

## Stage-two branch-observability preflight addendum

The next-stage preflight traced real TLines `E_2_3_1`, `E_1_2_1`,
`E_2_25_1`, and `E_16_19_1`, but none exposes an existing, semantically
confirmed P/Q/I signal path. Because the approved scope prohibited adding
meters or calculations, the stage ended in static fallback without GUI,
Build, Run, or new Output Channels.

P08 therefore remains `missing`; P09 line-overload protection and P10 branch
trip also remain `missing`. The recommended research direction remains
`branch observability only`, but a future task must explicitly authorize
minimal inline meters or establish a native TLine measurement interface.

## Full-network TLine P/Q/I observability implementation addendum

The later full-network TLine measurement stage implemented the previously
recommended branch-observability step as a static, monitor-only trial
extension. All 31 genuine P3 network `TLine` instances now have terminal A/B
native `master:multimeter` P/Q/Crms measurements and six Output Channels per
line, for 186 new branch channels and 448 total XML Output Channels.

This updates P08 from `missing` to `partially_aligned /
implemented_static_only`: the raw line P/Q/I observability bridge now exists,
but no Run has verified power-flow redistribution and no in-model loading
ratio, overload protection, or line trip logic exists. P09 and P10 remain
missing. The safe project name remains `controlled-interface validation
scaffold`; strict paper reproduction remains `not_achieved`.

## Paper-aligned 20 s baseline fault static configuration addendum

The trial project now contains a static paper-aligned baseline fault
configuration. The existing `master:tfaultn` component was reused and configured
for a three-phase fault at the structurally aligned P3 `N29` target, starting at
0.50 s and lasting 2.00 s. The project `Duration of Run` is 20 s. The main
project remains unchanged, the full-network TLine measurement layer remains at
448 XML Output Channels, and PSCAD Build artifacts verify N29 fault branches and
timing code.

This updates P03/P04/P05/P06 to `implemented_static_only` or
`structurally_aligned_adaptation` for the configuration layer. It does not
upgrade the overall reproduction level to strict or dynamic paper reproduction:
no Run was performed, and branch overload, line-trip, UFLS/UVLS, generator
protection, and mitigation mechanisms remain future work.

## Paper-aligned 20 s dynamic Run and full-network TLine response addendum

The approved single PSCAD GUI Run of the already configured 20 s N29
three-phase fault has now been parsed offline. The trial model hash remained
`F81959EA62211FF9C1536C8481B67675AFE4DDCC3C56E804D048731A4B88A300`, the main
model hash remained
`CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB`, and the
static XML Output Channel count remained 448.

The Run produced a valid 0-20 s time axis and all 31 genuine network TLines
were parsed with terminal A/B P/Q/I metrics, for 186 raw branch signals. This
updates P08 from `implemented_static_only` to
`dynamic_observation_not_causal`: raw power-flow/current redistribution is now
observable in the Run outputs, but loading ratios, overload status, relays,
line trips, and causality remain unavailable.

P09, P10, P11-P15 remain missing. Strict thesis reproduction remains
`not_achieved`; the safe project name remains `controlled-interface validation
scaffold`.

## Full-network TLine rating and offline loading addendum

The next offline audit traced exact generated `.tli` records for all 31 current
network TLines. Each record contains `Total MVA Rating = 100.0`, so the current
project now has a qualified apparent-power rating basis for every audited TLine
and an offline apparent-power loading-ratio reconstruction from the existing
20 s Run.

This refines P08 without upgrading P09/P10: raw redistribution and loading
ratio can be observed for qualified current-model lines, but no inverse-time
relay, thermal time model, protection action, line breaker command, branch
trip, or natural cascade mechanism has been implemented or validated.

The recommended future shadow-overload candidate is `E_28_29_1`; `E_16_19_1`
remains paper-relevant but ranks ninth under the current model's audited
post-clear loading metric. Strict thesis reproduction remains `not_achieved`.

## Stage-five-B semantic correction

The later TLine Total MVA semantic audit reclassified the uniform `100.0 MVA`
field as `uniform_model_value_or_default_parameter`, not a verified continuous
thermal or protection-grade rating. Therefore previous S/100 MVA values must be
read as a `100-MVA-normalized apparent-power response index`, not an overload
ratio. `E_28_29_1` remains only the highest normalized apparent-power response
line. Shadow overload relay modeling is blocked until auditable per-line
continuous thermal limits, or a reproducible paper-to-current-model rating
mapping, are available.

## Stage-six thermal-limit recovery result

Stage six recovered exact branch identity mapping from the current PSCAD TLines
to the PNNL 3IBR RAW network branch table, but did not recover usable continuous
thermal limits: all mapped current-network branch RATE fields are zero.  The
safe quantity remains the `100-MVA-normalized apparent-power response index`;
`protection-grade loading ratio` remains unavailable, and shadow relay modeling
remains blocked.

## Stage seven paper-calibrated equivalent first-trip attempt

Status: `paper_calibrated_first_trip_parser_fallback`.  Selected line `E_28_29_1` with equivalent capacity `7.872883989661206` and 1.1 + 5 s fallback logic. Generated code confirms the trial relay/breaker chain, but runtime PGB waveforms were unavailable; therefore no dynamic flow-driven trip or actual breaker-open causality is claimed.

## Stage eight runtime observability and dynamic result

Runtime Output Channel observability passed: all 13 canonical `PAPER_OVL1_*` channels are readable over 0-20 s. Dynamic classification is `stage8_pre_fault_false_trip`: `ABOVE_THRESHOLD` never asserted, while timer, trip request, breaker command, and open state were present at t=0. Flow-driven first-trip causality is not proven, no post-trip redistribution ranking is valid, and strict reproduction remains `not_achieved`.
## Stage nine short-run initialization repair and first trip

Status: `stage9_short_run_flow_driven_first_trip_pass`. The 9.0 s Run has healthy pre-fault initialization and records the equivalent E_28_29_1 threshold-to-timer-to-breaker first-trip chain. This remains a paper-calibrated equivalent protection result, not a verified PNNL thermal rating, real protection setting, second trip, or natural cascade. Strict reproduction remains `not_achieved`.
## Stage 10A DFIG event consistency and paper sequence

Status: `stage10_read_only_audit_complete_dfig_actual_no_trip_in_stage9`. Stage 4 contains a physical DFIG opening and matching event packet at 2.43 s; Stage 9 contains neither before the E_28_29_1 opening at 7.51 s. The channels are present and readable, so this is not an observability/parser failure. The verified signal-level cause is that Stage-9 fault-period VIBR1_2 stayed above the unchanged 0.9 duration-LVRT threshold. Stage 9 validates only the flow-driven E_28_29_1 protection subchain. Until a physical DFIG event precedes the first line trip, it is not a complete paper-style accident-chain reproduction.
## Stage 10B fault-to-DFIG static fallback

Decision: `no_defensible_electrical_difference_found`. XML geometry alone suggested a gap, but generated `P3.dta` proves the Stage-9 breaker and fault remain on the compiled `N29(1..3)` boundary. No permitted single interface repair is defensible, so GUI, Build, and Run are blocked. Strict reproduction remains `not_achieved`.
## Stage 10C compiled network and initial-state audit

Classification: `B_intended_PAPER_OVL1_closed_state_difference_quantified_but_not_proven_causal`. The only scoped compiled-network initialization candidate is PAPER breaker `RON=0.001 ohm`. Because the TLine input is `RXB p.u./m` with length `0.001 m`, RON equals about 60.0% of the line's reconstructed positive-sequence resistance and 5.54% of its |Z|, increasing |Z| by about 0.663%. Runtime E_28_29_1 P/I differs by about 51%-52%, but available evidence does not prove RON alone caused that meshed-network flow shift or the DFIG fault-voltage change. No model edit, Build, or Run is authorized.

## Stage 10D compiled-endpoint repair

`E_26_29_1` terminal B was found on compiled bus 19 rather than N29. An
electrical `N29` Node Label restored it to bus 1, preserved the PAPER breaker
as a series element, and restored the physical DFIG trip at 2.44 s in the
single 3.0 s validation Run. From this stage onward, every breaker insertion,
line-end move, or node-label edit must pass a generated-`P3.dta` TLine endpoint
bus and three-phase connectivity check before a Run is authorized.

## Stage 11 20 s / 50 us paper-like main-chain result

The repaired endpoint enabled the intended paper-like order to be observed in a
single 20 s runtime output set at 50 us solution step and 0.01 s plot step:
fault application at 0.50 s, fault clearing at 2.50 s, DFIG LVRT physical
breaker opening at 2.44 s, DFIG event packet/source-unavailability at 2.44 s,
`E_28_29_1` equivalent loading threshold crossing at 2.53 s, 5 s timer
completion at 7.53 s, and `PAPER_OVL1` physical line-breaker opening at
7.53 s.

This updates the safe project description from pure infrastructure to
`partial paper-like mechanism reproduction under trial-only equivalent
protection`. The remaining boundary is unchanged: the `PAPER_OVL1` limit is a
paper-calibrated equivalent capacity, not a recovered PNNL thermal rating, and
the 50 us result cannot be cited as proof of 5 us numerical equivalence or a
full multi-stage natural cascade.
