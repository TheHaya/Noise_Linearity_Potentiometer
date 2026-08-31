#pragma once
#include <Arduino.h>

// --------------- SIDE FUNCTION VARIABLES
extern int32_t user_go_to;
extern int32_t tester_val;

// --------------- SIDE FUNCTIONS
void go_to();
void go_zero();
void show_cur_pos();
void rel_tester();
// void tester();