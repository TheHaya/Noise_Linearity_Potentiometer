#pragma once
#include <Arduino.h>

// --------------- CONSTANTS
extern const int32_t ENDLESS_MERCY_TOLERANCE_TICK;


// --------------- VARIABLES
extern float endless_start_volt, endless_end_volt, endless_start_tick, endless_end_tick;
extern int32_t endless_sim_start, endless_sim_end;


// --------------- FUNCTIONS
void endless_init();
void find_endless_volt_crossover();
float correction_movement_endless_starts(float &current_volt, float goal_volt, int start, int timeout);
void find_endless_starting_point();