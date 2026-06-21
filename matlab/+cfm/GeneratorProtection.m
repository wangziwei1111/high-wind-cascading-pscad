function [trip, state, event] = GeneratorProtection(freqHz, voltagePu, dt, online, settings, state)
%GENERATORPROTECTION Frequency and voltage protection for conventional units.
arguments
    freqHz (:,1) double
    voltagePu (:,1) double
    dt (1,1) double {mustBeNonnegative}
    online (:,1) logical
    settings struct = struct()
    state struct = struct()
end
settings = cfm.defaultStruct(settings, struct( ...
    'underFreqHz', 47.5, 'overFreqHz', 51.5, 'freqDelay_s', 10.0, ...
    'underVoltagePu', 0.8, 'overVoltagePu', 1.3, 'voltageDelay_s', 2.0, 'ids', []));
n = numel(freqHz);
if ~isfield(state, 'timer_s'), state.timer_s = zeros(n,4); end
if ~isfield(state, 'tripped'), state.tripped = false(n,1); end
if isempty(settings.ids), settings.ids = "gen_" + string((1:n)'); end
trip = false(n,1);
event = cfm.emptyEvent();
checks = [freqHz < settings.underFreqHz, freqHz > settings.overFreqHz, voltagePu < settings.underVoltagePu, voltagePu > settings.overVoltagePu];
delays = [settings.freqDelay_s, settings.freqDelay_s, settings.voltageDelay_s, settings.voltageDelay_s];
types = ["generator_under_frequency","generator_over_frequency","generator_under_voltage","generator_over_voltage"];
commands = ["trip_generator","trip_generator","trip_generator","trip_generator"];
thresholds = [settings.underFreqHz, settings.overFreqHz, settings.underVoltagePu, settings.overVoltagePu];
values = [freqHz, freqHz, voltagePu, voltagePu];
for k = 1:n
    if ~online(k) || state.tripped(k)
        state.timer_s(k,:) = 0;
        continue
    end
    for j = 1:4
        if checks(k,j)
            state.timer_s(k,j) = state.timer_s(k,j) + dt;
            if state.timer_s(k,j) >= delays(j)
                trip(k) = true;
                state.tripped(k) = true;
                event(end+1) = cfm.EventLogger(0, types(j), settings.ids(k), values(k,j), thresholds(j), delays(j), commands(j), "generator protection"); %#ok<AGROW>
                break
            end
        else
            state.timer_s(k,j) = 0;
        end
    end
end
end

