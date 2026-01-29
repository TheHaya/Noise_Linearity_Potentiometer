#pragma once
#include <Arduino.h>
#include <Dynamixel2Arduino.h>
#include <vector>

// --------------- DYNAMIXEL VARIABLES
#define DXL_SERIAL Serial1
#define DEBUG_SERIAL Serial

extern const int DXL_DIR_PIN;
extern const uint8_t DID;
extern const float DXL_PROTOCOL;
extern const uint32_t DXL_BAUD;

extern Dynamixel2Arduino dxl;
using namespace ControlTableItem;


// --------------- SERVO CONSTANTS
extern const float DEG_PER_TICK;
extern const float TICK_PER_DEG;
extern const float RPM_PER_VEL;
extern const int POLL_TIMER;


// --------------- SERVO VARIABLES
extern int32_t stopped_tick;
extern float start_current;
extern float cal_cur0, cal_cur1, cal_cur2, cal_cur3;
extern float cur_tolerance;
extern bool cancelled;
extern int32_t cur_pos;
extern float cur_cur;

using std::vector;
extern vector<int> modes;

// --------------- HELPER FUNCTIONS
int32_t deg_to_tick(float deg);
float tick_to_deg(int32_t tick);
int32_t get_tick_position();
float get_deg_position();
uint32_t rpm_to_time(int32_t goal_tick, float rpm);

void dxl_init();


// --------------- DRIVE FUNCTIONS
void drive_to(int32_t tick, float rpm, uint8_t DYN_ID = 1);
bool reached_goal(int32_t target_tick, uint8_t measure_spd = 0, uint8_t measure_mode = 0, 
                    uint8_t error_tick = 1, uint32_t timeout = 20000, uint8_t DYN_ID = 1);