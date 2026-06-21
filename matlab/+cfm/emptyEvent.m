function events = emptyEvent()
%EMPTYEVENT Typed empty event array.
events = repmat(cfm.EventLogger(NaN, "", "", NaN, NaN, NaN, "", ""), 0, 1);
end

