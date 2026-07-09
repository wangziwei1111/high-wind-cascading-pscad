function cmd = CommandDispatcher(raw, obs)
%COMMANDDISPATCHER Convert VRT raw output into the PSCAD command contract.

if isfield(obs, 'wind_online')
    nWind = numel(obs.wind_online);
else
    nWind = 3;
end

cmd = struct();
cmd.wind_disconnect_cmd = false(nWind, 1);
if isfield(raw, 'wind_disconnect_cmd')
    value = logical(raw.wind_disconnect_cmd(:));
    cmd.wind_disconnect_cmd(1:min(nWind, numel(value))) = value(1:min(nWind, numel(value)));
end
cmd.any_action = any(cmd.wind_disconnect_cmd(:));
end
