function tests = testWindVRTTripShell
tests = functiontests(localfunctions);
end

function testImmediateLowVoltageTrip(testCase)
obs = baseObs();
obs.wind_pcc_voltage_pu(3) = 0.10;
[cmd, state, events] = pscad_cascade_step(0.01, 0.01, obs, [], default_protection_settings());
verifyTrue(testCase, cmd.wind_disconnect_cmd(3));
verifyTrue(testCase, cmd.any_action);
verifyTrue(testCase, state.wind_vrt.trip_commanded(3));
verifyEqual(testCase, events(1).target_id, 'wind_38');
verifyEqual(testCase, events(1).event_type, 'wind_vrt_trip');
end

function testInterpolatedLowVoltageDoesNotTripBeforeDelay(testCase)
obs = baseObs();
obs.wind_pcc_voltage_pu(3) = 0.50;
state = [];
cmd = [];
for i = 1:5
    [cmd, state] = pscad_cascade_step(i * 0.1, 0.1, obs, state, default_protection_settings());
end
verifyFalse(testCase, cmd.wind_disconnect_cmd(3));
verifyGreaterThan(testCase, state.wind_vrt.timer_s(3), 0);
end

function testInterpolatedLowVoltageTripsAfterDelay(testCase)
obs = baseObs();
obs.wind_pcc_voltage_pu(3) = 0.50;
state = [];
cmd = [];
for i = 1:13
    [cmd, state] = pscad_cascade_step(i * 0.1, 0.1, obs, state, default_protection_settings());
end
verifyTrue(testCase, cmd.wind_disconnect_cmd(3));
verifyTrue(testCase, state.wind_vrt.trip_commanded(3));
end

function testHighVoltageTripAfterHalfSecond(testCase)
obs = baseObs();
obs.wind_pcc_voltage_pu(2) = 1.26;
state = [];
cmd = [];
for i = 1:4
    [cmd, state] = pscad_cascade_step(i * 0.1, 0.1, obs, state, default_protection_settings());
end
verifyFalse(testCase, cmd.wind_disconnect_cmd(2));
for i = 5:6
    [cmd, state] = pscad_cascade_step(i * 0.1, 0.1, obs, state, default_protection_settings());
end
verifyTrue(testCase, cmd.wind_disconnect_cmd(2));
end

function testNormalVoltageResetsTimer(testCase)
obs = baseObs();
obs.wind_pcc_voltage_pu(1) = 0.50;
[~, state] = pscad_cascade_step(0.1, 0.1, obs, [], default_protection_settings());
verifyGreaterThan(testCase, state.wind_vrt.timer_s(1), 0);

obs.wind_pcc_voltage_pu(1) = 1.00;
[cmd, state] = pscad_cascade_step(0.2, 0.1, obs, state, default_protection_settings());
verifyFalse(testCase, cmd.wind_disconnect_cmd(1));
verifyEqual(testCase, state.wind_vrt.timer_s(1), 0);
end

function testOfflineFeedbackConfirmsTripWithoutRepeatingCommand(testCase)
obs = baseObs();
obs.wind_pcc_voltage_pu(3) = 0.10;
[cmd1, state] = pscad_cascade_step(0.01, 0.01, obs, [], default_protection_settings());
verifyTrue(testCase, cmd1.wind_disconnect_cmd(3));

obs.wind_online(3) = false;
[cmd2, state] = pscad_cascade_step(0.02, 0.01, obs, state, default_protection_settings());
verifyFalse(testCase, cmd2.wind_disconnect_cmd(3));
verifyTrue(testCase, state.wind_vrt.tripped(3));
end

function obs = baseObs()
obs.wind_pcc_voltage_pu = ones(3, 1);
obs.wind_active_power_MW = [632; 650; 830];
obs.wind_online = true(3, 1);
obs.simulation_time_s = 0;
obs.interface_dt_s = 0.1;
end
