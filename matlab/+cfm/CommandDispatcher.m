function cmd = CommandDispatcher(raw, obs, settings)
%COMMANDDISPATCHER Convert VRT raw output into the PSCAD command contract.
if nargin < 3
    settings = struct(); %#ok<NASGU>
end

if isfield(obs, 'line_online')
    nLine = numel(obs.line_online);
elseif isfield(raw, 'lineTrip')
    nLine = numel(raw.lineTrip);
else
    nLine = 46;
end

if isfield(obs, 'wind_online')
    nWind = numel(obs.wind_online);
else
    nWind = 3;
end
if isfield(obs, 'gen_online')
    nGen = numel(obs.gen_online);
elseif isfield(raw, 'generatorTrip')
    nGen = numel(raw.generatorTrip);
else
    nGen = 10;
end
if isfield(obs, 'load_online')
    nLoad = numel(obs.load_online);
else
    nLoad = 0;
end

cmd = struct();
cmd.line_trip_cmd = false(nLine, 1);
if isfield(raw, 'lineTrip')
    value = logical(raw.lineTrip(:));
    cmd.line_trip_cmd(1:min(nLine, numel(value))) = value(1:min(nLine, numel(value)));
    if isfield(obs, 'line_online')
        cmd.line_trip_cmd = cmd.line_trip_cmd & logical(obs.line_online(:));
    end
end

cmd.wind_disconnect_cmd = false(nWind, 1);
if isfield(raw, 'wind_disconnect_cmd')
    value = logical(raw.wind_disconnect_cmd(:));
    cmd.wind_disconnect_cmd(1:min(nWind, numel(value))) = value(1:min(nWind, numel(value)));
elseif isfield(raw, 'windCommand')
    value = string(raw.windCommand(:)) == "disconnect_wind_farm";
    cmd.wind_disconnect_cmd(1:min(nWind, numel(value))) = value(1:min(nWind, numel(value)));
end
if isfield(obs, 'wind_online')
    cmd.wind_disconnect_cmd = cmd.wind_disconnect_cmd & logical(obs.wind_online(:));
end

cmd.generator_trip_cmd = false(nGen, 1);
if isfield(raw, 'generatorTrip')
    value = logical(raw.generatorTrip(:));
    cmd.generator_trip_cmd(1:min(nGen, numel(value))) = value(1:min(nGen, numel(value)));
    if isfield(obs, 'gen_online')
        cmd.generator_trip_cmd = cmd.generator_trip_cmd & logical(obs.gen_online(:));
    end
end

cmd.load_shed_cmd = false(nLoad, 1);
cmd.load_shed_fraction = zeros(nLoad, 1);
if isfield(raw, 'loadShedding') && isstruct(raw.loadShedding) && isfield(raw.loadShedding, 'fraction')
    fraction = raw.loadShedding.fraction;
    if isscalar(fraction)
        cmd.load_shed_fraction(:) = fraction;
    else
        value = fraction(:);
        cmd.load_shed_fraction(1:min(nLoad, numel(value))) = value(1:min(nLoad, numel(value)));
    end
    cmd.load_shed_cmd = cmd.load_shed_fraction > 0;
    if isfield(obs, 'load_online')
        cmd.load_shed_cmd = cmd.load_shed_cmd & logical(obs.load_online(:));
    end
end

cmd.any_action = any(cmd.line_trip_cmd(:)) || any(cmd.wind_disconnect_cmd(:)) || ...
    any(cmd.generator_trip_cmd(:)) || any(cmd.load_shed_cmd(:));
end
