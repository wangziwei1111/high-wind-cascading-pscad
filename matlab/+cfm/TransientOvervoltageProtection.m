function [trip, state, event] = TransientOvervoltageProtection(voltagePu, dt, deviceOnline, settings, state)
%TRANSIENTOVERVOLTAGEPROTECTION Instantaneous or delayed TOV trip command.
arguments
    voltagePu (:,1) double
    dt (1,1) double {mustBeNonnegative}
    deviceOnline (:,1) logical
    settings struct = struct()
    state struct = struct()
end
settings = cfm.defaultStruct(settings, struct('thresholdPu', 1.3, 'delay_s', 0.0, 'ids', []));
n = numel(voltagePu);
if ~isfield(state, 'timer_s'), state.timer_s = zeros(n,1); end
if ~isfield(state, 'tripped'), state.tripped = false(n,1); end
if isempty(settings.ids), settings.ids = "device_" + string((1:n)'); end
trip = false(n,1);
event = cfm.emptyEvent();
for k = 1:n
    if ~deviceOnline(k) || state.tripped(k)
        state.timer_s(k) = 0;
        continue
    end
    if voltagePu(k) >= settings.thresholdPu
        state.timer_s(k) = state.timer_s(k) + dt;
        if state.timer_s(k) >= settings.delay_s
            trip(k) = true;
            state.tripped(k) = true;
            event(end+1) = cfm.EventLogger(0, "transient_overvoltage", settings.ids(k), voltagePu(k), settings.thresholdPu, settings.delay_s, "trip_device", "TOV protection"); %#ok<AGROW>
        end
    else
        state.timer_s(k) = 0;
    end
end
end

