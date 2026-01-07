#pragma once
#include <Arduino.h>

// --------------- VARIABLES
extern int tar_volt;

extern const size_t print_array_size;
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
extern float soll_deg_total;
extern float d11_deg, d12_deg, d21_deg, d22_deg, d31_deg, d32_deg;
extern int32_t d11_tick, d12_tick, d21_tick, d22_tick, d31_tick, d32_tick;
extern float ist_start_volt, ist_end_volt, ist_mid_volt;
extern float ccw_links, ccw_rechts, cw_links, cw_rechts, aktiv_ccw, aktiv_cw, ges_aktiv;
extern float real_mid_deg;
extern float lin_min, lin_max;


// --------------- LINEARITY FUNCTIONS
void lin_init();
float lerp_dead(int32_t x, int32_t d1, int32_t d2);
float dead_soll_volt_deg(float deg, float tar_volt,
                      float d12_deg, float d21_deg, float d22_deg, float d31_deg);
float corr_measure(float current_volt);
float correction_movement(float &current_volt, float goal_volt, 
                          int dead_direction = 0, int timeout = 8000);
void linearity_movement();
void calc_linearity();
void calc_summary();
void calc_errors();