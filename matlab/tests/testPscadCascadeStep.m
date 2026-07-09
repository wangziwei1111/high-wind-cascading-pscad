function tests = testPscadCascadeStep
tests = functiontests(localfunctions);
end

function testVectorCommandContract(testCase)
obs = baseObs();
obs.line_loading_pu(2) = 2.2;
[cmd, ~, events] = pscad_cascade_step(1.0, 0.1, obs, [], default_protection_settings());
verifySize(testCase, cmd.line_trip_cmd, [46 1]);
verifyTrue(testCase, cmd.line_trip_cmd(2));
verifyTrue(testCase, cmd.any_action);
verifyEqual(testCase, events(1).time_s, 1.0);
end

function testClosedLoopFeedbackSuppressesRepeatedLineTrip(testCase)
obs = baseObs();
obs.line_loading_pu(4) = 2.2;
[cmd1, state] = pscad_cascade_step(1.0, 0.1, obs, [], default_protection_settings());
obs.line_online(4) = false;
[cmd2, ~] = pscad_cascade_step(1.1, 0.1, obs, state, default_protection_settings());
verifyTrue(testCase, cmd1.line_trip_cmd(4));
verifyFalse(testCase, cmd2.line_trip_cmd(4));
end

function obs = baseObs()
obs.bus_voltage_pu = ones(39,1);
obs.bus_frequency_Hz = 50 * ones(39,1);
obs.line_loading_pu = zeros(46,1);
obs.line_online = true(46,1);
obs.wind_pcc_voltage_pu = ones(3,1);
obs.wind_online = true(3,1);
obs.gen_voltage_pu = ones(10,1);
obs.gen_frequency_Hz = 50 * ones(10,1);
obs.gen_online = true(10,1);
obs.load_voltage_pu = ones(19,1);
obs.load_online = true(19,1);
obs.simulation_time_s = 0;
obs.interface_dt_s = 0.1;
end
