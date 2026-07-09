function [raw, state, events] = VRTProtection(t, dt, obs, state, settings)
%VRTPROTECTION Paper-style wind-farm voltage ride-through trip shell.

if nargin < 4 || isempty(state)
    state = init_cascade_state();
end
if nargin < 5 || isempty(settings)
    settings = default_protection_settings();
end

if ~isfield(obs, 'wind_pcc_voltage_pu')
    error('VRTProtection:MissingObservation', 'obs.wind_pcc_voltage_pu is required.');
end
if ~isfield(obs, 'wind_online')
    error('VRTProtection:MissingObservation', 'obs.wind_online is required.');
end

voltage = obs.wind_pcc_voltage_pu(:);
online = logical(obs.wind_online(:));
nWind = numel(voltage);

state = ensureWindState(state, nWind, settings);
state.wind_vrt.tripped = state.wind_vrt.tripped | ~online;

raw = struct();
raw.wind_disconnect_cmd = false(nWind, 1);
events = repmat(cfm.EventLogger(NaN, '', '', '', NaN, NaN, NaN, '', '', ''), 0, 1);

for k = 1:nWind
    if ~online(k)
        state.wind_vrt.timer_s(k) = 0;
        state.wind_vrt.trip_commanded(k) = false;
        state.wind_vrt.tripped(k) = true;
        continue;
    end

    if state.wind_vrt.trip_commanded(k)
        raw.wind_disconnect_cmd(k) = true;
        continue;
    end

    [outside, delay_s, threshold, region] = evaluateVrtDelay(voltage(k), settings.wind.vrt);
    if ~outside
        state.wind_vrt.timer_s(k) = 0;
        continue;
    end

    if delay_s <= 0
        shouldTrip = true;
    else
        state.wind_vrt.timer_s(k) = state.wind_vrt.timer_s(k) + dt;
        shouldTrip = state.wind_vrt.timer_s(k) >= delay_s;
    end

    if shouldTrip
        raw.wind_disconnect_cmd(k) = true;
        state.wind_vrt.trip_commanded(k) = true;
        events(end + 1, 1) = cfm.EventLogger( ... %#ok<AGROW>
            t, ...
            'wind_vrt_trip', ...
            'wind_farm', ...
            getWindId(settings, k), ...
            voltage(k), ...
            threshold, ...
            delay_s, ...
            'disconnect_wind_farm', ...
            'VRTProtection', ...
            ['paper voltage ride-through criterion triggered: ' region]);
    end
end
end

function state = ensureWindState(state, nWind, settings)
if ~isfield(state, 'wind_vrt') || isempty(state.wind_vrt)
    state.wind_vrt = struct();
end
fields = {'timer_s', 'tripped', 'trip_commanded'};
defaults = {zeros(nWind, 1), false(nWind, 1), false(nWind, 1)};
for i = 1:numel(fields)
    name = fields{i};
    if ~isfield(state.wind_vrt, name) || numel(state.wind_vrt.(name)) ~= nWind
        state.wind_vrt.(name) = defaults{i};
    else
        state.wind_vrt.(name) = state.wind_vrt.(name)(:);
    end
end
if ~isfield(state, 'wind_ids') || numel(state.wind_ids) ~= nWind
    state.wind_ids = settings.wind.ids(:);
end
if ~isfield(state, 'event_log')
    state.event_log = repmat(cfm.EventLogger(NaN, '', '', '', NaN, NaN, NaN, '', '', ''), 0, 1);
end
end

function [outside, delay_s, threshold, region] = evaluateVrtDelay(vs, vrt)
outside = true;
delay_s = 0;
threshold = NaN;
region = 'normal';

if vs <= vrt.instant_low_pu
    threshold = vrt.instant_low_pu;
    region = 'Vs <= 0.20 pu';
elseif vs >= vrt.instant_high_pu
    threshold = vrt.instant_high_pu;
    region = 'Vs >= 1.30 pu';
elseif vs > vrt.low_curve_v1_pu && vs < vrt.low_curve_v2_pu
    delay_s = vrt.low_curve_t1_s + ...
        (vs - vrt.low_curve_v1_pu) * (vrt.low_curve_t2_s - vrt.low_curve_t1_s) / ...
        (vrt.low_curve_v2_pu - vrt.low_curve_v1_pu);
    threshold = vrt.low_curve_v2_pu;
    region = '0.20 pu < Vs < 0.90 pu';
elseif vs >= vrt.high_125_pu && vs < vrt.instant_high_pu
    delay_s = vrt.high_125_delay_s;
    threshold = vrt.high_125_pu;
    region = '1.25 pu <= Vs < 1.30 pu';
elseif vs >= vrt.high_120_pu && vs < vrt.high_125_pu
    delay_s = vrt.high_120_delay_s;
    threshold = vrt.high_120_pu;
    region = '1.20 pu <= Vs < 1.25 pu';
elseif vs >= vrt.high_110_pu && vs < vrt.high_120_pu
    delay_s = vrt.high_110_delay_s;
    threshold = vrt.high_110_pu;
    region = '1.10 pu <= Vs < 1.20 pu';
else
    outside = false;
end
end

function id = getWindId(settings, k)
if isfield(settings, 'wind') && isfield(settings.wind, 'ids') && k <= numel(settings.wind.ids)
    id = settings.wind.ids{k};
else
    id = sprintf('wind_%d', k);
end
end
