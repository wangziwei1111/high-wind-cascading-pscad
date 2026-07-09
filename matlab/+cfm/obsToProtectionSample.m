function sample = obsToProtectionSample(obs)
%OBSTOPROTECTIONSAMPLE Adapt PSCAD obs contract to package-internal names.
sample = struct();
sample.lineLoadRatio = getfielddef(obs, 'line_loading_pu', zeros(46,1));
sample.lineInService = logical(getfielddef(obs, 'line_online', true(numel(sample.lineLoadRatio),1)));
sample.windVoltagePu = getfielddef(obs, 'wind_pcc_voltage_pu', ones(3,1));
sample.windConnected = logical(getfielddef(obs, 'wind_online', true(numel(sample.windVoltagePu),1)));
sample.generatorFreqHz = getfielddef(obs, 'gen_frequency_Hz', 50 * ones(10,1));
sample.generatorVoltagePu = getfielddef(obs, 'gen_voltage_pu', ones(numel(sample.generatorFreqHz),1));
sample.generatorOnline = logical(getfielddef(obs, 'gen_online', true(numel(sample.generatorFreqHz),1)));
sample.loadVoltagePu = min(getfielddef(obs, 'load_voltage_pu', 1.0));
sample.loadOnline = logical(getfielddef(obs, 'load_online', true(1,1)));
busFreq = getfielddef(obs, 'bus_frequency_Hz', 50);
sample.systemFreqHz = min(busFreq(:));
sample.deviceVoltagePu = getfielddef(obs, 'bus_voltage_pu', ones(39,1));
sample.deviceOnline = true(numel(sample.deviceVoltagePu),1);
end

function value = getfielddef(s, name, defaultValue)
if isfield(s, name)
    value = s.(name);
else
    value = defaultValue;
end
value = value(:);
end
