#pragma once
#include <Arduino.h>

// --------------- RELAY VARIABLES
extern const int RELAY_AMOUNT;
extern const int RELAY_PINS[];

extern const uint16_t RELAY_1;
extern const uint16_t RELAY_2;
extern const uint16_t RELAY_3;
extern const uint16_t RELAY_4;
extern const uint16_t RELAY_5;
extern const uint16_t RELAY_6;
extern const uint16_t RELAY_7_AB;
extern const uint16_t RELAY_8_AB;
extern const uint16_t RELAY_10_AB;
extern const uint16_t RELAY_11_AB;
extern const uint16_t RELAY_9_AB;
extern const uint16_t RELAY_9_CD;
extern const uint16_t RELAY_9_EF;
extern const uint16_t RELAY_9_GH;

extern const uint16_t IDLE_RELAY_MODE;
extern const uint16_t INIT_RELAY_MODE;
extern const uint16_t POL_INIT_RELAY_MODE;
extern const uint16_t LINEARITY_RELAY_MODE;
extern const uint16_t POL_LINEARITY_RELAY_MODE;
extern const uint16_t NOISE_RELAY_MODE;
extern const uint16_t NOISE_LOADED_RELAY_MODE;
extern const uint16_t POL_NOISE_RELAY_MODE;
extern const uint16_t ELEC_DEG_RELAY_MODE;
extern const uint16_t POL_ELEC_DEG_RELAY_MODE;
extern const uint16_t TOTAL_RESISTANCE_RELAY_MODE;
extern const uint16_t INITIAL_RESISTANCE_RELAY_MODE;
extern const uint16_t FINAL_RESISTANCE_RELAY_MODE;
extern const uint16_t FIRST_HALF_RESISTANCE;
extern const uint16_t SECOND_HALF_RESISTANCE;
extern const uint16_t MIDDLE_RESISTANCE;

extern uint16_t current_mode;
extern bool relay_switch;

// --------------- RELAY FUNCTIONS
void relays_init();
void switch_relays(int idx, bool turn_on);

void apply_relay_mode(uint16_t mode);

void all_relays_off();