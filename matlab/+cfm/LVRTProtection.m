function [command, state, event] = LVRTProtection(voltagePu, dt, connected, settings, state)
%LVRTPROTECTION Wind low/high-voltage ride-through trip logic.
arguments
    voltagePu (:,1) double
    dt (1,1) double {mustBeNonnegative}
    connected (:,1) logical
    settings struct = struct()
    state struct = struct()
end
settings = cfm.defaultStruct(settings, struct( ...
    'lowVoltagePu', 0.9, 'deepVoltagePu', 0.2, 'deepDelay_s', 0.625, ...
    'lowDelay_s', 2.0, 'highVoltagePu', 1.1, 'highDelay_s', 10.0, ...
    'higherVoltagePu', 1.2, 'higherDelay_s', 1.0, ...
    'severeHighVoltagePu', 1.25, 'severeHighDelay_s', 0.5, ...
    'instantLowVoltagePu', 0.2, 'instantHighVoltagePu', 1.3, 'ids', []));
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
    if voltagePu(k) > settings.instantHighVoltagePu || voltagePu(k) <= settings.instantLowVoltagePu
        command(k) = "disconnect_wind_farm";
        state.tripped(k) = true;
        event(end+1) = cfm.EventLogger(0, "vrt_instant_trip", settings.ids(k), voltagePu(k), nearestThreshold(voltagePu(k), settings.instantLowVoltagePu, settings.instantHighVoltagePu), 0, "disconnect_wind_farm", "instant VRT boundary"); %#ok<AGROW>
        continue
    end
    if voltagePu(k) >= settings.lowVoltagePu && voltagePu(k) < settings.highVoltagePu
        state.timer_s(k) = 0;
        continue
    end
    command(k) = "protection_timing";
    state.timer_s(k) = state.timer_s(k) + dt;
    if voltagePu(k) < settings.lowVoltagePu
        slope = (settings.lowDelay_s - settings.deepDelay_s) / (settings.lowVoltagePu - settings.deepVoltagePu);
        delay = settings.deepDelay_s + slope * max(voltagePu(k) - settings.deepVoltagePu, 0);
        threshold = settings.lowVoltagePu;
        eventType = "lvrt_trip";
    elseif voltagePu(k) >= settings.severeHighVoltagePu
        delay = settings.severeHighDelay_s;
        threshold = settings.severeHighVoltagePu;
        eventType = "hvrt_trip";
    elseif voltagePu(k) >= settings.higherVoltagePu
        delay = settings.higherDelay_s;
        threshold = settings.higherVoltagePu;
        eventType = "hvrt_trip";
    else
        delay = settings.highDelay_s;
        threshold = settings.highVoltagePu;
        eventType = "hvrt_trip";
    end
    if state.timer_s(k) >= delay
        command(k) = "disconnect_wind_farm";
        state.tripped(k) = true;
        event(end+1) = cfm.EventLogger(0, eventType, settings.ids(k), voltagePu(k), threshold, delay, "disconnect_wind_farm", "parameterized VRT curve"); %#ok<AGROW>
    end
end
end

function threshold = nearestThreshold(value, lowThreshold, highThreshold)
if value <= lowThreshold
    threshold = lowThreshold;
else
    threshold = highThreshold;
end
end
