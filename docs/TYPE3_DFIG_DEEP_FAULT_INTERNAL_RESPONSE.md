# Type-3 DFIG ??????? LVRT ??????

???2026-06-24  
???????`C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46`  
??????????? `3IBR.inf` ? `3IBR_*.out`???? PSCAD GUI?? Build/Run?????? `.pscx/.pslx/XML` ??????

## ?????????

- ???????? `3IBR.gf46`?`C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46\3IBR.inf`?
- ?? `.out` ????? `4.9966 s`??? 5 s ??????? smoke test?
- ??????????? `1.8-2.0 s`???? `2.0-2.15 s`???? `4.0-5.0 s`?
- PGB ?????? `3IBR.inf` ?????? 10 ? PGB ???? `3IBR_NN.out`?? 1 ????????? `((PGB-1) mod 10)+2`?
- ?? CSV ???`data/reference/type3_dfig_deep_fault_internal_response_summary.csv`?

## ?????

| Signal | PGB | File | Col | Unit | Pre mean | Fault min | Fault mean | Fault max | Fault peak abs @s | Post mean | Limitation |
|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| `VIBR1_2` | 2 | `3IBR_01.out` | 3 | pu candidate | 0.99687637 | 0.05786476 | 0.13728806 | 0.98717140 | 2.000300 | 0.99696545 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `PIBR1_2` | 4 | `3IBR_01.out` | 5 | MW | 202.089 | -227.880 | -150.934 | 196.832 | 2.029350 | 199.197 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `QIBR1_2` | 6 | `3IBR_01.out` | 7 | MVAr | -13.826583 | -13.211935 | 3.924918 | 12.363727 | 2.000300 | -21.508556 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `SPD30` | 1 | `3IBR_01.out` | 2 | Hz candidate | 60.000000 | 60.000000 | 60.000000 | 60.000000 | 2.000300 | 60.000000 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `DFIG_IFLT_A_KA` | 19 | `3IBR_02.out` | 10 | kA | 0.00000013 | -106.300 | 18.604561 | 197.603 | 2.008600 | 0.00000000 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `DFIG_IFLT_B_KA` | 18 | `3IBR_02.out` | 9 | kA | 0.00000016 | -162.865 | -7.227925 | 98.558851 | 2.004450 | -0.00000002 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `DFIG_IFLT_C_KA` | 17 | `3IBR_02.out` | 8 | kA | -0.00000028 | -137.139 | -11.376630 | 87.315819 | 2.008600 | 0.00000002 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `DFIG_DBLK_CMD` | 22 | `3IBR_03.out` | 3 | logic | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 2.000300 | 1.000000 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `DFIG_BRK_STATE` | 21 | `3IBR_03.out` | 2 | logic, 0=closed by current project convention | 0.00000000 | 0.00000000 | 0.00000000 | 0.00000000 | 2.000300 | 0.00000000 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `DFIG_VWIND_MS` | 20 | `3IBR_02.out` | 11 | m/s | 11.000000 | 11.000000 | 11.000000 | 11.000000 | 2.000300 | 11.000000 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |

??????`VIBR1_2` ??????? `0.057865`???? `0.137288`????????????`DFIG_IFLT_A/B/C_KA` ?????????????? RSC?GSC???? Crowbar ?????

## DC-link ??

| Signal | PGB | File | Col | Unit | Pre mean | Fault min | Fault mean | Fault max | Fault peak abs @s | Post mean | Limitation |
|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| `Ecap_Det` | 256 | `3IBR_26.out` | 7 | kV candidate | 1.449787 | 1.124755 | 1.432150 | 2.070126 | 2.008600 | 1.449672 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `Edc_pu` | 284 | `3IBR_29.out` | 5 | pu candidate | 0.99985321 | 0.77591377 | 0.98768515 | 1.427780 | 2.008600 | 0.99977376 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `Ecap` | 326 | `3IBR_33.out` | 7 | kV candidate | 1.449782 | 1.333255 | 1.431543 | 1.761555 | 2.012750 | 1.449668 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `BRK_CHOP` | 328 | `3IBR_33.out` | 9 | logic candidate | 0.00000000 | 0.00000000 | 0.05405405 | 1.000000 | 2.008600 | 0.00000000 | Requires GUI semantic confirmation before using as formal internal LVRT explanation. |

