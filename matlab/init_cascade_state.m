function state = init_cascade_state()
%INIT_CASCADE_STATE Create persistent state for the wind VRT trip shell.

state = struct();
state.wind_ids = {'wind_33'; 'wind_35'; 'wind_38'};
state.wind_vrt = struct();
state.wind_vrt.timer_s = zeros(3, 1);
state.wind_vrt.tripped = false(3, 1);
state.wind_vrt.trip_commanded = false(3, 1);
state.event_log = repmat(cfm.EventLogger(NaN, '', '', '', NaN, NaN, NaN, '', '', ''), 0, 1);
state.last_command_time_s = NaN;
end
