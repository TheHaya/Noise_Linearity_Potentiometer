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
#include <endless_calibrate.h>
#include <endless_elec_deg.h>
#include <endless_noise.h>


// --------------- CONSTANTS
const int BUTTON = 19;
const int BUT_TIMER = 200;
const int LED_R = 16;
const int LED_Y = 17;
const int LED_G = 18;

// --------------- VARIABLES
const int POLLING_TIMER_PING = 200;
bool linear_checked;
elapsedMillis but_millis;
elapsedMillis servo_ping_timer;
bool servo_online = false;
bool but_up = HIGH;
bool but_press;
bool endless_poti;
bool calib_finished;
bool ping_ok;

// --------------- SETUP AND ASSIST FUNCTIONS

void setLEDS(int setting){
  switch(setting){
    case 0:
    digitalWrite(LED_R, LOW);
    digitalWrite(LED_Y, LOW);
    digitalWrite(LED_G, LOW);
    break;
    case 1:
    digitalWrite(LED_R, HIGH);
    digitalWrite(LED_Y, LOW);
    digitalWrite(LED_G, LOW);
    break;
    case 2:
    digitalWrite(LED_R, LOW);
    digitalWrite(LED_Y, HIGH);
    digitalWrite(LED_G, LOW);
    break;
    case 3:
    digitalWrite(LED_R, LOW);
    digitalWrite(LED_Y, LOW);
    digitalWrite(LED_G, HIGH);
    break;
    default:
    digitalWrite(LED_R, LOW);
    digitalWrite(LED_Y, LOW);
    digitalWrite(LED_G, HIGH);
    break;
  }
}

void measurements_init(){
  setLEDS(1);
  endless_poti = false;
  linear_checked = false;
  calib_finished = false;
  dxl_init();
  calibrate_init();
  endless_init();
  endless_noise_init();
  elec_deg_init();
  lin_init();
  
}

bool abort_if_cancelled(){
  if(!cancelled) return false;
  stop_motion();
  Serial.println("CANCEL");
  if(ping_ok){
    setLEDS(3);
  }
  all_relays_off();
  uint8_t error_code = 0;
  bool read_ok = read_hardware_error_status(error_code, DID);

  if (!read_ok) {
    Serial.println("HARDWARE_ERROR_STATUS konnte nicht gelesen werden");
  } else if (error_code != 0) {
    Serial.print("DXL HW Error: ");
    Serial.println(error_code, BIN);
  }
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
  dxl.writeControlTableItem(CURRENT_LIMIT, DID, 900);
  dxl.writeControlTableItem(PROFILE_ACCELERATION, DID, 500);
  dxl.torqueOn(DID);
  dxl.ledOn(DID);
  relays_init();
  all_relays_off();
  pinMode(BUTTON, INPUT_PULLUP);
  pinMode(LED_R, OUTPUT);
  pinMode(LED_Y, OUTPUT);
  pinMode(LED_G, OUTPUT);
}

// --------------- LOOP
void loop(){
  if(servo_ping_timer > POLLING_TIMER_PING){
    servo_ping_timer = 0;

    ping_ok = dxl.ping(DID);

    if(ping_ok && !servo_online){
      servo_online = true;
      setLEDS(3);
    }
    else if(!ping_ok && servo_online){
      servo_online = false;
      setLEDS(0);
    }
  }


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
      relays_init();
      calc_rpm();
      if(target_deg_total == 360){
        endless_poti = true;
        calibrate_currents();
      } 
      Serial.println("INIT_FINISH");
    }
    
    if(command == "CALIB_GO"){
      if(endless_poti){
        apply_relay_mode(INIT_RELAY_MODE);
        delay(1000);
        find_endless_volt_crossover();
        find_endless_starting_point();
        calib_finished = true;
      }
      else{
        apply_relay_mode(INIT_RELAY_MODE);
        delay(1000);
        if(!endless_poti){
          check_beginning(target_deg_total);
          if(abort_if_cancelled()) return;
        }
        calibrate_currents();
        if(abort_if_cancelled()) return;
        check_ends();
        if(abort_if_cancelled()) return; //  ÄNDERN: NUR MIT DMM = TRUE
      }
      // drive_to(ZERO_TICK, user_rpm);
      // reached_goal(ZERO_TICK, 2);
      drive_and_check(ZERO_TICK, user_rpm);
      Serial.println("CALIB_FINISH");
    }

    if(command == "NOISE_GO"){
      apply_relay_mode(NOISE_RELAY_MODE);
      if(target_deg_total == 360){
        endless_noise_preparation_movement();
        
        // drive_to(endless_sim_start, user_rpm);
        // reached_goal(endless_sim_start, 2, 0, 15000);  
      }
      else{
        noise_preparation_movement();
        // if(cancelled == false){
        // drive_to(sim_mercy_end, user_rpm);
        // reached_goal(sim_mercy_end, 2, 0, 15000); 
        drive_and_check(sim_mercy_end, user_rpm, 0);

        }
      if(cancelled == false){
        Serial.println("NOISE_READY");
      } else{
        Serial.println("CANCEL");
        return;
        // cancelled = false;
      }
      
    }
    if(command == "NOISE_START"){
      if(target_deg_total == 360){
        endless_noise_movement();
      } else{
        noise_movement(); 
      }
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
        if(endless_poti){
          endless_elec_deg_movement();
        } else{
          elec_deg_movement();
        }
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
      // drive_to(ZERO_TICK, user_rpm);
      // reached_goal(ZERO_TICK, 2);
      drive_and_check(ZERO_TICK, user_rpm);

      all_relays_off();
      dxl.ledOff(DID);
      setLEDS(3);
      cancelled = false;
      linear_checked = false;
    }

    if(command == "NOISE_END"){
      // drive_to(ZERO_TICK, user_rpm);
      // reached_goal(ZERO_TICK, 2);
      drive_and_check(ZERO_TICK, user_rpm);
      all_relays_off();
      dxl.ledOff(DID);
      setLEDS(2);
      cancelled = false;
      linear_checked = false;
    }

    if(command == "LIN_END"){
      // drive_to(ZERO_TICK, user_rpm);
      // reached_goal(ZERO_TICK, 2);
      drive_and_check(ZERO_TICK, user_rpm);
      all_relays_off();
      dxl.ledOff(DID);
      setLEDS(2);
      cancelled = false;
      linear_checked = false;
    }

    if(command == "FAULT_LED"){
      setLEDS(2);
    }

    if(command == "ZERO"){
      measurements_init();
      go_zero();
      setLEDS(3);
    } 

    if(command == "GOTO"){
      measurements_init();
      go_to();
      setLEDS(3);
    } 

    if(command == "WHERE"){
      measurements_init();
      show_cur_pos();
      setLEDS(3);
    }

    if(command == "TESTER"){
      tester();
    }
    
  }
}
