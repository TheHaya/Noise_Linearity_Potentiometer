#pragma once
#include <Arduino.h>


// --------------- VARIABLES
extern const size_t ELEC_ARRAY_SIZE;
extern int32_t elec_deg;
extern bool smaller_steps;
// --------------- ELEC_DEG_FUNCTIONS
void elec_deg_init();
void elec_deg_movement();