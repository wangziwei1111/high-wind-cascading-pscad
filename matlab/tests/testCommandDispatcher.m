function tests = testCommandDispatcher
tests = functiontests(localfunctions);
end

function testLoadShedFractionBroadcasts(testCase)
raw = struct();
raw.lineTrip = false(46,1);
raw.windCommand = repmat("hold_connected",3,1);
raw.generatorTrip = false(10,1);
raw.loadShedding = struct('fraction', 0.25);
raw.deviceTrip = false(39,1);
obs = struct('line_online', true(46,1), 'wind_online', true(3,1), 'gen_online', true(10,1), 'load_online', true(4,1));
cmd = cfm.CommandDispatcher(raw, obs, struct());
verifyTrue(testCase, all(cmd.load_shed_cmd));
verifyEqual(testCase, cmd.load_shed_fraction, 0.25 * ones(4,1));
end
