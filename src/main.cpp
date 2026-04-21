#include <Arduino.h>
#include <Dynamixel2Arduino.h>
#include <math.h>
#include <elapsedMillis.h>

#include <dxl_servo.h>
#include <calibrate.h>
#include <noise.h>
#include <linearity.h>
#include <elec_deg.h>
#include <relay.h>
#include <side_functions.h>

// --------------- CONSTANTS
const int BUTTON = 19;
const int BUT_TIMER = 200;
const int LED_R = 16;
const int LED_Y = 17;
const int LED_G = 18;

// --------------- VARIABLES
bool linear_checked;
elapsedMillis but_millis;
bool but_up = HIGH;
bool but_press;


// --------------- SETUP AND ASSIST FUNCTIONS
void measurements_init(){
  digitalWrite(LED_R, HIGH);
  digitalWrite(LED_Y, LOW);
  digitalWrite(LED_G, LOW);
  linear_checked = false;
  dxl_init();
  calibrate_init();
  elec_deg_init();
  lin_init();
  relays_init();
}

bool abort_if_cancelled(){
  if(!cancelled) return false;
  stop_motion();
  Serial.println("CANCEL");
  digitalWrite(LED_R, LOW);
  digitalWrite(LED_Y, LOW);
  digitalWrite(LED_G, HIGH);
  all_relays_off();
  return true;
}

void setup(){
  Serial.begin(115200);
  dxl.begin(DXL_BAUD);
  dxl.setPortProtocolVersion(DXL_PROTOCOL);

  dxl.torqueOff(DID);
  dxl.setOperatingMode(DID, OP_EXTENDED_POSITION);
  dxl.writeControlTableItem(DRIVE_MODE, DID, 0b101);
  dxl.writeControlTableItem(HOMING_OFFSET, DID, 0);
  dxl.writeControlTableItem(PROFILE_VELOCITY, DID, 1000);
  dxl.writeControlTableItem(CURRENT_LIMIT, DID, 910);
  dxl.writeControlTableItem(PROFILE_ACCELERATION, DID, 500);
  dxl.torqueOn(DID);
  dxl.ledOn(DID);
  relays_init();
  all_relays_off();
  pinMode(BUTTON, INPUT_PULLUP);
  pinMode(LED_R, OUTPUT);
  pinMode(LED_Y, OUTPUT);
  pinMode(LED_G, OUTPUT);
  digitalWrite(LED_R, LOW);
  digitalWrite(LED_Y, LOW);
  digitalWrite(LED_G, HIGH);
}

