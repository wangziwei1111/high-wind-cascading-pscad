function out = defaultStruct(in, defaults)
%DEFAULTSTRUCT Fill missing struct fields from defaults.
out = defaults;
if isempty(in)
    return
end
names = fieldnames(in);
for k = 1:numel(names)
    out.(names{k}) = in.(names{k});
end
end

