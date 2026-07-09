function [eventChain, summary] = FeedbackReplayAuditor(schedule, feedbackTrace, tolerance_s, noTripTime_s)
%FEEDBACKREPLAYAUDITOR Validate PSCAD feedback replay against a schedule.
if nargin < 3 || isempty(tolerance_s)
    tolerance_s = 0.015;
end
if nargin < 4 || isempty(noTripTime_s)
    noTripTime_s = 90.0;
end

rows = repmat(struct( ...
    'target_id', '', ...
    'target_type', '', ...
    'action', '', ...
    'scheduled_time_s', NaN, ...
    'command_transition_s', NaN, ...
    'breaker_transition_s', NaN, ...
    'status', '', ...
    'notes', ''), 0, 1);

for i = 1:height(schedule)
    targetId = char(schedule.target_id(i));
    prefix = lower(strrep(targetId, 'wind_', 'wf'));
    cmdColumn = [prefix '_trip_cmd'];
    stateColumn = [prefix '_brk_state'];
    cmdTime = transitionTime(feedbackTrace, cmdColumn, 0.5);
    stateTime = transitionTime(feedbackTrace, stateColumn, 1.0);
    scheduledTime = schedule.trip_time_s(i);

    if scheduledTime >= noTripTime_s || isnan(scheduledTime)
        ok = isnan(cmdTime) && isnan(stateTime);
        expected = 'expected no trip';
    else
        ok = ~isnan(cmdTime) && ~isnan(stateTime) && ...
            abs(cmdTime - scheduledTime) <= tolerance_s && ...
            abs(stateTime - scheduledTime) <= tolerance_s;
        expected = sprintf('expected trip at %.6g s', scheduledTime);
    end

    status = 'pass';
    if ~ok
        status = 'fail';
    end

    rows(end + 1, 1) = struct( ... %#ok<AGROW>
        'target_id', targetId, ...
        'target_type', char(schedule.target_type(i)), ...
        'action', char(schedule.action(i)), ...
        'scheduled_time_s', scheduledTime, ...
        'command_transition_s', cmdTime, ...
        'breaker_transition_s', stateTime, ...
        'status', status, ...
        'notes', expected);
end

eventChain = struct2table(rows);
summary = struct();
summary.total_scheduled_targets = height(schedule);
summary.passed_targets = sum(strcmp(eventChain.status, 'pass'));
summary.failed_targets = sum(strcmp(eventChain.status, 'fail'));
summary.all_passed = summary.failed_targets == 0;
end

function t = transitionTime(trace, columnName, threshold)
if ~ismember(columnName, trace.Properties.VariableNames)
    error('FeedbackReplayAuditor:MissingColumns', 'Feedback trace is missing column: %s', columnName);
end
values = trace.(columnName);
times = trace.time_s;
t = NaN;
for i = 2:numel(values)
    if values(i - 1) < threshold && values(i) >= threshold
        t = times(i);
        return
    end
end
end
