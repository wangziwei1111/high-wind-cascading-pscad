function [cmd, state, events] = pscad_cascade_step(t, dt, obs, state, settings)
%PSCAD_CASCADE_STEP Minimal PSCAD-MATLAB wind-farm trip-shell entry point.
% PSCAD measures the network and executes real breaker operations. MATLAB
% only evaluates the paper VRT criterion and returns wind disconnect commands.

if nargin < 4 || isempty(state)
    state = init_cascade_state();
end
if nargin < 5 || isempty(settings)
    settings = default_protection_settings();
end

[raw, state, events] = cfm.VRTProtection(t, dt, obs, state, settings);
cmd = cfm.CommandDispatcher(raw, obs);
cmd.any_action = any(cmd.wind_disconnect_cmd(:));
cmd.simulation_stop_cmd = false;
cmd.matlab_command_time_s = t;
state.last_command_time_s = t;

if ~isfield(state, 'event_log') || isempty(state.event_log)
    state.event_log = events;
elseif ~isempty(events)
    state.event_log = [state.event_log; events(:)];
end
end
