#include <Arduino.h>
#include <relay.h>


// --------------- RELAY VARIABLES
const int RELAY_AMOUNT = 16;
const int RELAY_PINS[RELAY_AMOUNT] = {3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18}; // Pins am Arduino

const uint16_t RELAY_1 = 1UL << 0;   // RELAY_1 ist in bit-schreibweise 0b0000000000000001
const uint16_t RELAY_2 = 1UL << 1;   // RELAY_2 ist in bit-schreibweise 0b0000000000000010
const uint16_t RELAY_3 = 1UL << 2;   // RELAY_3 ist in bit-schreibweise 0b0000000000000100
const uint16_t RELAY_4 = 1UL << 3;   // usw.
const uint16_t RELAY_5 = 1UL << 4;
const uint16_t RELAY_6 = 1UL << 5;
const uint16_t RELAY_7 = 1UL << 6;
const uint16_t RELAY_8 = 1UL << 7;
const uint16_t RELAY_9 = 1UL << 8;
const uint16_t RELAY_10 = 1UL << 9;
const uint16_t RELAY_11 = 1UL << 10;
const uint16_t RELAY_12 = 1UL << 11; // bis jetzt bis 0b0000100000000000

const uint16_t IDLE_RELAY_MODE = 0;
const uint16_t INIT_RELAY_MODE = RELAY_1 | RELAY_4 | RELAY_8;
const uint16_t LINEARITY_RELAY_MODE = RELAY_1 | RELAY_4 | RELAY_8;
const uint16_t NOISE_RELAY_MODE = RELAY_1 | RELAY_4 | RELAY_7 | RELAY_8;
const uint16_t NOISE_LOADED_RELAY_MODE = RELAY_7 | RELAY_9;
const uint16_t ELEC_DEG_RELAY_MODE = RELAY_1 | RELAY_4 | RELAY_8;

const uint16_t TOTAL_RESISTANCE_RELAY_MODE = RELAY_1 | RELAY_5;
const uint16_t INITIAL_RESISTANCE_RELAY_MODE = RELAY_1 | RELAY_4;
const uint16_t FINAL_RESISTANCE_RELAY_MODE = RELAY_2 | RELAY_5;
const uint16_t FIRST_HALF_RESISTANCE = RELAY_1 | RELAY_6;
const uint16_t SECOND_HALF_RESISTANCE = RELAY_3 | RELAY_6;
const uint16_t MIDDLE_RESISTANCE = RELAY_2 | RELAY_6;

uint16_t current_mode = 0;

void relays_init(){
    for (int i = 0; i < RELAY_AMOUNT; i++) {
    pinMode(RELAY_PINS[i], OUTPUT);
    digitalWrite(RELAY_PINS[i], HIGH); // AUS (bei active-low Relaisboards)
  }
  current_mode = 0;
}

void switch_relays(int idx, bool turn_on){
    uint8_t level = turn_on ? LOW : HIGH; 

    digitalWrite(RELAY_PINS[idx], level);
}

void apply_relay_mode(uint16_t mode){
    if(current_mode == mode) return;
    current_mode = mode;

    for(int i = 0; i < RELAY_AMOUNT; i++){
        bool turn_on = (mode >> i) & 0x01;
        switch_relays(i, turn_on);
    }
}

void all_relays_off(){
    apply_relay_mode(0);
} 