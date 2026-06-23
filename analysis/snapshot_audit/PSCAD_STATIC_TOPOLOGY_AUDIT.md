# PSCAD Static Topology Audit

Scope: read-only static audit of `external/pscad_snapshot_20260623/`. No PSCAD build/run and no source snapshot modification was performed.

## Source Files
- Current case: `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx`
- Type-3 library: `external/pscad_snapshot_20260623/type3_wtg_v46_trial/Type3WTG_Lib.pslx`
- Official Type-3 example case copy: `external/pscad_snapshot_20260623/type3_wtg_v46_trial/Type3_Ave_Nov_2018.pscx`

## P3 Page / Module Path
- The Type-3 replacement objects are inside the current case XML under the main project hierarchy. PSCAD tab observed earlier was `3IBR:Main(0):P1(0):P3(0)`; XML evidence is the hierarchy call for `Type3WTG_Lib:Type3_WTG_Avg` inside the case hierarchy.
- Hierarchy call line: `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:75161`
```xml
75158: </call>
75159: <call link="161593669" name="3IBR:REGC_A_1_2_1_1" z="920" view="false" instance="1" />
75160: </call>
75161: <call link="2147003001" name="Type3WTG_Lib:Type3_WTG_Avg" z="1180" view="false" instance="0">
75162: <call link="689018709" name="Type3WTG_Lib:Synchronization" z="330" view="false" instance="0" />
75163: <call link="1370289782" name="Type3WTG_Lib:WindTurbine_MechModel" z="550" view="false" instance="0">
75164: <call link="124098004" name="Type3WTG_Lib:PI_AntiWindUp_2" z="350" view="false" instance="0" />
```
- Nearest XML containers for the Type-3 instance:
  - `schematic` {'classid': 'UserCanvas', 'zoomlevel': '6', 'scrollx': '0', 'scrolly': '0'}
  - `Definition` {'classid': 'UserCmpDefn', 'name': 'P3', 'group': '', 'url': '', 'version': '', 'build': '', 'instances': '1', 'key': '', 'view': 'false', 'date': '1782199583', 'id': '99382095'}

## Type3WTG_Lib:Type3_WTG_Avg Instance
- Instance ID `2147003001`, name `Type3WTG_Lib:Type3_WTG_Avg`, defn `Type3WTG_Lib:Type3_WTG_Avg`, coordinates x/y/w/h=`1080/936/53/87`, disabled=`false`.
- Parameters: `Pbase=2.0`, `freq=60`, `VLL_Gr=33`, `No_WTG=100`, `Mrating=2.5`, `Vwind=Vwind`, `Dblk=Dblk_DFIG`.
- Source: `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:25406`
```xml
25402: <param name="bg_color" value="15792890" />
25403: <param name="opacity" value="25" />
25404: </paramlist><![CDATA[By the generator step up transfomer, it should provide 83.9 MW on the generator side so that the IBR units can provide 250 MW (83.333*3) to the collector bus by the plant level control, considering the power drop across each generator step-up transformer
25405: -Sangwon Seo 6/28/2023]]></Sticky>
25406: <User classid="UserCmp" name="Type3WTG_Lib:Type3_WTG_Avg" id="2147003001" x="1080" y="936" w="53" h="87" z="1180" orient="0" defn="Type3WTG_Lib:Type3_WTG_Avg" link="-1" q="4" disable="false">
25407: <paramlist link="-1" name="" crc="91134585">
25408: <param name="Name" value="" />
25409: <param name="Pbase" value="2.0" />
25410: <param name="freq" value="60" />
```

## Dblk_DFIG Signal Chain
- Static chain identified by coordinates and XML definitions: `TIME` data label/import at the compare input side -> `master:compare` ID `1776838349` with `X=0.2`, `OL=0`, `OH=1` -> `master:datalabel` ID `1031105444`, `Name=Dblk_DFIG` -> Type-3 parameter `Dblk=Dblk_DFIG`. Direction/source semantics still require PSCAD GUI confirmation, but the naming and placement match the intended chain.
- `dblk_label`: ID `1031105444`, defn `master:datalabel`, x/y=`360/1062`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:25584`, params subset `{'Name': 'Dblk_DFIG'}`.
```xml
25581: <vertex x="0" y="0" />
25582: <vertex x="-36" y="0" />
25583: </Wire>
25584: <User classid="UserCmp" defn="master:datalabel" id="1031105444" x="360" y="1062" w="66" h="21" z="1" orient="2" link="-1" q="4">
25585: <paramlist link="-1" name="" crc="98359112">
25586: <param name="Name" value="Dblk_DFIG" />
25587: </paramlist>
```
- `compare`: ID `1776838349`, defn `master:compare`, x/y=`432/1062`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:25589`, params subset `{'X': '0.2', 'OL': '0', 'OH': '1'}`.
```xml
25586: <param name="Name" value="Dblk_DFIG" />
25587: </paramlist>
25588: </User>
25589: <User classid="UserCmp" defn="master:compare" id="1776838349" x="432" y="1062" w="76" h="58" z="1160" orient="4" link="-1" q="4">
25590: <paramlist link="-1" name="" crc="86304751">
25591: <param name="X" value="0.2" />
25592: <param name="OL" value="0" />
```