?????`Edc_pu` ??????? `1.427780`?????? `2.00860 s`?`Ecap_Det` ??? `2.070126` kV candidate?????? DC-link ????/?????? `Ecap_Det` ?????? `Edc_pu` ????? GUI ??????????????

## Crowbar ? Chopper ????

| Signal | PGB | File | Col | Unit | Pre mean | Fault min | Fault mean | Fault max | Fault peak abs @s | Post mean | Limitation |
|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| `Iovercur` | 321 | `3IBR_33.out` | 2 | logic candidate | 0.00000000 | 0.00000000 | 0.00000000 | 0.00000000 | 2.000300 | 0.00000000 | Requires GUI semantic confirmation before using as formal internal LVRT explanation. |
| `Reset` | 322 | `3IBR_33.out` | 3 | logic candidate | 0.00000000 | 0.00000000 | 0.91891892 | 1.000000 | 2.012750 | 0.00000000 | Requires GUI semantic confirmation before using as formal internal LVRT explanation. |
| `S1` | 323 | `3IBR_33.out` | 4 | logic candidate | 0.00000000 | 0.00000000 | 0.00000000 | 0.00000000 | 2.000300 | 0.00000000 | Requires GUI semantic confirmation before using as formal internal LVRT explanation. |
| `Mono_out` | 324 | `3IBR_33.out` | 5 | logic candidate | 0.00000000 | 0.00000000 | 0.40540541 | 1.000000 | 2.012750 | 0.00000000 | Requires GUI semantic confirmation before using as formal internal LVRT explanation. |
| `Crowbar current:1` | 318 | `3IBR_32.out` | 9 | internal current candidate | -0.00000055 | -0.00000579 | 0.00000002 | 0.00000757 | 2.004450 | -0.00000011 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `Crowbar current:2` | 319 | `3IBR_32.out` | 10 | internal current candidate | 0.00000019 | -0.00001019 | -0.00000028 | 0.00000516 | 2.008600 | -0.00000010 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `Crowbar current:3` | 320 | `3IBR_32.out` | 11 | internal current candidate | 0.00000002 | -0.00000760 | 0.00000001 | 0.00000811 | 2.008600 | -0.00000011 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `BRK_CHOP` | 328 | `3IBR_33.out` | 9 | logic candidate | 0.00000000 | 0.00000000 | 0.05405405 | 1.000000 | 2.008600 | 0.00000000 | Requires GUI semantic confirmation before using as formal internal LVRT explanation. |
| `Imagn` | 327 | `3IBR_33.out` | 8 | current magnitude candidate | 0.30508306 | 0.30394386 | 0.92692634 | 1.120072 | 2.149700 | 0.28180928 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |

??????`Reset` ? `Mono_out` ?????? 0/1 ???`BRK_CHOP` ????????? `Iovercur=0`?`S1=0`??? `Crowbar current` ??????  
????????????Crowbar/???????????? GUI ?? `S1/Mono_out/Reset/Iovercur` ?????? active-high/active-low ??????? Crowbar ????

## RSC ??

