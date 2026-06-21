function tests = testProtectionLogic
tests = functiontests(localfunctions);
end

function testSlightOverloadDoesNotTripImmediately(testCase)
state = struct();
[trip, state] = cfm.OverloadProtection(1.05, 0.1, true, struct(), state);
verifyFalse(testCase, trip);
verifyGreaterThan(testCase, state.timer_s, 0);
end

function testSevereOverloadTripsEarlier(testCase)
state = struct();
trip = false;
for k = 1:12
    [trip, state] = cfm.OverloadProtection(1.5, 0.1, true, struct(), state);
    if trip, break; end
end
verifyTrue(testCase, trip);
verifyLessThan(testCase, state.timer_s, 5.0);
end

function testLvrtShortDipRecovers(testCase)
state = struct();
for k = 1:5
    [cmd, state] = cfm.LVRTProtection(0.5, 0.1, true, struct(), state);
end
verifyEqual(testCase, cmd, "protection_timing");
[cmd, state] = cfm.LVRTProtection(1.0, 0.1, true, struct(), state);
verifyEqual(testCase, cmd, "hold_connected");
verifyEqual(testCase, state.timer_s, 0);
end

function testLvrtDeepDipTripsAfterTimeout(testCase)
state = struct();
cmd = "hold_connected";
for k = 1:7
    [cmd, state] = cfm.LVRTProtection(0.1, 0.1, true, struct(), state);
end
verifyEqual(testCase, cmd, "disconnect_wind_farm");
verifyTrue(testCase, state.tripped);
end

function testUflsStagesOnlyActOnce(testCase)
state = struct();
[shed1, state] = cfm.UFLS_UVLS(48.9, 1.0, 0.2, true(3,1), struct(), state);
[shed2, state] = cfm.UFLS_UVLS(48.9, 1.0, 0.2, true(3,1), struct(), state);
verifyTrue(testCase, shed1.uflsStages(1));
verifyFalse(testCase, shed2.uflsStages(1));
verifyTrue(testCase, state.uflsDone(1));
end

function testTrippedLineDoesNotRepeatEvent(testCase)
state = struct();
[~, state, e1] = cfm.OverloadProtection(2.1, 0.1, true, struct(), state);
[~, ~, e2] = cfm.OverloadProtection(2.1, 0.1, true, struct(), state);
verifyEqual(testCase, numel(e1), 1);
verifyEqual(testCase, numel(e2), 0);
end

function testEventLogSortsByTime(testCase)
e = [cfm.EventLogger(2,"a","x",1,1,0,"cmd",""), cfm.EventLogger(1,"b","y",1,1,0,"cmd","")];
[~, idx] = sort([e.time_s]);
e = e(idx);
verifyEqual(testCase, [e.time_s], [1 2]);
end
