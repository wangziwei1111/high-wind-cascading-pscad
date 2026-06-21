function [commands, state, events] = ProtectionManager(sample, dt, settings, state)
%PROTECTIONMANAGER Aggregate protection outputs into PSCAD-neutral commands.
arguments
    sample struct
    dt (1,1) double {mustBeNonnegative}
    settings struct = struct()
    state struct = struct()
end
if ~isfield(state, 'overload'), state.overload = struct(); end
if ~isfield(state, 'lvrt'), state.lvrt = struct(); end
if ~isfield(state, 'generator'), state.generator = struct(); end
if ~isfield(state, 'loadShedding'), state.loadShedding = struct(); end
if ~isfield(state, 'tov'), state.tov = struct(); end

[lineTrip, state.overload, e1] = cfm.OverloadProtection(sample.lineLoadRatio(:), dt, sample.lineInService(:), getfielddef(settings,'overload',struct()), state.overload);
[windCmd, state.lvrt, e2] = cfm.LVRTProtection(sample.windVoltagePu(:), dt, sample.windConnected(:), getfielddef(settings,'lvrt',struct()), state.lvrt);
[genTrip, state.generator, e3] = cfm.GeneratorProtection(sample.generatorFreqHz(:), sample.generatorVoltagePu(:), dt, sample.generatorOnline(:), getfielddef(settings,'generator',struct()), state.generator);
[shed, state.loadShedding, e4] = cfm.UFLS_UVLS(sample.systemFreqHz, sample.loadVoltagePu, dt, sample.loadOnline(:), getfielddef(settings,'loadShedding',struct()), state.loadShedding);
[deviceTrip, state.tov, e5] = cfm.TransientOvervoltageProtection(sample.deviceVoltagePu(:), dt, sample.deviceOnline(:), getfielddef(settings,'tov',struct()), state.tov);

commands = struct('lineTrip', lineTrip, 'windCommand', windCmd, 'generatorTrip', genTrip, 'loadShedding', shed, 'deviceTrip', deviceTrip);
events = [e1, e2, e3, e4, e5];
end

function v = getfielddef(s, name, defaultValue)
if isfield(s, name), v = s.(name); else, v = defaultValue; end
end

