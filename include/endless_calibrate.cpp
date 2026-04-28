#pragma once

extern float endless_start_volt, endless_end_volt, endless_start_deg, endless_end_deg;

void find_endless_volt_crossover();
float correction_movement_endless_starts(float &current_volt, float goal_volt, int start, int timeout);
void find_endless_starting_point();