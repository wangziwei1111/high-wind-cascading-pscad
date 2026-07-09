function [eventChain, summary] = audit_feedback_replay(obsTraceCsv, tripScheduleCsv, feedbackTraceCsv, outputDir)
%AUDIT_FEEDBACK_REPLAY Audit Run B feedback against a MATLAB trip schedule.
if nargin < 4 || isempty(outputDir)
    outputDir = fullfile('results', 'offline_feedback_audit');
end
if ~isfolder(outputDir)
    mkdir(outputDir);
end

% Read obsTraceCsv to keep the public API explicit for the full audit step.
if ~isempty(obsTraceCsv)
    cfm.TraceReader(obsTraceCsv);
end
schedule = readtable(tripScheduleCsv, 'Delimiter', ',', 'VariableNamingRule', 'preserve');
schedule = normalizeScheduleNames(schedule);
feedbackTrace = cfm.TraceReader(feedbackTraceCsv);
[eventChain, summary] = cfm.FeedbackReplayAuditor(schedule, feedbackTrace);

writetable(eventChain, fullfile(outputDir, 'event_chain.csv'));
writeText(fullfile(outputDir, 'run_summary.json'), jsonencode(summary));
writeReport(fullfile(outputDir, 'validation_report.md'), summary, eventChain);
end

function writeReport(path, summary, eventChain)
lines = {
    '# Offline Feedback Replay Validation'
    ''
    sprintf('- total scheduled targets: %d', summary.total_scheduled_targets)
    sprintf('- passed targets: %d', summary.passed_targets)
    sprintf('- failed targets: %d', summary.failed_targets)
    sprintf('- all passed: %d', summary.all_passed)
    ''
    '## Event Chain'
    ''
};
for i = 1:height(eventChain)
    lines{end + 1, 1} = sprintf('- %s: %s, scheduled %.6g s, command %.6g s, breaker %.6g s', ...
        char(eventChain.target_id(i)), char(eventChain.status(i)), eventChain.scheduled_time_s(i), ...
        eventChain.command_transition_s(i), eventChain.breaker_transition_s(i)); %#ok<AGROW>
end
writeText(path, strjoin(lines, newline));
end

function writeText(path, text)
fid = fopen(path, 'w');
if fid < 0
    error('audit_feedback_replay:WriteFailed', 'Could not write %s', path);
end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, '%s', text);
end

function schedule = normalizeScheduleNames(schedule)
names = schedule.Properties.VariableNames;
for i = 1:numel(names)
    name = lower(regexprep(names{i}, '[^A-Za-z0-9]+', '_'));
    name = regexprep(name, '^_+|_+$', '');
    switch name
        case {'target_id', 'targetid'}
            schedule.Properties.VariableNames{i} = 'target_id';
        case {'target_type', 'targettype'}
            schedule.Properties.VariableNames{i} = 'target_type';
        case 'action'
            schedule.Properties.VariableNames{i} = 'action';
        case {'trip_time_s', 'triptime_s', 'triptimes'}
            schedule.Properties.VariableNames{i} = 'trip_time_s';
        case {'source_protection', 'sourceprotection'}
            schedule.Properties.VariableNames{i} = 'source_protection';
        case {'measured_value_at_decision', 'measuredvalueatdecision'}
            schedule.Properties.VariableNames{i} = 'measured_value_at_decision';
        case 'criterion'
            schedule.Properties.VariableNames{i} = 'criterion';
        case 'notes'
            schedule.Properties.VariableNames{i} = 'notes';
    end
end
end
