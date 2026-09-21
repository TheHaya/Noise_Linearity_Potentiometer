#pragma once
#include <Arduino.h>


// --------------- CALIBRATE CONSTANTS
extern const int32_t CHECK_END_MERCY;
extern const int32_t CALIBRATE_CURRENT_CCW;
extern const int32_t CALIBRATE_CURRENT_CW;
extern const int32_t ZERO_TICK;
extern const int32_t MERCY_TOLERANCE_TICK;
extern const int32_t SAFETY_TOLERANCE_TICK;
extern const float CHECK_ENDS_TOL_DEG;
// extern const float SAFETY_VOLT;
extern const int BEGINNING_TIMER;
// extern const float SLOW_RPM;

// --------------- CALIBRATE VARIABLES
extern int32_t start_tick, end_tick, real_mid_tick;
extern int32_t sim_mercy_start, sim_mercy_end;
extern int32_t safety_start, safety_end;
extern int32_t check_end_start;
extern int32_t check_end_end;
extern int32_t beginning_tick;
// extern float user_rpm, rpm1, rpm2, rpm3;
extern float d11_deg, d12_deg, d21_deg, d22_deg, d31_deg, d32_deg;
extern float real_time1, real_time2, real_time3;
extern float theo_time1, theo_time2, theo_time3;
extern float target_deg_total;
extern float delay1, delay2, delay3;
extern bool measure_start_resistance, measure_end_resistance, measure_total_resistance;
extern float ist_start_volt, ist_end_volt, ist_mid_volt;
extern float safety_pos_volt;
extern float tar_volt;

void calibrate_init();
float corr_measure(int start_end = 0);
float corr_measure_res(int start_end = 0);
bool calibrate_currents();
void check_ends();
float correction_movement(float &current_volt, float goal_volt, 
                          int dead_direction, int dead_half, bool smaller_steps = false, int timeout=30000);
float correction_movement_endless_starts(float &current_volt, float goal_volt, int start, int timeout=30000);
void check_beginning(float total_deg);
void find_endless_volt_crossover();
void find_endless_starting_point();
bool read_hardware_error_status(uint8_t &error_code, uint8_t id=1);
bool recover_dxl_after_fault(uint8_t id=1);
bool wait_for_dxl_after_reboot(uint8_t id = 1, uint32_t timeout_ms = 3000);
