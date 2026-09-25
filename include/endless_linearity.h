#pragma once
#include <Arduino.h>

// --------------- VARIABLES
extern const size_t PRINT_ARRAY_SIZE;
extern float print_ist_deg[];
extern float print_soll_deg[];
extern float print_soll_volt[];
extern float print_ist_volt[];
extern float print_real_diff_mid[];
extern float print_soll_volt_real[];
extern float print_linear_real[];
extern bool empty_cells[];
extern bool error_lin;
extern bool error_mech;
extern bool error_midDead;
extern bool error_lin_index[];

extern int32_t real_tick_total, soll_tick_total;

extern int32_t d11_tick, d12_tick, d21_tick, d22_tick, d31_tick, d32_tick;

extern float ccw_links, ccw_rechts, cw_links, cw_rechts, aktiv_ccw, aktiv_cw, ges_aktiv;
extern float real_mid_deg;
extern float lin_min, lin_max;

// --------------- LINEARITY FUNCTIONS
void endless_lin_init();


//float correction_movement(float &current_volt, float goal_volt, 
//                          int dead_direction = 0, int timeout = 8000);

void endless_linearity_movement();
void endless_calc_summary();
void endless_calc_linearity();
void endless_calc_errors();
