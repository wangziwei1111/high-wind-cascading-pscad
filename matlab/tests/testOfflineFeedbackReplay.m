function tests = testOfflineFeedbackReplay
tests = functiontests(localfunctions);
end

function testTripScheduleGenerationFromTrace(testCase)
workDir = tempname;
mkdir(workDir);
traceCsv = fullfile(workDir, 'obs_trace.csv');
scheduleCsv = fullfile(workDir, 'trip_schedule.csv');

trace = sampleObservationTrace();
writetable(trace, traceCsv);

schedule = compute_trip_schedule_from_pscad_trace(traceCsv, scheduleCsv, 99);

verifyTrue(testCase, isfile(scheduleCsv));
verifyEqual(testCase, height(schedule), 3);
verifyEqual(testCase, string(schedule.target_id(:)), ["wind_33"; "wind_35"; "wind_38"]);
verifyEqual(testCase, schedule.trip_time_s(1), 99);
verifyEqual(testCase, schedule.trip_time_s(2), 99);
verifyEqual(testCase, schedule.trip_time_s(3), 2.02, 'AbsTol', 1e-9);
verifyEqual(testCase, string(schedule.source_protection(3)), "VRTProtection");
verifyLessThan(testCase, schedule.measured_value_at_decision(3), 0.2);
end

function testFeedbackReplayAuditPasses(testCase)
workDir = tempname;
mkdir(workDir);
obsCsv = fullfile(workDir, 'obs_trace.csv');
scheduleCsv = fullfile(workDir, 'trip_schedule.csv');
feedbackCsv = fullfile(workDir, 'feedback_trace.csv');
outDir = fullfile(workDir, 'audit');

writetable(sampleObservationTrace(), obsCsv);
schedule = compute_trip_schedule_from_pscad_trace(obsCsv, scheduleCsv, 99);
feedback = sampleFeedbackTrace();
writetable(feedback, feedbackCsv);

[eventChain, summary] = audit_feedback_replay(obsCsv, scheduleCsv, feedbackCsv, outDir);

verifyTrue(testCase, summary.all_passed);
verifyEqual(testCase, summary.passed_targets, 3);
verifyEqual(testCase, height(eventChain), 3);
verifyEqual(testCase, eventChain.command_transition_s(3), 2.02, 'AbsTol', 1e-9);
verifyTrue(testCase, isfile(fullfile(outDir, 'event_chain.csv')));
verifyTrue(testCase, isfile(fullfile(outDir, 'run_summary.json')));
verifyTrue(testCase, isfile(fullfile(outDir, 'validation_report.md')));
end

function trace = sampleObservationTrace()
time_s = (1.98:0.01:2.08).';
WF33_PCC_VPU = ones(size(time_s));
WF35_PCC_VPU = ones(size(time_s));
WF38_PCC_VPU = ones(size(time_s));
WF38_PCC_VPU(time_s >= 2.01) = 0.47;
WF38_PCC_VPU(time_s >= 2.02) = 0.19;
WF38_PCC_VPU(time_s >= 2.03) = 0.08;
WF33_P_MW = 632 * ones(size(time_s));
WF35_P_MW = 650 * ones(size(time_s));
WF38_P_MW = 830 * ones(size(time_s));
WF33_ONLINE = ones(size(time_s));
WF35_ONLINE = ones(size(time_s));
WF38_ONLINE = ones(size(time_s));
trace = table(time_s, WF33_PCC_VPU, WF35_PCC_VPU, WF38_PCC_VPU, ...
    WF33_P_MW, WF35_P_MW, WF38_P_MW, WF33_ONLINE, WF35_ONLINE, WF38_ONLINE);
end

function trace = sampleFeedbackTrace()
time_s = (1.98:0.01:2.08).';
WF33_TRIP_CMD = zeros(size(time_s));
WF35_TRIP_CMD = zeros(size(time_s));
WF38_TRIP_CMD = double(time_s >= 2.02);
WF33_BRK_STATE = zeros(size(time_s));
WF35_BRK_STATE = zeros(size(time_s));
WF38_BRK_STATE = 2 * double(time_s >= 2.02);
WF33_P_MW = 632 * ones(size(time_s));
WF35_P_MW = 650 * ones(size(time_s));
WF38_P_MW = 830 * double(time_s < 2.02);
trace = table(time_s, WF33_TRIP_CMD, WF35_TRIP_CMD, WF38_TRIP_CMD, ...
    WF33_BRK_STATE, WF35_BRK_STATE, WF38_BRK_STATE, WF33_P_MW, WF35_P_MW, WF38_P_MW);
end