| Signal | PGB | File | Col | Unit | Pre mean | Fault min | Fault mean | Fault max | Fault peak abs @s | Post mean | Limitation |
|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| `I_RS:1` | 257 | `3IBR_26.out` | 8 | kA candidate | -0.00084938 | -1.715329 | 0.04064575 | 1.396186 | 2.004450 | -0.00084508 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `I_RS:2` | 258 | `3IBR_26.out` | 9 | kA candidate | -0.03785788 | -1.238164 | -0.07601179 | 1.560323 | 2.021050 | 0.00032144 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `I_RS:3` | 259 | `3IBR_26.out` | 10 | kA candidate | 0.03870693 | -1.451272 | 0.03536580 | 1.262370 | 2.025200 | 0.00052332 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `Idr_pu` | 312 | `3IBR_32.out` | 3 | pu candidate | -0.08265746 | -0.79778912 | -0.12936439 | 0.58070930 | 2.004450 | -0.09073838 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `Iqr_pu_RSC_A` | 298 | `3IBR_30.out` | 9 | pu candidate | 0.25746294 | 0.15379543 | 0.80782958 | 1.251003 | 2.025200 | 0.23117666 | Requires GUI semantic confirmation before using as formal internal LVRT explanation. |
| `Iqr_pu_RSC_B` | 314 | `3IBR_32.out` | 5 | pu candidate | 0.25746294 | 0.15379543 | 0.80782958 | 1.251003 | 2.025200 | 0.23117666 | Requires GUI semantic confirmation before using as formal internal LVRT explanation. |
| `Imax_pu` | 288 | `3IBR_29.out` | 9 | pu limit | 1.200000 | 1.200000 | 1.200000 | 1.200000 | 2.000300 | 1.200000 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `Imax_d_pu` | 317 | `3IBR_32.out` | 8 | pu limit | 1.172037 | 0.74777091 | 0.84965837 | 1.178725 | 2.008600 | 1.177293 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `ImaxN_d_pu` | 305 | `3IBR_31.out` | 6 | pu limit | -1.172037 | -1.178725 | -0.84965837 | -0.74777091 | 2.008600 | -1.177293 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `Low_Cu_Manag` | 311 | `3IBR_32.out` | 2 | logic/factor candidate | 1.000000 | 0.10380464 | 0.24806749 | 1.000000 | 2.000300 | 1.000000 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `Voltage_dip` | 285 | `3IBR_29.out` | 6 | logic candidate | 0.00000000 | 0.00000000 | 0.91891892 | 1.000000 | 2.012750 | 0.00000000 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |

?????RSC ?????? `I_RS:1..3` ???????????? `1.715329` kA candidate??????????`Voltage_dip` ? `Low_Cu_Manag` ????????????? RSC ??????/???????????`Iqr_pu` ??? PGB????????? GUI ???

## GSC ??

| Signal | PGB | File | Col | Unit | Pre mean | Fault min | Fault mean | Fault max | Fault peak abs @s | Post mean | Limitation |
|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| `Iconv:1` | 263 | `3IBR_27.out` | 4 | kA candidate | 0.00165626 | -0.49016083 | 0.03098534 | 1.077401 | 2.008600 | -0.00026590 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `Iconv:2` | 264 | `3IBR_27.out` | 5 | kA candidate | -0.00163039 | -1.532807 | -0.04573269 | 0.66359192 | 2.008600 | 0.00014703 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `Iconv:3` | 265 | `3IBR_27.out` | 6 | kA candidate | -0.00002587 | -0.85900755 | 0.01474736 | 1.160096 | 2.004450 | 0.00011887 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `Id_pu_Gsc` | 276 | `3IBR_28.out` | 7 | pu candidate | -0.03838890 | -1.141302 | -0.02870676 | 0.24462211 | 2.008600 | -0.04478018 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `Iq_pu_Gsc` | 275 | `3IBR_28.out` | 6 | pu candidate | 0.38093418 | 0.28761886 | 0.32794362 | 0.46369058 | 2.004450 | 0.37863532 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `Id_ord_pu` | 281 | `3IBR_29.out` | 2 | pu candidate | -0.03838608 | -1.104842 | -0.03054568 | 0.24450554 | 2.008600 | -0.04477539 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `Iq_ord_pu` | 279 | `3IBR_28.out` | 10 | pu candidate | 0.38093393 | 0.28818078 | 0.32595653 | 0.38506705 | 2.016900 | 0.37863728 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |

