function spec = PscadBridgeStub(mockInput)
%PSCADBRIDGESTUB Future PSCAD-MATLAB interface contract and mock container.
if nargin < 1
    mockInput = struct();
end
spec = struct();
spec.status = "stub_only_not_connected_to_pscad";
spec.pscad_to_matlab = ["time_s","bus_voltage_pu","bus_frequency_hz","line_loading_pu","breaker_status","wind_poc_voltage_pu","wind_active_power_mw","device_voltage_pu"];
spec.matlab_to_pscad = ["trip_line","shed_load","disconnect_wind_farm","trip_generator","trip_device"];
spec.mockInput = mockInput;
spec.notes = "This stub is for offline unit tests and interface planning only. Real PSCAD communication is pending user validation in PSCAD GUI.";
end

