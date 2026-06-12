#pragma once
#include <Arduino.h>

// --------------- CONSTANTS


// --------------- VARIABLES
extern float endless_noise_prep_start;
extern float endless_noise_prep_end;

// --------------- FUNCTIONS
void endless_noise_init();
void endless_noise_preparation_movement();
void endless_noise_movement();