- `time-sig`: ID `146328259`, defn `master:time-sig`, x/y=`522/1062`, source `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:25599`.
```xml
25596: <param name="conv" value="0" />
25597: </paramlist>
25598: </User>
25599: <User classid="UserCmp" defn="master:time-sig" id="146328259" x="522" y="1062" w="70" h="19" z="410" orient="4" link="-1" q="4">
25600: <paramlist link="-1" name="" crc="20913136" />
25601: </User>
25602: <Wire classid="WireOrthogonal" id="1270108321" name="" x="468" y="1062" w="28" h="10" orient="0">
```

## Vwind Signal Chain
- Static chain identified by XML: `master:var` ID `887206944`, `Name=windSpeed`, base/default `Value=11.0`, min/max `3.0/25`, linked to slider control ID `633315173`; output wire near y=1134 feeds rate-limiter-like component and `master:datalabel` ID `697683388`, `Name=Vwind`; Type-3 parameter uses `Vwind=Vwind`.
- `windSpeed_var`: ID `887206944`, defn `master:var`, x/y=`540/1134`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:25444`, params subset `{'Name': 'windSpeed', 'Value': '11.0', 'Min': '3.0', 'Max': '25', 'Units': '', 'Collect': '1'}`.
```xml
25440: <paramlist link="-1" name="" crc="98359112">
25441: <param name="Name" value="Vwind" />
25442: </paramlist>
25443: </User>
25444: <User classid="UserCmp" name="master:var" id="887206944" x="540" y="1134" w="66" h="51" z="420" orient="4" defn="master:var" link="-1" q="4">
25445: <paramlist link="-1" name="" crc="29663193">
25446: <param name="Name" value="windSpeed" />
25447: <param name="Group" value="" />
25448: <param name="Display" value="1" />
```
- `vwind_label`: ID `697683388`, defn `master:datalabel`, x/y=`360/1134`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:25439`, params subset `{'Name': 'Vwind'}`.
```xml
25435: <Wire classid="WireOrthogonal" id="1318845970" name="" x="504" y="1134" w="46" h="10" orient="0">
25436: <vertex x="0" y="0" />
25437: <vertex x="-36" y="0" />
25438: </Wire>
25439: <User classid="UserCmp" name="datalabel" defn="master:datalabel" id="697683388" x="360" y="1134" w="38" h="21" z="1" orient="0" link="-1" q="4">
25440: <paramlist link="-1" name="" crc="98359112">
25441: <param name="Name" value="Vwind" />
25442: </paramlist>
25443: </User>
```

- `rate_limiter`: ID `808965454`, defn `master:ratelimit`, x/y=`432/1134`, params `IR=10 [1/s]`, `DR=5 [1/s]`, source `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:25546`.
```xml
25542: <param name="Units" value="" />
25543: <param name="Collect" value="1" />
25544: </paramlist>
25545: </User>
25546: <User classid="UserCmp" defn="master:ratelimit" id="808965454" x="432" y="1134" w="76" h="58" z="1140" orient="4" link="-1" q="4">
25547: <paramlist link="-1" name="" crc="34241435">
25548: <param name="IR" value="10 [1/s]" />
25549: <param name="DR" value="5 [1/s]" />
25550: <param name="COM" value="Rate_Limiter" />
```

