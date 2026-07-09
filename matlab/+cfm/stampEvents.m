function events = stampEvents(events, time_s)
%STAMPEVENTS Apply current simulation time to newly generated events.
for k = 1:numel(events)
    events(k).time_s = time_s;
end
end
