function writetableOut = TripScheduleWriter(schedule, outputCsv)
%TRIPSCHEDULEWRITER Write a standard offline feedback trip schedule.
required = {'target_id', 'target_type', 'action', 'trip_time_s', ...
    'source_protection', 'measured_value_at_decision', 'criterion', 'notes'};
missing = setdiff(required, schedule.Properties.VariableNames);
if ~isempty(missing)
    error('TripScheduleWriter:MissingColumns', ...
        'Schedule is missing columns: %s', strjoin(missing, ', '));
end
outDir = fileparts(outputCsv);
if ~isempty(outDir) && ~isfolder(outDir)
    mkdir(outDir);
end
writeScheduleCsv(schedule, outputCsv, required);
writetableOut = schedule;
end

function writeScheduleCsv(schedule, outputCsv, columns)
fid = fopen(outputCsv, 'w');
if fid < 0
    error('TripScheduleWriter:WriteFailed', 'Could not write %s', outputCsv);
end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, '%s\n', strjoin(columns, ','));
for i = 1:height(schedule)
    values = cell(1, numel(columns));
    for j = 1:numel(columns)
        values{j} = csvField(schedule.(columns{j})(i));
    end
    fprintf(fid, '%s\n', strjoin(values, ','));
end
end

function text = csvField(value)
if iscell(value)
    value = value{1};
end
if isstring(value)
    text = char(value);
elseif ischar(value)
    text = value;
elseif isnumeric(value) || islogical(value)
    text = num2str(value, '%.15g');
else
    text = char(string(value));
end
text = strrep(text, '"', '""');
if contains(text, ',') || contains(text, '"') || contains(text, newline)
    text = ['"' text '"'];
end
end
