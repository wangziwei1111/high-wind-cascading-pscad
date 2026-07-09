function exportRunLogs(outputDir, obsTrace, cmdTrace, breakerActionTrace, eventChain, runSummary)
%EXPORTRUNLOGS Export clean rebuild audit traces.
if nargin < 1 || isempty(outputDir)
    outputDir = fullfile(pwd, '..', 'results');
end
if ~exist(outputDir, 'dir')
    mkdir(outputDir);
end
writeMaybeTable(fullfile(outputDir, 'obs_trace.csv'), obsTrace);
writeMaybeTable(fullfile(outputDir, 'cmd_trace.csv'), cmdTrace);
writeMaybeTable(fullfile(outputDir, 'breaker_action_trace.csv'), breakerActionTrace);
writeMaybeTable(fullfile(outputDir, 'event_chain.csv'), eventChain);
fid = fopen(fullfile(outputDir, 'run_summary.json'), 'w');
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, '%s\n', jsonencode(runSummary));
end

function writeMaybeTable(path, value)
if istable(value)
    writetable(value, path);
elseif isstruct(value)
    writetable(struct2table(value), path);
else
    writematrix(value, path);
end
end
