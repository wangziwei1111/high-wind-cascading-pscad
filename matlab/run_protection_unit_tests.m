function results = run_protection_unit_tests()
%RUN_PROTECTION_UNIT_TESTS Run offline protection logic tests.
root = fileparts(mfilename('fullpath'));
addpath(root);
addpath(fullfile(root, 'tests'));
results = [runtests('testProtectionLogic'), runtests('testPscadCascadeStep'), ...
    runtests('testCommandDispatcher'), runtests('testWindVRTTripShell'), ...
    runtests('testOfflineFeedbackReplay')];
disp(table(results));
assertSuccess(results);
end
