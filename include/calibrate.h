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
extern const float SAFETY_VOLT;
extern const int BEGINNING_TIMER;
extern const float SLOW_RPM;

// --------------- CALIBRATE VARIABLES
extern int32_t start_tick, end_tick, real_mid_tick;
extern int32_t sim_mercy_start, sim_mercy_end;

extern float user_rpm, rpm1, rpm2, rpm3;
extern float real_time1, real_time2, real_time3;
extern float theo_time1, theo_time2, theo_time3;
extern float target_deg_total;
extern float delay1, delay2, delay3;
extern float ist_start_volt, ist_end_volt, ist_mid_volt;
extern float safety_pos_volt;
extern float tar_volt;

void calibrate_init();
float corr_measure();
void calibrate_currents();
void check_ends();
float correction_movement(float &current_volt, float goal_volt, 
                          int dead_direction, int dead_half, int timeout=30000);
float correction_movement_low(float &current_volt, float goal_volt, 
                          int dead_direction, int dead_half, int timeout=30000);
void check_beginning(float total_deg);
// bool abort_if_cancelled();