// --------------- LOOP
void loop(){
  but_press = digitalRead(BUTTON);
  if(but_press == LOW && but_up == HIGH && but_millis > BUT_TIMER){
    Serial.println("BUTTON");
    but_millis = 0;
  }
  but_up = but_press;

  if(Serial.available()){
    String command = Serial.readStringUntil('\n');
    command.trim();

    if(command == "STOP"){
      cancelled = true;
      abort_if_cancelled();
      return;
    }

    // EINGABE VON PYTHON
    if(command.startsWith("SETV:")){tar_volt = command.substring(5).toFloat();}
    if(command.startsWith("SETW:")){target_deg_total = command.substring(5).toFloat();}
    if(command.startsWith("SETS:")){user_rpm = command.substring(5).toFloat();}
    if(command.startsWith("REL_SW:")){relay_switch = command.substring(7).toInt();}
    if(command.startsWith("goto:")){user_go_to = command.substring(5).toFloat();}
    if(command.startsWith("dead11:")){d11_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead12:")){d12_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead21:")){d21_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead22:")){d22_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead31:")){d31_deg = command.substring(7).toFloat();}
    if(command.startsWith("dead32:")){d32_deg = command.substring(7).toFloat();}
  
    if(command == "INIT_GO"){
      measurements_init();
      if(target_deg_total ==0){
        apply_relay_mode(ENDLESS_INIT_RELAY_MODE);
        delay(1000);
        find_endless_volt_crossover();
        find_endless_starting_point();
      }
      else{
        apply_relay_mode(INIT_RELAY_MODE);
        delay(1000);
        check_beginning(target_deg_total);        if(abort_if_cancelled()) return;
        calibrate_currents();     if(abort_if_cancelled()) return;
        check_ends();        if(abort_if_cancelled()) return; //  ÄNDERN: NUR MIT DMM = TRUE
      }
      // drive_to(ZERO_TICK, user_rpm);
      // reached_goal(ZERO_TICK, 2);
      Serial.println("INIT_FINISH");
    }

    if(command == "NOISE_GO"){
      if(abort_if_cancelled()) return;
      apply_relay_mode(NOISE_RELAY_MODE);
      // if(cancelled == false){
      drive_to(sim_mercy_end, user_rpm);
      reached_goal(sim_mercy_end, 2, 0, 15000); 
      if(cancelled == false){
        Serial.println("NOISE_READY");
      } else{
        Serial.println("CANCEL");
        return;
        // cancelled = false;
      }
    }
    if(command == "NOISE_START"){
      noise_movement(); 
      if(cancelled == true){
        Serial.println("CANCEL");
        return;
        // cancelled = false;
      }
      // drive_to(ZERO_TICK, user_rpm);
      // reached_goal(ZERO_TICK, 2);
      // all_relays_off();
      // dxl.ledOff(DID);
      Serial.println("NOISE_FINISH");
    }

    if(command == "LINEAR_GO"){
      linear_checked = true; if(abort_if_cancelled()) return;
      apply_relay_mode(LINEARITY_RELAY_MODE);
      if(cancelled == false){
        Serial.println("LINEAR_READY");
      } else{
        Serial.println("CANCEL");
        return;
        // cancelled = false;
      }
    }
    if(command == "LINEAR_START"){
      linearity_movement2(); if(abort_if_cancelled()) return;
      calc_summary2();
      calc_linearity2();
      calc_errors2();
      if(cancelled == true){
        Serial.println("CANCEL");
        return;
        // cancelled = false;
      }
      // drive_to(ZERO_TICK, user_rpm);
      // reached_goal(ZERO_TICK, 2);
      // dxl.ledOff(DID);
      Serial.println("LINEAR_FINISH");
    }

    if(linear_checked == false){ // Falls elec_deg und linear beide angekreuzt wurden dann einfach elec_deg ignorieren
      if(command == "ELEC_DEG_GO"){
        if(abort_if_cancelled()) return;
        apply_relay_mode(ELEC_DEG_RELAY_MODE);
        if(cancelled == false){
          Serial.println("ELEC_DEG_READY");
        } else{
          Serial.println("CANCEL");
          return;
          // cancelled = false;
        }
      }
      if(command == "ELEC_DEG_START"){
        elec_deg_movement();
        if(cancelled == true){
          Serial.println("CANCEL");
          return;
          //cancelled = false;
        }
        // drive_to(ZERO_TICK, user_rpm);
        // reached_goal(ZERO_TICK, 2);
        // dxl.ledOff(DID);
        Serial.println("ELEC_DEG_FINISH");
      }
    }

    if(command == "ALL_END"){
      drive_to(ZERO_TICK, user_rpm);
      reached_goal(ZERO_TICK, 2);
      all_relays_off();
      dxl.ledOff(DID);
      digitalWrite(LED_R, LOW);
      digitalWrite(LED_Y, LOW);
      digitalWrite(LED_G, HIGH);
      cancelled = false;
      linear_checked = false;
    }

    if(command == "NOISE_END"){
      drive_to(ZERO_TICK, user_rpm);
      reached_goal(ZERO_TICK, 2);
      all_relays_off();
      dxl.ledOff(DID);
      digitalWrite(LED_R, LOW);
      digitalWrite(LED_Y, HIGH);
      digitalWrite(LED_G, LOW);
      cancelled = false;
      linear_checked = false;
    }

    if(command == "FAULT_LED"){
      digitalWrite(LED_R, LOW);
      digitalWrite(LED_Y, HIGH);
      digitalWrite(LED_G, LOW);
    }

    if(command == "ZERO"){
      measurements_init();
      go_zero();
    } 

    if(command == "GOTO"){
      measurements_init();
      go_to();
    } 

    if(command == "WHERE"){
      measurements_init();
      show_cur_pos();
    }

    if(command == "TESTER"){
      apply_relay_mode(ENDLESS_INIT_RELAY_MODE);
    }
  
  }
}
