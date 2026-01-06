#pragma once
#include <Arduino.h>


extern const int32_t CHECK_END_START;
extern const int32_t CHECK_END_END;
extern const int32_t CALIBRATE_CURRENT_CCW;
extern const int32_t CALIBRATE_CURRENT_CW;
extern const int32_t ZERO_TICK;
extern const float MERCY_TOLERANCE_TICK;
extern const float CHECK_ENDS_TOL_DEG;

extern int32_t stopped_tick;
extern int32_t start_tick, end_tick, mid_tick;
extern int32_t sim_mercy_start, sim_mercy_end;

extern float slow_rpm;
extern float user_rpm, rpm1, rpm2, rpm3;
extern float real_time1, real_time2, real_time3;
extern float theo_time1, theo_time2, theo_time3;
extern float target_deg_total;
extern float delay1, delay2, delay3;
extern int32_t real_tick_total;
