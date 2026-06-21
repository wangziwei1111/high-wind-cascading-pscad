function [command, state, event] = LVRTProtection(voltagePu, dt, connected, settings, state)
%LVRTPROTECTION Parameterized low-voltage ride-through protection.
arguments
    voltagePu (:,1) double
    dt (1,1) double {mustBeNonnegative}
    connected (:,1) logical
    settings struct = struct()
    state struct = struct()
end
settings = cfm.defaultStruct(settings, struct( ...
    'lowVoltagePu', 0.9, 'deepVoltagePu', 0.2, 'deepDelay_s', 0.625, ...
    'lowDelay_s', 2.0, 'ids', []));
n = numel(voltagePu);
if ~isfield(state, 'timer_s'), state.timer_s = zeros(n,1); end
if ~isfield(state, 'tripped'), state.tripped = false(n,1); end
if isempty(settings.ids), settings.ids = "wind_" + string((1:n)'); end
command = repmat("hold_connected", n, 1);
event = cfm.emptyEvent();
for k = 1:n
    if ~connected(k) || state.tripped(k)
        command(k) = "already_disconnected";
        state.timer_s(k) = 0;
        continue
    end
    if voltagePu(k) >= settings.lowVoltagePu
        state.timer_s(k) = 0;
        continue
    end
    command(k) = "protection_timing";
    state.timer_s(k) = state.timer_s(k) + dt;
    delay = settings.lowDelay_s;
    threshold = settings.lowVoltagePu;
    if voltagePu(k) <= settings.deepVoltagePu
        delay = settings.deepDelay_s;
        threshold = settings.deepVoltagePu;
    end
    if state.timer_s(k) >= delay
        command(k) = "disconnect_wind_farm";
        state.tripped(k) = true;
        event(end+1) = cfm.EventLogger(0, "lvrt_trip", settings.ids(k), voltagePu(k), threshold, delay, "disconnect_wind_farm", "parameterized LVRT curve"); %#ok<AGROW>
    end
end
end

