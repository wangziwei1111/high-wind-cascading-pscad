function trace = TraceReader(traceCsv)
%TRACEREADER Read a PSCAD observation/feedback trace with standard aliases.
trace = readtable(traceCsv);
trace = normalizeNames(trace);
required = {'time_s'};
missing = setdiff(required, trace.Properties.VariableNames);
if ~isempty(missing)
    error('TraceReader:MissingColumns', 'Trace is missing columns: %s', strjoin(missing, ', '));
end
end

function tableOut = normalizeNames(tableIn)
tableOut = tableIn;
names = tableOut.Properties.VariableNames;
for i = 1:numel(names)
    canonical = canonicalName(names{i});
    if ~strcmp(canonical, names{i})
        tableOut.Properties.VariableNames{i} = canonical;
    end
end
end

function name = canonicalName(name)
lowerName = lower(regexprep(name, '[^A-Za-z0-9]+', '_'));
lowerName = regexprep(lowerName, '^_+|_+$', '');
switch lowerName
    case {'time', 't', 'time_s'}
        name = 'time_s';
    case {'wf33_pcc_vpu', 'wf33_v_pu', 'wf33_pcc_v_pu'}
        name = 'wf33_v_pu';
    case {'wf35_pcc_vpu', 'wf35_v_pu', 'wf35_pcc_v_pu'}
        name = 'wf35_v_pu';
    case {'wf38_pcc_vpu', 'wf38_v_pu', 'wf38_pcc_v_pu'}
        name = 'wf38_v_pu';
    case {'wf33_p_mw', 'wf33_pcc_p', 'wf33_pcc_p_mw'}
        name = 'wf33_p_mw';
    case {'wf35_p_mw', 'wf35_pcc_p', 'wf35_pcc_p_mw'}
        name = 'wf35_p_mw';
    case {'wf38_p_mw', 'wf38_pcc_p', 'wf38_pcc_p_mw'}
        name = 'wf38_p_mw';
    case {'wf33_online'}
        name = 'wf33_online';
    case {'wf35_online'}
        name = 'wf35_online';
    case {'wf38_online'}
        name = 'wf38_online';
    case {'wf33_trip_cmd'}
        name = 'wf33_trip_cmd';
    case {'wf35_trip_cmd'}
        name = 'wf35_trip_cmd';
    case {'wf38_trip_cmd'}
        name = 'wf38_trip_cmd';
    case {'wf33_brk_state', 'wf33_breaker_state'}
        name = 'wf33_brk_state';
    case {'wf35_brk_state', 'wf35_breaker_state'}
        name = 'wf35_brk_state';
    case {'wf38_brk_state', 'wf38_breaker_state'}
        name = 'wf38_brk_state';
    otherwise
        name = lowerName;
end
end
