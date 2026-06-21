function [shed, state, event] = UFLS_UVLS(freqHz, voltagePu, dt, loadOnline, settings, state)
%UFLS_UVLS Multi-stage under-frequency and under-voltage load shedding.
arguments
    freqHz (1,1) double
    voltagePu (1,1) double
    dt (1,1) double {mustBeNonnegative}
    loadOnline (:,1) logical
    settings struct = struct()
    state struct = struct()
end
settings = cfm.defaultStruct(settings, struct( ...
    'uflsFreqHz', [49.0 48.5 48.0], 'uflsDelay_s', [0.2 0.2 0.2], ...
    'uflsShedFraction', [0.25 0.40 0.55], 'uvlsVoltagePu', 0.8, ...
    'uvlsDelay_s', 1.0, 'uvlsShedFraction', 0.25));
nStages = numel(settings.uflsFreqHz);
if ~isfield(state, 'uflsTimer_s'), state.uflsTimer_s = zeros(1,nStages); end
if ~isfield(state, 'uflsDone'), state.uflsDone = false(1,nStages); end
if ~isfield(state, 'uvlsTimer_s'), state.uvlsTimer_s = 0; end
if ~isfield(state, 'uvlsDone'), state.uvlsDone = false; end
shed = struct('uflsStages', false(1,nStages), 'uvls', false, 'fraction', 0);
event = cfm.emptyEvent();
if any(loadOnline)
    for j = 1:nStages
        if ~state.uflsDone(j) && freqHz <= settings.uflsFreqHz(j)
            state.uflsTimer_s(j) = state.uflsTimer_s(j) + dt;
            if state.uflsTimer_s(j) >= settings.uflsDelay_s(j)
                state.uflsDone(j) = true;
                shed.uflsStages(j) = true;
                shed.fraction = max(shed.fraction, settings.uflsShedFraction(j));
                event(end+1) = cfm.EventLogger(0, "ufls_stage", "load_stage_" + j, freqHz, settings.uflsFreqHz(j), settings.uflsDelay_s(j), "shed_load", "one-shot UFLS stage"); %#ok<AGROW>
            end
        elseif ~state.uflsDone(j)
            state.uflsTimer_s(j) = 0;
        end
    end
    if ~state.uvlsDone && voltagePu <= settings.uvlsVoltagePu
        state.uvlsTimer_s = state.uvlsTimer_s + dt;
        if state.uvlsTimer_s >= settings.uvlsDelay_s
            state.uvlsDone = true;
            shed.uvls = true;
            shed.fraction = max(shed.fraction, settings.uvlsShedFraction);
            event(end+1) = cfm.EventLogger(0, "uvls", "load_uvls", voltagePu, settings.uvlsVoltagePu, settings.uvlsDelay_s, "shed_load", "one-shot UVLS stage"); %#ok<AGROW>
        end
    elseif ~state.uvlsDone
        state.uvlsTimer_s = 0;
    end
end
end

