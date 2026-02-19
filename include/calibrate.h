#pragma once
#include <Arduino.h>


// --------------- CALIBRATE CONSTANTS
extern const int32_t CHECK_END_START;
extern const int32_t CHECK_END_END;
extern const int32_t CALIBRATE_CURRENT_CCW;
extern const int32_t CALIBRATE_CURRENT_CW;
extern const int32_t ZERO_TICK;
extern const float MERCY_TOLERANCE_TICK;
extern const float CHECK_ENDS_TOL_DEG;


// --------------- CALIBRATE VARIABLES
extern int32_t stopped_tick;
extern int32_t start_tick, end_tick;
extern int32_t sim_mercy_start, sim_mercy_end;

extern float slow_rpm;
extern float user_rpm, rpm1, rpm2, rpm3;
extern float real_time1, real_time2, real_time3;
extern float theo_time1, theo_time2, theo_time3;
extern float target_deg_total;
extern float delay1, delay2, delay3;
extern float ist_start_volt, ist_end_volt, ist_mid_volt;
extern float safety_pos_volt;
extern float tar_volt;

float corr_measure(float current_volt);
void calibrate_currents();
void check_ends(bool uses_dmm=false);
float correction_movement(float &current_volt, float goal_volt, 
                          int dead_direction, int dead_half, int timeout=18000);