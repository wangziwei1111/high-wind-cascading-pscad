function schedule = export_trip_schedule(schedule, outputScheduleCsv)
%EXPORT_TRIP_SCHEDULE Write a standard trip schedule table.
schedule = cfm.TripScheduleWriter(schedule, outputScheduleCsv);
end