## GBUS30/N30 -> Type-3 Electrical Path
- Static topology is inferred from component identity, placement, and local wires in the P3 coordinate range. PSCAD node-solving confirmation would require GUI/build, which was intentionally not run in this audit.
- `gbus30`: ID `4961`, defn `master:annotation`, x/y=`432/936`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:20317`, params `{'AL2': 'GBUS30  '}`.
- `n30`: ID `4962`, defn `master:nodelabel`, x/y=`432/990`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:20323`, params `{'Name': 'N30'}`.
- `breaker`: ID `521858026`, defn `master:breaker3`, x/y=`864/990`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:25606`, params `{'NAME': 'BRK_DFIG'}`.
- `breaker_label`: ID `1046505114`, defn `master:datalabel`, x/y=`918/1026`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:25739`, params `{'Name': 'BRK_DFIG'}`.
- `xfmr`: ID `113665858`, defn `master:xfmr-3p2w`, x/y=`990/990`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:25647`, params `{'Name': 'XFMR_DFIG_22_33', 'Tmva': '250.0 [MVA]', 'V1': '22 [kV]', 'V2': '33 [kV]', 'Xl': '0.1 [pu]', 'CuL': '0.005 [pu]', 'YD1': '0', 'YD2': '0', 'Lead': '1', 'Ideal': '1', 'f': '60.0 [Hz]'}`.
- `type3`: ID `2147003001`, defn `Type3WTG_Lib:Type3_WTG_Avg`, x/y=`1080/936`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:25406`, params `{'Name': ''}`.
- Local branch wires around x=400..1150, y=900..1080:
  - Wire ID `382112048` at x/y/w/h=`414/990/136/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:20313`, vertices `[{'x': '0', 'y': '0'}, {'x': '126', 'y': '0'}]`
  - Wire ID `3986754` at x/y/w/h=`576/990/118/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:21131`, vertices `[{'x': '0', 'y': '0'}, {'x': '108', 'y': '0'}]`
  - Wire ID `169022313` at x/y/w/h=`720/990/64/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:21256`, vertices `[{'x': '0', 'y': '0'}, {'x': '54', 'y': '0'}]`
  - Wire ID `1270108321` at x/y/w/h=`468/1062/28/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:25602`, vertices `[{'x': '0', 'y': '0'}, {'x': '18', 'y': '0'}]`
  - Wire ID `1812570648` at x/y/w/h=`792/990/46/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:25725`, vertices `[{'x': '0', 'y': '0'}, {'x': '36', 'y': '0'}]`
  - Wire ID `717906805` at x/y/w/h=`900/990/46/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:25729`, vertices `[{'x': '0', 'y': '0'}, {'x': '36', 'y': '0'}]`
  - Wire ID `880906506` at x/y/w/h=`846/1026/82/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:25744`, vertices `[{'x': '0', 'y': '0'}, {'x': '72', 'y': '0'}]`
  - Wire ID `1703525761` at x/y/w/h=`1026/990/64/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:25748`, vertices `[{'x': '0', 'y': '0'}, {'x': '54', 'y': '0'}, {'x': '36', 'y': '0'}]`
  - Wire ID `605387583` at x/y/w/h=`810/1044/82/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:31725`, vertices `[{'x': '0', 'y': '0'}, {'x': '72', 'y': '0'}]`
  - Wire ID `1328112715` at x/y/w/h=`810/1008/82/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:31883`, vertices `[{'x': '0', 'y': '0'}, {'x': '72', 'y': '0'}]`
  - Wire ID `1816657825` at x/y/w/h=`558/900/46/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:34224`, vertices `[{'x': '0', 'y': '0'}, {'x': '36', 'y': '0'}]`
  - Wire ID `134059866` at x/y/w/h=`558/972/46/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:34228`, vertices `[{'x': '0', 'y': '0'}, {'x': '36', 'y': '0'}]`
  - Wire ID `1615417441` at x/y/w/h=`558/936/46/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:34256`, vertices `[{'x': '0', 'y': '0'}, {'x': '36', 'y': '0'}]`
  - Wire ID `570133704` at x/y/w/h=`558/1008/46/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:34260`, vertices `[{'x': '0', 'y': '0'}, {'x': '36', 'y': '0'}]`
  - Wire ID `1033836074` at x/y/w/h=`558/1044/46/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:34288`, vertices `[{'x': '0', 'y': '0'}, {'x': '36', 'y': '0'}]`
  - Wire ID `1696358935` at x/y/w/h=`558/1080/46/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:34320`, vertices `[{'x': '0', 'y': '0'}, {'x': '36', 'y': '0'}]`
  - Wire ID `1801242401` at x/y/w/h=`846/900/46/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:34652`, vertices `[{'x': '0', 'y': '0'}, {'x': '36', 'y': '0'}]`
  - Wire ID `1764578492` at x/y/w/h=`846/918/46/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:34656`, vertices `[{'x': '0', 'y': '0'}, {'x': '36', 'y': '0'}]`
  - Wire ID `1587700175` at x/y/w/h=`846/936/46/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:34660`, vertices `[{'x': '0', 'y': '0'}, {'x': '36', 'y': '0'}]`
  - Wire ID `121694392` at x/y/w/h=`846/954/46/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:34689`, vertices `[{'x': '0', 'y': '0'}, {'x': '36', 'y': '0'}]`
  - Wire ID `1175583470` at x/y/w/h=`846/972/46/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:34693`, vertices `[{'x': '0', 'y': '0'}, {'x': '36', 'y': '0'}]`
  - Wire ID `2124600534` at x/y/w/h=`450/936/46/28`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:37316`, vertices `[{'x': '0', 'y': '0'}, {'x': '18', 'y': '0'}, {'x': '18', 'y': '18'}, {'x': '36', 'y': '18'}]`
  - Wire ID `1432261836` at x/y/w/h=`450/900/46/28`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:37322`, vertices `[{'x': '0', 'y': '0'}, {'x': '18', 'y': '0'}, {'x': '18', 'y': '-18'}, {'x': '36', 'y': '-18'}]`
  - Wire ID `390609325` at x/y/w/h=`558/954/28/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:37328`, vertices `[{'x': '0', 'y': '0'}, {'x': '18', 'y': '0'}]`
  - Wire ID `529606073` at x/y/w/h=`756/954/28/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:38944`, vertices `[{'x': '0', 'y': '0'}, {'x': '18', 'y': '0'}]`
  - Wire ID `1893393661` at x/y/w/h=`432/900/82/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:41358`, vertices `[{'x': '0', 'y': '0'}, {'x': '72', 'y': '0'}]`
  - Wire ID `1878401149` at x/y/w/h=`648/900/28/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:41694`, vertices `[{'x': '0', 'y': '0'}, {'x': '-18', 'y': '0'}]`
  - Wire ID `211851179` at x/y/w/h=`792/900/28/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:41974`, vertices `[{'x': '0', 'y': '0'}, {'x': '18', 'y': '0'}]`
  - Wire ID `635134267` at x/y/w/h=`1026/954/28/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:42882`, vertices `[{'x': '0', 'y': '0'}, {'x': '18', 'y': '0'}]`
  - Wire ID `759591092` at x/y/w/h=`1026/900/28/10`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:42886`, vertices `[{'x': '0', 'y': '0'}, {'x': '18', 'y': '0'}]`

## Original First 22/0.6 kV + IBR_AVM Branch Status
- Current `3IBR.pscx` contains two active `3IBR:IBR_AVM_2_1_1` instances, not three. This is consistent with the first IBR_AVM branch having been removed from current active topology while the remaining two IBR branches stay present.
- Remaining IBR_AVM instance 1: ID `1220231535`, x/y=`990/1332`, disabled=`false`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:24816`.
- Remaining IBR_AVM instance 2: ID `202861579`, x/y=`990/1656`, disabled=`false`, line `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:24905`.
- The `IBR_AVM_2_1_1` definition itself remains in the case with `instances="0"` in its definition metadata; live instances are represented through hierarchy calls at the bottom of the project file.
- Definition evidence: `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:35995`
```xml
35993: </graphics>
35994: </Definition>
35995: <Definition classid="UserCmpDefn" name="IBR_AVM_2_1_1" group="" url="" version="" build="" crc="35817128" instances="0" key="" view="false" date="1782199584" id="772335225">
35996: <paramlist name="">
35997: <param name="Description" value="" />
```


