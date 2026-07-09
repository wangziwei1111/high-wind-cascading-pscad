function schedule = compute_trip_schedule_from_pscad_trace(obsTraceCsv, outputScheduleCsv, noTripTime_s)
%COMPUTE_TRIP_SCHEDULE_FROM_PSCAD_TRACE Create a standard trip schedule.
if nargin < 2
    outputScheduleCsv = '';
end
if nargin < 3 || isempty(noTripTime_s)
    noTripTime_s = 99.0;
end

trace = cfm.TraceReader(obsTraceCsv);
required = {'wf33_v_pu', 'wf35_v_pu', 'wf38_v_pu'};
missing = setdiff(required, trace.Properties.VariableNames);
if ~isempty(missing)
    error('compute_trip_schedule_from_pscad_trace:MissingColumns', ...
        'Observation trace is missing columns: %s', strjoin(missing, ', '));
end

settings = default_protection_settings();
windIds = string(settings.wind.ids(:));
state = [];
online = true(numel(windIds), 1);
tripTimes = nan(numel(windIds), 1);
measuredValues = nan(numel(windIds), 1);
criteria = strings(numel(windIds), 1);

for i = 1:height(trace)
    t = trace.time_s(i);
    if i == 1
        dt = 0;
    else
        dt = trace.time_s(i) - trace.time_s(i - 1);
    end

    obs = struct();
    obs.wind_pcc_voltage_pu = [trace.wf33_v_pu(i); trace.wf35_v_pu(i); trace.wf38_v_pu(i)];
    obs.wind_active_power_MW = optionalVector(trace, i, {'wf33_p_mw', 'wf35_p_mw', 'wf38_p_mw'}, [632; 650; 830]);
    obs.wind_online = online;
    obs.simulation_time_s = t;
    obs.interface_dt_s = dt;

    [cmd, state, events] = pscad_cascade_step(t, dt, obs, state, settings);
    newlyTripped = cmd.wind_disconnect_cmd(:) & online;
    for k = find(newlyTripped).'
        tripTimes(k) = t;
        measuredValues(k) = obs.wind_pcc_voltage_pu(k);
        criteria(k) = criterionFromEvents(events, windIds(k));
    end
    online(newlyTripped) = false;
end

tripTimes(isnan(tripTimes)) = noTripTime_s;
schedule = table( ...
    windIds, ...
    repmat("wind_farm", numel(windIds), 1), ...
    repmat("disconnect_wind_farm", numel(windIds), 1), ...
    tripTimes, ...
    repmat("VRTProtection", numel(windIds), 1), ...
    measuredValues, ...
    criteria, ...
    repmat("Generated from PSCAD observation trace by offline feedback workflow.", numel(windIds), 1), ...
    'VariableNames', {'target_id', 'target_type', 'action', 'trip_time_s', ...
    'source_protection', 'measured_value_at_decision', 'criterion', 'notes'});

if ~isempty(outputScheduleCsv)
    cfm.TripScheduleWriter(schedule, outputScheduleCsv);
end
end

function values = optionalVector(trace, rowIndex, names, defaults)
values = defaults;
for i = 1:numel(names)
    if ismember(names{i}, trace.Properties.VariableNames)
        values(i) = trace.(names{i})(rowIndex);
    end
end
end

function criterion = criterionFromEvents(events, targetId)
criterion = "";
for i = 1:numel(events)
    if strcmp(string(events(i).target_id), targetId)
        criterion = string(events(i).description);
        return
    end
end
end
