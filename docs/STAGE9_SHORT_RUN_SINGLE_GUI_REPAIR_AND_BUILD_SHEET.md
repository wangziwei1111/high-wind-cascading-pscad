# Stage 9 short-run single GUI repair and Build sheet

Do not open the main `3IBR` project. Open only `3IBR_DFIG1_TRIAL`.

## A. Repair the Timer inactive value

1. In the project Definitions list, open `PAPER_OVL1_RELAY`, then open its
   `Schematic`.
2. Find the chain `1 - ABOVE_TH -> Timer -> Simple Set/Reset Latch`.
3. The Timer has: left `F`, top `On`, bottom `Off`, and right `O`.
4. Double-click the **lower** Constant `1.0` connected directly to the Timer
   bottom `Off` (`VOff`) port. Its component ID is `522397627`.
5. Change only its Value from `1.0` to `0.0`, then click **OK**.
6. Do not change the upper Constant `1.0` connected to Timer top `On` (`VOn`).

No wire is to be removed or added. Preserve these connections exactly:

- `1 - ABOVE_TH -> Timer F`
- upper `1.0 -> Timer On`
- lower corrected `0.0 -> Timer Off`
- `Timer O -> TIMER_STATE` and `Timer O -> latch S`
- existing `0.0 -> latch R`
- latch `Q -> TRIP_REQ`; leave `Qbar` unused

Confirm without changing the Timer parameters:

- Timer Trigger Threshold: `0.5`
- Delay until ON: `5.0 s`
- Duration ON: `100 s`

Confirm without changing the latch parameters:

- mode: `Simple Set/Reset Latch`
- type: `RS`
- Initial State of Output Q: `Low [0]`
- Interpolation Compatibility: `Disabled`

## B. Set the short Run duration

1. Return to the trial project main canvas.
2. On the PSCAD 4.6 **Home** ribbon, in the Simulation settings area, set
   **Duration of Run (s)** from `20` to `9.0`.
3. Leave **Solution Time Step (us)** at `5`.
4. Leave **Channel Plot Step (us)** at `10000`.

Do not change Output Channel/PGB settings or output paths.

## C. Save and Build exactly once

1. Save `3IBR_DFIG1_TRIAL`.
2. Click **Build** once and wait for completion.
3. Confirm `Build Errors = 0`.
4. Do **not** Run, open Graph, or take a screenshot.

Expected static state after Build:

| Condition | TIMER | TRIP_REQUEST | BRK_CMD | BRK_STATE |
|---|---:|---:|---|---|
| t=0, ABOVE=0 | 0 | 0 | closed command (0) | closed |
| 0.20-0.45 s, ABOVE=0 | 0 | 0 | closed command (0) | closed |
| ABOVE continuously <5 s | 0 | 0 | closed command (0) | closed |
| ABOVE continuously 5 s | 1 | 1 | open command (1) | open |

Frozen: `E_28_29_1`, capacity `7.872883989661206 pu`, threshold `1.1`, delay
`5.0 s`, N29 fault `0.50-2.50 s`, breaker position/polarity, P/Q/S calculations,
13 Output Channels, EMTDC step, and plot step.
