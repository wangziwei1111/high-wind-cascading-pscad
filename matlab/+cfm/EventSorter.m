function events = EventSorter(events)
%EVENTSORTER Return events ordered by time and stable component name.
if isempty(events)
    return
end
[~, idx] = sort([events.time_s]);
events = events(idx);
end
