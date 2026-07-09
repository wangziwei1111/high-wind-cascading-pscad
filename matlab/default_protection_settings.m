function settings = default_protection_settings()
%DEFAULT_PROTECTION_SETTINGS Paper-style wind VRT settings for Stage 16.

settings = struct();
settings.wind = struct();
settings.wind.ids = {'wind_33'; 'wind_35'; 'wind_38'};

settings.wind.vrt = struct();
settings.wind.vrt.normal_low_pu = 0.90;
settings.wind.vrt.normal_high_pu = 1.10;
settings.wind.vrt.instant_low_pu = 0.20;
settings.wind.vrt.instant_high_pu = 1.30;
settings.wind.vrt.low_curve_v1_pu = 0.20;
settings.wind.vrt.low_curve_t1_s = 0.625;
settings.wind.vrt.low_curve_v2_pu = 0.90;
settings.wind.vrt.low_curve_t2_s = 2.0;
settings.wind.vrt.high_125_pu = 1.25;
settings.wind.vrt.high_120_pu = 1.20;
settings.wind.vrt.high_110_pu = 1.10;
settings.wind.vrt.high_125_delay_s = 0.5;
settings.wind.vrt.high_120_delay_s = 1.0;
settings.wind.vrt.high_110_delay_s = 10.0;
end