Additional transformer evidence near the first replaced/remaining branches:

- Upstream retained ETRAN transformer: ID `4960`, defn `ETRAN:Electranix_xfmr_2w`, name `E_2_30_1`, x/y=`342/990`, Xl=`0.0181`, line source in `3IBR.pscx` around the GBUS30/N30 section.
- Remaining old IBR branch transformer 1: ID `275469438`, defn `ETRAN:Electranix_xfmr_2w`, name `E_2_30_1`, x/y=`864/1332`, Xl=`0.06245`; it is paired spatially with remaining IBR_AVM ID `1220231535`.
- Remaining old IBR branch transformer 2: ID `1076244314`, defn `ETRAN:Electranix_xfmr_2w`, name `E_2_30_1`, x/y=`864/1656`, Xl=`0.06245`; it is paired spatially with remaining IBR_AVM ID `202861579`.
- No current `3IBR:IBR_AVM_2_1_1` instance exists near the first replacement branch y?990. The active Type-3 replacement occupies x/y=`1080/936` and connects through new transformer ID `113665858`. This is a static absence check, not a solved-netlist proof.

Port-level limitation: the current XML records component placements, wires, and hierarchy calls, but this audit did not evaluate PSCAD terminal pin connectivity. The exact IBR_AVM port-level disconnection must be treated as `static XML evidence: first IBR instance absent from current case; no solved electrical connectivity proof in this audit`.

## Other IBR Branches
- Two `3IBR:IBR_AVM_2_1_1` instances remain in current case and hierarchy calls:
  - ID `1220231535` at XML line `24816`; hierarchy call `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:75155`.
  - ID `202861579` at XML line `24905`; hierarchy call `external/pscad_snapshot_20260623/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx:75149`.

## Static-Audit Limits
- This audit did not solve PSCAD connectivity or rebuild EMTDC. Wire-to-terminal connectivity, exact AC_sys pin mapping, and source/receiver direction for Data Labels should be confirmed in PSCAD GUI before further electrical edits.
