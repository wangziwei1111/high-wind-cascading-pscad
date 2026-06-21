# Model Sources Audit

| Source | Model use | Contains PSCAD files | Downloaded | License status | Compatibility | Follow-up manual action |
| -- | ---- | ------------: | ----: | ----- | --- | ------ |
| PNNL Enhanced IEEE-39 three IBR | Preferred IEEE-39 dynamic network + multi-IBR base | Yes: `3IBR.pscx`, `ETRAN46.pslx`, `ETRAN_GF46.lib`, `.dyr` | Yes, local ignored clone | No LICENSE file found in repository; do not redistribute copied model files | README states PSCAD 5.0 used for shown results; E-TRAN runtime library included | Open in PSCAD GUI, load E-TRAN libraries, verify compile/run, identify three IBR buses and ports |
| PSCAD official IEEE 39 Bus System | Fallback IEEE-39 PSCAD benchmark | Official PSCAD benchmark page and technical note indicate PSCAD model | Not downloaded | PSCAD/MHI terms apply | Official benchmark; version/access to be verified through PSCAD account | Download only through official access; do not commit |
| PSCAD official Type-3 WTG v4.6 | Candidate manual WECC Type-3 DFIG replacement | Official example/model documentation | Not downloaded | PSCAD/MHI terms apply | PSCAD v4.6 article; v4.5 variant also exists | Import manually into PSCAD and adapt as aggregate wind farm only after license-compliant access |

PNNL README states the three-IBR folder contains PSSE, PSLF and PSCAD files for BusFault at bus 16 and Generator trip at Gen 32, and that IBRs use WECC-approved generic models. Local `READ ME.docx` for the three-IBR folder states PSCAD version 5.0 was used for shown results and the PSCAD model was converted from the PSSE raw file using E-TRAN.

Official sources used:

- [PNNL GitHub repository](https://github.com/pnnltestsystem/Enhanced-IEEE-39-Bus-System-with-Inverter-based-Resources-on-Multi-Time-Scale-Platforms)
- [PSCAD IEEE 39 Bus System](https://www.pscad.com/knowledge-base/article/28)
- [PSCAD Type 3 WTG for PSCAD v4.6](https://www.pscad.com/knowledge-base/article/496)
- [PSCAD Type-3 wind turbine model PDF](https://www.pscad.com/uploads/knowledge_base/type_3_wind_turbine_model.pdf)

