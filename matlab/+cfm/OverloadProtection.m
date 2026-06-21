function [trip, state, event] = OverloadProtection(loadRatio, dt, lineState, settings, state)
%OVERLOADPROTECTION Inverse-time line overload protection.
arguments
    loadRatio (:,1) double
    dt (1,1) double {mustBeNonnegative}
    lineState (:,1) logical
    settings struct = struct()
    state struct = struct()
end
settings = cfm.defaultStruct(settings, struct( ...
    'pickup', 1.0, 'anchorRatio', 1.1, 'anchorDelay_s', 5.0, ...
    'curveExponent', 1.0, 'instantaneousRatio', 2.0, 'ids', []));
n = numel(loadRatio);
if ~isfield(state, 'timer_s'), state.timer_s = zeros(n,1); end
if ~isfield(state, 'tripped'), state.tripped = false(n,1); end
if isempty(settings.ids), settings.ids = "line_" + string((1:n)'); end
trip = false(n,1);
event = cfm.emptyEvent();
for k = 1:n
    if ~lineState(k) || state.tripped(k)
        state.timer_s(k) = 0;
        continue
    end
    if loadRatio(k) <= settings.pickup
        state.timer_s(k) = 0;
        continue
    end
    state.timer_s(k) = state.timer_s(k) + dt;
    if loadRatio(k) >= settings.instantaneousRatio
        delay = 0;
    else
        delay = settings.anchorDelay_s * ((settings.anchorRatio - settings.pickup) / max(loadRatio(k) - settings.pickup, eps)) ^ settings.curveExponent;
    end
    if state.timer_s(k) >= delay
        trip(k) = true;
        state.tripped(k) = true;
        event(end+1) = cfm.EventLogger(0, "line_overload", settings.ids(k), loadRatio(k), settings.pickup, delay, "trip_line", "inverse-time overload"); %#ok<AGROW>
    end
end
end