?????GSC ?????? `Iconv:1..3` ???????????? `1.532807` kA candidate?`Id_pu_Gsc/Id_ord_pu` ?????????????????? dq ????? GUI ???

## ????????

| Signal | PGB | File | Col | Unit | Pre mean | Fault min | Fault mean | Fault max | Fault peak abs @s | Post mean | Limitation |
|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| `Wpu` | 254 | `3IBR_26.out` | 5 | pu candidate | 1.205632 | 1.206159 | 1.212632 | 1.218622 | 2.149700 | 1.200021 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `Pwind_pu` | 250 | `3IBR_25.out` | 11 | pu candidate | 1.129572 | 0.47485603 | 0.82325607 | 1.084518 | 2.008600 | 0.94930140 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `TM` | 229 | `3IBR_23.out` | 10 | pu candidate | -0.93695071 | -0.89915718 | -0.67946168 | -0.38968607 | 2.008600 | -0.79107088 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `TE` | 230 | `3IBR_23.out` | 11 | pu candidate | -0.80755046 | -2.243988 | -0.22397291 | 0.12028806 | 2.004450 | -0.79278672 | Mapped from latest inf/out; physical sign and exact base may still require GUI confirmation. |
| `Dblk_VdcCtrl` | 234 | `3IBR_24.out` | 5 | logic candidate | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 2.000300 | 1.000000 | Requires GUI semantic confirmation before using as formal internal LVRT explanation. |
| `Dblk_Rotor` | 235 | `3IBR_24.out` | 6 | logic candidate | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 2.000300 | 1.000000 | Requires GUI semantic confirmation before using as formal internal LVRT explanation. |
| `Freq_PLL` | 304 | `3IBR_31.out` | 5 | Hz-like internal PLL candidate | 60.020707 | 51.000000 | 59.980114 | 69.000000 | 2.008600 | 60.003027 | Requires GUI semantic confirmation before using as formal internal LVRT explanation. |

??????`Wpu` ?????? `1.205632`??????? `1.218622`??????? `1.200021`???????????????????????????  
?????`Freq_PLL` ?????? `51.000` ? `69.000` ??????? Type-3 ?? PLL ??????? `SPD30` ?????

## ? POC ????????

- `VIBR1_2` ? `2.0-2.15 s` ??????? `0.057865`?
- ???????????? `197.603 kA`?????????????
- `Edc_pu` ???`Ecap_Det` ???RSC/GSC ??????????????????? POC ?????????
- ??? `4.0-5.0 s`?`PIBR1_2` ???? `199.197 MW`?`VIBR1_2` ???? `0.996965`?

## ????? / ???? / ?????

??????
- ?????????? `3IBR.inf` ? `3IBR_*.out`?????????
- ?? POC ???P/Q??????Dblk/Vwind/BRK ?????????
- ?? Type-3 ?? PGB ?????????????? DC-link?RSC/GSC ???Crowbar ???Chopper??????PLL ???

?????
- DC-link ????????/?????
- RSC/GSC ??????????????
- ?????? `Wpu` ???????????????
- Crowbar ??????????????? Crowbar ????

???????????? GUI ??????
1. `S1`?`Mono_out`?`Reset`?`Iovercur` ??????? Crowbar ????? 1/0 ???
2. `Ecap_Det` ????`Edc_pu` ??????????????? DC-link kV/pu?
3. `I_RS:1..3`?`Iconv:1..3`?`Crowbar current:1..3` ??????????
4. ??? `Iqr_pu/Pg_pu/Qg_pu` ??????????????

## ??

?? 5 s ??????????????????? POC ????????Type-3 ???????????? P/V ?????????? DC-link ???RSC/GSC ????????????Crowbar ????????????????????????? GUI ?????????????????????
